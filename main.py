import logging
from services import ConnectToExchange, ConvertToPandas, PatternService

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
  connection = ConnectToExchange(timeframe='1h')
  connection.start()
  candles = connection.fetch_candles()
  df = ConvertToPandas(candles=candles)
  logger.info("Output 5 candles: \n%s",df.pd_candles.head())
  patterns = PatternService(candles=df.pd_candles())
  logger.info("Output patterns", patterns.get_patterns())

