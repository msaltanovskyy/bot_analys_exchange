import asyncio
import logging
from services import ConnectToExchange, ConvertToPandas, PatternService, IndicatorService

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CONFIG_MARKET_SYMBOLS = ['BTC/USD', 'ETH/USD', 'BTC/USDT', 'SOL/USDT']


if __name__ == '__main__':

  for symbol in CONFIG_MARKET_SYMBOLS:
    logger.info(f"\n----------------Checking {symbol}----------------------")
    connection = ConnectToExchange(timeframe='1h', market_symbol=symbol)
    asyncio.run(connection.start())
    candles = connection.candles
    pd = ConvertToPandas(candles)
    # logger.info("Output 5 candles: \n%s",pd.df_candles.tail())
    patterns = PatternService(candles=pd.df_candles, delta=connection.get_delta())
    patterns.get_last_candle_pattern()
    indicator = IndicatorService(candles=pd.df_candles)
    indicator.get_trend()

