# Market Anomaly Detection - Project Summary

## 📋 Project Overview

| Field | Value |
|-------|-------|
| **Course** | Big Data / Master IPS |
| **Deadline** | February 15, 2026 |
| **Topic** | Cryptocurrency Market Anomaly Detection |
| **Technologies** | Apache Spark MLlib, PySpark, Docker, Jupyter |
| **Data** | Bitcoin (BTCUSDT) hourly prices from Binance API |

---

## 🎯 What We Built

A system that detects unusual market behavior using **4 machine learning algorithms**, all implemented with **100% Apache Spark MLlib**.

### The Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ANOMALY DETECTION PIPELINE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PHASE 1: DATA COLLECTION                                                   │
│  ─────────────────────────                                                  │
│  Binance API ──→ 1000 hourly candles ──→ data/raw/BTCUSDT_1h.csv           │
│                                                                             │
│  PHASE 2: PREPROCESSING                                                     │
│  ──────────────────────                                                     │
│  Raw data ──→ Feature Engineering ──→ 6 features ──→ data/processed/       │
│                                                                             │
│  PHASE 3: ANOMALY DETECTION (4 Methods)                                     │
│  ──────────────────────────────────────                                     │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Z-Score    │  │   K-Means    │  │Random Forest │  │     GMM      │    │
│  │ (Statistical)│  │ (Clustering) │  │(Classification)│ │(Probabilistic)│   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                 │                 │            │
│         └────────────┬────┴────────┬────────┴────────┬────────┘            │
│                      ▼             ▼                 ▼                      │
│                   ┌─────────────────────────────────────┐                   │
│                   │         CONSENSUS VOTING            │                   │
│                   │    (2+ methods agree = ANOMALY)     │                   │
│                   └─────────────────────────────────────┘                   │
│                                    │                                        │
│                                    ▼                                        │
│                          30 anomalies detected                              │
│                              (3.07%)                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
market-anomaly-detection/
│
├── data/
│   ├── raw/                          # Original data from Binance
│   │   ├── BTCUSDT_1h.csv
│   │   └── ETHUSDT_1h.csv
│   ├── processed/                    # Data with engineered features
│   │   ├── BTCUSDT_1h_processed.csv
│   │   └── ETHUSDT_1h_processed.csv
│   └── results/                      # Output from each algorithm
│       ├── zscore_results/
│       ├── kmeans_results/
│       ├── rf_results/
│       ├── gmm_results/
│       └── final_results/            # Combined with consensus
│
├── notebooks/                        # Jupyter notebooks (run in order)
│   ├── 01_data_exploration.ipynb     # Explore raw data
│   ├── 02_preprocessing.ipynb        # Create features
│   ├── 03_zscore.ipynb               # Z-Score method
│   ├── 04_kmeans.ipynb               # K-Means method
│   ├── 05_random_forest.ipynb        # Random Forest method
│   ├── 06_gmm.ipynb                  # GMM method
│   └── 07_comparison.ipynb           # Compare all methods
│
├── docs/
│   ├── JOURNAL.md                    # Session-by-session log
│   ├── ARCHITECTURE.md               # System design
│   ├── ANOMALY_DETECTION_CHEAT_SHEET.md  # Algorithm explanations
│   └── PROJECT_SUMMARY.md            # This file
│
├── docker-compose.yml                # Docker setup for PySpark
└── README.md
```

---

## 🔢 The Data

### Raw Data (from Binance API)
| Column | Description |
|--------|-------------|
| timestamp | When the candle started |
| open | Price at start of hour |
| high | Highest price during hour |
| low | Lowest price during hour |
| close | Price at end of hour |
| volume | Trading volume |

### Engineered Features (6 total)
| Feature | What It Measures | Formula |
|---------|------------------|---------|
| return | Price change % | (close - prev_close) / prev_close × 100 |
| log_return | Log price change | ln(close / prev_close) |
| volatility_24h | 24h rolling std | std(return, window=24) |
| volume_change | Volume change % | (volume - prev_volume) / prev_volume × 100 |
| volume_ratio | Volume vs average | volume / mean(volume, window=24) |
| price_range | Intraday volatility | (high - low) / close × 100 |

### Data Stats
| Metric | Value |
|--------|-------|
| Total rows (raw) | 1000 |
| Total rows (processed) | 976 (lost 24 to rolling window) |
| Date range | Dec 17, 2025 → Jan 27, 2026 |
| Columns (processed) | 12 (6 original + 6 features) |

---

## 🤖 The 4 Algorithms

### 1. Z-Score (Statistical)
```
What:     Measures distance from mean in standard deviations
Formula:  Z = (value - mean) / stddev
Rule:     |Z| > 3 → Anomaly
Spark:    pyspark.sql.functions (mean, stddev)
```

### 2. K-Means (Clustering)
```
What:     Groups similar points, flags distant ones
How:      3 clusters, distance to center
Rule:     distance > mean + 2*std → Anomaly
Spark:    pyspark.ml.clustering.KMeans
```

### 3. Random Forest (Classification)
```
What:     Learns anomaly patterns from examples
How:      100 trees, trained on K-Means labels
Rule:     Predicted as 1 → Anomaly
Spark:    pyspark.ml.classification.RandomForestClassifier
```

### 4. GMM (Probabilistic)
```
What:     Models data as probability distributions
How:      3 Gaussian components
Rule:     probability < 5th percentile → Anomaly
Spark:    pyspark.ml.clustering.GaussianMixture
```

### Consensus
```
Each method votes (0 or 1)
Total votes = zscore + kmeans + rf + gmm
If votes >= 2 → HIGH CONFIDENCE ANOMALY
```

---

## 📊 Results

### Summary
| Metric | Value |
|--------|-------|
| Total data points | 976 |
| High-confidence anomalies | 30 |
| Anomaly rate | 3.07% |

### Per Method
| Method | Anomalies | Rate |
|--------|-----------|------|
| Z-Score | ~35 | 3.6% |
| K-Means | ~40 | 4.1% |
| Random Forest | ~40 | 4.1% |
| GMM | ~49 | 5.0% |
| **Consensus (2+)** | **30** | **3.07%** |

### Sample Anomalies Detected
| Timestamp | Return | Votes | Description |
|-----------|--------|-------|-------------|
| 2025-12-18 13:00 | +1.82% | 3/4 | Price spike |
| 2025-12-18 17:00 | -1.74% | 3/4 | Sharp drop |
| 2025-12-18 19:00 | -1.73% | 3/4 | Continued drop |
| 2025-12-18 21:00 | +1.24% | 3/4 | Recovery bounce |

---

## ✅ Completed Tasks

| # | Task | Date |
|---|------|------|
| 1 | Set up GitHub repository | 27/01 |
| 2 | Learn trading concepts | 27/01 |
| 3 | Collect data from Binance | 27/01 |
| 4 | Create preprocessing pipeline | 28/01 |
| 5 | Engineer 6 features | 28/01 |
| 6 | Implement Z-Score | 30/01 |
| 7 | Implement K-Means | 30/01 |
| 8 | Implement Random Forest | 30/01 |
| 9 | Implement GMM | 30/01 |
| 10 | Create comparison notebook | 30/01 |
| 11 | Generate final results | 30/01 |
| 12 | Create cheat sheet | 30/01 |

---

## 📝 TODO (Before Feb 15)

### High Priority
- [ ] Write paper (IEEE format)
- [ ] Prepare presentation slides
- [ ] Practice explaining algorithms

### Medium Priority
- [ ] Add visualizations (price chart with anomalies)
- [ ] Create architecture diagram for paper

### Low Priority
- [ ] Run on ETH data
- [ ] Clean up code comments
- [ ] Hyperparameter tuning

---

## 🚀 How To Run

```bash
# 1. Start Docker
docker-compose up

