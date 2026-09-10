import logging
from services import ConnectToExchange, ConvertToPandas, PatternService, IndicatorService

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
  connection = ConnectToExchange(timeframe='1h')
  connection.start()
  candles = connection.fetch_candles()
  pd = ConvertToPandas(candles)
  #logger.info("Output 5 candles: \n%s",pd.df_candles.tail())
  patterns = PatternService(candles=pd.df_candles, delta=connection.get_delta())
  patterns.get_last_candle_pattern()
  indicator = IndicatorService(candles = pd.df_candles)
  indicator.get_trend()

