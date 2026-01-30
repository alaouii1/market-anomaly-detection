# 📅 Project Journal

---

## Session 1 - [27/01/2026]

### What We Did
- [x] Set up GitHub repository
- [x] Learned trading concepts (OHLCV, candles, etc.)
- [x] Tested Binance API with Postman and Python
- [x] Created data collection script
- [x] Collected 1000 candles for BTCUSDT and ETHUSDT
- [x] Saved data to CSV files

### What We Learned

#### Trading Concepts
- OHLCV = Open, High, Low, Close, Volume
- A candle summarizes price movement over a time period
- Interval = duration of each candle (1m, 1h, 1d, etc.)

#### Technical Concepts
- REST API = Request → Response → Connection closes
- WebSocket = Connection stays open, data pushed in real-time
- Pandas DataFrame = A table for data manipulation
- CSV = Simple file format for storing tabular data

### Files Created
```
market-anomaly-detection/
├── collect_historical.py      # Data collection script
├── data/
│   └── raw/
│       ├── BTCUSDT_1h.csv    # Bitcoin data (1000 candles)
│       └── ETHUSDT_1h.csv    # Ethereum data (1000 candles)
└── docs/
    ├── 00_GLOSSARY.md        # Definitions
    ├── 02_API_BINANCE.md     # API documentation
    └── 04_JOURNAL.md         # This file
```

### Data Collected
| Symbol | Rows | Date Range | Price Range |
|--------|------|------------|-------------|
| BTCUSDT | 1000 | Dec 17, 2025 → Jan 27, 2026 | $84,450 → $97,924 |
| ETHUSDT | 1000 | Dec 17, 2025 → Jan 27, 2026 | TBD |

### Problems Encountered
1. **403 Error in Postman** → Solved by using Python directly
2. **Understanding raw Binance data** → Learned it returns array of arrays, not JSON objects

---

## Session 2 - [28/01/2026]

### What We Did
- [x] Learned why raw prices can't be used for ML (meaningless without context)
- [x] Learned what preprocessing and feature engineering mean
- [x] Created 6 features for anomaly detection
- [x] Learned about rolling windows and standard deviation
- [x] Learned why we drop first 24 rows (NaN from rolling)
- [x] Learned what normalization is and why we do it later (in ML notebook)
- [x] Ran preprocessing notebook successfully
- [x] Generated processed data files

### What We Learned

#### Why Raw Prices Don't Work
- $86,626 alone is meaningless - is it high? low? normal?
- $1000 move means different things at different price levels
- We need RELATIVE features (percentages) that mean the same at any price

#### Preprocessing Concepts
- **Preprocessing** = Cleaning raw data before ML (like washing vegetables before cooking)
- **Feature** = A property the model learns from
- **Feature Engineering** = Creating new useful columns from existing data

#### The 6 Features We Created

| Feature | What It Measures | Why Useful |
|---------|------------------|------------|
| return | Price change this hour (%) | Detects sudden price jumps |
| log_return | Same, better math | Can be added across time, academic standard |
| volatility_24h | How chaotic last 24 hours | Detects unstable periods |
| volume_change | Volume change from last hour (%) | Detects sudden trading activity |
| volume_ratio | Volume vs 24h average | Detects abnormal volume (2.0 = double normal) |
| price_range | Price swing within the hour (%) | Catches volatility that return misses |

#### Statistical Concepts
- **Standard Deviation (std)** = How spread out values are from the mean
- **Rolling Window** = Sliding calculation using last N rows
- **NaN** = Missing value, ML models crash on these

