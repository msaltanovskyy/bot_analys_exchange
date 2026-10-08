import json
import asyncio
import logging
import pandas as pd
from services import ConnectToExchange, MarketData, OrderFlowAnalys
from core import IndicatorAnalyzer, AnalysisResult, PatternAnalysis, MultiframeAnalys

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
        data = await md.get_market_data()
        logger.info(
            f"\n---------------- Checking {symbol}, {tf} ----------------"
        )

        ticker = data.ticker
        candles = pd.DataFrame.from_records(data.candles,
                                            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        book = data.order_book
        trades = data.trades
        #market = data.get("symbols")
        #balance = data.get("balance")

        order_flow = OrderFlowAnalys()
        order_flow_result = order_flow.calculate_result(trades, book, ticker)
        spread = order_flow_result.get("spread")
        imbalance = order_flow_result.get("imbalance")
        delta = order_flow_result.get("delta")

        pattern_analyzer = PatternAnalysis(candles)
        pattern_result = pattern_analyzer.analyze()

        indicator_analyzer = IndicatorAnalyzer(candles,delta)
        indicator_result = (indicator_analyzer.get_analysis())

        result = AnalysisResult(pattern_result, indicator_result)
        score = result.calculate_score()
        signal = result.generate_signal()
        #mtf_analysis = MultiframeAnalys(

        #)

        logger.info(
          f"{symbol} -> "
          f"Score: {score:.2f} | "
          f"Signal: {signal}"
        )

    await connect.close_connection()

if __name__ == '__main__':
    asyncio.run(main())
