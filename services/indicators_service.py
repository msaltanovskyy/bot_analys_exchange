import numpy as np
import talib
from pandas import DataFrame
import logging

logger = logging.getLogger(__name__)

class IndicatorService:
  candles: DataFrame
  def __init__(self, candles):
    self.candles = candles

  def indicators_analysis(self) -> dict:
    close_p = self.candles["close"].to_numpy(dtype=float)

    result = {
      "ema200": talib.EMA(close_p, timeperiod=200),
    }

    return result

  def get_trend(self):
    indicators = self.indicators_analysis()

    ema = indicators['ema200']

    if ema is None or len(ema) < 201:
      logger.warning("IndicatorService.get_trend : ema200 is None or > 201")

    last_ema = float(ema[-2])

    if np.isnan(last_ema):
      logger.warning("IndicatorService.get_trend : last_ema is None (NaN)")

    last_close = float(self.candles['close'].iloc[-2])
    diff_precent = ((last_close-last_ema)/last_ema)*100
    if diff_precent > 0.15:
      logger.info(f"Trend BULLISH (Close: {last_close:.2f} > EMA200: {last_ema:.2f})")
      return "BULLISH"
    elif diff_precent < -0.15:
      logger.info(f"Trend BEARISH (Close: {last_close:.2f} < EMA200: {last_ema:.2f})")
      return "BEARISH"
    else:
      logger.info(f"Trend NEUTRAL / FLAT (Close: {last_close:.2f} near EMA200: {last_ema:.2f})")
      return "NEUTRAL"


