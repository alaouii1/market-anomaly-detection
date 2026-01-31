"""
=============================================================================
BINANCE WEBSOCKET → KAFKA PRODUCER
=============================================================================

This script:
  1. Connects to Binance WebSocket for real-time candle data
  2. Listens for BTC, ETH, PAXG price updates
  3. When a candle CLOSES, sends it to Kafka topic 'crypto-candles'

Binance WebSocket Requirements (from docs):
  - Base URL: wss://stream.binance.com:9443
  - Combined streams: /stream?streams=<stream1>/<stream2>
  - Symbols must be LOWERCASE
  - Server sends PING every 20 seconds → we MUST reply with PONG within 60s
  - Connection is valid for 24 hours max → expect disconnection

Architecture:
  Binance WebSocket ──► This Script ──► Kafka (crypto-candles topic)

Usage (inside Jupyter container):
  cd work/src
  python kafka_producer.py

Requirements:
  pip install websocket-client kafka-python

=============================================================================
"""

import json
import time
from datetime import datetime
from kafka import KafkaProducer
import websocket
import threading

# =============================================================================
# CONFIGURATION
# =============================================================================

# Kafka settings
# Use 'broker:9093' when running inside Docker (Jupyter container)
# Use 'localhost:9092' when running from your laptop directly
KAFKA_BOOTSTRAP_SERVERS = 'broker:9093'  # DOCKER listener (from Jupyter container)
KAFKA_TOPIC = 'crypto-candles'

# Binance WebSocket settings
# Docs: https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams
#
# Available intervals: 1s, 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
# Using 1m for demo (faster feedback), use '1h' to match your batch data
SYMBOLS = ['btcusdt', 'ethusdt', 'paxgusdt']  # Must be lowercase!
INTERVAL = '1m'

# Build WebSocket URL
# Combined streams format: /stream?streams=btcusdt@kline_1m/ethusdt@kline_1m/...
# Response format: {"stream": "btcusdt@kline_1m", "data": {actual_payload}}
STREAMS = '/'.join([f"{symbol}@kline_{INTERVAL}" for symbol in SYMBOLS])
WEBSOCKET_URL = f"wss://stream.binance.com:9443/stream?streams={STREAMS}"

# Alternative base URL (also valid per docs):
# WEBSOCKET_URL = f"wss://stream.binance.com:443/stream?streams={STREAMS}"


# =============================================================================
# KAFKA PRODUCER SETUP
# =============================================================================

def create_kafka_producer():
    """
    Create and return a Kafka producer.
    
    In Java terms, this is like:
        Properties props = new Properties();
        props.put("bootstrap.servers", "broker:9093");
        props.put("key.serializer", StringSerializer.class);
        props.put("value.serializer", StringSerializer.class);
        KafkaProducer<String, String> producer = new KafkaProducer<>(props);
    """
    producer = KafkaProducer(
        # Where to find Kafka brokers
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        
        # How to serialize the message key (symbol name)
        # We encode strings to bytes using UTF-8
        key_serializer=lambda k: k.encode('utf-8') if k else None,
        
        # How to serialize the message value (JSON candle data)
        # We convert dict to JSON string, then to bytes
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        
        # Wait for leader to acknowledge (1 = leader only, 'all' = all replicas)
        acks=1,
        
        # Retry failed sends
        retries=3,
    )
    
    print(f"✅ Kafka producer connected to {KAFKA_BOOTSTRAP_SERVERS}")
    return producer


# =============================================================================
# MESSAGE PROCESSING
# =============================================================================

def process_candle(producer, raw_message):
    """
    Process incoming WebSocket message and send to Kafka if candle is closed.
    
    Binance combined stream format:
    {
        "stream": "btcusdt@kline_1m",
        "data": {
            "e": "kline",
            "s": "BTCUSDT",
            "k": { ... kline data ... }
        }
    }
    
    We only send CLOSED candles to Kafka (when k.x == true).
    Open candles update every second - we don't want that noise.
    """
    
    # Parse combined stream format
    # The actual kline data is inside "data" field
    stream_name = raw_message.get('stream', '')
    data = raw_message.get('data', raw_message)  # Fallback for raw streams
    
    # Verify it's a kline event
    if data.get('e') != 'kline':
        return
    
    kline = data['k']
    symbol = data['s']      # e.g., "BTCUSDT" (uppercase in response)
    is_closed = kline['x']  # Is this kline closed?
    
    # Only process CLOSED candles
    # Docs: Updates push every 1000ms for 1s interval, 2000ms for others
    if not is_closed:
        # Print a dot to show we're receiving data
        print('.', end='', flush=True)
        return
    
    # ==========================================================================
    # EXTRACT CANDLE DATA
    # ==========================================================================
    # Field mapping from Binance docs:
    #   t  = Kline start time (ms)
    #   T  = Kline close time (ms)  
    #   o  = Open price
    #   h  = High price
    #   l  = Low price
    #   c  = Close price
    #   v  = Base asset volume (e.g., BTC volume)
    #   q  = Quote asset volume (e.g., USDT volume)
    #   n  = Number of trades
    #   x  = Is this kline closed?
    #   V  = Taker buy base asset volume
    #   Q  = Taker buy quote asset volume
    # ==========================================================================
    
    candle = {
        # Identifiers
        'symbol': symbol,
        'interval': kline['i'],
        
        # Timestamps
        'open_time': kline['t'],           # Kline start time (ms since epoch)
        'close_time': kline['T'],          # Kline close time (ms since epoch)
        'datetime': datetime.fromtimestamp(kline['t'] / 1000).isoformat(),
        
        # OHLC prices (converted to float)
        'open': float(kline['o']),
        'high': float(kline['h']),
        'low': float(kline['l']),
        'close': float(kline['c']),
        
        # Volume data
        'volume': float(kline['v']),           # Base asset volume
        'quote_volume': float(kline['q']),     # Quote asset volume (USDT)
        'taker_buy_volume': float(kline['V']), # Taker buy base volume
        'taker_buy_quote_volume': float(kline['Q']),  # Taker buy quote volume
        
        # Trade count
        'trades': int(kline['n']),
        
        # Metadata
        'is_closed': True,  # We only send closed candles
        'received_at': datetime.utcnow().isoformat(),
    }
    
    # ==========================================================================
    # SEND TO KAFKA
    # ==========================================================================
    # Key = symbol (ensures all candles for same symbol go to same partition)
    # This maintains ordering per symbol
    
    future = producer.send(
        topic=KAFKA_TOPIC,
        key=symbol,
        value=candle
    )
    
    # Wait for send to complete (synchronous for debugging)
    # In production, you'd use callbacks instead
    try:
        record_metadata = future.get(timeout=10)
        print(f"\n{'='*60}")
        print(f"✅ [{symbol}] CLOSED CANDLE → Kafka")
        print(f"   Topic: {KAFKA_TOPIC}")
        print(f"   Partition: {record_metadata.partition}, Offset: {record_metadata.offset}")
        print(f"   Time: {candle['datetime']}")
        print(f"   OHLC: O={candle['open']:.2f} H={candle['high']:.2f} L={candle['low']:.2f} C={candle['close']:.2f}")
        print(f"   Volume: {candle['volume']:.4f} {symbol.replace('USDT', '')}")
        print(f"   Trades: {candle['trades']}")
        print(f"{'='*60}")
    except Exception as e:
        print(f"\n❌ Failed to send {symbol} candle: {e}")


