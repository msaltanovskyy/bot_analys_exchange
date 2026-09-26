import asyncio
import logging
from dataclasses import asdict

import pandas as pd

from services import OrderFlowAnalys
from analysis import PatternAnalyzer
from analysis import IndicatorAnalyzer
from analysis import AnalysisResult
from data import AnalysisData

logger = logging.getLogger(__name__)


class Analysis:

    def __init__(self, market_data):
        self.market_data = market_data

    async def analyze(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> dict:

        ticker_task = self.market_data.fetch_ticker(symbol)
        candles_task = self.market_data.fetch_candles(
            symbol,
            timeframe,
            limit,
        )
        order_book_task = self.market_data.fetch_order_book(symbol)
        trades_task = self.market_data.fetch_trades(symbol)

        ticker, candles, order_book, trades = await asyncio.gather(
            ticker_task,
            candles_task,
            order_book_task,
            trades_task,
        )

        dataframe = pd.DataFrame(
            candles,
            columns=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ],
        )

        dataframe["timestamp"] = pd.to_datetime(
            dataframe["timestamp"],
            unit="ms",
            utc=True,
        )

        if len(dataframe) < 3:
            raise ValueError(
                f"Not enough candles for {symbol} {timeframe}"
            )

        order_flow = OrderFlowAnalys()

        spread = order_flow.calculate_spread(ticker)
        imbalance = order_flow.calculate_imbalance(order_book)
        delta = order_flow.calculate_delta(trades)

        pattern_result = PatternAnalyzer(
            dataframe
        ).analyze()

        indicator_result = IndicatorAnalyzer(
            dataframe,
            delta,
        ).get_analysis()

        result = AnalysisResult(
            pattern_result,
            indicator_result,
        )

        score = result.calculate_score()
        signal = result.generate_signal()

        closed_candle = dataframe.iloc[-2]
        current_candle = dataframe.iloc[-1]

        analysis = result.get_result()

        data = AnalysisData(
          symbol = symbol,
          timeframe = timeframe,
          spread = spread,
          imbalance = imbalance,
          delta = delta,
          rsi=indicator_result['rsi'],
          ema200=indicator_result['ema200'],
          close_price=indicator_result["close_price"],
          is_uptrend=indicator_result["is_uptrend"],
          volume_anomaly=indicator_result["volume_anomaly"],
          near_support=indicator_result["near_support"],
          near_resistance=indicator_result["near_resistance"],
          candles=candles,
          closed_candle_timestamp=closed_candle['timestamp'],
          current_candle_timestamp=current_candle['timestamp'],
          score=score,
          signal=signal
        )

        analysis.update(asdict(data))

        return analysis
