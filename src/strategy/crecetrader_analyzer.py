#!/usr/bin/env python3
"""
Crecetrader Analyzer - Context-Aware Price Action Analysis
Implements Crecetrader methodology: localization, wick analysis, market phases, vacío

Core Principle: Context (localization) matters more than patterns
- Same candle has different meaning at support vs resistance vs empty space
- Wick analysis shows absorption of buys (lower wicks) or sells (upper wicks)
- Market volatility phase (expansion/compression) affects entry quality
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from enum import Enum


class CandleLocalization(Enum):
    """Candle position in price range - Crecetrader's localization concept"""
    SUPPORT = "support"        # At market floor/support level
    RESISTANCE = "resistance"  # At market ceiling/resistance level
    MIDDLE = "middle"          # In the middle of recent range
    EMPTY_SPACE = "vacío"      # In previously untested price area


class VolatilityPhase(Enum):
    """Market volatility context - Crecetrader's market environment assessment"""
    EXPANSION = "expansion"    # Wide candle bodies, strong directional move
    COMPRESSION = "compression"  # Small candle bodies, low volatility, indecision
    CHOPPY = "choppy"          # Enredado - avoid these, confusing signals


class WickAnalysis(Enum):
    """Wick pattern meaning - Shows absorption of buyers/sellers"""
    STRONG_BULL = "strong_bull"    # Large lower wick, small/no upper wick = buyers absorbed sellers
    STRONG_BEAR = "strong_bear"    # Large upper wick, small/no lower wick = sellers absorbed buyers
    INDECISION = "indecision"      # Large both wicks = battle, no direction won
    NEUTRAL = "neutral"            # Small both wicks = calm