# =============================================================================
# WEBSOCKET HANDLERS
# =============================================================================

# Global producer reference (accessible from callbacks)
kafka_producer = None


def on_message(ws, message):
    """
    Called when WebSocket receives a message.
    Messages are JSON strings that we parse and process.
    """
    try:
        data = json.loads(message)
        process_candle(kafka_producer, data)
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON decode error: {e}")
    except Exception as e:
        print(f"\n❌ Error processing message: {e}")


def on_error(ws, error):
    """Called when WebSocket encounters an error."""
    print(f"\n❌ WebSocket error: {error}")


def on_close(ws, close_status_code, close_msg):
    """
    Called when WebSocket connection closes.
    
    Binance docs: Connection is valid for 24 hours max.
    We should reconnect when disconnected.
    """
    print(f"\n🔌 WebSocket closed")
    print(f"   Status code: {close_status_code}")
    print(f"   Message: {close_msg}")
    print("   Reconnecting in 5 seconds...")
    time.sleep(5)
    start_websocket()


def on_open(ws):
    """Called when WebSocket connection opens."""
    print(f"\n🔌 WebSocket CONNECTED to Binance")
    print(f"   URL: {WEBSOCKET_URL[:50]}...")
    print(f"   Streams: {', '.join(SYMBOLS)}")
    print(f"   Interval: {INTERVAL}")
    print(f"\n⏳ Waiting for candles to close...")
    print(f"   (dots = live updates, ✅ = closed candle sent to Kafka)")
    print(f"   For {INTERVAL} interval, expect closed candles every {INTERVAL}\n")


def on_ping(ws, message):
    """
    Called when server sends a PING frame.
    
    Binance docs:
    - Server sends ping every 20 seconds
    - We MUST reply with pong within 60 seconds
    - The websocket-client library auto-replies with pong
    
    This callback is just for logging/debugging.
    """
    print(f" [ping]", end='', flush=True)


def on_pong(ws, message):
    """
    Called when we receive a PONG frame (response to our ping).
    Usually not needed, but good for debugging.
    """
    print(f" [pong]", end='', flush=True)


# =============================================================================
# MAIN
# =============================================================================

def start_websocket():
    """
    Start the WebSocket connection to Binance.
    
    Key settings:
    - ping_interval=20: We send ping every 20s (matches Binance's ping)
    - ping_timeout=10: Wait 10s for pong response
    - The library automatically handles ping/pong frames
    """
    ws = websocket.WebSocketApp(
        WEBSOCKET_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_ping=on_ping,    # Log when server pings us
        on_pong=on_pong,    # Log pong responses
    )
    
    # run_forever() with ping settings
    # The library handles ping/pong automatically
    ws.run_forever(
        ping_interval=20,   # Send ping every 20 seconds
        ping_timeout=10,    # Wait 10 seconds for pong
    )


def main():
    """Main entry point."""
    global kafka_producer
    
    print("=" * 60)
    print("BINANCE WEBSOCKET → KAFKA PRODUCER")
    print("=" * 60)
    print(f"Kafka Server:  {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"Kafka Topic:   {KAFKA_TOPIC}")
    print(f"Symbols:       {', '.join([s.upper() for s in SYMBOLS])}")
    print(f"Interval:      {INTERVAL}")
    print(f"WebSocket URL: {WEBSOCKET_URL[:60]}...")
    print("=" * 60)
    
    # Create Kafka producer
    try:
        kafka_producer = create_kafka_producer()
    except Exception as e:
        print(f"\n❌ Failed to connect to Kafka: {e}")
        print("   Make sure Kafka is running: docker-compose up -d")
        print("   And that you're running this from inside Jupyter container")
        return
    
    # Start WebSocket connection (blocks forever, reconnects on disconnect)
    try:
        print("\n🚀 Starting WebSocket connection...")
        start_websocket()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    finally:
        if kafka_producer:
            kafka_producer.flush()  # Send any pending messages
            kafka_producer.close()
            print("✅ Kafka producer closed cleanly")


if __name__ == "__main__":
    main()