"""
SPARK STREAMING CONSUMER - REAL ML MODELS
==========================================
This is the REAL DEAL - loads actual trained models and uses them for predictions.

Flow:
1. Kafka → Read streaming data
2. Calculate features (already done by producer, or recalculate)
3. Load REAL trained models (K-Means, GMM, Random Forest)
4. Apply each model for prediction
5. Consensus voting (2+ models agree = high confidence anomaly)
6. Output results

Models Used:
- Z-Score: Statistical anomaly (|z| > 3 from batch statistics)
- K-Means: Cluster-based (assigned to anomaly cluster)
- GMM: Probability-based (assigned to anomaly cluster)
- Random Forest: Classifier trained on batch anomalies
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, when, lit, abs as spark_abs,
    current_timestamp, window, count, sum as spark_sum,
    udf, struct
)
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, 
    BooleanType, LongType, IntegerType, TimestampType
)
from pyspark.ml import PipelineModel
from pyspark.ml.clustering import KMeansModel, GaussianMixtureModel
from pyspark.ml.classification import RandomForestClassificationModel
from pyspark.ml.feature import VectorAssembler
import json
import os

# ============================================================================
# CONFIGURATION
# ============================================================================

# Use "broker:9093" when running inside Docker (Jupyter container)
# Use "localhost:9092" when running on your laptop directly
KAFKA_BOOTSTRAP = "broker:9093"  # For Docker network
# KAFKA_BOOTSTRAP = "localhost:9092"  # Uncomment if running outside Docker

KAFKA_TOPIC = "crypto-candles"
MODELS_PATH = "models"  # Where trained models are saved
OUTPUT_PATH = "output/streaming_results"  # Where to save results

# Feature columns - must match what the models were trained on
# Using "volatility" (not "volatility_24h") to match 1-minute preprocessing
FEATURE_COLS = ["return", "log_return", "volatility", "volume_change", "volume_ratio", "price_range"]

# ============================================================================
# INITIALIZE SPARK
# ============================================================================

print("="*70)
print("SPARK STREAMING ANOMALY DETECTION - REAL ML MODELS")
print("="*70)

spark = SparkSession.builder \
    .appName("RealTimeAnomalyDetection") \
    .config("spark.sql.streaming.checkpointLocation", "/tmp/checkpoint") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# ============================================================================
# LOAD TRAINED MODELS
# ============================================================================

print("\n📦 LOADING TRAINED MODELS...")
print("-" * 50)

# 1. Load Z-Score parameters
print("Loading Z-Score parameters...")
with open(f"{MODELS_PATH}/zscore_params.json", "r") as f:
    zscore_params = json.load(f)
print(f"   ✅ Z-Score params loaded for {len(zscore_params)} features")

# 2. Load preprocessing pipeline (VectorAssembler + StandardScaler)
print("Loading preprocessing pipeline...")
preprocessing_model = PipelineModel.load(f"{MODELS_PATH}/preprocessing_model")
print("   ✅ Preprocessing pipeline loaded")

# 3. Load K-Means model
print("Loading K-Means model...")
kmeans_model = KMeansModel.load(f"{MODELS_PATH}/kmeans_model")
with open(f"{MODELS_PATH}/kmeans_anomaly_cluster.json", "r") as f:
    kmeans_anomaly_cluster = json.load(f)["anomaly_cluster"]
print(f"   ✅ K-Means loaded (anomaly cluster: {kmeans_anomaly_cluster})")

# 4. Load GMM model
print("Loading GMM model...")
gmm_model = GaussianMixtureModel.load(f"{MODELS_PATH}/gmm_model")
with open(f"{MODELS_PATH}/gmm_anomaly_cluster.json", "r") as f:
    gmm_anomaly_cluster = json.load(f)["anomaly_cluster"]
print(f"   ✅ GMM loaded (anomaly cluster: {gmm_anomaly_cluster})")

# 5. Load Random Forest model
print("Loading Random Forest model...")
rf_model = RandomForestClassificationModel.load(f"{MODELS_PATH}/rf_model")
print("   ✅ Random Forest loaded")

# 6. Load configuration
with open(f"{MODELS_PATH}/config.json", "r") as f:
    config = json.load(f)
ZSCORE_THRESHOLD = config.get("zscore_threshold", 3.0)
CONSENSUS_THRESHOLD = config.get("consensus_threshold", 2)

print(f"\n✅ ALL MODELS LOADED SUCCESSFULLY!")
print(f"   Z-Score threshold: {ZSCORE_THRESHOLD}")
print(f"   Consensus threshold: {CONSENSUS_THRESHOLD}+ models must agree")

# ============================================================================
# KAFKA STREAM SCHEMA
# ============================================================================

schema = StructType([
    StructField("timestamp", StringType(), True),
    StructField("event_time", LongType(), True),
    StructField("symbol", StringType(), True),
    StructField("open", DoubleType(), True),
    StructField("high", DoubleType(), True),
    StructField("low", DoubleType(), True),
    StructField("close", DoubleType(), True),
    StructField("volume", DoubleType(), True),
    StructField("is_closed", BooleanType(), True),
    StructField("return", DoubleType(), True),
    StructField("log_return", DoubleType(), True),
    StructField("volatility", DoubleType(), True),  # Changed from volatility_24h
    StructField("volume_change", DoubleType(), True),
    StructField("volume_ratio", DoubleType(), True),
    StructField("price_range", DoubleType(), True),
])

# ============================================================================
# READ FROM KAFKA
# ============================================================================

print("\n📡 CONNECTING TO KAFKA...")
print("-" * 50)

df_kafka = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
    .option("subscribe", KAFKA_TOPIC) \
    .option("startingOffsets", "latest") \
    .load()

# Parse JSON from Kafka
df_parsed = df_kafka \
    .selectExpr("CAST(value AS STRING) as json_str") \
    .select(from_json(col("json_str"), schema).alias("data")) \
    .select("data.*")

print(f"   ✅ Subscribed to topic: {KAFKA_TOPIC}")

# ============================================================================
# APPLY ML MODELS
# ============================================================================

def apply_all_models(batch_df, batch_id):
    """
    Apply all 4 trained models to each micro-batch.
    This is where the REAL ML happens!
    """
    if batch_df.count() == 0:
        return
    
    print(f"\n{'='*70}")
    print(f"PROCESSING BATCH {batch_id} - {batch_df.count()} records")
    print(f"{'='*70}")
    
    # Handle null values
    df = batch_df.na.fill(0.0, FEATURE_COLS)
    
    # -------------------------------------------------------------------------
    # MODEL 1: Z-SCORE (Statistical)
    # -------------------------------------------------------------------------
    print("\n🔹 Applying Z-Score model...")
    
    for feature in FEATURE_COLS:
        mean_val = zscore_params[feature]["mean"]
        std_val = zscore_params[feature]["std"]
        if std_val == 0:
            std_val = 1.0  # Avoid division by zero
        
        z_col = f"z_{feature}"
        df = df.withColumn(z_col, spark_abs((col(feature) - mean_val) / std_val))
    
    # Z-Score anomaly: any feature has |z| > threshold
    z_cols = [f"z_{f}" for f in FEATURE_COLS]
    zscore_condition = None
    for z_col in z_cols:
        if zscore_condition is None:
            zscore_condition = col(z_col) > ZSCORE_THRESHOLD
        else:
            zscore_condition = zscore_condition | (col(z_col) > ZSCORE_THRESHOLD)
    
    df = df.withColumn("zscore_anomaly", when(zscore_condition, 1).otherwise(0))
    
    # -------------------------------------------------------------------------
    # MODEL 2, 3, 4: K-MEANS, GMM, RANDOM FOREST (ML Models)
    # -------------------------------------------------------------------------
    print("🔹 Applying preprocessing (VectorAssembler + StandardScaler)...")
    df_features = preprocessing_model.transform(df)
    
    print("🔹 Applying K-Means model...")
    df_kmeans = kmeans_model.transform(df_features)
    df_kmeans = df_kmeans.withColumn(
        "kmeans_anomaly", 
        when(col("kmeans_cluster") == kmeans_anomaly_cluster, 1).otherwise(0)
    )
    
    print("🔹 Applying GMM model...")
    df_gmm = gmm_model.transform(df_kmeans)
    df_gmm = df_gmm.withColumn(
        "gmm_anomaly",
        when(col("gmm_cluster") == gmm_anomaly_cluster, 1).otherwise(0)
    )
    
    print("🔹 Applying Random Forest model...")
    df_rf = rf_model.transform(df_gmm)
    df_rf = df_rf.withColumn(
        "rf_anomaly",
        col("rf_prediction").cast(IntegerType())
    )
    
    # -------------------------------------------------------------------------
    # CONSENSUS VOTING
    # -------------------------------------------------------------------------
    print("🔹 Computing consensus...")
    
    df_final = df_rf.withColumn(
        "anomaly_votes",
        col("zscore_anomaly") + col("kmeans_anomaly") + col("gmm_anomaly") + col("rf_anomaly")
    ).withColumn(
        "is_anomaly",
        when(col("anomaly_votes") >= CONSENSUS_THRESHOLD, True).otherwise(False)
    ).withColumn(
        "confidence",
        when(col("anomaly_votes") >= 4, "VERY_HIGH")
        .when(col("anomaly_votes") >= 3, "HIGH")
        .when(col("anomaly_votes") >= 2, "MEDIUM")
        .otherwise("LOW")
    )
    
    # -------------------------------------------------------------------------
    # OUTPUT RESULTS
    # -------------------------------------------------------------------------
    
    # Select relevant columns for output
    result_cols = [
        "timestamp", "symbol", "close", "volume",
        "return", "log_return", "volatility", "volume_change", "volume_ratio", "price_range",
        "zscore_anomaly", "kmeans_anomaly", "gmm_anomaly", "rf_anomaly",
        "anomaly_votes", "is_anomaly", "confidence"
    ]
    
    df_output = df_final.select(result_cols)
    
    # Print summary
    total = df_output.count()
    anomalies = df_output.filter(col("is_anomaly") == True).count()
    
    print(f"\n📊 BATCH {batch_id} RESULTS:")
    print(f"   Total records: {total}")
    print(f"   Anomalies detected: {anomalies} ({100*anomalies/total:.1f}%)")
    
    # Show anomalies if any
    if anomalies > 0:
        print(f"\n🚨 ANOMALIES DETECTED:")
        df_output.filter(col("is_anomaly") == True).show(truncate=False)
    
    # Show sample of normal data
    print(f"\n📈 SAMPLE DATA:")
    df_output.select(
        "timestamp", "symbol", "close", 
        "zscore_anomaly", "kmeans_anomaly", "gmm_anomaly", "rf_anomaly",
        "anomaly_votes", "confidence"
    ).show(10, truncate=False)
    
    # Save to parquet (append mode)
    try:
        df_output.write \
            .mode("append") \
            .partitionBy("symbol") \
            .parquet(OUTPUT_PATH)
        print(f"   ✅ Results saved to {OUTPUT_PATH}")
    except Exception as e:
        print(f"   ⚠️ Could not save to parquet: {e}")


# ============================================================================
# START STREAMING
# ============================================================================

print("\n🚀 STARTING STREAM PROCESSING...")
print("-" * 50)
print(f"   Kafka topic: {KAFKA_TOPIC}")
print(f"   Models: Z-Score, K-Means, GMM, Random Forest")
print(f"   Consensus: {CONSENSUS_THRESHOLD}+ votes required")
print(f"   Output: {OUTPUT_PATH}")
print("\n⏳ Waiting for data from Kafka...")
print("   (Make sure kafka_producer.py is running!)")
print("-" * 50)

# Use foreachBatch to apply our custom model logic
query = df_parsed \
    .writeStream \
    .foreachBatch(apply_all_models) \
    .outputMode("update") \
    .trigger(processingTime="5 seconds") \
    .start()

# Keep the stream running
try:
    query.awaitTermination()
except KeyboardInterrupt:
    print("\n\n🛑 Stopping stream...")
    query.stop()
    spark.stop()
    print("✅ Stream stopped gracefully")