import logging
from dataclasses import asdict
from typing import Any

import numpy as np
import talib
from pandas import DataFrame
from data import IndicatorData

logger = logging.getLogger(__name__)


class IndicatorAnalyzer:

    CLOSED_CANDLE = -2

    def __init__(self, candles: DataFrame, delta: float):
        self.candles = candles
        self.delta = delta

        self.close_p = (
            candles["close"].to_numpy(dtype=float)
            if "close" in candles and not candles.empty
            else np.array([])
        )
        self.volume_p = (
            candles["volume"].to_numpy(dtype=float)
            if "volume" in candles and not candles.empty
            else np.array([])
        )
        self.high_p = (
            candles["high"].to_numpy(dtype=float)
            if "high" in candles and not candles.empty
            else np.array([])
        )
        self.low_p = (
            candles["low"].to_numpy(dtype=float)
            if "low" in candles and not candles.empty
            else np.array([])
        )

    def _is_data_valid(self, min_len: int = 2) -> bool:
        return len(self.close_p) >= min_len

    def get_ema200(self) -> float | None:
        if not self._is_data_valid(200):
            return None

        ema200 = talib.EMA(self.close_p, timeperiod=200)
        value = ema200[self.CLOSED_CANDLE]
        return None if np.isnan(value) else float(value)

    def get_macd(self) -> dict:
        if not self._is_data_valid(35):
            return {
                "macd": None,
                "macd_signal": None,
                "macd_hist": None,
                "macd_bullish": False,
                "macd_bearish": False,
            }

        macd, macd_signal, macd_hist = talib.MACD(
            self.close_p, fastperiod=12, slowperiod=26, signalperiod=9
        )

        idx = self.CLOSED_CANDLE
        val_macd = macd[idx]
        val_signal = macd_signal[idx]
        val_hist = macd_hist[idx]

        if np.isnan(val_macd) or np.isnan(val_signal):
            return {
                "macd": None,
                "macd_signal": None,
                "macd_hist": None,
                "macd_bullish": False,
                "macd_bearish": False,
            }


        macd_bullish = val_macd > val_signal and val_hist > 0
        macd_bearish = val_macd < val_signal and val_hist < 0

        return {
            "macd": float(val_macd),
            "macd_signal": float(val_signal),
            "macd_hist": float(val_hist),
            "macd_bullish": macd_bullish,
            "macd_bearish": macd_bearish,
        }

    def get_vwap(self) -> float | None:

        if not self._is_data_valid(14):
            return None

        typical_price = (self.high_p + self.low_p + self.close_p) / 3.0
        tp_v = typical_price * self.volume_p

        cum_tp_v = np.cumsum(tp_v)
        cum_v = np.cumsum(self.volume_p)

        vwap_series = np.where(cum_v != 0, cum_tp_v / cum_v, np.nan)
        val = vwap_series[self.CLOSED_CANDLE]

        return None if np.isnan(val) else float(val)

    def is_anomaly_volume(self, threshold_factor: float = 1.5) -> bool:
        if not self._is_data_valid(20):
            return False

        volume_sma = talib.SMA(self.volume_p, timeperiod=20)
        sma_val = volume_sma[self.CLOSED_CANDLE]

        if np.isnan(sma_val):
            return False

        return self.volume_p[self.CLOSED_CANDLE] > (sma_val * threshold_factor)

    def is_bollinger_bands(self) -> tuple[bool, bool]:
        if not self._is_data_valid(20):
            return False, False

        upper, middle, lower = talib.BBANDS(self.close_p, timeperiod=20)
        idx = self.CLOSED_CANDLE

        if np.isnan(lower[idx]) or np.isnan(upper[idx]):
            return False, False

        return self.low_p[idx] <= lower[idx], self.high_p[idx] >= upper[idx]

    def get_rsi(self) -> float | None:
        if not self._is_data_valid(15):
            return None

        rsi = talib.RSI(self.close_p, timeperiod=14)
        val = rsi[self.CLOSED_CANDLE]
        return None if np.isnan(val) else float(val)

    def get_analysis(self) -> dict[str | Any, None | float | int | bool | Any] | IndicatorData:
        if not self._is_data_valid(2):
            return {
                "ema200": None,
                "close_price": 0.0,
                "is_uptrend": False,
                "delta": self.delta,
                "volume_anomaly": False,
                "near_support": False,
                "near_resistance": False,
                "rsi": None,
                "rsi_oversold": False,
                "rsi_overbought": False,
                "macd": None,
                "macd_bullish": False,
                "macd_bearish": False,
                "vwap": None,
                "above_vwap": False,
            }

        close_price = float(self.close_p[self.CLOSED_CANDLE])
        ema200 = self.get_ema200()
        near_support, near_resistance = self.is_bollinger_bands()
        rsi = self.get_rsi()
        macd_data = self.get_macd()
        vwap = self.get_vwap()

        data = IndicatorData(
          ema200 = ema200,
          close_price = close_price,
          is_uptrend = ema200 is not None and close_price > ema200,
          delta = self.delta,
          volume_anomaly = self.is_anomaly_volume(),
          near_support = near_support,
          near_resistance = near_resistance,
          rsi = rsi,
          rsi_oversold = rsi is not None and rsi < 35,
          rsi_overbought = rsi is None and rsi > 65,
          macd = macd_data["macd"],
          macd_hist = macd_data["macd_hist"],
          macd_bullish = macd_data["macd_bullish"],
          macd_bearish = macd_data["macd_bearish"],
          vwap = vwap,
          above_vwap = vwap is not None and close_price > vwap,
        )

        return asdict(data)
