import logging

import numpy as np
import talib
from pandas import DataFrame

logger = logging.getLogger(__name__)


class PatternAnalyzer:

    def __init__(self, candles: DataFrame):
        self.candles = candles

    def analyze(self) -> dict[str, int]:
        open_p = self.candles["open"].to_numpy(dtype=float)
        high_p = self.candles["high"].to_numpy(dtype=float)
        low_p = self.candles["low"].to_numpy(dtype=float)
        close_p = self.candles["close"].to_numpy(dtype=float)

        return {
            "engulfing": int(
                talib.CDLENGULFING(open_p, high_p, low_p, close_p)[-2]
            ),
            "hammer": int(
                talib.CDLHAMMER(open_p, high_p, low_p, close_p)[-2]
            ),
            "soldiers": int(
                talib.CDL3WHITESOLDIERS(open_p, high_p, low_p, close_p)[-2]
            ),
            "shooting_star": int(
                talib.CDLSHOOTINGSTAR(open_p, high_p, low_p, close_p)[-2]
            ),
            "inverted_hammer": int(
                talib.CDLINVERTEDHAMMER(open_p, high_p, low_p, close_p)[-2]
            ),
            "morning_star": int(
                talib.CDLMORNINGSTAR(
                    open_p,
                    high_p,
                    low_p,
                    close_p,
                    penetration=0.3
                )[-2]
            ),
            "evening_star": int(
                talib.CDLEVENINGSTAR(
                    open_p,
                    high_p,
                    low_p,
                    close_p,
                    penetration=0.3
                )[-2]
            ),
            "crows": int(
                talib.CDL3BLACKCROWS(open_p, high_p, low_p, close_p)[-2]
            ),
            "piercing": int(
                talib.CDLPIERCING(open_p, high_p, low_p, close_p)[-2]
            ),
            "dark_cloud": int(
                talib.CDLDARKCLOUDCOVER(
                    open_p,
                    high_p,
                    low_p,
                    close_p,
                    penetration=0.3
                )[-2]
            ),
            "harami": int(
                talib.CDLHARAMI(open_p, high_p, low_p, close_p)[-2]
            ),
            "doji": int(
                talib.CDLDOJI(open_p, high_p, low_p, close_p)[-2]
            ),
        }
