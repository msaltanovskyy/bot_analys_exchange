import asyncio
import logging
import pandas as pd
from services import ConnectToExchange, MarketData, OrderFlowAnalys
from analysis import IndicatorAnalyzer, AnalysisResult, PatternAnalysis, MultiframeAnalys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


CONFIG_MARKET_SYMBOLS = ['BTC/USDT', 'BTC/USD', 'ETH/BTC']

TIMEFRAME = '4h'
LIMIT = 500


async def main():

    connect = ConnectToExchange()
    exchange = connect.get_exchange()



    for symbol in CONFIG_MARKET_SYMBOLS:
        md = MarketData(exchange, symbol,timeframe=TIMEFRAME,limit=LIMIT)
        data = await md.get_market_data()
        logger.info(
            f"\n---------------- Checking {symbol} ----------------"
        )

        ticker = data.get("ticker")
        candles = pd.DataFrame.from_records(data.get("candles"),
                                            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        book = data.get("order_book")
        trades = data.get("trades")
        #market = data.get("symbols")
        #balance = data.get("balance")

        order_flow = OrderFlowAnalys()
        spread = order_flow.calculate_spread(ticker)
        imbalance = order_flow.calculate_imbalance(book)
        delta = order_flow.calculate_delta(trades)

        pattern_analyzer = PatternAnalysis(candles)
        pattern_result = pattern_analyzer.analyze()

        indicator_analyzer = IndicatorAnalyzer(candles,delta)
        indicator_result = (indicator_analyzer.get_analysis())

        result = AnalysisResult(pattern_result, indicator_result)
        score = result.calculate_score()
        signal = result.generate_signal()
        mtf_analysis = MultiframeAnalys(

        )

        logger.info(
          f"{symbol} -> "
          f"Score: {score:.2f} | "
          f"Signal: {signal}"
        )

    await connect.close_connection()

if __name__ == '__main__':
    asyncio.run(main())
