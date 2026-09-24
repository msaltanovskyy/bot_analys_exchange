import asyncio
import logging
import threading

from scheduler.analysis_scheduler import AnalysisScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_scheduler(st, symbols,timeframes, limit):
  st.session_state.stop_event.clear()

  scheduler = AnalysisScheduler(
    symbols=symbols,
    timeframes=timeframes,
    results=st.session_state.results,
    lock=st.session_state.lock,
    stop_event=st.session_state.stop_event,
    max_concurrent_tasks=5,
    limit = limit
  )

  def run_scheduler():
    asyncio.run(scheduler.start())

  thread = threading.Thread(
    target=run_scheduler,
    daemon=True,
  )
  thread.start()

  st.session_state.scheduler = scheduler
  st.session_state.scheduler_thread = thread
  st.session_state.running = True


def stop_scheduler(st):
  st.session_state.stop_event.set()
  st.session_state.running = False
  logger.info("Stop requested.")
