# Real-Time Market Anomaly Detection

A production-ready system for detecting anomalies in cryptocurrency markets using **Kafka**, **Spark Structured Streaming**, and **Unsupervised Learning**.

## 🧠 Core Concepts

This system implements a **Dual-Stream Detection Architecture**, meaning it analyzes market data in two different ways simultaneously to catch different types of anomalies.

### 1. Per-Candle Detection (Micro-Level)
*   **Goal**: Detect if a *single specific candle* (1 minute) is abnormal compared to historical stats.
*   **Method**: **Z-Score Analysis**.
*   **Features**:
    *   `Return`: Percentage price change per minute.
    *   `Log Return`: Logarithmic return (better for statistical normality).
    *   `Price Range`: Volatility within the candle `(High - Low) / Low`.
*   **Logic**: If any feature deviates by a Z-Score > 3 (approx 99.7% prob), it's flagged.

### 2. Sliding Window Detection (Macro-Level)
*   **Goal**: Detect if a *time period* (e.g., the last hour) is unusually volatile.
*   **Method**: **Sliding Window Aggregation**.
*   **Configuration**: 1-Hour Window, Sliding every 1-Minute.
*   **Features**:
    *   `Std Dev(Returns)`: How "choppy" is the price action?
    *   `Max(Price Range)`: What was the biggest wick in the hour?
    *   `Avg(Volume)`: Is trading volume unusually high?
*   **Logic**: If window statistics exceed historical thresholds, the *entire window* is abnormal.

### 3. Consensus Voting 🗳️
One model can be wrong. We use a **Consensus System** to reduce false positives.
*   **Rule**: At least **2 independent indicators** must flag an anomaly for it to be confirmed.
*   **Confidence Levels**:
    *   **3 Votes**: HIGH Confidence (Definitely check this!)
    *   **2 Votes**: MEDIUM Confidence (Likely anomaly)
    *   **1 Vote**: LOW Confidence (Noise/Warning)

---

## 🏗️ System Architecture

```mermaid
graph LR
    Binance[Binance WebSocket] -->|Real-time 1m Candles| Producer[Kafka Producer]
    Producer -->|Topic: crypto-candles| Kafka[Kafka Broker]
    Kafka -->Consumer[Spark Streaming Consumer]
    
    subgraph Analysis Engine
        Consumer --> Stream1[Stream 1: Per-Candle Z-Score]
        Consumer --> Stream2[Stream 2: Sliding Window]
        Stream1 & Stream2 --> Voting[Consensus Voting]
    end
    
    Voting -->|Live Alerts| Dashboard[Streamlit UI]
    Voting -->|CSV Logs| Storage[Data Lake (CSVs)]
```

---

## 🚀 Running the Project (Pipeline)

You need **4 Terminals** to run the full pipeline.

### Step 1: Start Infrastructure (Terminal 1)
Start the Docker containers for Kafka, Zookeeper, and Spark.
```bash
docker-compose up -d
```
*   **Services**: Kafka (9092), Zookeeper (2181), Spark Driver (8888), Streamlit (8501).

### Step 2: Start Producer (Terminal 1 - continued)
Enter the container and start sending data from Binance to Kafka.
```bash
docker exec -it jupyter bash
cd work/src
python kafka_producer.py
```
> You should see dots `.` indicating messages sent.

### Step 3: Start Spark Consumer (Terminal 2)
This is the "Brain". It reads from Kafka, finds anomalies, and saves them to CSV.
```bash
# Open NEW terminal
docker exec -it jupyter bash
cd work/src

# Submit job with Kafka library
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 spark_consumer.py
```
> You will see "Requesting 4096 bytes" and initialization logs.

### Step 4: Start Dashboard (Terminal 3)
Visualize the results in real-time.
```bash
# Open NEW terminal (Local machine or inside container)
# If local: pip install streamlit plotly

streamlit run src/dashboard.py
```
*   **Open Browser**: [http://localhost:8501](http://localhost:8501)

---

## 📁 Project Structure

```text
market-anomaly-detection/
├── src/
│   ├── dashboard.py         # Streamlit Real-time UI
│   ├── kafka_producer.py    # Fetches Binance data -> Kafka
│   ├── spark_consumer.py    # Spark engine (Per-Candle + Window logic)
│   ├── data_collection/     
│   │   └── collect_historical.py # Script to download training data
│   └── models/
│       └── model_params.json     # Dynamic thresholds (Edit this to tune!)
├── data/
│   └── results/             # Live anomaly outputs (CSVs)
├── notebooks/               # Analysis & Training (Jupyter)
├── docker-compose.yml       # Infrastructure config
└── requirements.txt         # Python dependencies
```

## ⚙️ Configuration
All thresholds (Z-Scores, Mean, Std Dev) are loaded **dynamically** from:
`src/models/model_params.json`

Check this file to see the statistics used for detection.
