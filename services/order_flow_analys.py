import logging

logger = logging.getLogger(__name__)

class OrderFlowAnalys:

  def calculate_spread(self, ticker):

    ask = ticker.get('ask')
    bid = ticker.get('bid')
    last = ticker.get('last')

    if ask is not None and bid is not None and last:
      spread = (ask - bid) / last
      logger.info(f"Spread: {spread:.6%}")
      return spread
    else:
      logger.error(f"Incomplete data (Ask: {ask}, Bid: {bid}, Last: {last})")
      return None

  def calculate_imbalance(self,book):

    bid_volume = sum(amount for price, amount in book.get('bids', []))
    ask_volume = sum(amount for price, amount in book.get('asks', []))

    total_volume = bid_volume + ask_volume
    if total_volume > 0:
      imbalance = (bid_volume - ask_volume) / total_volume
      logger.info(f"Imbalance: {imbalance:.4f}")
      return imbalance
    else:
      imbalance = 0.0
      return imbalance

  def calculate_delta(self,trades):
    buy_volume = sum(
      trade['amount'] for trade in trades if trade.get('side') == 'buy'
    )
    sell_volume = sum(
      trade['amount'] for trade in trades if trade.get('side') == 'sell'
    )

    delta = buy_volume - sell_volume
    logger.info(
      f"Buy vol: {buy_volume:.4f} | Sell vol: {sell_volume:.4f} | Delta:"
      f" {delta:.4f}"
    )
    return delta
