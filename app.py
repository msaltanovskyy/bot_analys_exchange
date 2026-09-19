import asyncio
import logging
import threading
import time

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import streamlit as st
import talib

from scheduler.analysis_scheduler import AnalysisScheduler
from services import ConnectToExchange, MarketData

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


# ============================================================
# Load market symbols
# ============================================================

@st.cache_data(ttl=3600)
def load_symbols():
    async def _load():
        connection = ConnectToExchange()
        try:
            market_data = MarketData(connection.get_exchange())
            return await market_data.fetch_market_symbols()
        finally:
            await connection.close_connection()

    return asyncio.run(_load())


markets = load_symbols()

# ============================================================
# Sidebar
# ============================================================

st.sidebar.title("Market Analyzer")

symbols = st.sidebar.multiselect(
    "Symbols",
    markets,
    default=markets[:2] if markets else [],
)

available_timeframes = [
    "1m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d"
]

timeframes = st.sidebar.multiselect(
    "Timeframes",
    available_timeframes,
    default=["15m", "1h"],
)


# ============================================================
# Scheduler control
# ============================================================

def start_scheduler():
    st.session_state.stop_event.clear()

    scheduler = AnalysisScheduler(
        symbols=symbols,
        timeframes=timeframes,
        results=st.session_state.results,
        lock=st.session_state.lock,
        stop_event=st.session_state.stop_event,
        max_concurrent_tasks=5,
    )

    def run_scheduler():
        asyncio.run(scheduler.start())

    thread = threading.Thread(
        target=run_scheduler,
        daemon=True,
    )
    thread.start()

    st.session_state.scheduler = scheduler
    st.session_state.scheduler_thread = thread
    st.session_state.running = True


def stop_scheduler():
    st.session_state.stop_event.set()
    st.session_state.running = False
    logger.info("Stop requested.")


# ============================================================
# Start / Stop buttons
# ============================================================

col1, col2 = st.sidebar.columns(2)

with col1:
    if st.button(
        "▶ Start",
        disabled=st.session_state.running,
        use_container_width=True,
    ):
        if not symbols:
            st.error("Select at least one symbol.")
        elif not timeframes:
            st.error("Select at least one timeframe.")
        else:
            with st.session_state.lock:
                st.session_state.results.clear()
            start_scheduler()
            st.rerun()

with col2:
    if st.button(
        "■ Stop",
        disabled=not st.session_state.running,
        use_container_width=True,
    ):
        stop_scheduler()
        st.rerun()

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
        use_container_width=True,
    )

# ============================================================
# Details & Visualizations
# ============================================================

