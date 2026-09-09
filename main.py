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
  df = ConvertToPandas(candles)
  logger.info("Output 5 candles: \n%s",df.df_candles.tail())
  patterns = PatternService(candles=df.df_candles)
  patterns_results = patterns.patterns_analysis()
  logger.info(f"Output patterns {patterns_results}")

