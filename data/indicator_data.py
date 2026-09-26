from dataclasses import dataclass


@dataclass
class IndicatorData:
  ema200:str
  close_price:float
  is_uptrend:bool
  delta:float
  volume_anomaly:float
  near_support:bool
  near_resistance:float
  rsi:float
  rsi_oversold:float
  rsi_overbought:float
  macd:float
  macd_hist:float
  macd_bullish:float
  macd_bearish:float
  vwap:float
  above_vwap:float
