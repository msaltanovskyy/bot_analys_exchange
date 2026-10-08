from dataclasses import dataclass


@dataclass
class MFData:
  symbol:str
  timeframes: str
  tf_details:dict
  overall_signal:str
  trend_alignment:str
