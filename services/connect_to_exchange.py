import ccxt.async_support as ccxt


class ConnectToExchange:

    def __init__(self) -> None:
      self.exchange = ccxt.binance({
        'enableRateLimit': True,
        'options': {
          'defaultType': 'spot',
        },
        # Подключаем альтернативный домен API, не блокируемый в США
        'urls': {
          'api': {
            'public': 'https://api1.binance.com/api/v3',
            'private': 'https://api1.binance.com/api/v3',
          }
        }
      })
    def get_exchange(self):
        return self.exchange

    async def close_connection(self) -> None:
        await self.exchange.close()
