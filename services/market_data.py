import logging

import ccxt.async_support as ccxt


logger = logging.getLogger(__name__)


class MarketData:

    def __init__(self, exchange) -> None:
        self.exchange = exchange

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

    async def fetch_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> list:

        try:
            return await self.exchange.fetch_ohlcv(
                symbol,
                timeframe,
                limit=limit,
            )

        except ccxt.BaseError as e:
            logger.error(
                f"Fetch candles error {symbol} {timeframe}: {e}"
            )
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

