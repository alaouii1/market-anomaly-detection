"""
=============================================================================
REAL-TIME ANOMALY DETECTION - TWO APPROACHES
=============================================================================

This consumer implements TWO types of anomaly detection:

1. PER-CANDLE DETECTION (Point-based, matches batch processing)
   - Applies Z-Score to individual candles as they arrive
   - Detects: "Is THIS specific candle anomalous?"
   - Uses: return, log_return, price_range features
   - Consensus: 2+ features flagged = anomaly
   - Output: streaming_candle_anomalies/

2. WINDOW DETECTION (Aggregate-based, period volatility)
   - Sliding 1-hour windows, updated every 1 minute
   - Detects: "Is this TIME PERIOD volatile?"
   - Uses: window statistics (avg, std, max)
   - Consensus: 2+ window metrics flagged = anomaly
   - Output: streaming_window_anomalies/

Both approaches are valid for real-time monitoring:
- Candle detection: Immediate alerts on unusual individual candles
- Window detection: Identifies sustained volatile periods

This matches our batch processing methodology while adding real-time
sliding window analysis for period-based monitoring.
=============================================================================
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, abs as abs_, when, lit, round as round_,
    log, current_timestamp, concat_ws, window, mean, stddev, max, last
)
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, LongType,
    IntegerType, BooleanType
)
import json
import os

# =============================================================================
# CONFIGURATION
# =============================================================================

KAFKA_BOOTSTRAP_SERVERS = "broker:9093"
KAFKA_TOPIC = "crypto-candles"
CHECKPOINT_DIR = "/tmp/spark-checkpoint/anomaly-detection-v2"
OUTPUT_PATH = "/home/jovyan/work/data/results/streaming_anomalies"


# =============================================================================
# MODEL PARAMETERS (Dynamic Load)
# =============================================================================

def load_model_params(file_path="models/model_params.json"):
    """Load model parameters from JSON file."""
    if not os.path.exists(file_path):
        print(f"⚠️ WARNING: Config file not found at {file_path}")
        print("   Using fallback/default values (NOT RECOMMENDED for production)")
        return None
        
    try:
        with open(file_path, 'r') as f:
            params = json.load(f)
        print(f"✅ Loaded model parameters from {file_path}")
        print(f"   Created: {params.get('_created', 'Unknown date')}")
        return params
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return None

# Load params
PARAMS = load_model_params()

# Set globals from loaded params or fallbacks
if PARAMS:
    # Z-Score Stats
    ZSCORE_STATS = PARAMS["zscore"]["statistics"]
    ZSCORE_THRESHOLD = PARAMS["zscore"]["threshold"]
    
    # Simplified Thresholds from 'streaming_simplified' section
    # If not present, derive from zscore stats roughly
    simple = PARAMS.get("streaming_simplified", {})
    VOLUME_SPIKE_THRESHOLD = simple.get("volume_spike_threshold_pct", 200.0)
    VOLATILITY_THRESHOLD = simple.get("price_range_threshold_pct", 1.5)
    
    # Consensus
    MIN_CONSENSUS_VOTES = PARAMS["consensus"]["min_votes"]
else:
    # FALLBACKS (The old hardcoded values)
    ZSCORE_THRESHOLD = 3.0
    ZSCORE_STATS = {
        "return": {"mean": 0.0034, "std": 0.3741},
        "log_return": {"mean": 0.0027, "std": 0.3744},
        "price_range": {"mean": 0.4972, "std": 0.3956}
    }
    VOLUME_SPIKE_THRESHOLD = 200.0
    VOLATILITY_THRESHOLD = 1.5
    MIN_CONSENSUS_VOTES = 2


# =============================================================================
# SCHEMA
# =============================================================================

candle_schema = StructType([
    StructField("symbol", StringType(), True),
    StructField("interval", StringType(), True),
    StructField("open_time", LongType(), True),
    StructField("close_time", LongType(), True),
    StructField("datetime", StringType(), True),
    StructField("open", DoubleType(), True),
    StructField("high", DoubleType(), True),
    StructField("low", DoubleType(), True),
    StructField("close", DoubleType(), True),
    StructField("volume", DoubleType(), True),
    StructField("quote_volume", DoubleType(), True),
    StructField("taker_buy_volume", DoubleType(), True),
    StructField("taker_buy_quote_volume", DoubleType(), True),
    StructField("trades", IntegerType(), True),
    StructField("is_closed", BooleanType(), True),
    StructField("received_at", StringType(), True),
])


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 70)
    print("REAL-TIME ANOMALY DETECTION SYSTEM")
    print("=" * 70)
    print()
    print("Models loaded from batch training:")
    print(f"  • Z-Score: threshold = {ZSCORE_THRESHOLD} (using batch mean/std)")
    print(f"  • Volume Spike: threshold = {VOLUME_SPIKE_THRESHOLD}%")
    print(f"  • Volatility: threshold = {VOLATILITY_THRESHOLD}%")
    print(f"  • Consensus: {MIN_CONSENSUS_VOTES}+ models agree = ANOMALY")
    print()
    
    # =========================================================================
    # STEP 1: SPARK SESSION
    # =========================================================================
    print("[1/6] Creating Spark session...")
    
    spark = SparkSession.builder \
        .appName("RealTimeAnomalyDetection") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    print(f"      ✅ Spark {spark.version}")
    
    # =========================================================================
    # STEP 2: KAFKA SOURCE
    # =========================================================================
    print("[2/6] Connecting to Kafka...")
    
    kafka_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", KAFKA_TOPIC) \
        .option("startingOffsets", "latest") \
        .option("failOnDataLoss", "false") \
        .load()
    
    print(f"      ✅ Connected to {KAFKA_TOPIC}")
    
    # =========================================================================
    # STEP 3: PARSE JSON
    # =========================================================================
    print("[3/6] Parsing JSON...")
    
    parsed_df = kafka_df \
        .selectExpr("CAST(value AS STRING) as json") \
        .select(from_json(col("json"), candle_schema).alias("data")) \
        .select("data.*") \
        .withColumn("timestamp", (col("close_time") / 1000).cast("timestamp"))
    
    print("      ✅ Schema applied & Timestamp parsed")
    
    # 1. Base Features
    base_df = parsed_df \
        .withColumn("return", ((col("close") - col("open")) / col("open")) * 100) \
        .withColumn("price_range", ((col("high") - col("low")) / col("low")) * 100)

    # =========================================================================
    # STEP 4: PER-CANDLE ANOMALY DETECTION (matches batch methodology)
    # =========================================================================
    print("[4/6] Calculating per-candle features & anomalies...")
    print(f"      Using Z-Score threshold: {ZSCORE_THRESHOLD}")

    # Calculate all features
    features_df = base_df \
        .withColumn("log_return", log((col("close") / col("open"))) * 100) \
        .withColumn("return_zscore",
            (col("return") - lit(ZSCORE_STATS["return"]["mean"])) / lit(ZSCORE_STATS["return"]["std"])
        ) \
        .withColumn("log_return_zscore",
            (col("log_return") - lit(ZSCORE_STATS["log_return"]["mean"])) / lit(ZSCORE_STATS["log_return"]["std"])
        ) \
        .withColumn("price_range_zscore",
            (col("price_range") - lit(ZSCORE_STATS["price_range"]["mean"])) / lit(ZSCORE_STATS["price_range"]["std"])
        )

    # Per-candle anomaly detection (Z-Score method from batch)
    candle_anomalies = features_df \
        .withColumn("anomaly_return", when(abs_(col("return_zscore")) > ZSCORE_THRESHOLD, 1).otherwise(0)) \
        .withColumn("anomaly_log_return", when(abs_(col("log_return_zscore")) > ZSCORE_THRESHOLD, 1).otherwise(0)) \
        .withColumn("anomaly_price_range", when(abs_(col("price_range_zscore")) > ZSCORE_THRESHOLD, 1).otherwise(0)) \
        .withColumn("candle_votes",
            col("anomaly_return") + col("anomaly_log_return") + col("anomaly_price_range")
        ) \
        .withColumn("is_candle_anomaly", when(col("candle_votes") >= 2, True).otherwise(False))

    # Output candle anomalies to separate stream
    candle_output = candle_anomalies.select(
        col("timestamp"),
        col("symbol"),
        col("open"),
        col("high"),
        col("low"),
        col("close"),
        col("volume"),
        col("return"),
        col("log_return"),
        col("price_range"),
        col("return_zscore"),
        col("log_return_zscore"),
        col("price_range_zscore"),
        col("candle_votes"),
        col("is_candle_anomaly")
    )
    
    # =========================================================================
    # STEP 5: SLIDING WINDOW ANALYSIS
    # =========================================================================
    print("[5/6] Sliding window analysis & Consensus Voting...")
    
    # Define Window
    window_duration = "1 hour"
    slide_duration = "1 minute"
    print(f"      Window: {window_duration}, Slide: {slide_duration}")
    
    windowed_agg = base_df \
        .withWatermark("timestamp", "10 minutes") \
        .groupBy(
            window(col("timestamp"), window_duration, slide_duration),
            col("symbol")
        ) \
        .agg(
            # Aggregated Stats
            round_(mean("return"), 4).alias("avg_return"),
            round_(stddev("return"), 4).alias("std_return"),
            round_(mean("price_range"), 4).alias("avg_range"),
            round_(max("price_range"), 4).alias("max_range"),
            round_(mean("volume"), 2).alias("avg_volume"),
            
            # Current/Last values
            last("close").alias("close"),
            last("timestamp").alias("last_ts")
        )

    # Apply ML Models (Dynamic Thresholds)
    model_df = windowed_agg \
        .withColumn("volatility_anomaly", 
            # Compare window std to historical std (from batch)
            when(col("std_return") > (lit(ZSCORE_STATS["return"]["std"]) * 2.0), 1).otherwise(0)
        ) \
        .withColumn("range_anomaly",
            # Max range in window exceeds threshold
            when(col("max_range") > lit(VOLATILITY_THRESHOLD), 1).otherwise(0)
        ) \
        .withColumn("volume_anomaly",
            # Volume spike detection
            when(col("avg_volume") > (lit(ZSCORE_STATS["volume_change"]["mean"]) + 
                                       lit(ZSCORE_STATS["volume_change"]["std"]) * 2), 1).otherwise(0)
        )

    # Calculate Consensus
    consensus_df = model_df \
        .withColumn("total_votes", 
            col("volatility_anomaly") + col("range_anomaly") + col("volume_anomaly")
        ) \
        .withColumn("is_anomaly", 
            when(col("total_votes") >= MIN_CONSENSUS_VOTES, True).otherwise(False)
        ) \
        .withColumn("confidence",
            when(col("total_votes") >= 3, "HIGH")
            .when(col("total_votes") == 2, "MEDIUM")
            .when(col("total_votes") == 1, "LOW")
            .otherwise("NONE")
        ) \
        .withColumn("anomaly_reasons",
            concat_ws(" | ",
                when(col("volatility_anomaly") == 1, "VOLATILITY").otherwise(lit("")),
                when(col("range_anomaly") == 1, "RANGE").otherwise(lit("")),
                when(col("volume_anomaly") == 1, "VOLUME").otherwise(lit(""))
            )
        )

    output_df = consensus_df \
        .select(
            # Window results
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            col("symbol"),
            col("close"),
            col("avg_return"),
            col("std_return"),
            col("max_range"),
            col("avg_volume"),
            
            # Models
            col("volatility_anomaly"),
            col("range_anomaly"),
            col("volume_anomaly"),
            
            # Consensus
            col("total_votes"),
            col("is_anomaly"),
            col("confidence"),
            col("anomaly_reasons")
        )

    # =========================================================================
    # STEP 6: START DUAL STREAMS
    # =========================================================================
    print("[6/6] Starting dual output streams...")
    
    CANDLE_ANOMALY_PATH = "/home/jovyan/work/data/results/streaming_candle_anomalies"
    WINDOW_ANOMALY_PATH = "/home/jovyan/work/data/results/streaming_window_anomalies"
    print(f"      Candle anomalies → {CANDLE_ANOMALY_PATH}")
    print(f"      Window anomalies → {WINDOW_ANOMALY_PATH}")

    # 1. Output Candle Anomalies (APPEND mode)
    # coalesce(1) attempts to merge partitions to write fewer files
    candle_query = candle_output \
        .coalesce(1) \
        .writeStream \
        .outputMode("append") \
        .format("csv") \
        .option("path", CANDLE_ANOMALY_PATH) \
        .option("header", "true") \
        .option("checkpointLocation", CHECKPOINT_DIR + "_candles") \
        .trigger(processingTime="5 seconds") \
        .start()

    # 2. Output Window Anomalies (APPEND mode)
    window_query = output_df \
        .coalesce(1) \
        .writeStream \
        .outputMode("append") \
        .format("csv") \
        .option("path", WINDOW_ANOMALY_PATH) \
        .option("header", "true") \
        .option("checkpointLocation", CHECKPOINT_DIR + "_windows") \
        .trigger(processingTime="10 seconds") \
        .start()
    
    # 3. Console Output (UPDATE mode for monitoring)
    print("\n" + "="*70)
    print("🚀 STREAMING STARTED (DUAL MODE)")
    print("="*70)
    
    console_query = output_df \
        .writeStream \
        .outputMode("update") \
        .format("console") \
        .option("truncate", "false") \
        .option("numRows", 10) \
        .option("checkpointLocation", CHECKPOINT_DIR + "_console") \
        .trigger(processingTime="10 seconds") \
        .start()
    
    try:
        spark.streams.awaitAnyTermination()
    except KeyboardInterrupt:
        print("\n⚠️ Shutting down gracefully...")


if __name__ == "__main__":
    main()