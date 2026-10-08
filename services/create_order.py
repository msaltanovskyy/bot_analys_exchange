import logging

import ccxt

logger = logging.getLogger(__name__)

class CreateOrder:
  def __init__(self, exchange):
    self.exchange = exchange

  async def create_order(self, symbol: str, side: str, order_type: str,
                         price: float, amount: float,):
    try:
      return await self.exchange.create_orders(symbol,order_type,side,amount,price)
    except ccxt.BaseError as e:
      logger.error(f"Order not create {symbol}: {e}")