#### Why Normalize Later (Not Now)
- Not all models need normalization (Isolation Forest doesn't)
- Original values are easier to interpret (-2.5% vs -1.87)
- Standard practice: normalize as part of ML pipeline

### Files Created
```
market-anomaly-detection/
├── notebooks/
│   └── 02_preprocessing.ipynb    # Preprocessing notebook
├── data/
│   └── processed/
│       ├── BTCUSDT_1h_processed.csv   # BTC with 6 features
│       └── ETHUSDT_1h_processed.csv   # ETH with 6 features
```

### Data After Preprocessing
| Symbol | Rows | Columns | Features Added |
|--------|------|---------|----------------|
| BTCUSDT | 976 | 12 | return, log_return, volatility_24h, volume_change, volume_ratio, price_range |
| ETHUSDT | 976 | 12 | return, log_return, volatility_24h, volume_change, volume_ratio, price_range |

(Lost 24 rows due to rolling window NaN - this is expected)

### Key Decisions Made
1. **Normalization** → Do it later in ML notebook, not now
2. **Rolling window** → 24 hours (1 day of data)
3. **Handle NaN** → Drop rows (only lose 2.4% of data)

---

## Session 3 - [30/01/2026]

### What We Did
- [x] Studied example papers from professor (Smart Grid, CKD Prediction, Tesla Sentiment)
- [x] Decided to use 100% Spark MLlib (no sklearn) based on professor's examples
- [x] Changed from Isolation Forest to K-Means (Isolation Forest not in Spark MLlib)
- [x] Implemented 4 anomaly detection methods using Spark MLlib
- [x] Created separate notebook for each algorithm (clean architecture)
- [x] Ran all notebooks successfully
- [x] Generated final results with 30 anomalies detected (3.07%)
- [x] Created cheat sheet to understand each algorithm

### What We Learned

#### Why 100% Spark MLlib?
- Professor's example papers all use Spark MLlib
- Even with small data (400 rows in CKD example), they used Spark
- Course is about Big Data → Must use Big Data tools
- Same code scales from 1,000 to 1,000,000,000 rows

#### The 4 Methods Implemented

| # | Method | Type | How It Detects Anomalies | Spark Component |
|---|--------|------|--------------------------|-----------------|
| 1 | Z-Score | Statistical | Points far from the mean (\|z\| > 3) | pyspark.sql.functions |
| 2 | K-Means | Clustering | Points far from cluster centers | pyspark.ml.clustering.KMeans |
| 3 | Random Forest | Classification | Learns patterns from K-Means labels | pyspark.ml.classification.RandomForestClassifier |
| 4 | GMM | Probabilistic | Points with low probability | pyspark.ml.clustering.GaussianMixture |

#### Key Concepts Learned

**Z-Score:**
- Formula: (value - mean) / standard_deviation
- |Z| > 3 means point is in 0.3% most extreme values
- Weakness: Looks at each feature independently

**K-Means:**
- Groups similar points into K clusters
- Anomaly = point far from any cluster center
- Threshold: distance > mean + 2*stddev

**Random Forest:**
- 100 decision trees vote together
- Semi-supervised: Uses K-Means labels for training
- Gives feature importance (which features matter most)

**GMM (Gaussian Mixture Model):**
- Like K-Means but with soft probabilities
- Each point gets probability of belonging to data
- Anomaly = low probability (bottom 5%)

**Consensus Approach:**
- Each method has blind spots
- When 2+ methods agree → High confidence anomaly
- Better than relying on single method

### Files Created
```
market-anomaly-detection/
├── notebooks/
│   ├── 03_zscore.ipynb           # Z-Score method
│   ├── 04_kmeans.ipynb           # K-Means method
│   ├── 05_random_forest.ipynb    # Random Forest method
│   ├── 06_gmm.ipynb              # GMM method
│   └── 07_comparison.ipynb       # Compare all methods
├── data/
│   └── results/
│       ├── zscore_results/       # Z-Score output
│       ├── kmeans_results/       # K-Means output
│       ├── rf_results/           # Random Forest output
│       ├── gmm_results/          # GMM output
│       └── final_results/        # Combined results with consensus
├── docker-compose.yml            # Updated for PySpark
└── docs/
    └── ANOMALY_DETECTION_CHEAT_SHEET.md  # Study guide
```

### Results Achieved

| Metric | Value |
|--------|-------|
| Total data points | 976 |
| Anomalies detected | 30 |
| Anomaly rate | 3.07% |
| Method | Consensus (2+ votes) |

**Anomalies per method:**
| Method | Anomalies | Percentage |
|--------|-----------|------------|
| Z-Score | ~35 | ~3.6% |
| K-Means | ~40 | ~4.1% |
| Random Forest | ~40 | ~4.1% |
| GMM | ~49 | ~5.0% |
| **Consensus (2+)** | **30** | **3.07%** |

**Sample anomalies found:**
- 2025-12-18 13:00 → Return +1.82% (big price spike)
- 2025-12-18 17:00 → Return -1.74% (sharp drop)
- 2025-12-18 19:00 → Return -1.73% (another drop)
- 2025-12-18 21:00 → Return +1.24% (recovery)

### Key Decisions Made
1. **100% Spark MLlib** → No sklearn, no pandas in ML code
2. **4 methods instead of original plan** → K-Means replaces Isolation Forest, GMM replaces One-Class SVM
3. **Separate notebooks** → One per algorithm (clean architecture)
4. **Consensus voting** → 2+ methods must agree for anomaly
5. **Threshold choices:**
   - Z-Score: |z| > 3
   - K-Means: distance > mean + 2*std
   - GMM: probability < 5th percentile

### Problems Encountered
1. **Isolation Forest not in Spark MLlib** → Switched to K-Means
2. **One-Class SVM not in Spark MLlib** → Switched to GMM
3. **Confusion about scalability** → Clarified that Spark is required even for small data (course requirement)

---

## Project Status Summary

### ✅ COMPLETED

| Phase | Task | Status |
|-------|------|--------|
| Setup | GitHub repo | ✅ |
| Setup | Docker environment | ✅ |
| Data | Collect from Binance API | ✅ |
| Data | Preprocessing & feature engineering | ✅ |
| Models | Z-Score implementation | ✅ |
| Models | K-Means implementation | ✅ |
| Models | Random Forest implementation | ✅ |
| Models | GMM implementation | ✅ |
| Models | Comparison & consensus | ✅ |
| Results | Final anomaly detection | ✅ |

### 📝 TODO (Before Feb 15)

| Task | Priority | Estimated Time |
|------|----------|----------------|
| Write paper (IEEE format) | HIGH | 2-3 days |
| Add visualizations (price chart with anomalies) | MEDIUM | 1 day |
| Run on ETH data (currently only BTC) | LOW | 30 min |
| Clean up code & comments | LOW | 1 hour |
| Prepare presentation | HIGH | 1 day |

### 🔮 OPTIONAL (If Time Permits)

| Task | Description |
|------|-------------|
| Real-time system | WebSocket → Kafka → Spark Streaming |
| More cryptocurrencies | Add XRPUSDT, SOLUSDT, etc. |
| Hyperparameter tuning | Optimize K, threshold values |
| More visualizations | Confusion matrix, ROC curves |

---

## Next Session Tasks
- [ ] Write paper introduction
- [ ] Create architecture diagram for paper
- [ ] Add visualizations (price chart with anomalies marked)
- [ ] Prepare answers for professor's questions
