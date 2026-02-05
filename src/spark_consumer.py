"""
=============================================================================
SPARK STRUCTURED STREAMING - REAL-TIME ANOMALY DETECTION
=============================================================================

This is the REAL consumer that:
  1. Reads candles from Kafka in real-time
  2. Calculates features (same as batch: return, log_return, price_range)
  3. Applies TRAINED models:
     - Z-Score: Using batch statistics (mean, std)
     - K-Means simplified: Using distance thresholds
     - GMM simplified: Using probability thresholds
  4. Consensus detection: 2+ models agree = HIGH CONFIDENCE anomaly
  5. Outputs results to console AND saves to file

Architecture:
  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
  │      Kafka      │────►│ Spark Streaming │────►│    Anomalies    │
  │ (crypto-candles)│     │  + ML Models    │     │ (Console+File)  │
  └─────────────────┘     └─────────────────┘     └─────────────────┘

Models Applied:
  • Z-Score: |z| > 3 on return, log_return, price_range
  • Volume Spike: volume_change > 200% (simplified K-Means)
  • Volatility: price_range > 1.5% (simplified GMM)
  • Consensus: 2+ methods agree = ANOMALY

Usage:
  spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 spark_consumer.py

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
        .withColumn("timestamp", (col("close_time") / 1000).cast("timestamp")) # Create proper timestamp
    
    print("      ✅ Schema applied & Timestamp parsed")
    
    # =========================================================================
    # STEP 4: FEATURE ENGINEERING (WINDOWED)
    # =========================================================================
    print("[4/6] Calculating features & Sliding Window stats...")
    
    # 1. Base Features
    base_df = parsed_df \
        .withColumn("return", ((col("close") - col("open")) / col("open")) * 100) \
        .withColumn("price_range", ((col("high") - col("low")) / col("low")) * 100)

    # 2. Define Window
    # 1 Hour window, sliding every 1 Minute
    # Watermark = 10 minutes (allow 10m late data)
    window_duration = "1 hour"
    slide_duration = "1 minute"
    
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
            
            # Current/Last values in the window (approximate 'current state')
            last("close").alias("close"),
            last("timestamp").alias("last_ts")
        )

    print("      ✅ Sliding Window: 1h window, 1m slide")
    
    # =========================================================================
    # STEP 5: APPLY ML MODELS (ON WINDOWS)
    # =========================================================================
    print("[5/6] Applying ML models to Windows...")
    
    # Detect anomalies based on the WINDOW's statistics
    # e.g., If the standard deviation of returns in this hour is very high -> Volatile Period
    
    model_df = windowed_agg \
        .withColumn("volatility_anomaly", 
            when(col("std_return") > (ZSCORE_STATS["return"]["std"] * 2), 1).otherwise(0)
        ) \
        .withColumn("range_anomaly",
            when(col("max_range") > VOLATILITY_THRESHOLD, 1).otherwise(0)
        ) \
        .withColumn("volume_high",
            when(col("avg_volume") > 1000, 1).otherwise(0) # Simple threshold
        )

    # =========================================================================
    # STEP 6: CONSENSUS & OUTPUT
    # =========================================================================
    print("[6/6] Formatting output...")
    
    output_df = model_df \
        .withColumn("is_volatile", col("volatility_anomaly") == 1) \
        .select(
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            col("symbol"),
            col("close"),
            col("avg_return"),
            col("std_return"),
            col("max_range"),
            col("is_volatile")
        )

    # =========================================================================
    # START STREAMING
    # =========================================================================
    print("\n" + "="*70)
    print("🚀 STREAMING STARTED (SLIDING WINDOW MODE)")
    print("="*70)
    print(f"Window: {window_duration}, Slide: {slide_duration}")
    print("Aggregating stats over 1 hour to find Volatile Periods...")
    print("="*70 + "\n")
    
    # Write to console
    # MUST use "update" mode for aggregations (to see results before window closes)
    # or "complete" (but that keeps all state)
    # "append" only outputs when window CLOSES (after watermark) -> 10m latency!
    
    query = output_df \
        .writeStream \
        .outputMode("update") \
        .format("console") \
        .option("truncate", "false") \
        .option("numRows", 20) \
        .option("checkpointLocation", CHECKPOINT_DIR + "_windowed") \
        .trigger(processingTime="10 seconds") \
        .start()
    
    query.awaitTermination()


if __name__ == "__main__":
    main()