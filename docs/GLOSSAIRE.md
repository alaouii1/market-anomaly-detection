# 📚 Glossary - Terms to Know

## Trading & Markets

### Trading
Buying something cheap, selling it expensive, keeping the difference.

**Example:**
- Buy 1 Bitcoin at $80,000
- Sell 1 Bitcoin at $85,000
- Profit: $5,000

### Financial Market
A place where people buy and sell assets.
- **Binance** = A market for cryptocurrencies
- Thousands of transactions happen every second

### Transaction
When a buyer and seller agree on a price and exchange happens.

---

## Price Data Concepts

### OHLCV
A summary of price movement over a time period (5 values):

| Letter | Name | Meaning |
|--------|------|---------|
| **O** | Open | Price at the START of the period |
| **H** | High | HIGHEST price during the period |
| **L** | Low | LOWEST price during the period |
| **C** | Close | Price at the END of the period |
| **V** | Volume | Quantity traded during the period |

### Candle (Kline)
A visual representation of OHLCV data.
```
         High
          │
      ┌───┴───┐
      │       │ ← Body (between Open and Close)
      └───┬───┘
          │
         Low
```

- **Green candle** = Price went UP (Close > Open)
- **Red candle** = Price went DOWN (Close < Open)

### Interval (Timeframe)
The duration of each candle:
- `1m` = 1 minute
- `5m` = 5 minutes
- `15m` = 15 minutes
- `1h` = 1 hour
- `4h` = 4 hours
- `1d` = 1 day

### Volume
The quantity of an asset traded during a period.
- **High volume** = Many people trading → Price movement is "serious"
- **Low volume** = Few people trading → Price can be easily manipulated

---

## Symbols

### BTCUSDT
- **BTC** = Bitcoin (what you buy)
- **USDT** = Tether/Dollar (what you pay with)
- **BTCUSDT** = Price of Bitcoin in dollars

### Other Examples
- `ETHUSDT` = Ethereum in dollars
- `BNBUSDT` = Binance Coin in dollars

---

## API Concepts

### API (Application Programming Interface)
A way for programs to communicate with each other.

**Analogy:**
```
You (client) → Waiter (API) → Kitchen (Binance)
"I want BTC    Transmits      Prepares
 price"        your request   the data
```

### REST API
- You request → You get a response → Connection closes
- **Use case:** Fetch historical data

### WebSocket
- Connection opens → Stays open → Server pushes data to you
- **Use case:** Real-time streaming

### Endpoint
A specific URL path for a resource in the API.
- `/api/v3/ticker/price` = Get current price
- `/api/v3/klines` = Get historical candles

### HTTP Status Codes
| Code | Meaning |
|------|---------|
| 200 | OK - Success ✅ |
| 400 | Bad Request - Your request is malformed |
| 403 | Forbidden - Access denied |
| 404 | Not Found - Endpoint doesn't exist |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Server Error - Binance's problem |

---

## Python / Pandas Concepts

### Pandas
A Python library for data manipulation. Like Excel but in code.
```python
import pandas as pd  # "pd" is the universal alias
```

### DataFrame
A table (rows and columns) in Pandas.
```
   timestamp      open      high       low     close    volume
0  2025-12-17  86752.27  86756.74  86209.11  86626.39  634.29
1  2025-12-17  86626.40  87005.27  86587.82  86777.98  454.66
```

| Term | Meaning |
|------|---------|
| **Row** | One horizontal line (one candle) |
| **Column** | One vertical line (e.g., all "open" prices) |
| **Index** | Row number (0, 1, 2...) |

### Common DataFrame Operations

| Code | What it does |
|------|--------------|
| `pd.DataFrame(data)` | Create a table |
| `df[['col1', 'col2']]` | Select columns |
| `df['col'].astype(float)` | Convert to numbers |
| `df.head(10)` | Show first 10 rows |
| `df.describe()` | Show statistics |
| `df.to_csv('file.csv')` | Save to CSV file |

### CSV (Comma Separated Values)
A simple file format for tables.
```
timestamp,open,high,low,close,volume
2025-12-17,86752.27,86756.74,86209.11,86626.39,634.29
```

### Data Types
| Type | Example | Description |
|------|---------|-------------|
| `string` | `"86752.27"` | Text (can't do math) |
| `float` | `86752.27` | Decimal number (can do math) |
| `int` | `86752` | Whole number |
| `datetime` | `2025-12-17 05:00:00` | Date and time |