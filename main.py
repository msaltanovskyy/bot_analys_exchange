import json
import asyncio
import logging
import pandas as pd
from services import ConnectToExchange, MarketData, OrderFlowAnalys
from core import Analysis, analysis

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

with open('config.json', 'r') as f:
  config = json.load(f)

CONFIG_MARKET_SYMBOLS = config["analysis"]["symbols"]
TIMEFRAMES = config["analysis"]["timeframes"]
LIMIT = config["analysis"]["limit"]


async def main():

    connect = ConnectToExchange()
    exchange = connect.get_exchange()

    for symbol in CONFIG_MARKET_SYMBOLS:
      for tf in TIMEFRAMES:
        md = MarketData(exchange, symbol,timeframe=tf,limit=LIMIT)
        logger.info(
            f"\n---------------- Checking {symbol}, {tf} ----------------"
        )

        analysis = Analysis(market_data=md)
        await analysis.analyze(symbol=symbol,timeframe=tf, limit=LIMIT)

    await connect.close_connection()

if __name__ == '__main__':
    asyncio.run(main())
