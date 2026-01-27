# 🔌 Binance API Guide

## Overview

We use Binance API to collect cryptocurrency price data.

**Base URL:** `https://api.binance.com`

**No API key required** for public market data.

---

## Endpoints We Use

### 1. Get Current Price

**Endpoint:** `/api/v3/ticker/price`

**Example:**
```
GET https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT
```

**Response:**
```json
{
    "symbol": "BTCUSDT",
    "price": "87808.41000000"
}
```

**Python Code:**
```python
import requests

url = "https://api.binance.com/api/v3/ticker/price"
params = {"symbol": "BTCUSDT"}

response = requests.get(url, params=params)
data = response.json()

print(f"Bitcoin price: ${data['price']}")
```

---

### 2. Get Historical Candles (Klines)

**Endpoint:** `/api/v3/klines`

**Parameters:**
| Parameter | Required | Description |
|-----------|----------|-------------|
| `symbol` | Yes | Trading pair (e.g., "BTCUSDT") |
| `interval` | Yes | Candle duration (e.g., "1h", "1d") |
| `limit` | No | Number of candles (default: 500, max: 1000) |

**Interval Options:**
- `1m`, `3m`, `5m`, `15m`, `30m` (minutes)
- `1h`, `2h`, `4h`, `6h`, `8h`, `12h` (hours)
- `1d`, `3d` (days)
- `1w` (week)
- `1M` (month)

**Example:**
```
GET https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=100
```

**Response (array of arrays):**
```json
[
    [
        1672531200000,    // [0] Open time (timestamp in ms)
        "86752.27",       // [1] Open price
        "86756.74",       // [2] High price
        "86209.11",       // [3] Low price
        "86626.39",       // [4] Close price
        "634.29318",      // [5] Volume
        1672534799999,    // [6] Close time
        "54943284.50",    // [7] Quote asset volume
        1500,             // [8] Number of trades
        "317.14659",      // [9] Taker buy base volume
        "27471642.25",    // [10] Taker buy quote volume
        "0"               // [11] Ignore
    ],
    // ... more candles
]
```

**Python Code:**
```python
import requests

url = "https://api.binance.com/api/v3/klines"
params = {
    "symbol": "BTCUSDT",
    "interval": "1h",
    "limit": 1000
}

response = requests.get(url, params=params)
data = response.json()

print(f"Received {len(data)} candles")
```

---

## Rate Limits

Binance limits how many requests you can make:
- **1200 requests per minute** for most endpoints
- If you exceed → 429 error (Too Many Requests)

**Best Practice:** Don't spam requests. Add delays if needed.

---

## Error Handling

Always check the status code:
```python
response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    # Success - process data
elif response.status_code == 429:
    print("Rate limit exceeded. Wait and retry.")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
```

---

## WebSocket (Real-Time Data)

For real-time streaming (Phase 2 of our project):

**Base URL:** `wss://stream.binance.com:9443`

**Stream Examples:**
| Stream | Description |
|--------|-------------|
| `btcusdt@trade` | Every individual trade |
| `btcusdt@kline_1m` | 1-minute candle updates |
| `btcusdt@ticker` | 24h statistics |

**Example URL:**
```
wss://stream.binance.com:9443/ws/btcusdt@trade
```

*We'll implement this in Phase 2.*