"""
BATCH MODEL TRAINING & SAVING
Run this ONCE to train all models on historical data and save them for streaming use.

This creates:
- models/zscore_params.json (mean, std for each feature)
- models/kmeans_model/ (Spark MLlib KMeans)
- models/rf_model/ (Spark MLlib RandomForest)
- models/gmm_model/ (Spark MLlib GMM)
- models/scaler_model/ (StandardScaler for feature normalization)
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, mean, stddev, lit
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.clustering import KMeans, GaussianMixture
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml import Pipeline
import json
import os

# Initialize Spark
spark = SparkSession.builder \
    .appName("TrainAnomalyModels") \
    .config("spark.driver.memory", "4g") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

print("="*60)
print("STEP 1: LOADING AND PREPARING DATA")
print("="*60)

# Load your preprocessed data
# For 1-minute data, use the output from preprocess_1m_data.py
DATA_PATH = "data/processed/BTCUSDT_1m_features.csv"

# Alternative: Load multiple symbols
# DATA_PATHS = ["data/processed/BTCUSDT_1m_features.csv", "data/processed/ETHUSDT_1m_features.csv"]

try:
    df = spark.read.csv(DATA_PATH, header=True, inferSchema=True)
    print(f"Loaded {df.count()} rows from {DATA_PATH}")
    
    # If you want to load multiple files:
    # df = spark.read.csv("data/processed/*_1m_features.csv", header=True, inferSchema=True)
    
except Exception as e:
    print(f"ERROR loading data: {e}")
    print("\nMake sure you've run:")
    print("  1. python collect_1m_data.py")
    print("  2. python preprocess_1m_data.py")
    print("\nCreating sample data for demonstration...")
    
    from pyspark.sql.functions import rand, randn
    df = spark.range(10000).select(
        col("id").alias("timestamp"),
        (50000 + randn() * 1000).alias("close"),
        (1000000 + randn() * 100000).alias("volume"),
        (randn() * 0.002).alias("return"),          # Smaller for 1-min data
        (randn() * 0.002).alias("log_return"),      # Smaller for 1-min data
        (0.001 + rand() * 0.003).alias("volatility"),  # Renamed from volatility_24h
        (randn() * 0.5).alias("volume_change"),
        (1 + randn() * 0.3).alias("volume_ratio"),
        (0.0005 + rand() * 0.002).alias("price_range")  # Smaller for 1-min data
    )

# Feature columns for ML models
# Note: "volatility" instead of "volatility_24h" to match preprocess_1m_data.py output
FEATURE_COLS = ["return", "log_return", "volatility", "volume_change", "volume_ratio", "price_range"]

# Create models directory
os.makedirs("models", exist_ok=True)

print("\n" + "="*60)
print("STEP 2: TRAINING Z-SCORE MODEL (Statistical Parameters)")
print("="*60)

# Calculate mean and std for each feature
zscore_params = {}
for feature in FEATURE_COLS:
    stats = df.select(
        mean(col(feature)).alias("mean"),
        stddev(col(feature)).alias("std")
    ).collect()[0]
    zscore_params[feature] = {
        "mean": float(stats["mean"]) if stats["mean"] else 0.0,
        "std": float(stats["std"]) if stats["std"] else 1.0
    }
    print(f"  {feature}: mean={zscore_params[feature]['mean']:.6f}, std={zscore_params[feature]['std']:.6f}")

# Save Z-Score parameters
with open("models/zscore_params.json", "w") as f:
    json.dump(zscore_params, f, indent=2)
print("✅ Z-Score parameters saved to models/zscore_params.json")

print("\n" + "="*60)
print("STEP 3: PREPARING FEATURES FOR ML MODELS")
print("="*60)

# Assemble features into vector
assembler = VectorAssembler(inputCols=FEATURE_COLS, outputCol="features_raw")

# Scale features (important for K-Means and GMM)
scaler = StandardScaler(inputCol="features_raw", outputCol="features", withMean=True, withStd=True)

# Build preprocessing pipeline
preprocessing_pipeline = Pipeline(stages=[assembler, scaler])
preprocessing_model = preprocessing_pipeline.fit(df)
df_scaled = preprocessing_model.transform(df)

# Save the preprocessing pipeline (scaler)
preprocessing_model.write().overwrite().save("models/preprocessing_model")
print("✅ Preprocessing pipeline saved to models/preprocessing_model")

print("\n" + "="*60)
print("STEP 4: TRAINING K-MEANS MODEL")
print("="*60)

# K-Means clustering
kmeans = KMeans(k=3, featuresCol="features", predictionCol="kmeans_cluster", seed=42)
kmeans_model = kmeans.fit(df_scaled)

# Print cluster centers
print("Cluster centers:")
for i, center in enumerate(kmeans_model.clusterCenters()):
    print(f"  Cluster {i}: {center[:3]}...")  # Show first 3 dimensions

# Save K-Means model
kmeans_model.write().overwrite().save("models/kmeans_model")
print("✅ K-Means model saved to models/kmeans_model")

# Determine which cluster is the "anomaly" cluster (smallest one)
df_with_kmeans = kmeans_model.transform(df_scaled)
cluster_counts = df_with_kmeans.groupBy("kmeans_cluster").count().collect()
anomaly_cluster = min(cluster_counts, key=lambda x: x["count"])["kmeans_cluster"]
print(f"Anomaly cluster (smallest): {anomaly_cluster}")

# Save anomaly cluster info
with open("models/kmeans_anomaly_cluster.json", "w") as f:
    json.dump({"anomaly_cluster": int(anomaly_cluster)}, f)

print("\n" + "="*60)
print("STEP 5: TRAINING GMM MODEL")
print("="*60)

# Gaussian Mixture Model
gmm = GaussianMixture(k=3, featuresCol="features", predictionCol="gmm_cluster", 
                       probabilityCol="gmm_probability", seed=42)
gmm_model = gmm.fit(df_scaled)

# Save GMM model
gmm_model.write().overwrite().save("models/gmm_model")
print("✅ GMM model saved to models/gmm_model")

# Determine anomaly cluster for GMM
df_with_gmm = gmm_model.transform(df_scaled)
gmm_cluster_counts = df_with_gmm.groupBy("gmm_cluster").count().collect()
gmm_anomaly_cluster = min(gmm_cluster_counts, key=lambda x: x["count"])["gmm_cluster"]

with open("models/gmm_anomaly_cluster.json", "w") as f:
    json.dump({"anomaly_cluster": int(gmm_anomaly_cluster)}, f)
print(f"GMM anomaly cluster (smallest): {gmm_anomaly_cluster}")

print("\n" + "="*60)
print("STEP 6: TRAINING RANDOM FOREST MODEL")
print("="*60)

# For Random Forest, we need labels. We'll use Z-Score anomalies as training labels
# This is semi-supervised: use statistical anomalies to train the classifier

from pyspark.sql.functions import when, abs as spark_abs

# Create Z-Score based labels (anomaly if any feature has |z| > 3)
df_labeled = df_scaled
for feature in FEATURE_COLS:
    z_col = f"z_{feature}"
    df_labeled = df_labeled.withColumn(
        z_col,
        spark_abs((col(feature) - zscore_params[feature]["mean"]) / zscore_params[feature]["std"])
    )

# Label: 1 if any z-score > 3, else 0
z_cols = [f"z_{f}" for f in FEATURE_COLS]
anomaly_condition = None
for z_col in z_cols:
    if anomaly_condition is None:
        anomaly_condition = col(z_col) > 3
    else:
        anomaly_condition = anomaly_condition | (col(z_col) > 3)

df_labeled = df_labeled.withColumn("label", when(anomaly_condition, 1.0).otherwise(0.0))

label_counts = df_labeled.groupBy("label").count().collect()
print(f"Training labels: {dict((int(r['label']), r['count']) for r in label_counts)}")

# Train Random Forest
rf = RandomForestClassifier(
    featuresCol="features",
    labelCol="label",
    predictionCol="rf_prediction",
    probabilityCol="rf_probability",
    numTrees=100,
    maxDepth=10,
    seed=42
)
rf_model = rf.fit(df_labeled)

# Save Random Forest model
rf_model.write().overwrite().save("models/rf_model")
print("✅ Random Forest model saved to models/rf_model")

# Print feature importances
print("\nFeature Importances:")
for i, importance in enumerate(rf_model.featureImportances.toArray()):
    print(f"  {FEATURE_COLS[i]}: {importance:.4f}")

print("\n" + "="*60)
print("STEP 7: SAVING FEATURE CONFIGURATION")
print("="*60)

# Save feature column configuration
config = {
    "feature_columns": FEATURE_COLS,
    "zscore_threshold": 3.0,
    "consensus_threshold": 2  # Need 2+ models to agree for high-confidence anomaly
}

with open("models/config.json", "w") as f:
    json.dump(config, f, indent=2)
print("✅ Configuration saved to models/config.json")

print("\n" + "="*60)
print("ALL MODELS TRAINED AND SAVED!")
print("="*60)
print("""
Models saved in ./models/:
  - zscore_params.json        (Z-Score statistics)
  - preprocessing_model/      (VectorAssembler + StandardScaler)
  - kmeans_model/             (K-Means clustering)
  - kmeans_anomaly_cluster.json
  - gmm_model/                (Gaussian Mixture Model)
  - gmm_anomaly_cluster.json
  - rf_model/                 (Random Forest classifier)
  - config.json               (Feature configuration)

Now run spark_streaming_consumer.py to use these models in real-time!
""")

spark.stop()