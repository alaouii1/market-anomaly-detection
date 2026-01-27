# 📅 Project Journal

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

### Next Session Tasks
- [ ] Explore data (visualizations)
- [ ] Calculate additional features (returns, volatility)
- [ ] Implement first ML model (Z-Score baseline)
