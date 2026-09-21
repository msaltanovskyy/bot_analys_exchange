import logging
import ccxt.async_support as ccxt

logger = logging.getLogger(__name__)

class ConnectToExchange:

    def __init__(self, exchange_name: str = "binance") -> None:

        try:
            if exchange_name.lower() == "binance":
                self.exchange = ccxt.binance({
                    "enableRateLimit": True,
                })

            elif exchange_name.lower() == "bybit":
                self.exchange = ccxt.bybit({
                    "enableRateLimit": True,
                })

            else:
                raise ValueError(
                    f"Unsupported exchange: {exchange_name}"
                )

            logger.info(f"Connected to {exchange_name}")

        except Exception as e:
            logger.error(
                f"Connection to {exchange_name} failed: {e}"
            )
            raise


    def get_exchange(self):
        return self.exchange

    async def close_connection(self) -> None:
        await self.exchange.close()
