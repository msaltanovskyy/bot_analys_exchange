from dataclasses import dataclass

@dataclass
class MarketModel:
  ticker: dict
  candles:dict
  order_book:dict
  trades:dict
