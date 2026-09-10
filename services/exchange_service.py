import logging
from typing import Any, List, Optional
import ccxt
from ccxt.base.types import OrderBook, Trade

logger = logging.getLogger(__name__)


class ConnectToExchange:

  def __init__(self, timeframe: str = '1m') -> None:
    self.timeframe = timeframe
    self.market_symbol: str = ''
    self.candles: List[List[Any]] = []
    self.spread: float = 0.0
    self.delta: float = 0.0
    self.imbalance: float = 0.0
    self.market_symbols: dict = {}

    try:
      self.exchange = ccxt.binance({
          'enableRateLimit': True,
      })
      self.market_symbols = self.exchange.load_markets()
    except ccxt.BaseError as e:
      logger.error(f"Error loading market info or connection: {e}")

  def get_delta(self):
    return self.delta

  def set_market_symbol(self) -> str:
    while True:
      user_symbol = input("Set market symbol (def. BTC/USDT): ").strip().upper()
      if not user_symbol:
        user_symbol = 'BTC/USDT'

      if user_symbol in self.market_symbols:
        self.market_symbol = user_symbol
        logger.info(f"Market symbol set to: {self.market_symbol}")
        return self.market_symbol

      logger.info(f"Symbol not found: {user_symbol}. Try again!")

  def fetch_ticker(self) -> int | float:
    for attempt in range(1, 6):
      try:
        ticker = self.exchange.fetch_ticker(self.market_symbol)
        #logger.info(f"Fetched ticker: {ticker}")

        ask = ticker.get('ask')
        bid = ticker.get('bid')
        last = ticker.get('last')

        if ask is not None and bid is not None and last:
          self.spread = (ask - bid) / last
          logger.info(f"Spread: {self.spread:.6%}")
          return self.spread

        logger.error(
            f"Attempt {attempt}/5: Incomplete data (Ask: {ask}, Bid: {bid},"
            f" Last: {last})"
        )
      except ccxt.BaseError as e:
        logger.error(f"Attempt {attempt}/5 failed with API error: {e}")

    return None

  def fetch_candles(self) -> Optional[List[List[Any]]]:
    for attempt in range(1, 6):
      try:
        candles = self.exchange.fetch_ohlcv(
            self.market_symbol, self.timeframe, limit = 500
        )
        if candles:
          logger.info(f"Fetched candles count: {len(candles)}, timeframe {self.timeframe}")
          self.candles = candles
          return candles
        logger.error(f"Attempt {attempt}/5: Empty candles data received.")
      except ccxt.BaseError as e:
        logger.error(f"Attempt {attempt}/5 failed: {e}")

    return None

  def fetch_order_book(self) -> Optional[OrderBook]:
    for attempt in range(1, 6):
      try:
        order_book = self.exchange.fetch_order_book(
            self.market_symbol, limit=10
        )
        bid_volume = sum(amount for price, amount in order_book.get('bids', []))
        ask_volume = sum(amount for price, amount in order_book.get('asks', []))

        total_volume = bid_volume + ask_volume
        if total_volume > 0:
          self.imbalance = (bid_volume - ask_volume) / total_volume
          logger.info(f"Imbalance: {self.imbalance:.4f}")
        else:
          self.imbalance = 0.0

        return order_book
      except ccxt.BaseError as e:
        logger.error(f"Attempt {attempt}/5 failed: {e}")

    return None

  def fetch_trades(self) -> Optional[List[Trade]]:
    try:
      trades = self.exchange.fetch_trades(self.market_symbol)

      buy_volume = sum(
          trade['amount'] for trade in trades if trade.get('side') == 'buy'
      )
      sell_volume = sum(
          trade['amount'] for trade in trades if trade.get('side') == 'sell'
      )

      self.delta = buy_volume - sell_volume
      logger.info(
          f"Buy vol: {buy_volume:.4f} | Sell vol: {sell_volume:.4f} | Delta:"
          f" {self.delta:.4f}"
      )
      return trades
    except ccxt.BaseError as e:
      logger.error(f"Fetch trades error: {e}")
      return None

  def start(self):
    self.set_market_symbol()
    self.fetch_ticker()
    self.fetch_order_book()
    self.fetch_trades()

