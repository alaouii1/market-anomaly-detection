"""
BINANCE 1-MINUTE DATA COLLECTION
================================
Collects 1-minute candles for training models that match streaming data.

Note: Binance API limit is 1000 candles per request.
For 1-minute data: 1000 candles = ~16.6 hours
To get more data, we need multiple requests.
"""

import requests
import pandas as pd
import os
import time
from datetime import datetime, timedelta

def get_klines(symbol, interval, limit, start_time=None, end_time=None):
    """
    Fetch historical candles from Binance API.
    
    Parameters:
    - symbol: "BTCUSDT", "ETHUSDT", etc.
    - interval: "1m", "1h", "1d", etc.
    - limit: number of candles (max 1000)
    - start_time: start timestamp in milliseconds (optional)
    - end_time: end timestamp in milliseconds (optional)
    
    Returns:
    - List of candles (raw data)
    """
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    
    if start_time:
        params["startTime"] = start_time
    if end_time:
        params["endTime"] = end_time
    
    response = requests.get(url, params=params)
    return response.json()


def get_klines_extended(symbol, interval, days=7):
    """
    Fetch multiple days of data by making multiple API requests.
    
    For 1-minute data:
    - 1 day = 1440 candles
    - 7 days = 10,080 candles
    
    Parameters:
    - symbol: "BTCUSDT", "ETHUSDT", etc.
    - interval: "1m", "5m", etc.
    - days: how many days of historical data
    
    Returns:
    - List of all candles
    """
    all_data = []
    
    # Calculate time range
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
    
    current_start = start_time
    request_count = 0
    
    print(f"   Fetching {days} days of {interval} data...")
    print(f"   Date range: {datetime.fromtimestamp(start_time/1000)} → {datetime.fromtimestamp(end_time/1000)}")
    
    while current_start < end_time:
        # Fetch batch
        data = get_klines(symbol, interval, limit=1000, start_time=current_start)
        
        if not data:
            break
        
        all_data.extend(data)
        request_count += 1
        
        # Move to next batch (start after last candle)
        current_start = data[-1][0] + 1
        
        # Progress update
        if request_count % 5 == 0:
            print(f"   ... {len(all_data)} candles collected ({request_count} requests)")
        
        # Rate limiting - be nice to Binance API
        time.sleep(0.1)
    
    print(f"   ✅ Total: {len(all_data)} candles in {request_count} requests")
    return all_data


def to_dataframe(raw_data):
    """
    Convert raw Binance data to a clean DataFrame.
     
    Parameters:
    - raw_data: List of lists from Binance API
    
    Returns:
    - DataFrame with OHLCV columns
    """
    df = pd.DataFrame(raw_data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades',
        'taker_buy_base', 'taker_buy_quote', 'ignore'
    ])
    
    # Keep only useful columns
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    
    # Convert types
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)
    
    # Remove duplicates (if any)
    df = df.drop_duplicates(subset=['timestamp'])
    
    # Sort by time
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    return df


def collect_and_save(symbol, interval, days, output_dir="data/raw"):
    """
    Collect data for a symbol and save to CSV.
    
    Parameters:
    - symbol: "BTCUSDT", "ETHUSDT", etc.
    - interval: "1m", "1h", etc.
    - days: number of days of historical data
    - output_dir: where to save the CSV
    """
    print(f"\n📥 Collecting {symbol} ({interval})...")
    
    # Get data (extended for multiple days)
    raw_data = get_klines_extended(symbol, interval, days)
    
    # Transform
    df = to_dataframe(raw_data)
    print(f"   📊 Clean data: {len(df)} candles")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Save
    filename = f"{output_dir}/{symbol}_{interval}.csv"
    df.to_csv(filename, index=False)
    print(f"   💾 Saved to: {filename}")
    
    return df


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    
    print("=" * 60)
    print("📥 BINANCE 1-MINUTE DATA COLLECTION")
    print("=" * 60)
    
    # Configuration
    symbols = ["BTCUSDT", "ETHUSDT"]  # Cryptos to collect
    interval = "1m"                    # 1 MINUTE candles
    days = 7                           # 7 days of data (~10,000 candles per symbol)
    
    print(f"\nSymbols: {symbols}")
    print(f"Interval: {interval}")
    print(f"Days: {days} days (~{days * 1440} candles per symbol)")
    
    # Collect all symbols
    dataframes = {}
    for symbol in symbols:
        df = collect_and_save(symbol, interval, days)
        dataframes[symbol] = df
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    for symbol, df in dataframes.items():
        print(f"\n{symbol}:")
        print(f"   Rows: {len(df)}")
        print(f"   Date range: {df['timestamp'].min()} → {df['timestamp'].max()}")
        print(f"   Price range: ${df['low'].min():,.2f} → ${df['high'].max():,.2f}")
        print(f"   Avg volume: {df['volume'].mean():,.2f}")
    
    print("\n" + "=" * 60)
    print("✅ ALL DONE!")
    print("=" * 60)
    print(f"\nNext steps:")
    print(f"1. Run preprocessing on the 1m data")
    print(f"2. Train models with: python train_and_save_models.py")
    print(f"3. Start streaming with matching 1m interval")