class CrecetraderAnalyzer:
    """
    Analyzes price action through Crecetrader lens: context, localization, wick patterns

    Key metrics:
    - Candle localization (where in range it formed)
    - Wick analysis (absorption patterns)
    - Market volatility phase (expansion vs compression)
    - Entry quality score based on Crecetrader principles
    """

    def __init__(self, lookback: int = 20):
        """
        Initialize analyzer

        Args:
            lookback: Number of candles to analyze for support/resistance levels
        """
        self.lookback = lookback

    def analyze_candle(self,
                      open_: float, high: float, low: float, close: float,
                      support_level: Optional[float] = None,
                      resistance_level: Optional[float] = None) -> Dict:
        """
        Analyze single candle using Crecetrader methodology

        Args:
            open_: Candle open price
            high: Candle high price
            low: Candle low price
            close: Candle close price
            support_level: Market support (floor/piso) - if None, will look at lows
            resistance_level: Market resistance (ceiling/techo) - if None, will look at highs

        Returns:
            {
                'body_strength': float (0-1),  # % of range that is body
                'upper_wick_pct': float,       # % of high that is wick
                'lower_wick_pct': float,       # % of low that is wick
                'wick_analysis': WickAnalysis,
                'candle_range': float,
                'direction': str ('BULL' or 'BEAR'),
                'body_size': float
            }
        """
        candle_range = high - low
        if candle_range == 0:
            candle_range = 0.0001  # Prevent division by zero for doji

        # Calculate wicks
        if close > open_:  # Bull candle
            body_low = open_
            body_high = close
            direction = "BULL"
        else:  # Bear candle
            body_low = close
            body_high = open_
            direction = "BEAR"

        body_size = body_high - body_low
        upper_wick = high - body_high
        lower_wick = body_low - low

        # Strength: what % of the range is the body (not wicks)
        body_strength = body_size / candle_range if candle_range > 0 else 0

        # Wick analysis - absorption patterns
        upper_wick_pct = upper_wick / candle_range if candle_range > 0 else 0
        lower_wick_pct = lower_wick / candle_range if candle_range > 0 else 0

        # Determine wick pattern
        wick_analysis = self._analyze_wicks(
            upper_wick_pct, lower_wick_pct, body_strength, direction
        )

        return {
            'body_strength': body_strength,
            'upper_wick_pct': upper_wick_pct,
            'lower_wick_pct': lower_wick_pct,
            'wick_analysis': wick_analysis,
            'candle_range': candle_range,
            'body_size': body_size,
            'direction': direction,
            'upper_wick': upper_wick,
            'lower_wick': lower_wick
        }

    def _analyze_wicks(self, upper_wick_pct: float, lower_wick_pct: float,
                       body_strength: float, direction: str) -> WickAnalysis:
        """Determine wick pattern meaning"""
        wick_threshold = 0.25  # 25% of range

        upper_is_large = upper_wick_pct > wick_threshold
        lower_is_large = lower_wick_pct > wick_threshold

        # Strong body, small wicks = direction won
        if body_strength > 0.60:
            if direction == "BULL" and not upper_is_large:
                return WickAnalysis.STRONG_BULL
            elif direction == "BEAR" and not lower_is_large:
                return WickAnalysis.STRONG_BEAR

        # Both large wicks = indecision/battle
        if upper_is_large and lower_is_large:
            return WickAnalysis.INDECISION

        # Small both wicks = calm
        if not upper_is_large and not lower_is_large:
            return WickAnalysis.NEUTRAL

        # Single large wick depends on direction
        if upper_is_large and direction == "BEAR":
            return WickAnalysis.STRONG_BEAR
        elif lower_is_large and direction == "BULL":
            return WickAnalysis.STRONG_BULL

        return WickAnalysis.NEUTRAL

    def determine_localization(self,
                              high: float, low: float, close: float,
                              support_level: float,
                              resistance_level: float) -> CandleLocalization:
        """
        Determine candle localization in market context
        Crecetrader principle: Location determines meaning

        Args:
            high, low, close: Candle OHLC
            support_level: Market floor (piso)
            resistance_level: Market ceiling (techo)

        Returns:
            CandleLocalization enum showing where candle formed
        """
        range_size = resistance_level - support_level
        if range_size <= 0:
            return CandleLocalization.MIDDLE

        # Distance from support
        distance_from_support = close - support_level
        support_threshold = range_size * 0.33  # Bottom 33% = support area

        # Distance from resistance
        distance_from_resistance = resistance_level - close
        resistance_threshold = range_size * 0.33  # Top 33% = resistance area

        # Check if in untested price area (vacío)
        if high > resistance_level or low < support_level:
            return CandleLocalization.EMPTY_SPACE

        # Check if near support or resistance
        if distance_from_support < support_threshold:
            return CandleLocalization.SUPPORT
        elif distance_from_resistance < resistance_threshold:
            return CandleLocalization.RESISTANCE
        else:
            return CandleLocalization.MIDDLE

    def analyze_volatility_phase(self, closes: np.ndarray,
                                limit: int = 10) -> Tuple[VolatilityPhase, float]:
        """
        Determine market volatility phase using recent candle ranges

        Args:
            closes: Array of closing prices (last N candles)
            limit: Number of candles to analyze (default 10)

        Returns:
            Tuple of (VolatilityPhase, volatility_score 0-1)
        """
        if len(closes) < 3:
            return VolatilityPhase.NEUTRAL, 0.5

        # Use recent data
        recent = closes[-limit:] if len(closes) >= limit else closes

        # Calculate average range
        ranges = []
        for i in range(1, len(recent)):
            range_size = abs(recent[i] - recent[i-1])
            ranges.append(range_size)

        avg_range = np.mean(ranges) if ranges else 0
        std_range = np.std(ranges) if ranges else 0

        # Current candle range (last one)
        current_range = abs(recent[-1] - recent[-2]) if len(recent) >= 2 else 0

        # Calculate volatility score (0-1)
        if avg_range > 0:
            volatility_score = min(1.0, current_range / (avg_range * 2))
        else:
            volatility_score = 0.5

        # Determine phase
        # Expansion: current range >> average
        if current_range > avg_range * 1.5:
            phase = VolatilityPhase.EXPANSION
        # Compression: current range << average
        elif current_range < avg_range * 0.5:
            phase = VolatilityPhase.COMPRESSION
        # Choppy: high std but low current range (conflicting signals)
        elif std_range > avg_range * 0.5 and current_range < avg_range:
            phase = VolatilityPhase.CHOPPY
        else:
            phase = VolatilityPhase.COMPRESSION

        return phase, volatility_score

    def calculate_entry_quality_score(self,
                                     candle_info: Dict,
                                     localization: CandleLocalization,
                                     volatility_phase: VolatilityPhase,
                                     signal_type: str = "LONG") -> float:
        """
        Calculate entry quality score based on Crecetrader principles

        Higher score = better entry quality

        Scoring logic:
        - Strong body + favorable wick analysis = high quality
        - At support (for LONG) or resistance (for SHORT) = bonus
        - During expansion phase = bonus
        - During compression or choppy = penalty

        Args:
            candle_info: Result from analyze_candle()
            localization: CandleLocalization from determine_localization()
            volatility_phase: VolatilityPhase from analyze_volatility_phase()
            signal_type: "LONG" or "SHORT"

        Returns:
            Score 0.0-1.0 where 1.0 is perfect entry
        """
        score = 0.5  # Base score

        # 1. Body strength (25% weight)
        body_strength = candle_info['body_strength']
        if body_strength > 0.60:
            score += 0.15  # Strong body
        elif body_strength < 0.30:
            score -= 0.10  # Weak body

        # 2. Wick analysis (25% weight)
        wick = candle_info['wick_analysis']
        direction = candle_info['direction']

        if signal_type == "LONG":
            if wick == WickAnalysis.STRONG_BULL and direction == "BULL":
                score += 0.15  # Perfect for long
            elif wick == WickAnalysis.STRONG_BEAR:
                score -= 0.10  # Bad for long
            elif wick == WickAnalysis.INDECISION:
                score -= 0.05  # Uncertain
        else:  # SHORT
            if wick == WickAnalysis.STRONG_BEAR and direction == "BEAR":
                score += 0.15  # Perfect for short
            elif wick == WickAnalysis.STRONG_BULL:
                score -= 0.10  # Bad for short
            elif wick == WickAnalysis.INDECISION:
                score -= 0.05  # Uncertain

        # 3. Localization (25% weight)
        if signal_type == "LONG":
            if localization == CandleLocalization.SUPPORT:
                score += 0.15  # Buying at support is good
            elif localization == CandleLocalization.RESISTANCE:
                score -= 0.10  # Buying at resistance is risky
        else:  # SHORT
            if localization == CandleLocalization.RESISTANCE:
                score += 0.15  # Shorting at resistance is good
            elif localization == CandleLocalization.SUPPORT:
                score -= 0.10  # Shorting at support is risky

        # 4. Volatility phase (25% weight)
        if volatility_phase == VolatilityPhase.EXPANSION:
            score += 0.10  # Expansion favors directional moves
        elif volatility_phase == VolatilityPhase.CHOPPY:
            score -= 0.15  # Avoid choppy markets (enredado)
        # Compression is neutral

        # Clamp between 0 and 1
        score = max(0.0, min(1.0, score))

        return score

    def analyze_price_action(self,
                            opens: np.ndarray,
                            highs: np.ndarray,
                            lows: np.ndarray,
                            closes: np.ndarray,
                            support_level: Optional[float] = None,
                            resistance_level: Optional[float] = None) -> Dict:
        """
        Complete Crecetrader analysis of price action (last candle in context)

        Args:
            opens, highs, lows, closes: OHLC arrays
            support_level: Market support level (if None, will be recent low)
            resistance_level: Market resistance level (if None, will be recent high)

        Returns:
            Complete analysis including:
            - candle_analysis: Candle structure
            - localization: Where in range it formed
            - volatility_phase: Market condition
            - context_description: Human-readable description
        """
        if len(closes) == 0:
            return None

        # Use recent support/resistance if not provided
        if support_level is None:
            support_level = np.min(lows[-self.lookback:])
        if resistance_level is None:
            resistance_level = np.max(highs[-self.lookback:])

        # Analyze last candle
        candle = self.analyze_candle(
            opens[-1], highs[-1], lows[-1], closes[-1],
            support_level, resistance_level
        )

        # Determine localization
        localization = self.determine_localization(
            highs[-1], lows[-1], closes[-1],
            support_level, resistance_level
        )

        # Analyze volatility
        volatility_phase, volatility_score = self.analyze_volatility_phase(closes)

        # Build context description
        context = self._build_context_description(
            candle, localization, volatility_phase
        )

        return {
            'candle_analysis': candle,
            'localization': localization,
            'volatility_phase': volatility_phase,
            'volatility_score': volatility_score,
            'support_level': support_level,
            'resistance_level': resistance_level,
            'range_size': resistance_level - support_level,
            'context_description': context
        }

    def _build_context_description(self, candle: Dict,
                                  localization: CandleLocalization,
                                  volatility_phase: VolatilityPhase) -> str:
        """Generate human-readable context description"""
        parts = []

        # Wick description
        wick = candle['wick_analysis']
        if wick == WickAnalysis.STRONG_BULL:
            parts.append("Bulls absorbed sellers (lower wick)")
        elif wick == WickAnalysis.STRONG_BEAR:
            parts.append("Bears absorbed buyers (upper wick)")
        elif wick == WickAnalysis.INDECISION:
            parts.append("Battle between buyers/sellers (both wicks)")
        else:
            parts.append("Calm market (small wicks)")

        # Body strength
        if candle['body_strength'] > 0.60:
            parts.append("strong body")
        elif candle['body_strength'] < 0.30:
            parts.append("weak body")

        # Localization
        if localization == CandleLocalization.SUPPORT:
            parts.append("@ support")
        elif localization == CandleLocalization.RESISTANCE:
            parts.append("@ resistance")
        elif localization == CandleLocalization.EMPTY_SPACE:
            parts.append("en vacío")
        else:
            parts.append("en medio")

        # Volatility
        if volatility_phase == VolatilityPhase.EXPANSION:
            parts.append("volatility expanding")
        elif volatility_phase == VolatilityPhase.CHOPPY:
            parts.append("ENREDADO (avoid)")
        else:
            parts.append("low volatility")

        return " | ".join(parts)
