from dataclasses import dataclass

import pandas as pd


@dataclass
class AnalysisData:
  symbol: str
  timeframe: str
  spread: float
  imbalance: float
  delta: float
  rsi: float
  ema200: float
  close_price: float
  is_uptrend: bool
  volume_anomaly: float
  near_support: float
  near_resistance: float
  candles: pd.DataFrame
  closed_candle_timestamp: int
  current_candle_timestamp: int
  score: float
  signal: str

