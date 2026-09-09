import talib
import logging
from pandas import DataFrame

logger = logging.getLogger(__name__)
class PatternService:

  candles: DataFrame

  def __init__(self, candles):
    self.candles = candles

  def patterns_analysis(self) -> dict:
    open_p = self.candles["open"].to_numpy(dtype=float)
    high_p = self.candles["high"].to_numpy(dtype=float)
    low_p = self.candles["low"].to_numpy(dtype=float)
    close_p = self.candles["close"].to_numpy(dtype=float)

    results = {
      "engulfing": talib.CDLENGULFING(open_p, high_p, low_p, close_p),
      "hammer": talib.CDLHAMMER(open_p, high_p, low_p, close_p),
      "soldiers": talib.CDL3WHITESOLDIERS(open_p, high_p, low_p, close_p),
      "doji": talib.CDLDOJI(open_p, high_p, low_p, close_p),
      "shooting_star": talib.CDLSHOOTINGSTAR(open_p, high_p, low_p, close_p),
      "inverted_hammer": talib.CDLINVERTEDHAMMER(
        open_p, high_p, low_p, close_p
      ),
      "morning_star": talib.CDLMORNINGSTAR(
        open_p, high_p, low_p, close_p, penetration=0
      ),
      "evening_star": talib.CDLEVENINGSTAR(
        open_p, high_p, low_p, close_p, penetration=0
      ),
      "crows": talib.CDL3BLACKCROWS(open_p, high_p, low_p, close_p),
      "piercing": talib.CDLPIERCING(open_p, high_p, low_p, close_p),
      "dark_cloud": talib.CDLDARKCLOUDCOVER(
        open_p, high_p, low_p, close_p, penetration=0
      ),
      "harami": talib.CDLHARAMI(open_p, high_p, low_p, close_p),
    }

    last_candle_patterns = {}

    for pattern_name, values in results.items():
      last_value = values[-1]

      if last_value > 0:
        last_candle_patterns[pattern_name] = "BULLISH"
      elif last_value < 0:
        last_candle_patterns[pattern_name] = "BEARISH"
      else:
        logger.info(f"Pattern not found {pattern_name}!")

    return last_candle_patterns

