import logging
import numpy as np
import talib
from pandas import DataFrame

logger = logging.getLogger(__name__)


class PatternService:

    candles: DataFrame
    delta: float = 0.0

    def __init__(self, candles: DataFrame, delta: float):
        self.candles = candles
        self.delta = delta

    def patterns_analysis(self) -> dict:
        open_p = self.candles["open"].to_numpy(dtype=float)
        high_p = self.candles["high"].to_numpy(dtype=float)
        low_p = self.candles["low"].to_numpy(dtype=float)
        close_p = self.candles["close"].to_numpy(dtype=float)

        return {
            "engulfing": talib.CDLENGULFING(open_p, high_p, low_p, close_p),
            "hammer": talib.CDLHAMMER(open_p, high_p, low_p, close_p),
            "soldiers": talib.CDL3WHITESOLDIERS(open_p, high_p, low_p, close_p),
            "shooting_star": talib.CDLSHOOTINGSTAR(open_p, high_p, low_p, close_p),
            "inverted_hammer": talib.CDLINVERTEDHAMMER(open_p, high_p, low_p, close_p),
            "morning_star": talib.CDLMORNINGSTAR(open_p, high_p, low_p, close_p, penetration=0.3),
            "evening_star": talib.CDLEVENINGSTAR(open_p, high_p, low_p, close_p, penetration=0.3),
            "crows": talib.CDL3BLACKCROWS(open_p, high_p, low_p, close_p),
            "piercing": talib.CDLPIERCING(open_p, high_p, low_p, close_p),
            "dark_cloud": talib.CDLDARKCLOUDCOVER(open_p, high_p, low_p, close_p, penetration=0.3),
            "harami": talib.CDLHARAMI(open_p, high_p, low_p, close_p),
            "doji": talib.CDLDOJI(open_p, high_p, low_p, close_p),
        }

    def is_anomaly_volume(self) -> bool:
        volume_p = self.candles["volume"].to_numpy(dtype=float)
        volume_sma = talib.SMA(volume_p, timeperiod=20)

        # Проверка на NaN
        if np.isnan(volume_sma[-2]):
            return False

        return float(volume_p[-2]) > float(volume_sma[-2])

    def is_bollinger_bands(self) -> tuple[bool, bool]:
        close_p = self.candles["close"].to_numpy(dtype=float)
        upper, middle, lower = talib.BBANDS(close_p, timeperiod=20)

        if np.isnan(lower[-2]) or np.isnan(upper[-2]):
            return False, False

        near_support = self.candles["low"].iloc[-2] <= lower[-2]
        near_resistance = self.candles["high"].iloc[-2] >= upper[-2]
        return near_support, near_resistance

    def is_RSI(self) -> tuple[bool, bool, float]:
        close_p = self.candles["close"].to_numpy(dtype=float)
        rsi_arr = talib.RSI(close_p, timeperiod=14)

        if np.isnan(rsi_arr[-2]):
            return False, False, 50.0

        last_value = float(rsi_arr[-2])
        is_oversold = last_value < 35
        is_overbought = last_value > 65

        return is_oversold, is_overbought, last_value

    def get_last_candle_pattern(self) -> tuple[dict, dict]:

        if len(self.candles) < 30:
            logger.warning("Not enough candles for technical analysis (min 30 required)")
            return {}, {}

        pattern_results: dict = self.patterns_analysis()
        bullish_pattern = {}
        bearish_pattern = {}

        is_anomaly_vol = self.is_anomaly_volume()
        near_support, near_resistance = self.is_bollinger_bands()
        is_rsi_oversold, is_rsi_overbought, rsi_value = self.is_RSI()

        logger.info(f"Volume high: {is_anomaly_vol}")
        logger.info(f"BBands: Support: {near_support} | Resistance: {near_resistance}")
        logger.info(f"RSI: {rsi_value:.2f} (Oversold: {is_rsi_oversold}, Overbought: {is_rsi_overbought})")

        for pattern_name, values in pattern_results.items():
            last_value = values[-2]

            if last_value > 0:
                bullish_pattern[pattern_name] = "BULLISH"
                logger.info(f"Bullish pattern: {pattern_name}")
            elif last_value < 0:
                bearish_pattern[pattern_name] = "BEARISH"
                logger.info(f"Bearish pattern: {pattern_name}")

        if bullish_pattern and bearish_pattern:
            logger.info("Patterns conflict -> HOLD")
        elif bullish_pattern and self.delta > 0:
            if is_anomaly_vol and near_support and is_rsi_oversold:
                logger.info(f"Bullish pattern {bullish_pattern} + Delta {self.delta} -> BUY 🟢")
            else:
                logger.info(f"Bullish pattern {bullish_pattern} found, but filters rejected -> HOLD")
        elif bearish_pattern and self.delta < 0:
            if is_anomaly_vol and near_resistance and is_rsi_overbought:
                logger.info(f"Bearish pattern {bearish_pattern} + Delta {self.delta} -> SELL 🔴")
            else:
                logger.info(f"Bearish pattern {bearish_pattern} found, but filters rejected -> HOLD")
        else:
            logger.info("No pattern conditions met -> HOLD")

        return bullish_pattern, bearish_pattern
