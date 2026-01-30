# 📖 Glossary

All terms and concepts used in this project, organized by category.

---

## 📈 Trading / Market Terms

| Term | Definition |
|------|------------|
| **OHLCV** | Open, High, Low, Close, Volume - the 5 values in a candlestick |
| **Candlestick** | Visual representation of price movement over a time period |
| **Open** | Price at the start of the period |
| **High** | Highest price during the period |
| **Low** | Lowest price during the period |
| **Close** | Price at the end of the period |
| **Volume** | Amount of asset traded during the period |
| **Interval** | Duration of each candle (1m, 5m, 1h, 1d, etc.) |
| **Volatility** | How much price fluctuates (high volatility = chaotic) |
| **Bull market** | Prices going up |
| **Bear market** | Prices going down |
| **Whale** | Large trader who can move markets |
| **Spot market** | Buy/sell for immediate delivery |

---

## 🔌 API / Data Collection Terms

| Term | Definition |
|------|------------|
| **API** | Application Programming Interface - way to get data from a service |
| **REST API** | Request → Response → Connection closes |
| **WebSocket** | Connection stays open, server pushes data in real-time |
| **Endpoint** | Specific URL to get specific data |
| **Rate limit** | Maximum requests allowed per time period |
| **JSON** | Data format: `{"key": "value"}` |
| **CSV** | Comma-Separated Values - simple table format |

---

## 🧹 Preprocessing Terms

| Term | Definition |
|------|------------|
| **Preprocessing** | Cleaning and preparing data before ML |
| **Feature** | A property/column the model learns from |
| **Feature Engineering** | Creating new useful columns from existing data |
| **Rolling Window** | Calculation using last N rows (sliding window) |
| **NaN** | Not a Number - missing value |
| **Normalization** | Scaling values to a standard range (e.g., 0-1) |
| **Standardization** | Scaling to mean=0, std=1 |

---

## 📊 Statistics Terms

| Term | Definition |
|------|------------|
| **Mean (μ)** | Average value |
| **Standard Deviation (σ)** | How spread out values are from the mean |
| **Variance** | Standard deviation squared |
| **Z-Score** | How many standard deviations from the mean: `(x - μ) / σ` |
| **Percentile** | Value below which X% of data falls (e.g., 95th percentile) |
| **Quantile** | Same as percentile but expressed as decimal (0.95) |
| **Normal Distribution** | Bell curve - most values near mean |
| **Outlier** | Value far from the rest of the data |

---

## 🤖 Machine Learning Terms

| Term | Definition |
|------|------------|
| **ML (Machine Learning)** | Computer learns patterns from data |
| **Model** | Algorithm + learned parameters |
| **Training** | Teaching the model using data |
| **Prediction** | Model's output for new data |
| **Feature Vector** | All features combined into one array |
| **Label** | The answer/category we're trying to predict |
| **Supervised Learning** | Learning from labeled examples |
| **Unsupervised Learning** | Finding patterns without labels |
| **Semi-supervised** | Using unlabeled data to generate labels, then training |
| **Classification** | Predicting categories (anomaly vs normal) |
| **Clustering** | Grouping similar data points |
| **Overfitting** | Model memorizes training data, fails on new data |

---

## 🎯 Anomaly Detection Terms

| Term | Definition |
|------|------------|
| **Anomaly** | Unusual/abnormal data point |
| **Outlier** | Same as anomaly |
| **Normal** | Typical/expected data point |
| **Threshold** | Cutoff value to decide anomaly vs normal |
| **Contamination** | Expected percentage of anomalies in data |
| **Consensus** | Agreement between multiple methods |
| **False Positive** | Normal point incorrectly flagged as anomaly |
| **False Negative** | Anomaly missed (not flagged) |

---

## 🔥 Spark / Big Data Terms

