import asyncio

from services import ConnectToExchange, MarketData


def load_symbols():
  async def _load():
    connection = ConnectToExchange()
    try:
      market_data = MarketData(connection.get_exchange())
      return await market_data.fetch_market_symbols()
    finally:
      await connection.close_connection()

  return asyncio.run(_load())
