import logging
import numpy as np
import talib
from pandas import DataFrame

logger = logging.getLogger(__name__)


class PatternService:

    candles: DataFrame
    delta: float = 0.0

    BUY_THRESHOLD: float = 2.5
    SELL_THRESHOLD: float = -3.5

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
        return last_value < 35, last_value > 65, last_value

    def get_last_candle_pattern(self) -> tuple[dict, dict, float]:
        if len(self.candles) < 30:
            logger.warning("Not enough candles for technical analysis")
            return {}, {}, 0.0

        score: float = 0.0
        pattern_results: dict = self.patterns_analysis()
        bullish_pattern, bearish_pattern = {}, {}

        for pattern_name, values in pattern_results.items():
            last_value = values[-2]
            if last_value > 0:
                bullish_pattern[pattern_name] = "BULLISH"
                score += 2.0
                logger.info(f"Pattern (+2.0): {pattern_name} (Bullish)")
            elif last_value < 0:
                bearish_pattern[pattern_name] = "BEARISH"
                score -= 2.0
                logger.info(f"Pattern (-2.0): {pattern_name} (Bearish)")

        # 2. Оценка Дельты (Delta)
        if self.delta > 0:
            score += 1.0
            logger.info(f"Delta (+1.0): {self.delta:.2f} > 0")
        elif self.delta < 0:
            score -= 1.0
            logger.info(f"Delta (-1.0): {self.delta:.2f} < 0")


        is_anomaly_vol = self.is_anomaly_volume()
        if is_anomaly_vol:
            vol_bonus = 1.0 if score >= 0 else -1.0
            score += vol_bonus
            logger.info(f"Volume Anomaly ({vol_bonus:+.1f}): High volume confirmed")


        near_support, near_resistance = self.is_bollinger_bands()
        if near_support:
            score += 1.5
            logger.info("BBands (+1.5): Price near Support (Lower band)")
        if near_resistance:
            score -= 1.5
            logger.info("BBands (-1.5): Price near Resistance (Upper band)")

        is_rsi_oversold, is_rsi_overbought, rsi_val = self.is_RSI()
        if is_rsi_oversold:
            score += 1.5
            logger.info(f"RSI (+1.5): Oversold ({rsi_val:.1f})")
        elif is_rsi_overbought:
            score -= 1.5
            logger.info(f"RSI (-1.5): Overbought ({rsi_val:.1f})")

        logger.info(f"TOTAL SCORE: {score:.1f} (Thresholds: BUY >= {self.BUY_THRESHOLD}, SELL <= {self.SELL_THRESHOLD})")

        if score >= self.BUY_THRESHOLD:
            logger.info(f"Signal generated -> BUY 🟢 (Score: {score:.1f})")
        elif score <= self.SELL_THRESHOLD:
            logger.info(f"Signal generated -> SELL 🔴 (Score: {score:.1f})")
        else:
            logger.info(f"Signal rejected -> HOLD (Score: {score:.1f})")

        return bullish_pattern, bearish_pattern, score
