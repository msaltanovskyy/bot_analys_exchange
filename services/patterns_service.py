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
      "shooting_star": talib.CDLSHOOTINGSTAR(open_p, high_p, low_p, close_p),
      "inverted_hammer": talib.CDLINVERTEDHAMMER(
        open_p, high_p, low_p, close_p
      ),
      "morning_star": talib.CDLMORNINGSTAR(
        open_p, high_p, low_p, close_p, penetration=0.3
      ),
      "evening_star": talib.CDLEVENINGSTAR(
        open_p, high_p, low_p, close_p, penetration=0.3
      ),
      "crows": talib.CDL3BLACKCROWS(open_p, high_p, low_p, close_p),
      "piercing": talib.CDLPIERCING(open_p, high_p, low_p, close_p),
      "dark_cloud": talib.CDLDARKCLOUDCOVER(
        open_p, high_p, low_p, close_p, penetration=0.3
      ),
      "harami": talib.CDLHARAMI(open_p, high_p, low_p, close_p),
    }

    return results

  #VOLUME SMA
  def is_anomaly_volume(self):
    volume_p = self.candles["volume"].to_numpy(dtype=float)
    volume_sma = talib.SMA(volume_p, timeperiod=20)
    return float(volume_p[-2]) > float(volume_sma[-2])

  #BOLLINGER BANDS
  def is_bollinger_bands(self):
    close_p = self.candles["close"].to_numpy(dtype=float)
    upper,middle,lower = talib.BBANDS(close_p, timeperiod=20)
    near_support = self.candles["low"].iloc[-2] <= lower[-2]
    near_resistance = self.candles["high"].iloc[-2] >= upper[-2]
    return near_support, near_resistance


  def get_last_candle_pattern(self):
    pattern_results: dict = self.patterns_analysis()
    bullish_pattern = {}
    bearish_pattern = {}
    is_anomaly_volume = self.is_anomaly_volume()
    near_support, near_resistance = self.is_bollinger_bands()


    logger.info(f"Volume high {is_anomaly_volume}")
    logger.info(f"Bollinger Bands. Support: {near_support}, Resistance: {near_resistance}")

    for pattern_name, values in pattern_results.items():
      last_value = values[-2]

      if last_value > 0:
        bullish_pattern[pattern_name] = "BULLISH"
        logger.info("Bullish pattern: " + pattern_name)
      elif last_value < 0:
        bearish_pattern[pattern_name] = "BEARISH"
        logger.info("Bearish pattern: " + pattern_name)

    if bullish_pattern and bearish_pattern:
      logger.info("Patterns conflict -> HOLD")
    elif bullish_pattern and self.delta > 0:
      if is_anomaly_volume and near_support:
        logger.info(f"Bullish pattern found {bullish_pattern} and delta {self.delta} -> BUY")
      else:
        logger.info(f"Bullish pattern found {bullish_pattern} but filters reject -> HOLD")
    elif bearish_pattern and self.delta < 0:
      if is_anomaly_volume and near_resistance:
        logger.info(f"Bearish pattern found {bearish_pattern} and delta {self.delta} -> SELL")
      else:
        logger.info(f"Bearish pattern found {bearish_pattern} but filters reject -> HOLD")
    else:
      logger.info("Not patterns -> HOLD")


    return bullish_pattern, bearish_pattern

