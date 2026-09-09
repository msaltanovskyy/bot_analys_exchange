import pandas
import talib
from pandas import DataFrame


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
    }

    last_candle_patterns = {}

    for pattern_name, values in results.items():
      last_value = values[-1]

      if last_value > 0:
        last_candle_patterns[pattern_name] = "BULLISH" 
      elif last_value < 0:
        last_candle_patterns[pattern_name] = "BEARISH"

    return last_candle_patterns

