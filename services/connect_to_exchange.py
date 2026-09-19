import ccxt.async_support as ccxt


class ConnectToExchange:

    def __init__(self) -> None:
        self.exchange = ccxt.binance({
            "enableRateLimit": True,
        })

    def get_exchange(self):
        return self.exchange

    async def close_connection(self) -> None:
        await self.exchange.close()
