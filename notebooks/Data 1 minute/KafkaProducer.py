"""
KAFKA PRODUCER - Binance WebSocket to Kafka
Streams real-time cryptocurrency candle data to Kafka topic.

Features:
- Connects to Binance WebSocket for 1-minute klines
- Calculates required features in real-time
- Produces to Kafka topic 'crypto-candles'
"""

import json
import time
import math
from datetime import datetime
from collections import deque
from kafka import KafkaProducer
import websocket
import threading

# Configuration
# Use "broker:9093" when running inside Docker (Jupyter container)
# Use "localhost:9092" when running on your laptop directly
KAFKA_BOOTSTRAP = "broker:9093"  # For Docker network
# KAFKA_BOOTSTRAP = "localhost:9092"  # Uncomment if running outside Docker

KAFKA_TOPIC = "crypto-candles"
SYMBOL = "btcusdt"
INTERVAL = "1m"  # 1-minute candles for real-time feel

# Store recent data for feature calculation
price_history = deque(maxlen=100)  # For volatility calculation
volume_history = deque(maxlen=24)  # For volume ratio

class BinanceKafkaProducer:
    def __init__(self):
        print("Initializing Kafka Producer...")
        self.producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None
        )
        self.last_close = None
        self.running = True
        print(f"✅ Connected to Kafka at {KAFKA_BOOTSTRAP}")
        
    def calculate_features(self, candle):
        """Calculate all 6 features required by the ML models"""
        close = float(candle['c'])
        open_price = float(candle['o'])
        high = float(candle['h'])
        low = float(candle['l'])
        volume = float(candle['v'])
        
        # Store for historical calculations
        price_history.append(close)
        volume_history.append(volume)
        
        # 1. Return (percentage change from last close)
        if self.last_close and self.last_close != 0:
            ret = (close - self.last_close) / self.last_close
        else:
            ret = 0.0
        
        # 2. Log return
        if self.last_close and self.last_close > 0 and close > 0:
            log_ret = math.log(close / self.last_close)
        else:
            log_ret = 0.0
            
        # 3. Volatility (std of returns over last 24 periods)
        if len(price_history) >= 2:
            returns = []
            prices = list(price_history)
            for i in range(1, len(prices)):
                if prices[i-1] != 0:
                    returns.append((prices[i] - prices[i-1]) / prices[i-1])
            if returns:
                mean_ret = sum(returns) / len(returns)
                variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
                volatility = math.sqrt(variance)
            else:
                volatility = 0.0
        else:
            volatility = 0.0
            
        # 4. Volume change (percentage change from last volume)
        if len(volume_history) >= 2:
            prev_vol = volume_history[-2]
            if prev_vol != 0:
                volume_change = (volume - prev_vol) / prev_vol
            else:
                volume_change = 0.0
        else:
            volume_change = 0.0
            
        # 5. Volume ratio (current volume / average volume)
        if len(volume_history) >= 2:
            avg_vol = sum(list(volume_history)[:-1]) / (len(volume_history) - 1)
            if avg_vol != 0:
                volume_ratio = volume / avg_vol
            else:
                volume_ratio = 1.0
        else:
            volume_ratio = 1.0
            
        # 6. Price range (high-low as percentage of close)
        if close != 0:
            price_range = (high - low) / close
        else:
            price_range = 0.0
            
        self.last_close = close
        
        return {
            "return": ret,
            "log_return": log_ret,
            "volatility": volatility,  # Changed from volatility_24h
            "volume_change": volume_change,
            "volume_ratio": volume_ratio,
            "price_range": price_range
        }
    
    def on_message(self, ws, message):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            
            if 'k' in data:  # Kline/candlestick data
                candle = data['k']
                is_closed = candle['x']  # Is this candle closed?
                
                # Calculate features
                features = self.calculate_features(candle)
                
                # Build message for Kafka
                record = {
                    "timestamp": datetime.now().isoformat(),
                    "event_time": candle['t'],
                    "symbol": candle['s'],
                    "open": float(candle['o']),
                    "high": float(candle['h']),
                    "low": float(candle['l']),
                    "close": float(candle['c']),
                    "volume": float(candle['v']),
                    "is_closed": is_closed,
                    # All 6 features for ML models
                    "return": features["return"],
                    "log_return": features["log_return"],
                    "volatility": features["volatility"],  # Changed from volatility_24h
                    "volume_change": features["volume_change"],
                    "volume_ratio": features["volume_ratio"],
                    "price_range": features["price_range"]
                }
                
                # Send to Kafka
                self.producer.send(
                    KAFKA_TOPIC,
                    key=candle['s'],
                    value=record
                )
                
                # Print status
                status = "CLOSED ✓" if is_closed else "updating"
                print(f"[{record['timestamp'][:19]}] {candle['s']} Close: ${float(candle['c']):,.2f} | "
                      f"Return: {features['return']*100:+.3f}% | "
                      f"Range: {features['price_range']*100:.3f}% | {status}")
                
        except Exception as e:
            print(f"Error processing message: {e}")
    
    def on_error(self, ws, error):
        print(f"WebSocket Error: {error}")
        
    def on_close(self, ws, close_status, close_msg):
        print("WebSocket connection closed")
        
    def on_open(self, ws):
        print(f"✅ Connected to Binance WebSocket")
        print(f"   Streaming {SYMBOL.upper()} {INTERVAL} candles to Kafka topic '{KAFKA_TOPIC}'")
        print("-" * 80)
        
    def start(self):
        """Start the WebSocket connection"""
        ws_url = f"wss://stream.binance.com:9443/ws/{SYMBOL}@kline_{INTERVAL}"
        
        print(f"\n{'='*60}")
        print("BINANCE → KAFKA PRODUCER")
        print(f"{'='*60}")
        print(f"WebSocket: {ws_url}")
        print(f"Kafka Topic: {KAFKA_TOPIC}")
        print(f"Features: return, log_return, volatility, volume_change, volume_ratio, price_range")
        print(f"{'='*60}\n")
        
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        
        self.ws.run_forever()
        
    def stop(self):
        self.running = False
        if hasattr(self, 'ws'):
            self.ws.close()
        self.producer.close()


if __name__ == "__main__":
    producer = BinanceKafkaProducer()
    try:
        producer.start()
    except KeyboardInterrupt:
        print("\n\nShutting down producer...")
        producer.stop()