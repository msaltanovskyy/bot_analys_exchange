import logging

logger = logging.getLogger(__name__)


class AnalysisResult:

    BUY_THRESHOLD = 3.5
    SELL_THRESHOLD = -3.5

    def __init__(
        self,
        pattern_result: dict,
        indicator_result: dict
    ):
        self.pattern_result = pattern_result
        self.indicator_result = indicator_result

        self.bullish_patterns = {}
        self.bearish_patterns = {}

        self.score = 0.0
        self.signal = "HOLD"

    def calculate_score(self) -> float:

        self.score = 0.0

        self._analyze_trend()
        self._analyze_patterns()
        self._analyze_delta()
        self._analyze_volume()
        self._analyze_bollinger()
        self._analyze_rsi()
        self._analyze_macd()
        self._analyze_vwap()

        return self.score

    def _analyze_trend(self):

        if self.indicator_result.get("is_uptrend"):
            self.score += 2.0
            logger.info("Trend (+2.0): BULLISH")
        else:
            self.score -= 2.0
            logger.info("Trend (-2.0): BEARISH")

    def _analyze_patterns(self):

        for name, value in self.pattern_result.items():
            if value > 0:
                weight = 0.5 if name == "doji" else 2.0
                self.bullish_patterns[name] = "BULLISH"
                self.score += weight
                logger.info(f"Pattern (+{weight}): {name} (Bullish)")

            elif value < 0:
                self.bearish_patterns[name] = "BEARISH"
                self.score -= 2.0
                logger.info(f"Pattern (-2.0): {name} (Bearish)")

    def _analyze_delta(self):

        delta = self.indicator_result.get("delta", 0)

        if delta > 0:
            self.score += 1.0
            logger.info(f"Delta (+1.0): {delta:.2f} > 0")
        elif delta < 0:
            self.score -= 1.0
            logger.info(f"Delta (-1.0): {delta:.2f} < 0")

    def _analyze_volume(self):

        if not self.indicator_result.get("volume_anomaly"):
            return

        bonus = 1.0 if self.score >= 0 else -1.0
        self.score += bonus
        logger.info(f"Volume Anomaly ({bonus:+.1f})")

    def _analyze_bollinger(self):

        if self.indicator_result.get("near_support"):
            self.score += 1.5
            logger.info("BBands (+1.5): Support")

        if self.indicator_result.get("near_resistance"):
            self.score -= 1.5
            logger.info("BBands (-1.5): Resistance")

    def _analyze_rsi(self):

        rsi = self.indicator_result.get("rsi")

        if rsi is None:
            return

        if self.indicator_result.get("rsi_oversold"):
            self.score += 1.5
            logger.info(f"RSI (+1.5): Oversold ({rsi:.1f})")
        elif self.indicator_result.get("rsi_overbought"):
            self.score -= 1.5
            logger.info(f"RSI (-1.5): Overbought ({rsi:.1f})")

    def _analyze_macd(self):

        if self.indicator_result.get("macd_bullish"):
            self.score += 1.5
            logger.info("MACD (+1.5): Bullish Crossover / Momentum")
        elif self.indicator_result.get("macd_bearish"):
            self.score -= 1.5
            logger.info("MACD (-1.5): Bearish Crossover / Momentum")

    def _analyze_vwap(self):

        above_vwap = self.indicator_result.get("above_vwap")

        if above_vwap is True:
            self.score += 1.0
            logger.info("VWAP (+1.0): Price > VWAP")
        elif above_vwap is False:
            self.score -= 1.0
            logger.info("VWAP (-1.0): Price < VWAP")

    def generate_signal(self) -> str:

        is_uptrend = self.indicator_result.get("is_uptrend", False)

        if self.score >= self.BUY_THRESHOLD:
            if is_uptrend:
                self.signal = "BUY"
            else:
                logger.info("BUY signal generated against main trend (Reversal)")
                self.signal = "BUY (Контртренд)"

        elif self.score <= self.SELL_THRESHOLD:
            if not is_uptrend:
                self.signal = "SELL"
            else:
                logger.info("SELL signal generated against main trend (Reversal)")
                self.signal = "SELL (Контртренд)"

        else:
            self.signal = "HOLD"

        logger.info(f"TOTAL SCORE: {self.score:.1f}")
        logger.info(f"SIGNAL: {self.signal}")

        return self.signal

    def get_result(self) -> dict:

        return {
            "signal": self.signal,
            "score": self.score,
            "bullish_patterns": self.bullish_patterns,
            "bearish_patterns": self.bearish_patterns,
        }
