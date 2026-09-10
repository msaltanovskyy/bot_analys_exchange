import talib
import logging
from pandas import DataFrame

logger = logging.getLogger(__name__)

class PatternService:

  candles: DataFrame
  delta = 0.0

  def __init__(self, candles, delta ):
    self.candles = candles
    self.delta = delta

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

    return results


  def get_last_candle_pattern(self):
    pattern_results: dict = self.patterns_analysis()
    #last_candle_patterns = {}
    bullish_pattern = {}
    bearish_pattern = {}
    for pattern_name, values in pattern_results.items():
      last_value = values[-1]

      if last_value > 0:
        bullish_pattern[pattern_name] = "BULLISH"
        logger.info("Bullish pattern: " + pattern_name)
      elif last_value < 0:
        bearish_pattern[pattern_name] = "BEARISH"
        logger.info("Bearish pattern: " + pattern_name)

    if bullish_pattern and bearish_pattern:
      logger.info("Patterns conflict -> HOLD")
    elif bullish_pattern and self.delta > 0:
      logger.info(f"Bullish pattern found {bullish_pattern} and delta {self.delta} -> BUY")
    elif bearish_pattern and self.delta < 0:
      logger.info(f"Bearish pattern found {bullish_pattern} and delta {self.delta} -> SELL")
    else:
      logger.info("Result -> HOLD")


    return bullish_pattern, bearish_pattern

