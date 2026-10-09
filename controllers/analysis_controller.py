import asyncio
import logging
import threading
from datetime import datetime, timezone

from services import ConnectToExchange
from services import MarketData
from core import Analysis, MultiframeAnalys

logger = logging.getLogger(__name__)


class AnalysisController:

  def __init__(
    self,
    symbols: list[str],
    timeframes: list[str],
    results: dict,
    lock: threading.Lock,
    stop_event: threading.Event,
    max_concurrent_tasks: int = 5,
    limit: int = 0,
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

    self.limit = limit

  async def start(self) -> None:
    logger.info("Analysis scheduler starting...")
    self.semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
    self.exchange_connection = ConnectToExchange()

    exchange = self.exchange_connection.get_exchange()
    self.market_data = MarketData(exchange)
    self.analysis_service = Analysis(self.market_data)

    try:
      await self._initial_analysis()
      await self._run_loop()
    finally:
      logger.info("Closing exchange connection...")
      await self.exchange_connection.close_connection()
      logger.info("Analysis scheduler stopped.")

  async def _initial_analysis(self) -> None:
    logger.info("Starting initial market analysis...")
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
      logger.warning("No symbols or timeframes selected.")
      return

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for task_result in results:
      if isinstance(task_result, Exception):
        logger.error(f"Initial analysis task failed: {task_result}")

    logger.info("Initial market analysis completed.")

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
        await asyncio.gather(*tasks, return_exceptions=True)
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

  async def _check_symbol(self, symbol: str, timeframe: str) -> None:
    try:
      candles = await self.market_data.fetch_candles(
        symbol,
        timeframe,
        limit=self.limit,
      )
      if not candles or len(candles) < 2:
        logger.warning(f"Not enough candles: {symbol} {timeframe}")
        return

      closed_timestamp = datetime.fromtimestamp(
        candles[-2][0] / 1000,
        tz=timezone.utc,
      )
      key = (symbol, timeframe)
      last_timestamp = self.last_processed.get(key)

      if last_timestamp is not None and closed_timestamp <= last_timestamp:
        return

      logger.info(
        f"New closed candle: {symbol} {timeframe} | closed={closed_timestamp}"
      )
      await self._analyze_symbol(
        symbol=symbol,
        timeframe=timeframe,
        initial=False,
        closed_timestamp=closed_timestamp,
      )
    except Exception:
      logger.exception(f"Analysis check error: {symbol} {timeframe}")

  async def _analyze_symbol(
    self,
    symbol: str,
    timeframe: str,
    initial: bool = False,
    closed_timestamp=None,
  ) -> None:
    async with self.semaphore:
      try:
        result = await self.analysis_service.analyze(symbol, timeframe, self.limit)
        key = (symbol, timeframe)

        if initial:
          closed_timestamp = result.get("closed_candle_timestamp")
          if hasattr(closed_timestamp, "to_pydatetime"):
            closed_timestamp = closed_timestamp.to_pydatetime()

        with self.lock:
          self.results[key] = result
        self.last_processed[key] = closed_timestamp

        signal = result.get("signal", "HOLD")
        score = result.get("score", 0.0)
        is_uptrend = "🟢 BULL" if result.get("is_uptrend") else "🔴 BEAR"
        sig_icon = "🟢" if "BUY" in signal else ("🔴" if "SELL" in signal else "⚪")

        logger.info(
          f"  ├─ [{symbol:<8} | {timeframe:<3}] {sig_icon} {signal:<16} | "
          f"Score: {score:+5.1f} | Trend: {is_uptrend}"
        )

        mtf = MultiframeAnalys(
          results=self.results,
          symbol=symbol,
          timeframes=self.timeframes,
          lock=self.lock
        )
        mf_result = mtf.mf_analysis()

        if len(mf_result.tf_details) == len(self.timeframes):
          self._log_mtf_card(mf_result)

      except Exception:
        logger.exception(f"❌ [ERROR] Failed analyzing {symbol} {timeframe}")

  def _log_mtf_card(self, mf_result) -> None:
    sig = mf_result.overall_signal
    if "BUY" in sig:
      badge = "🚀 STRONG BUY" if "STRONG" in sig else "🟢 BUY"
    elif "SELL" in sig:
      badge = "💥 STRONG SELL" if "STRONG" in sig else "🔴 SELL"
    else:
      badge = "⚪ NEUTRAL / HOLD"

    aligned = "✅ Совпадают" if mf_result.trend_alignment else "⚠️ Разнонаправленные"
    border = "═" * 60

    tf_summary = []
    for tf, details in mf_result.tf_details.items():
      t_sig = details["signal"]
      s_icon = "🟢" if "BUY" in t_sig else ("🔴" if "SELL" in t_sig else "⚪")
      tf_summary.append(f"{tf}: {s_icon} {details['score']:+.1f}")

    tfs_str = " | ".join(tf_summary)

    logger.info(
      f"\n{border}\n"
      f" 📌 МОНЕТА:  {mf_result.symbol}\n"
      f" 🎯 СИГНАЛ:  {badge}\n"
      f" 📈 ТРЕНДЫ:  {aligned}\n"
      f" 📊 ТФ ДЕТАЛИ: {tfs_str}\n"
      f"{border}\n"
    )
