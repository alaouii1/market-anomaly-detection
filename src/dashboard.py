
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import os
import glob
from datetime import datetime

# ==============================================================================
# CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="Crypto Anomaly Detection",
    page_icon="🚨",
    layout="wide"
)

# Paths to the streaming data (CSV output from Spark)
DATA_BASE_DIR = "/home/jovyan/work/data/results" if os.environ.get("AM_I_IN_DOCKER") else "data/results"
CANDLE_DIR = os.path.join(DATA_BASE_DIR, "streaming_candle_anomalies")
WINDOW_DIR = os.path.join(DATA_BASE_DIR, "streaming_window_anomalies")

# ==============================================================================
# DATA LOADING
# ==============================================================================
@st.cache_data(ttl=2)
def load_latest_data(directory):
    """Load and combine the most recent CSV files from Spark stream."""
    if not os.path.exists(directory):
        return pd.DataFrame()
        
    try:
        # Get all CSV files
        # Spark creates temp files named starting with . inside the _spark_metadata
        # We must filter for actual part-xxxx.csv files
        all_files = glob.glob(os.path.join(directory, "part-*.csv"))

        if not all_files:
            return pd.DataFrame()
            
        # Sort by modification time (newest last)
        all_files.sort(key=os.path.getmtime)
        
        # Take the last 5 files (avoids reading thousands of tiny files)
        recent_files = all_files[-5:] 
        
        dfs = []
        for f in recent_files:
            try:
                # Read CSV
                # on_bad_lines='skip' helps if spark is writing midpoint
                if os.path.getsize(f) > 0:
                    df = pd.read_csv(f, on_bad_lines='skip')
                    dfs.append(df)
            except Exception:
                continue # Skip locked/corrupt files
                
        if not dfs:
            return pd.DataFrame()
            
        full_df = pd.concat(dfs, ignore_index=True)
        
        # Clean timestamps
        if 'timestamp' in full_df.columns:
            full_df['timestamp'] = pd.to_datetime(full_df['timestamp'], errors='coerce')
            full_df = full_df.dropna(subset=['timestamp']) # valid dates only
            full_df = full_df.sort_values('timestamp')
            
        return full_df.tail(200) # Keep reasonable history
        
    except Exception as e:
        # st.error(f"Error loading data: {e}") 
        # Suppress errors on UI to avoid flickering
        return pd.DataFrame()

# ==============================================================================
# DASHBOARD LAYOUT
# ==============================================================================

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🚨 Real-Time Market Anomaly Detection")
    st.markdown("**Live monitoring of streaming crypto data**")
with col2:
    st.image("https://cryptologos.cc/logos/bitcoin-btc-logo.png", width=50)

# ------------------------------------------------------------------------------
# 1. CANDLE MONITOR (Per-Candle Detection)
# ------------------------------------------------------------------------------
st.divider()
st.subheader("1. Live Price & Anomaly Monitor (Candle-Level)")

# Load Candle Data
candle_df = load_latest_data(CANDLE_DIR)

if not candle_df.empty:
    # Setup Data
    latest_price = candle_df['close'].iloc[-1]
    last_return = candle_df['return'].iloc[-1]
    
    # Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Live Price (BTC)", f"${latest_price:,.2f}")
    m2.metric("Return (1m)", f"{last_return:.2f}%", delta_color="inverse")
    
    # Count anomalies in view
    recent_anoms = candle_df[candle_df['is_candle_anomaly'] == True].shape[0]
    m3.metric("Anomalies Detected", f"{recent_anoms} / {len(candle_df)}")
    
    if recent_anoms > 0:
        m4.error("⚠️ ANOMALY ACTIVE")
    else:
        m4.success("✅ MARKET NORMAL")

    # Interactive Chart
    fig = go.Figure()

    # Price Line
    fig.add_trace(go.Scatter(
        x=candle_df['timestamp'], 
        y=candle_df['close'],
        mode='lines',
        name='Price'
    ))

    # Anomaly Markers
    anomalies = candle_df[candle_df['is_candle_anomaly'] == True]
    if not anomalies.empty:
        fig.add_trace(go.Scatter(
            x=anomalies['timestamp'],
            y=anomalies['close'],
            mode='markers',
            marker=dict(color='red', size=12, symbol='x'),
            name='ANOMALY'
        ))

    fig.update_layout(
        title="BTCUSDT - Real-Time",
        template="plotly_dark",
        height=400,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Recent Alerts Table
    if not anomalies.empty:
        st.markdown("##### 🚨 Recent Alerts")
        st.dataframe(
            anomalies[['timestamp', 'close', 'return', 'candle_votes', 'is_candle_anomaly']].tail(5).iloc[::-1],
            hide_index=True
        )

else:
    st.info("Waiting for data stream... (Start the Spark Consumer)")


# ------------------------------------------------------------------------------
# 2. WINDOW MONITOR (Sliding Window Volatility)
# ------------------------------------------------------------------------------
st.divider()
st.subheader("2. Volatility Monitor (1H Sliding Window)")

window_df = load_latest_data(WINDOW_DIR)

if not window_df.empty:
    last_window = window_df.iloc[-1]
    
    # Metrics
    w1, w2, w3, w4 = st.columns(4)
    w1.metric("Window Std Dev", f"{last_window.get('std_return', 0):.4f}")
    w2.metric("Max Price Range", f"{last_window.get('max_range', 0):.2f}%")
    
    status = "VOLATILE" if last_window.get('is_anomaly') else "STABLE"
    if status == "VOLATILE":
        w3.error(f"Status: {status}")
    else:
        w3.success(f"Status: {status}")
        
    w4.metric("Consensus Votes", f"{last_window.get('total_votes', 0)} / 3")
    
    # Table
    st.markdown("##### Latest Window Stats")
    st.dataframe(window_df.tail(10).iloc[::-1], hide_index=True)

else:
    st.info("Waiting for window data... (Takes 1-2 mins to initialize)")


# ------------------------------------------------------------------------------
# Auto-Refresh Logic
# ------------------------------------------------------------------------------
time.sleep(2)  # Update every 2 seconds
st.rerun()

