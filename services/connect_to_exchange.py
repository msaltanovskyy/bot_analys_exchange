import logging
import ccxt.async_support as ccxt
from .env_config import EnvConfig

logger = logging.getLogger(__name__)

class ConnectToExchange:

    def __init__(self, exchange_name: str = "binance") -> None:
        config = EnvConfig()
        try:
          if config.DEBUG_MODE:
            self.exchange = ccxt.binance(
              {
                "apiKey": config.PUBLIC_TESTNET_API_KEY,
                "secret": config.PRIVATE_TESTNET_API_KEY,
                "enableRateLimit": True,
              }
            )
            self.exchange.set_sandbox_mode(True)
            logger.info(f"Connected to {exchange_name}, DEBUG_MODE = {config.DEBUG_MODE}")
            logger.info(f"API keys: {config.PUBLIC_TESTNET_API_KEY} \n {config.PRIVATE_TESTNET_API_KEY} ")
          else:
            self.exchange = ccxt.binance({
              "enableRateLimit": True,
            })
            logger.info(f"Connected to {exchange_name}, DEBUG_MODE = {config.DEBUG_MODE}")
        except Exception as e:
            logger.error(
                f"Connection to {exchange_name} failed: {e}"
            )
            raise


    def get_exchange(self):
        return self.exchange

    async def close_connection(self) -> None:
        await self.exchange.close()
