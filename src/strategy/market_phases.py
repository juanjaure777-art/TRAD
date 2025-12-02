#!/usr/bin/env python3
"""
Market Phase Detection Module - v3.3 Dynamic Permissiveness
Detects market phases based on Crecetrader methodology
Phases: IMPULSE, CORRECTIVE, REVERSAL, NEUTRAL
"""

from typing import Tuple, Optional
import numpy as np


class MarketPhaseDetector:
    """Detects market phases for dynamic permissiveness adjustment"""

    def __init__(self, lookback_period: int = 20, correction_threshold: float = 0.50):
        """
        Args:
            lookback_period: Periods to analyze for trend
            correction_threshold: Percentage (0-1) to consider corrective phase
        """
        self.lookback_period = lookback_period
        self.correction_threshold = correction_threshold

    def detect_phase(
        self,
        closes: np.ndarray,
        ema9: float,
        ema21: float,
        current_price: float,
        atr: float,
        recent_high: float,
        recent_low: float,
    ) -> Tuple[str, dict]:
        """
        Detect current market phase

        Returns:
            Tuple of (phase_name, phase_details)
            phase_name: "IMPULSE", "CORRECTIVE", "REVERSAL", "NEUTRAL"
        """

        details = {
            "phase": "NEUTRAL",
            "confidence": 0.0,
            "trend_direction": "UNDEFINED",
            "volatility_level": self._calculate_volatility(closes, current_price, atr),
            "momentum_strength": self._calculate_momentum(closes),
            "correction_percent": 0.0,
            "ema_separation": abs(ema9 - ema21) / current_price * 100,
        }

        # Detect trend direction and strength
        trend_direction = self._detect_trend(ema9, ema21)
        details["trend_direction"] = trend_direction

        if trend_direction == "BULLISH":
            # Check if in impulse or corrective phase
            recent_change = (closes[-1] - closes[-self.lookback_period]) / closes[-self.lookback_period]

            # Calculate from recent high
            if recent_high > 0:
                correction_from_high = (recent_high - current_price) / recent_high
                details["correction_percent"] = correction_from_high * 100

                # IMPULSE: Strong uptrend, price near highs, EMA strong separation
                if recent_change > 0.02 and correction_from_high < 0.005 and details["ema_separation"] > 0.5:
                    details["phase"] = "IMPULSE"
                    details["confidence"] = min(1.0, abs(recent_change) + (1.0 - correction_from_high))

                # CORRECTIVE: Pulled back but still in trend
                elif self.correction_threshold * recent_change <= abs(recent_high - closes[-1]) <= recent_change:
                    details["phase"] = "CORRECTIVE"
                    details["confidence"] = correction_from_high

                # REVERSAL: Significant pullback or trend breaking
                elif correction_from_high > self.correction_threshold or ema9 < ema21:
                    details["phase"] = "REVERSAL"
                    details["confidence"] = min(1.0, correction_from_high)
                else:
                    details["phase"] = "NEUTRAL"
                    details["confidence"] = 0.5

        elif trend_direction == "BEARISH":
            # Similar logic for downtrend
            recent_change = (closes[-self.lookback_period] - closes[-1]) / closes[-self.lookback_period]

            if recent_low > 0:
                correction_from_low = (current_price - recent_low) / recent_low
                details["correction_percent"] = correction_from_low * 100

                if recent_change > 0.02 and correction_from_low < 0.005 and details["ema_separation"] > 0.5:
                    details["phase"] = "IMPULSE"
                    details["confidence"] = min(1.0, abs(recent_change) + (1.0 - correction_from_low))

                elif self.correction_threshold * recent_change <= abs(recent_low - closes[-1]) <= recent_change:
                    details["phase"] = "CORRECTIVE"
                    details["confidence"] = correction_from_low

                elif correction_from_low > self.correction_threshold or ema9 > ema21:
                    details["phase"] = "REVERSAL"
                    details["confidence"] = min(1.0, correction_from_low)
                else:
                    details["phase"] = "NEUTRAL"
                    details["confidence"] = 0.5
        else:
            # NEUTRAL trend
            details["phase"] = "NEUTRAL"
            details["confidence"] = 0.3

        return details["phase"], details

    def _detect_trend(self, ema9: float, ema21: float) -> str:
        """Detect trend direction from EMA"""
        if ema9 > ema21:
            return "BULLISH"
        elif ema9 < ema21:
            return "BEARISH"
        else:
            return "NEUTRAL"

    def _calculate_volatility(self, closes: np.ndarray, current_price: float, atr: float) -> str:
        """Calculate volatility level (LOW, MEDIUM, HIGH)"""
        if len(closes) < 2:
            return "MEDIUM"

        atr_percent = (atr / current_price) * 100

        if atr_percent < 0.5:
            return "LOW"
        elif atr_percent < 1.5:
            return "MEDIUM"
        else:
            return "HIGH"

    def _calculate_momentum(self, closes: np.ndarray) -> str:
        """Calculate momentum strength (WEAK, MODERATE, STRONG)"""
        if len(closes) < 5:
            return "WEAK"

        recent_momentum = abs(closes[-1] - closes[-5]) / closes[-5]

        if recent_momentum < 0.01:
            return "WEAK"
        elif recent_momentum < 0.03:
            return "MODERATE"
        else:
            return "STRONG"

    def get_suggested_mode(self, phase: str, phase_details: dict) -> int:
        """
        Get suggested permissiveness mode based on phase
        Mode 5: Maximum Selective (REVERSAL)
        Mode 4: Selective (IMPULSE Early)
        Mode 3: Balanced (IMPULSE Middle)
        Mode 2: Permissive (CORRECTIVE)
        Mode 1: Very Permissive (REVERSAL Reversive)
        """
        confidence = phase_details.get("confidence", 0.0)
        volatility = phase_details.get("volatility_level", "MEDIUM")
        momentum = phase_details.get("momentum_strength", "WEAK")

        if phase == "REVERSAL":
            if confidence > 0.7 and volatility == "HIGH":
                return 5  # Maximum selective
            else:
                return 1  # Very permissive

        elif phase == "IMPULSE":
            if confidence > 0.8:
                return 5  # Maximum selective
            elif confidence > 0.6:
                return 4  # Selective
            else:
                return 3  # Balanced

        elif phase == "CORRECTIVE":
            if momentum == "STRONG":
                return 3  # Balanced
            else:
                return 2  # Permissive

        else:  # NEUTRAL
            return 3  # Balanced (default)
