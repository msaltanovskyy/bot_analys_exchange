import pandas as pd
from pandas import DataFrame


class ConvertToPandas:
  candles = []
  pd_candles = []

  def __init__(self, candles):
    self.candles = candles
    self.pd_candles = self.convert_to_pandas()

  def convert_to_pandas(self) -> DataFrame:
    columns = ['timestamp','open','high','low','close','volume']
    df = pd.DataFrame(self.candles, columns=columns)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    return df
