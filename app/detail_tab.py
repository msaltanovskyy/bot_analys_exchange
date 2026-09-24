from plotly.subplots import make_subplots
import numpy as np
import plotly.graph_objects as go


def detail_tab(current_results, st, talib):
  if current_results:
    st.divider()
    st.subheader("Details")

    for key, result in current_results.items():
      symbol, timeframe = key

      # Metrics
      with st.expander(f"{symbol} — {timeframe}"):

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

        # Стилизация
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
          width="stretch",
        )
