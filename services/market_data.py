import asyncio
import logging
from typing import Any

import ccxt.async_support as ccxt



logger = logging.getLogger(__name__)


class MarketData:

    def __init__(self, exchange,symbol, timeframe, limit) -> None:
        self.exchange = exchange
        self.symbol = symbol
        self.timeframe = timeframe
        self.limit = limit

    async def fetch_market_symbols(self) -> list[str]:
        try:
            markets = await self.exchange.load_markets()
            symbols = [
                symbol
                for symbol, market in markets.items()
                if market.get("active") and market.get("spot")
            ]

            logger.info(
                f"Fetch market symbols: {len(symbols)} complete!"
            )

            return symbols
        except ccxt.BaseError as e:
            logger.error(
                f"Fetch market data error: {e}"
            )
            raise

    async def fetch_ticker(self, symbol: str) -> dict:
        try:
            return await self.exchange.fetch_ticker(symbol)
        except ccxt.BaseError as e:
            logger.error(
                f"Fetch ticker error {symbol}: {e}"
            )
            raise

    async def fetch_candles(self,symbol: str,timeframe: str,limit: int) -> dict[str, Any] | None:
      try:
        all_candles = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

        if len(all_candles) >= 2:
          return all_candles

        logger.warning(f"Not enough candles history for {symbol} (got {len(all_candles)})")
        return None
      except ccxt.BaseError as e:
        logger.error(f"Fetch candles error {symbol} {timeframe}: {e}")
        raise

    async def fetch_order_book(self, symbol: str) -> dict:
        try:
            return await self.exchange.fetch_order_book(symbol)
        except ccxt.BaseError as e:
            logger.error(
                f"Fetch order book error {symbol}: {e}"
            )
            raise

    async def fetch_trades(self, symbol: str) -> list:
        try:
            return await self.exchange.fetch_trades(symbol)
        except ccxt.BaseError as e:
            logger.error(
                f"Fetch trades error {symbol}: {e}"
            )
            raise

    async def fetch_balances(self):
      try:
        balance = await self.exchange.fetch_balance(params={"type": "spot", "omitZeroBalances": True})
        return balance

      except ccxt.BaseError as e:
        logger.error(f"Fetch balance error: {e}")
        return "Not available"


    async def get_market_data(self):
      async with asyncio.TaskGroup() as tg:
        t_ticker = tg.create_task(self.fetch_ticker(self.symbol))
        t_candles = tg.create_task(self.fetch_candles(self.symbol, self.timeframe, self.limit))
        t_order_book = tg.create_task(self.fetch_order_book(self.symbol))
        t_trades = tg.create_task(self.fetch_trades(self.symbol))
        #t_balance = tg.create_task(self.fetch_balances())

      return {
        "ticker": t_ticker.result(),
        "candles": t_candles.result(),
        "order_book": t_order_book.result(),
        "trades": t_trades.result(),
        #"balance": t_balance.result(),
      }

