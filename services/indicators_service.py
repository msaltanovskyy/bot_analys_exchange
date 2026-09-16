import numpy as np
import talib
from pandas import DataFrame
import logging

logger = logging.getLogger(__name__)

class IndicatorService:
  candles: DataFrame
  indicators_result = []

  def __init__(self, candles):
    self.candles = candles
    self.indicators_result = self.indicators_analysis()


  def indicators_analysis(self) -> dict:
    close_p = self.candles["close"].to_numpy(dtype=float)
    volume_p = self.candles["volume"].to_numpy(dtype=float)
    result = {
      "ema200": talib.EMA(close_p, timeperiod=200),
      "rsi":talib.RSI(close_p, timeperiod=20),
      "sma":talib.SMA(close_p, timeperiod=20),
      "bbands": talib.BBANDS(volume_p, timeperiod=20),
    }

    return result

  def is_rsi(self):
    rsi = self.indicators_result['rsi']


  def is_sma(self):
    sma = self.indicators_result['sma']

  def is_bbands(self):
    bbands = self.indicators_result['bbands']


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
      trend_bullish = "BULLISH"
      logger.info(f"Trend BULLISH (Close: {last_close:.2f} > EMA200: {last_ema:.2f})")
      return trend_bullish
    elif diff_precent < -0.15:
      trend_bearish = "BEARISH"
      logger.info(f"Trend BEARISH (Close: {last_close:.2f} < EMA200: {last_ema:.2f})")
      return trend_bearish
    else:
      trend_neutral = "NEUTRAL"
      logger.info(f"Trend NEUTRAL / FLAT (Close: {last_close:.2f} near EMA200: {last_ema:.2f})")
      return trend_neutral


