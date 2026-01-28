# Anomaly Detection Project - Glossary & Key Concepts

> **Purpose**: Quick reference for the team. Read this before diving into the code.
> 
> **Last updated**: January 2026

---

## Table of Contents

1. [Data Concepts](#1-data-concepts)
2. [Statistics Concepts](#2-statistics-concepts)
3. [Preprocessing Concepts](#3-preprocessing-concepts)
4. [Features We Created](#4-features-we-created)
5. [Anomaly Detection Concepts](#5-anomaly-detection-concepts)
6. [Python/Pandas Basics](#6-pythonpandas-basics)
7. [Our 4 Models Summary](#7-our-4-models-summary)
8. [Project Workflow](#8-project-workflow)

---

## 1. Data Concepts

### OHLCV Data

Financial market data format. Each row = one time period (we use 1 hour).

| Column | Meaning | Example |
|--------|---------|---------|
| **O**pen | Price at START of the hour | $87,000 |
| **H**igh | HIGHEST price during the hour | $87,500 |
| **L**ow | LOWEST price during the hour | $86,800 |
| **C**lose | Price at END of the hour | $87,200 |
| **V**olume | How much was traded | 500 BTC |

### Candlestick

One row of OHLCV data. Called "candlestick" because of how it's visualized in trading charts.

### Return (Price Change)

How much the price changed from the previous period, as a percentage.

```
return = (current_price - previous_price) / previous_price × 100
```

**Example:**
- Hour 1 close: $90,000
- Hour 2 close: $91,800
- Return = (91,800 - 90,000) / 90,000 × 100 = **+2%**

**Why use returns instead of raw price?**
- Raw price going from $90,000 to $95,000 over a month = normal
- Raw price going from $90,000 to $95,000 in 1 hour = anomaly
- Returns capture the **speed** of change, which is what matters for anomaly detection

---

## 2. Statistics Concepts

### Mean (Average)

Sum of all values divided by count.

```
Values: 100, 150, 200, 250, 300
Mean = (100 + 150 + 200 + 250 + 300) / 5 = 200
```

### Standard Deviation (std)

**Simple definition:** How spread out the data is. The average distance from the mean.

**Low std** = values clustered close to mean (predictable)
**High std** = values spread far from mean (volatile)

**Example:**
```
Class A scores: 78, 80, 79, 81, 80  → Mean=80, Std≈1 (consistent)
Class B scores: 50, 95, 70, 100, 60 → Mean=75, Std≈20 (all over the place)
```

### Z-Score

**Definition:** How many standard deviations a value is from the mean.

**Formula:**
```
Z-score = (value - mean) / std
```

**Example with our BTC data:**
- Mean return = 0%
- Std return = 0.39%
- One hour had return = -2.97%

```
Z-score = (-2.97 - 0) / 0.39 = -7.6
```

This means: that hour's return was **7.6 standard deviations below average**. Extremely unusual.

**Interpretation:**

| Z-score | Meaning |
|---------|---------|
| 0 | Exactly average |
| ±1 | Normal (68% of data is here) |
| ±2 | Unusual but happens (95% of data within this) |
| ±3 | Rare (99.7% of data within this) |
| Beyond ±3 | **Very rare → Likely anomaly** |

### The 68-95-99.7 Rule

For normally distributed data:
- 68% of values are within ±1 std of mean
- 95% of values are within ±2 std of mean
- 99.7% of values are within ±3 std of mean

```
         |------ 68% ------|
         |------- 95% --------|
         |-------- 99.7% --------|
         
    -3   -2   -1    0    1    2    3   (Z-scores)
     |    |    |    |    |    |    |
   rare  unusual  normal  unusual  rare
```

### Rolling Window

A sliding calculation that moves through your data. At each row, calculate using the last N rows.

**Example with window of 3:**
```
Data: [0.1, 0.2, 0.3, 0.4, 0.5]

Row 3: Calculate using [0.1, 0.2, 0.3]
Row 4: Calculate using [0.2, 0.3, 0.4]
Row 5: Calculate using [0.3, 0.4, 0.5]

Rows 1-2: NaN (not enough data yet)
```

### Normalization

Rescaling features to the same range so ML models treat them equally.

**Problem:** Features have different scales
- return: -2% to +2%
- volume_ratio: 0.5 to 5.0

**Solution:** Rescale both to similar range (e.g., -1 to +1)

---

## 3. Preprocessing Concepts

| Term | Definition |
|------|------------|
| **Preprocessing** | Cleaning and preparing raw data before giving it to ML models. Like washing and cutting vegetables before cooking. |
| **Feature** | A measurable property of your data that the model uses to learn |
| **Feature Engineering** | Creating NEW useful columns from existing data |
| **Missing Value (NaN)** | A cell with no value. ML models crash on these. Must remove or fill. |
| **Datetime** | A data type that Python understands as a date/time, not just text |

### Why We Create Features (Not Use Raw Prices)

Raw price ($86,626) is meaningless alone:
- Is it high? Low? Normal?
- $1000 move in 2015 (when BTC = $200) is HUGE
- $1000 move in 2024 (when BTC = $90,000) is normal

Features like "return" are **relative** - they mean the same thing at any price level.
- 0.5% change is always 0.5%, whether BTC is $100 or $100,000

### Why We Drop First 24 Rows

Rolling window of 24 needs 24 rows of data.
- Row 1: Need 24, have 1 → NaN
- Row 2: Need 24, have 2 → NaN
- ...
- Row 23: Need 24, have 23 → NaN
- Row 24: Need 24, have 24 → ✅ First real value

We delete rows with NaN because ML models can't handle them.

---

## 4. Features We Created

| Feature | Formula | What It Measures |
|---------|---------|------------------|
| **return** | (current - previous) / previous × 100 | How much price changed this hour (%) |
| **log_return** | ln(current / previous) × 100 | Same as return, but with better math properties. Can be added across time periods. |
| **volatility_24h** | std of last 24 returns | How chaotic/stable the last 24 hours were. High = wild market. Low = calm market. |
| **volume_change** | (current_vol - previous_vol) / previous_vol × 100 | How much trading activity changed from last hour (%) |
| **volume_ratio** | current_volume / average(last 24h volume) | Current volume compared to what's normal. Value of 2.0 = double normal trading. |
| **price_range** | (high - low) / close × 100 | How much price swung WITHIN the hour. Catches volatility that return misses. |

### Feature Details

**return vs log_return:**
- For small changes (<5%), they're almost identical
- log_return can be added across time (regular return can't)
- Academic papers prefer log_return

**volatility_24h:**
- Low (0.3) = calm market
- High (2.0) = chaotic market

**volume_ratio:**
- 1.0 = normal volume
- 2.0 = double normal
- 5.0 = 5x normal (something big is happening!)

**price_range:**
- Catches volatility that return misses
- Example: price goes up $3000 then down $3000 in same hour
- Return = 0% (looks normal), but price_range = 7% (actually wild!)

---

## 5. Anomaly Detection Concepts

### What is an Anomaly?

A data point that is **significantly different** from the normal pattern. Also called: outlier, outlying observation, exception.

**Examples in crypto markets:**
- Sudden price crash (-3% in one hour)
- Sudden price spike (+2.5% in one hour)  
- Extremely high volume (10x normal)
- High volume with no price movement (unusual combination)

### Threshold

The cutoff value we choose to decide "normal" vs "anomaly".

**Common choice:** Z-score threshold of 3

```
If |Z-score| > 3 → Anomaly
If |Z-score| ≤ 3 → Normal
```

**Why 3?** It's a convention. Only 0.3% of normal data exceeds this, so anything beyond is likely unusual.

**You can adjust it:**
- Threshold = 2 → Catch more anomalies (but more false positives)
- Threshold = 3 → Standard balance
- Threshold = 4 → Only extreme cases (might miss some)

### Single-Column vs Multi-Column Detection

| Approach | Method | Limitation |
|----------|--------|------------|
| Single-column | Z-Score | Only looks at one variable (e.g., return OR volume) |
| Multi-column | Isolation Forest, One-Class SVM, LOF | Looks at combinations (e.g., return AND volume together) |

**Why multi-column matters:**

| Hour | Return | Volume | Z-Score (return) | Unusual? |
|------|--------|--------|------------------|----------|
| A | +0.5% | 500 | 1.2 | Looks normal |
| B | +0.5% | 5000 | 1.2 | Looks normal |

Hour B has **10x normal volume** but small price move. Z-Score misses it because it only checks return. Isolation Forest would catch it because the **combination** is unusual.

---

## 6. Python/Pandas Basics

### What is Pandas?

Python library for data manipulation. Think of it like SQL tables in memory.

**Java equivalent:** Like working with a database ResultSet, but much easier.

### DataFrame

A table with rows and columns. Our `btc` variable is a DataFrame.

```python
btc = pd.read_csv('BTCUSDT_1h.csv')  # Load CSV into DataFrame
btc.head()      # Show first 5 rows
btc.tail()      # Show last 5 rows
btc.shape       # (rows, columns) → (1000, 6)
btc.info()      # Column names and types
btc.describe()  # Statistics for each column
```

### Selecting Columns

```python
btc['close']              # One column (returns a Series)
btc[['close', 'volume']]  # Multiple columns (returns DataFrame)
```

### Creating New Columns

```python
btc['return'] = btc['close'].pct_change() * 100
btc['z_score'] = (btc['return'] - btc['return'].mean()) / btc['return'].std()
```

### Filtering Rows

**Java way:**
```java
List<Row> anomalies = data.stream()
    .filter(row -> Math.abs(row.zScore) > 3)
    .collect(Collectors.toList());
```

**Pandas way:**
```python
anomalies = btc[abs(btc['z_score']) > 3]
```

### Common Functions

| Function | What it does |
|----------|--------------|
| `df.mean()` | Average of each column |
| `df.std()` | Standard deviation of each column |
| `df.min()` | Minimum value |
| `df.max()` | Maximum value |
| `df.pct_change()` | Percentage change from previous row |
| `df.rolling(n)` | Create rolling window of n rows |
| `df.dropna()` | Remove rows with NaN |
| `abs(x)` | Absolute value |

---

## 7. Our 4 Models Summary

| Model | Type | How it works | Pros | Cons |
|-------|------|--------------|------|------|
| **Z-Score** | Statistical | Flag if \|Z-score\| > threshold | Simple, fast, interpretable | Single column only |
| **Isolation Forest** | Machine Learning | Isolates anomalies by random splits | Multi-column, no assumptions | Less interpretable |
| **One-Class SVM** | Machine Learning | Learns boundary around normal data | Good for complex patterns | Slow on big data |
| **LOF** | Machine Learning | Compares local density to neighbors | Finds local anomalies | Sensitive to parameters |

### How Each Model Thinks

**Z-Score**: "How far is this value from the average?"

**Isolation Forest**: "How easy is it to isolate this point?" (Anomalies are easier to isolate)

**One-Class SVM**: "Is this point inside or outside the boundary of normal data?"

**LOF**: "Is this point in a less dense area compared to its neighbors?"

### When to Use What

- **Z-Score**: Quick check, single variable, need to explain results
- **Isolation Forest**: Multiple variables, don't know what anomalies look like
- **One-Class SVM**: Clear boundary between normal/abnormal
- **LOF**: Data has varying densities, want to find local anomalies

---

## 8. Project Workflow

### Phase 1: Data Collection (DONE ✅)

```
1. Download data from Binance API
2. Save to CSV files
3. 1000 hourly candles for BTC and ETH
```

### Phase 2: Preprocessing (DONE ✅)

```
1. Load data
2. Check for missing values
3. Convert timestamp to datetime
4. Create 6 features (return, log_return, volatility_24h, volume_change, volume_ratio, price_range)
5. Drop first 24 rows (NaN from rolling window)
6. Save processed data
```

### Phase 3: Modeling (NEXT)

```
1. Implement Isolation Forest
2. Implement One-Class SVM
3. Implement LOF
4. Compare all models
```

### Phase 4: Evaluation

```
1. Compare models on same data
2. Measure: precision, recall, F1-score
3. Visualize detected anomalies
4. Choose best model
```

### Phase 5: Streaming (Kafka + Spark)

```
1. Set up Kafka producer (sends live data)
2. Set up Spark Streaming consumer
3. Apply trained model in real-time
4. Generate alerts
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│                   ANOMALY DETECTION                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Z-Score = (value - mean) / std                         │
│                                                          │
│  If |Z-Score| > 3 → ANOMALY                             │
│                                                          │
│  ──────────────────────────────────────────────────     │
│     -3      -2      -1       0       1       2       3  │
│      │       │       │       │       │       │       │  │
│    ANOMALY         NORMAL              NORMAL    ANOMALY │
│                                                          │
├─────────────────────────────────────────────────────────┤
│  Our Data (BTC hourly):                                 │
│  • Mean return: ~0%                                     │
│  • Std return: ~0.39%                                   │
│  • Anomaly threshold: ±1.17% (3 × 0.39)                │
│  • Found: 20 anomalies in 1000 hours (2%)              │
└─────────────────────────────────────────────────────────┘
```

---

## Terms We'll Add Later

As we progress, we'll add:
- Isolation Forest specific terms (contamination, n_estimators)
- SVM terms (kernel, hyperplane, nu parameter)
- LOF terms (n_neighbors, local density, reachability distance)
- Kafka/Spark streaming terms
- Evaluation metrics (precision, recall, F1)