# 2. Open Jupyter
http://localhost:8888
Password: anomaly

# 3. Run notebooks in order
01_data_exploration.ipynb
02_preprocessing.ipynb
03_zscore.ipynb
04_kmeans.ipynb
05_random_forest.ipynb
06_gmm.ipynb
07_comparison.ipynb
```

---

## 📚 Key Learnings

### Technical
- Spark MLlib for distributed machine learning
- VectorAssembler to combine features
- StandardScaler for normalization
- Semi-supervised learning (using K-Means labels for Random Forest)

### Domain
- Cryptocurrency market behavior
- What constitutes an anomaly (sudden price moves, unusual volume)
- Why relative features (%) are better than absolute prices

### Architecture
- Separate notebook per algorithm (maintainability)
- Consensus voting (robustness)
- 100% Spark (scalability requirement)

---

## 📄 For The Paper

### Abstract (Draft)
> "We implemented four anomaly detection methods using Apache Spark MLlib: Z-Score (statistical), K-Means (clustering), Random Forest (classification), and Gaussian Mixture Model (probabilistic). Each method was applied to 976 hours of Bitcoin market data with 6 engineered features. A consensus-based approach was used where points flagged by at least two methods were classified as high-confidence anomalies. The system detected 30 anomalies (3.07%), corresponding to significant market events such as sudden price movements exceeding 1.5% per hour. All implementations used 100% distributed Spark operations, ensuring scalability for Big Data applications."

### Key Points to Mention
1. 100% Spark MLlib (no sklearn)
2. 4 different algorithmic approaches
3. Consensus voting for confidence
4. Scalable to Big Data
5. Real anomalies detected correspond to actual market events

---

*Last updated: January 30, 2026*
