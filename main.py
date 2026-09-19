import asyncio
import logging

from services import ConnectToExchange, MarketData, OrderFlowAnalys, PatternAnalyzer, IndicatorAnalyzer, AnalysisResult

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
    data = MarketData(exchange)


    for symbol in CONFIG_MARKET_SYMBOLS:

        logger.info(
            f"\n---------------- Checking {symbol} ----------------"
        )

        ticker = await data.fetch_ticker(symbol)
        candles = await data.fetch_candles(
            symbol,
            TIMEFRAME,
            LIMIT
        )
        book = await data.fetch_order_book(symbol)
        trades = await data.fetch_trades(symbol)
        market = await data.fetch_market_symbols()

        order_flow = OrderFlowAnalys()
        spread = order_flow.calculate_spread(ticker)
        imbalance = order_flow.calculate_imbalance(book)
        delta = order_flow.calculate_delta(trades)

        pattern_analyzer = PatternAnalyzer(candles)
        pattern_result = pattern_analyzer.analyze()

        indicator_analyzer = IndicatorAnalyzer(candles,delta)
        indicator_result = (indicator_analyzer.get_analysis())

        result = AnalysisResult(pattern_result,indicator_result)
        score = result.calculate_score()
        signal = result.generate_signal()

        logger.info(
          f"{symbol} -> "
          f"Score: {score:.2f} | "
          f"Signal: {signal}"
        )

    await connect.close_connection()

if __name__ == '__main__':
    asyncio.run(main())
