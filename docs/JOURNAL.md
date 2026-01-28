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

## Next Session Tasks
- [ ] Implement Isolation Forest model
- [ ] Understand how Isolation Forest works
- [ ] Detect anomalies in BTC data
- [ ] Visualize anomalies on price chart