import logging
import threading
import time

import streamlit as st
import talib
from app import detail_tab, ConfigSidebar, load_symbols, start_scheduler,stop_scheduler

# ============================================================
# Logging
# ============================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# Streamlit config
# ============================================================

st.set_page_config(
    page_title="Crypto Market Analyzer",
    layout="wide",
)

# ============================================================
# Session state
# ============================================================

if "results" not in st.session_state:
    st.session_state.results = {}

if "lock" not in st.session_state:
    st.session_state.lock = threading.Lock()

if "stop_event" not in st.session_state:
    st.session_state.stop_event = threading.Event()

if "scheduler" not in st.session_state:
    st.session_state.scheduler = None

if "scheduler_thread" not in st.session_state:
    st.session_state.scheduler_thread = None

if "running" not in st.session_state:
    st.session_state.running = False


# Load market symbols
@st.cache_data(ttl=3600)
def get_markets():
    return load_symbols()

markets = get_markets()

#CONFIG SIDEBAR
configSidebar = ConfigSidebar()
configSidebar.sidebar_main_frame(st = st, markets = markets)
timeframes = configSidebar.timeframes
symbols = configSidebar.symbols
limit = configSidebar.limit

# Start / Stop buttons
configSidebar.sidebar_buttons(
    st=st,
    start_scheduler=lambda: start_scheduler(
        st,
        symbols,
        timeframes,
        limit
    ),
    stop_scheduler=lambda: stop_scheduler(st),
)

# ============================================================
# Status
# ============================================================

if st.session_state.running:
    st.success("Analyzer is running")
else:
    st.info("Analyzer is stopped")

# ============================================================
# Copy results from background thread
# ============================================================

with st.session_state.lock:
    current_results = dict(st.session_state.results)

# ============================================================
# No data
# ============================================================

if not current_results:
    st.info("Waiting for market data...")

# ============================================================
# Market analysis table
# ============================================================

else:
    st.subheader("Market Analysis")

    rows = []
    for key, result in current_results.items():
        symbol, timeframe = key

        rows.append(
            {
                "Symbol": symbol,
                "Timeframe": timeframe,
                "Signal": result.get("signal", "HOLD"),
                "Score": round(result.get("score", 0.0), 2),
                "RSI": (
                    round(result["rsi"], 2)
                    if result.get("rsi") is not None
                    else None
                ),
                "EMA200": result.get("ema200"),
                "MACD Bullish": result.get("macd_bullish", False),
                "Above VWAP": result.get("above_vwap", False),
                "Delta": round(result.get("delta", 0.0), 4),
                "Volume anomaly": result.get("volume_anomaly", False),
                "Support": result.get("near_support", False),
                "Resistance": result.get("near_resistance", False),
                "Closed candle": str(result.get("closed_candle_timestamp")),
            }
        )

    st.dataframe(
        rows,
        width="stretch",
    )


# Details & Visualizations
detail_tab(current_results = current_results, st = st, talib = talib)

# ============================================================
# Automatic UI refresh
# ============================================================

if st.session_state.running:
    time.sleep(5)
    st.rerun()
