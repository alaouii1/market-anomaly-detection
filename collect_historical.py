import requests
import pandas as pd
import os


def get_klines(symbol, interval, limit):
    """
    Fetch historical candles from Binance API.
    
    Parameters:
    - symbol: "BTCUSDT", "ETHUSDT", etc.
    - interval: "1m", "1h", "1d", etc.
    - limit: number of candles (max 1000)
    
    Returns:
    - List of candles (raw data)
    """
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    response = requests.get(url, params=params)
    return response.json()


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
    
    return df


def collect_and_save(symbol, interval, limit, output_dir="data/raw"):
    """
    Collect data for a symbol and save to CSV.
    
    Parameters:
    - symbol: "BTCUSDT", "ETHUSDT", etc.
    - interval: "1h", "1d", etc.
    - limit: number of candles
    - output_dir: where to save the CSV
    """
    print(f"\n📥 Collecting {symbol}...")
    
    # Get data
    raw_data = get_klines(symbol, interval, limit)
    print(f"   ✅ Received {len(raw_data)} candles")
    
    # Transform
    df = to_dataframe(raw_data)
    
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
    print("📥 BINANCE DATA COLLECTION")
    print("=" * 60)
    
    # Configuration
    symbols = ["BTCUSDT", "ETHUSDT"]  # Cryptos to collect
    interval = "1h"                    # 1 hour candles
    limit = 1000                       # 1000 candles each
    
    print(f"\nSymbols: {symbols}")
    print(f"Interval: {interval}")
    print(f"Limit: {limit} candles per symbol")
    
    # Collect all symbols
    dataframes = {}
    for symbol in symbols:
        df = collect_and_save(symbol, interval, limit)
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
    
    print("\n✅ ALL DONE!")