| Term | Definition |
|------|------------|
| **Apache Spark** | Distributed computing framework for Big Data |
| **PySpark** | Python interface for Spark |
| **Spark MLlib** | Spark's machine learning library |
| **DataFrame** | Distributed table (like pandas but scalable) |
| **SparkSession** | Entry point to all Spark functionality |
| **Transformation** | Operation that creates new DataFrame (lazy) |
| **Action** | Operation that returns a result (triggers computation) |
| **Lazy Evaluation** | Spark doesn't compute until you ask for results |
| **Partition** | Chunk of data processed on one machine |
| **Distributed** | Data/computation spread across multiple machines |
| **Scalable** | Can handle more data by adding more machines |

---

## 🧮 Algorithm-Specific Terms

### Z-Score
| Term | Definition |
|------|------------|
| **Z-Score** | `(value - mean) / std` - distance from mean in std units |
| **Threshold (3)** | Values with \|Z\| > 3 are in 0.3% most extreme |

### K-Means
| Term | Definition |
|------|------------|
| **K** | Number of clusters |
| **Centroid** | Center point of a cluster |
| **Cluster** | Group of similar data points |
| **Inertia** | Sum of distances from points to their centroids |
| **Elbow Method** | Technique to choose optimal K |

### Random Forest
| Term | Definition |
|------|------------|
| **Decision Tree** | Series of yes/no questions leading to prediction |
| **Random Forest** | Many decision trees voting together |
| **Ensemble** | Combining multiple models |
| **Feature Importance** | Which features matter most for prediction |
| **numTrees** | Number of trees in the forest |
| **maxDepth** | Maximum depth of each tree |

### GMM (Gaussian Mixture Model)
| Term | Definition |
|------|------------|
| **Gaussian** | Normal distribution (bell curve) |
| **Mixture Model** | Data modeled as combination of distributions |
| **Component** | One Gaussian distribution in the mixture |
| **Probability** | How likely a point belongs to the data |
| **Soft Assignment** | Point has probability for each cluster (vs hard 0/1) |

---

## 🐳 Docker Terms

| Term | Definition |
|------|------------|
| **Docker** | Tool to run applications in isolated containers |
| **Container** | Isolated environment with everything needed to run app |
| **Image** | Template to create containers |
| **docker-compose** | Tool to define and run multi-container apps |
| **Volume** | Shared folder between container and host |
| **Port** | Network door (e.g., 8888 for Jupyter) |

---

## 📓 Jupyter Terms

| Term | Definition |
|------|------------|
| **Jupyter Notebook** | Interactive document with code + text + output |
| **Cell** | One block of code or text |
| **Kernel** | The engine that runs your code |
| **Markdown** | Simple text formatting (# header, **bold**, etc.) |

---

## 📐 Evaluation Metrics

| Term | Definition |
|------|------------|
| **Accuracy** | % of correct predictions |
| **Precision** | Of predicted anomalies, how many were real? |
| **Recall** | Of real anomalies, how many did we catch? |
| **F1-Score** | Balance of precision and recall |
| **Confusion Matrix** | Table showing TP, TN, FP, FN |
| **TP (True Positive)** | Correctly identified anomaly |
| **TN (True Negative)** | Correctly identified normal |
| **FP (False Positive)** | Normal flagged as anomaly (false alarm) |
| **FN (False Negative)** | Anomaly missed |

---

## 🔗 Project-Specific Terms

| Term | Definition |
|------|------------|
| **return** | Price change % from previous hour |
| **log_return** | Natural log of price ratio (academic standard) |
| **volatility_24h** | Standard deviation of returns over 24 hours |
| **volume_change** | Volume change % from previous hour |
| **volume_ratio** | Current volume / 24h average volume |
| **price_range** | (high - low) / close × 100 |
| **VectorAssembler** | Spark tool to combine columns into feature vector |
| **StandardScaler** | Spark tool to normalize features |
| **Consensus Voting** | Multiple methods must agree for confidence |

---

*Last updated: January 30, 2026*