if current_results:
    st.divider()
    st.subheader("Details")

    for key, result in current_results.items():
        symbol, timeframe = key

        with st.expander(f"{symbol} — {timeframe}"):
            # ------------------------------------------------
            # Metrics
            # ------------------------------------------------
            m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)

            with m_col1:
                st.metric("Signal", result.get("signal", "HOLD"))

            with m_col2:
                st.metric("Score", round(result.get("score", 0.0), 2))

            with m_col3:
                rsi = result.get("rsi")
                st.metric(
                    "RSI",
                    round(rsi, 2) if rsi is not None else "N/A",
                )

            with m_col4:
                st.metric("Delta", round(result.get("delta", 0.0), 4))

            with m_col5:
                macd_status = (
                    "Bullish 🚀"
                    if result.get("macd_bullish")
                    else ("Bearish 🔻" if result.get("macd_bearish") else "Neutral")
                )
                st.metric("MACD", macd_status)

            # ------------------------------------------------
            # Candle timestamps
            # ------------------------------------------------
            st.write("Closed candle:", result.get("closed_candle_timestamp"))
            st.write("Current candle:", result.get("current_candle_timestamp"))

            # =================================================
            # Patterns
            # =================================================
            st.markdown("### Patterns")

            bullish = result.get("bullish_patterns", {})
            bearish = result.get("bearish_patterns", {})

            if bullish:
                st.write("Bullish:", ", ".join(bullish.keys()))

            if bearish:
                st.write("Bearish:", ", ".join(bearish.keys()))

            if not bullish and not bearish:
                st.write("No detected patterns")

            # =================================================
            # Indicators Summary
            # =================================================
            st.markdown("### Indicators Status")

            indicator_col1, indicator_col2 = st.columns(2)

            with indicator_col1:
                st.write("EMA200:", result.get("ema200"))
                st.write("Uptrend:", result.get("is_uptrend"))
                st.write("Volume anomaly:", result.get("volume_anomaly"))
                st.write("VWAP:", result.get("vwap"))

            with indicator_col2:
                st.write("Bollinger support:", result.get("near_support"))
                st.write("Bollinger resistance:", result.get("near_resistance"))
                st.write("Above VWAP:", result.get("above_vwap"))
                st.write("Imbalance:", result.get("imbalance"))

            # =================================================
            # Interactive Chart with Overlay Indicators
            # =================================================
            st.markdown("### Chart & Technical Indicators")

            candles = result["candles"].copy()

            # Преобразуем числовые поля в numpy массивы для TA-Lib
            close_p = candles["close"].to_numpy(dtype=float)
            high_p = candles["high"].to_numpy(dtype=float)
            low_p = candles["low"].to_numpy(dtype=float)
            vol_p = candles["volume"].to_numpy(dtype=float)

            # 1. Расчёт EMA 200
            if len(close_p) >= 200:
                candles["ema200"] = talib.EMA(close_p, timeperiod=200)
            else:
                candles["ema200"] = np.nan

            # 2. Расчёт Bollinger Bands (20, 2)
            if len(close_p) >= 20:
                bb_upper, bb_mid, bb_lower = talib.BBANDS(close_p, timeperiod=20)
                candles["bb_upper"] = bb_upper
                candles["bb_lower"] = bb_lower
            else:
                candles["bb_upper"] = np.nan
                candles["bb_lower"] = np.nan

            # 3. Расчёт VWAP
            tp = (high_p + low_p + close_p) / 3.0
            tp_vol = tp * vol_p
            cum_tp_vol = np.cumsum(tp_vol)
            cum_vol = np.cumsum(vol_p)
            candles["vwap"] = np.where(cum_vol != 0, cum_tp_vol / cum_vol, np.nan)

            # 4. Расчёт MACD (12, 26, 9)
            if len(close_p) >= 35:
                macd, macd_signal, macd_hist = talib.MACD(
                    close_p, fastperiod=12, slowperiod=26, signalperiod=9
                )
                candles["macd"] = macd
                candles["macd_signal"] = macd_signal
                candles["macd_hist"] = macd_hist
            else:
                candles["macd"] = np.nan
                candles["macd_signal"] = np.nan
                candles["macd_hist"] = np.nan

            # -------------------------------------------------
            # Построение 2-уровневого графика Plotly
            # -------------------------------------------------
            fig = make_subplots(
                rows=2,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.04,
                row_heights=[0.75, 0.25],
                subplot_titles=(
                    f"{symbol} ({timeframe}) — Price, EMA, VWAP & BBands",
                    "MACD Oscillator",
                ),
            )

            # --- Подграфик 1: Японские свечи ---
            fig.add_trace(
                go.Candlestick(
                    x=candles["timestamp"],
                    open=candles["open"],
                    high=candles["high"],
                    low=candles["low"],
                    close=candles["close"],
                    name="Price",
                ),
                row=1,
                col=1,
            )

            # --- EMA 200 ---
            fig.add_trace(
                go.Scatter(
                    x=candles["timestamp"],
                    y=candles["ema200"],
                    mode="lines",
                    name="EMA 200",
                    line=dict(color="#9C27B0", width=1.5),
                ),
                row=1,
                col=1,
            )

            # --- VWAP ---
            fig.add_trace(
                go.Scatter(
                    x=candles["timestamp"],
                    y=candles["vwap"],
                    mode="lines",
                    name="VWAP",
                    line=dict(color="#FF9800", width=1.5),
                ),
                row=1,
                col=1,
            )

            # --- Bollinger Bands (Верхняя и нижняя границы с заливкой) ---
            fig.add_trace(
                go.Scatter(
                    x=candles["timestamp"],
                    y=candles["bb_upper"],
                    mode="lines",
                    name="BB Upper",
                    line=dict(color="#78909C", width=1, dash="dot"),
                ),
                row=1,
                col=1,
            )

            fig.add_trace(
                go.Scatter(
                    x=candles["timestamp"],
                    y=candles["bb_lower"],
                    mode="lines",
                    name="BB Lower",
                    line=dict(color="#78909C", width=1, dash="dot"),
                    fill="tonexty",
                    fillcolor="rgba(120, 144, 156, 0.08)",
                ),
                row=1,
                col=1,
            )

            # --- Подграфик 2: MACD ---
            hist_colors = np.where(
                candles["macd_hist"] >= 0, "#26A69A", "#EF5350"
            )

            fig.add_trace(
                go.Bar(
                    x=candles["timestamp"],
                    y=candles["macd_hist"],
                    name="MACD Hist",
                    marker_color=hist_colors,
                    opacity=0.6,
                ),
                row=2,
                col=1,
            )

            fig.add_trace(
                go.Scatter(
                    x=candles["timestamp"],
                    y=candles["macd"],
                    mode="lines",
                    name="MACD Line",
                    line=dict(color="#2962FF", width=1.2),
                ),
                row=2,
                col=1,
            )

            fig.add_trace(
                go.Scatter(
                    x=candles["timestamp"],
                    y=candles["macd_signal"],
                    mode="lines",
                    name="Signal Line",
                    line=dict(color="#FF6D00", width=1.2),
                ),
                row=2,
                col=1,
            )

            # -------------------------------------------------
            # Стилизация и 레이아웃
            # -------------------------------------------------
            fig.update_layout(
              height=650,
              template="plotly_dark",
              xaxis_rangeslider_visible=False,
              xaxis2_rangeslider_visible=False,
              hovermode="x unified",
              margin=dict(l=20, r=20, t=70, b=20),
              legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.08,
                xanchor="center",
                x=0.5,
                font=dict(size=11),
              ),
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

# ============================================================
# Automatic UI refresh
# ============================================================

if st.session_state.running:
    time.sleep(5)
    st.rerun()
