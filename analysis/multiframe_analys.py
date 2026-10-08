import logging
import re
from typing import Any
from data import MFData

logger = logging.getLogger(__name__)


def tf_to_minutes(tf: str) -> int:
  match = re.match(r"^(\d+)([mhd])$", tf.lower().strip())
  if not match:
    return 1

  value, unit = int(match.group(1)), match.group(2)
  if unit == "m":
    return value
  elif unit == "h":
    return value * 60
  elif unit == "d":
    return value * 1440
  return 1


class MultiframeAnalys:

  def __init__(
      self,
      results: dict[tuple[str, str], dict[str, Any]],
      symbol: str,
      timeframes: list[str],
      lock: Any,
  ):
    self.results = results
    self.symbol = symbol
    self.timeframes = sorted(timeframes, key=tf_to_minutes)
    self.lock = lock

  def _calculate_dynamic_weights(self) -> dict[str, float]:

    total_tfs = len(self.timeframes)
    if total_tfs == 0:
      return {}
    if total_tfs == 1:
      return {self.timeframes[0]: 1.0}

    raw_weights = {tf: idx + 1 for idx, tf in enumerate(self.timeframes)}
    sum_weights = sum(raw_weights.values())

    return {tf: w / sum_weights for tf, w in raw_weights.items()}

  def mf_analysis(self) -> MFData:
    tf_details = {}
    weights = self._calculate_dynamic_weights()

    weighted_score = 0.0
    total_active_weight = 0.0

    uptrends_count = 0
    valid_tfs_count = 0

    with self.lock:
      for tf in self.timeframes:
        key = (self.symbol, tf)
        res = self.results.get(key)

        if not res:
          continue

        valid_tfs_count += 1
        w = weights.get(tf, 1.0 / len(self.timeframes))

        is_uptrend = res.get("is_uptrend", False)
        score = res.get("score", 0.0)

        if is_uptrend:
          uptrends_count += 1

        weighted_score += score * w
        total_active_weight += w

        tf_details[tf] = {
            "signal": res.get("signal", "HOLD"),
            "score": score,
            "is_uptrend": is_uptrend,
            "macd_bullish": res.get("macd_bullish", False),
            "macd_bearish": res.get("macd_bearish", False),
            "rsi": res.get("rsi"),
        }

    if valid_tfs_count == 0:
      return MFData(
          symbol=self.symbol,
          timeframes=self.timeframes,
          overall_signal="NO_DATA",
          trend_alignment=False,
          tf_details={},
      )

    final_score = (
        weighted_score / total_active_weight if total_active_weight > 0 else 0.0
    )

    all_uptrends = uptrends_count == valid_tfs_count
    all_downtrends = uptrends_count == 0
    trend_alignment = all_uptrends or all_downtrends

    overall_signal = "NEUTRAL"

    if final_score >= 1.2 and all_uptrends:
      overall_signal = "STRONG_BUY"
    elif final_score >= 0.6 and uptrends_count >= (valid_tfs_count - 1):
      overall_signal = "BUY"
    elif final_score <= -1.2 and all_downtrends:
      overall_signal = "STRONG_SELL"
    elif final_score <= -0.6 and uptrends_count <= 1:
      overall_signal = "SELL"

    return MFData(
        symbol=self.symbol,
        timeframes=self.timeframes,
        overall_signal=overall_signal,
        trend_alignment=trend_alignment,
        tf_details=tf_details,
    )
