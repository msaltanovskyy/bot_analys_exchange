import json
import asyncio
import logging
import threading
from controllers import AnalysisController

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

    results = {}
    lock = threading.Lock()
    stop_event = threading.Event()

    controller = AnalysisController(
        symbols=CONFIG_MARKET_SYMBOLS,
        timeframes=TIMEFRAMES,
        results=results,
        lock=lock,
        stop_event=stop_event,
        max_concurrent_tasks=5,
        limit=LIMIT,
    )

    try:
        await controller.start()
    except KeyboardInterrupt:
        logger.info("Stop user(Ctrl+C).")
        stop_event.set()


if __name__ == '__main__':
    asyncio.run(main())
