import asyncio
import logging
import threading
from datetime import datetime, timezone

from services import ConnectToExchange
from services import MarketData
from services.analysis_service import AnalysisService


logger = logging.getLogger(__name__)


class AnalysisScheduler:

    def __init__(
        self,
        symbols: list[str],
        timeframes: list[str],
        results: dict,
        lock: threading.Lock,
        stop_event: threading.Event,
        max_concurrent_tasks: int = 5,
    ) -> None:

        self.symbols = symbols
        self.timeframes = timeframes

        self.results = results
        self.lock = lock
        self.stop_event = stop_event

        self.max_concurrent_tasks = max_concurrent_tasks

        self.semaphore = None

        self.exchange_connection = None
        self.market_data = None
        self.analysis_service = None

        self.last_processed = {}

    # ========================================================
    # START
    # ========================================================

    async def start(self) -> None:

        logger.info(
            "Analysis scheduler starting..."
        )

        self.semaphore = asyncio.Semaphore(
            self.max_concurrent_tasks
        )

        self.exchange_connection = ConnectToExchange()

        exchange = (
            self.exchange_connection.get_exchange()
        )

        self.market_data = MarketData(
            exchange
        )

        self.analysis_service = AnalysisService(
            self.market_data
        )

        try:

            await self._initial_analysis()

            await self._run_loop()

        finally:

            logger.info(
                "Closing exchange connection..."
            )

            await (
                self.exchange_connection
                .close_connection()
            )

            logger.info(
                "Analysis scheduler stopped."
            )

    # ========================================================
    # INITIAL ANALYSIS
    # ========================================================

    async def _initial_analysis(self) -> None:

        logger.info(
            "Starting initial market analysis..."
        )

        tasks = [
            self._analyze_symbol(
                symbol=symbol,
                timeframe=timeframe,
                initial=True,
            )
            for symbol in self.symbols
            for timeframe in self.timeframes
        ]

        if not tasks:

            logger.warning(
                "No symbols or timeframes selected."
            )

            return

        results = await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )

        for task_result in results:

            if isinstance(
                task_result,
                Exception,
            ):

                logger.error(
                    f"Initial analysis task failed: "
                    f"{task_result}"
                )

        logger.info(
            "Initial market analysis completed."
        )

    # ========================================================
    # MAIN LOOP
    # ========================================================

    async def _run_loop(self) -> None:

        while not self.stop_event.is_set():

            tasks = [
                self._check_symbol(
                    symbol,
                    timeframe,
                )
                for symbol in self.symbols
                for timeframe in self.timeframes
            ]

            if tasks:

                await asyncio.gather(
                    *tasks,
                    return_exceptions=True,
                )

            # Проверяем новые свечи каждые 5 секунд
            try:

                await asyncio.wait_for(
                    asyncio.to_thread(
                        self.stop_event.wait,
                        5,
                    ),
                    timeout=5,
                )

            except asyncio.TimeoutError:

                pass

    # ========================================================
    # CHECK SYMBOL
    # ========================================================

    async def _check_symbol(
        self,
        symbol: str,
        timeframe: str,
    ) -> None:

        try:

            candles = (
                await self.market_data.fetch_candles(
                    symbol,
                    timeframe,
                    limit=3,
                )
            )

            if len(candles) < 2:

                logger.warning(
                    f"Not enough candles: "
                    f"{symbol} {timeframe}"
                )

                return

            # ------------------------------------------------
            # CCXT timestamp:
            #
            # candles[-1][0] -> current candle
            # candles[-2][0] -> closed candle
            #
            # timestamp приходит как milliseconds int.
            # ------------------------------------------------

            closed_timestamp = datetime.fromtimestamp(
                candles[-2][0] / 1000,
                tz=timezone.utc,
            )

            key = (
                symbol,
                timeframe,
            )

            last_timestamp = (
                self.last_processed.get(key)
            )

            # ------------------------------------------------
            # Свеча уже была обработана
            # ------------------------------------------------

            if (
                last_timestamp is not None
                and closed_timestamp <= last_timestamp
            ):

                return

            logger.info(
                f"New closed candle: "
                f"{symbol} {timeframe} | "
                f"closed={closed_timestamp}"
            )

            await self._analyze_symbol(
                symbol=symbol,
                timeframe=timeframe,
                initial=False,
                closed_timestamp=closed_timestamp,
            )

        except Exception:

            logger.exception(
                f"Analysis check error: "
                f"{symbol} {timeframe}"
            )

    # ========================================================
    # ANALYZE SYMBOL
    # ========================================================

    async def _analyze_symbol(
        self,
        symbol: str,
        timeframe: str,
        initial: bool = False,
        closed_timestamp=None,
    ) -> None:

        async with self.semaphore:

            try:

                logger.info(
                    f"Starting analysis: "
                    f"{symbol} {timeframe}"
                )

                result = (
                    await self.analysis_service.analyze(
                        symbol,
                        timeframe,
                    )
                )

                key = (
                    symbol,
                    timeframe,
                )

                # ------------------------------------------------
                # При первом анализе timestamp приходит из
                # AnalysisService как pandas. Timestamp.
                #
                # Приводим его к обычному datetime UTC.
                # ------------------------------------------------

                if initial:

                    closed_timestamp = (
                        result[
                            "closed_candle_timestamp"
                        ]
                    )

                    if hasattr(
                        closed_timestamp,
                        "to_pydatetime",
                    ):

                        closed_timestamp = (
                            closed_timestamp.to_pydatetime()
                        )

                # ------------------------------------------------
                # Сохраняем результат
                # ------------------------------------------------

                with self.lock:

                    self.results[key] = result

                # ------------------------------------------------
                # Запоминаем последнюю обработанную свечу
                # ------------------------------------------------

                self.last_processed[key] = (
                    closed_timestamp
                )

                logger.info(
                    f"Analysis completed: "
                    f"{symbol} {timeframe} | "
                    f"closed candle="
                    f"{closed_timestamp}"
                )

            except Exception:

                logger.exception(
                    f"Analysis error: "
                    f"{symbol} {timeframe}"
                )
