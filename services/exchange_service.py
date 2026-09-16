import logging
import asyncio
from typing import Any, List, Optional
import ccxt.async_support as ccxt
from ccxt.base.types import OrderBook, Trade

logger = logging.getLogger(__name__)


class ConnectToExchange:

  market_symbol = ''

  def __init__(self, timeframe, market_symbol) -> None:
    self.timeframe = timeframe
    self.market_symbol: str = ''
    self.candles: List[List[Any]] = []
    self.spread: float = 0.0
    self.delta: float = 0.0
    self.imbalance: float = 0.0
    self.market_symbol = market_symbol
    self.market_symbols = []
    self.exchange: ccxt.Exchange = ccxt.binance({
      'enableRateLimit': True,
    })

  async def initialize(self) -> None:
    self.market_symbols = await self.exchange.load_markets()

  async def close_connection(self) -> None:
    await self.exchange.close()


  def get_delta(self):
    return self.delta


  def check_market_symbol(self) -> bool:
    if self.market_symbol in self.market_symbols:
      logger.info(f"Market symbol set to: {self.market_symbol}")
      return True
    else:
      logger.warning(f"Symbol not found: {self.market_symbol}. Config not correct!")
      return False

  async def fetch_ticker(self) -> int | float:
    for attempt in range(1, 6):
      try:
        ticker = await self.exchange.fetch_ticker(self.market_symbol)
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

  async def fetch_candles(self) -> Optional[List[List[Any]]]:
    for attempt in range(1, 6):
      try:
        candles = await self.exchange.fetch_ohlcv(
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

  async def fetch_order_book(self) -> Optional[OrderBook]:
    for attempt in range(1, 6):
      try:
        order_book = await self.exchange.fetch_order_book(
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

  async def fetch_trades(self) -> Optional[List[Trade]]:
    try:
      trades = await self.exchange.fetch_trades(self.market_symbol)

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

  async def start(self) -> None:
    try:

      await self.initialize()

      check_sym = self.check_market_symbol()
      if check_sym:
        await asyncio.gather(
          self.fetch_ticker(),
          self.fetch_order_book(),
          self.fetch_trades(),
          self.fetch_candles()
        )
        logger.info("Operations finished successfully!")
      else:
        logger.warning("Aborted due to invalid market symbol.")
    finally:
      await self.close_connection()
      logger.info("Connection closed!")

