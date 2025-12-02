#!/usr/bin/env python3
"""
Market Analyzer - Calculate volatility and momentum using Crecetrader methodology

Implements TODO items from bot.py with Crecetrader context:
- Volatility: Based on candle ranges and market phase (expansion/compression)
- Momentum: Based on price direction and trend strength

Volatility calculation:
- High volatility = large candle bodies, wide ranges (expansion phase)
- Low volatility = small candle bodies, tight ranges (compression phase)

Momentum calculation:
- Positive momentum = price making higher highs/lows (uptrend)
- Negative momentum = price making lower highs/lows (downtrend)
- Neutral momentum = sideways consolidation
"""

import numpy as np
from typing import Dict, Tuple
from enum import Enum


class Volatility(Enum):
    """Market volatility levels"""
    EXTREME = "extreme"  # > 2x average
    HIGH = "high"        # > 1.3x average
    NORMAL = "normal"    # 0.7x - 1.3x average
    LOW = "low"          # < 0.7x average


class Momentum(Enum):
    """Market momentum direction and strength"""
    STRONG_UP = "strong_up"      # Consecutive higher highs, strong uptrend
    MODERATE_UP = "moderate_up"  # Higher highs, moderate uptrend
    NEUTRAL = "neutral"          # Sideways, no clear direction
    MODERATE_DOWN = "moderate_down"  # Lower highs, moderate downtrend
    STRONG_DOWN = "strong_down"      # Consecutive lower highs, strong downtrend


class MarketAnalyzer:
    """Analyzes market volatility and momentum using Crecetrader principles"""

    def __init__(self, lookback: int = 20):
        """
        Initialize analyzer

        Args:
            lookback: Number of candles to analyze (default 20)
        """
        self.lookback = lookback

    def calculate_volatility(self,
                            opens: np.ndarray,
                            highs: np.ndarray,
                            lows: np.ndarray,
                            closes: np.ndarray) -> Dict:
        """
        Calculate market volatility using Crecetrader candle analysis

        Analyzes recent candle ranges to determine if market is in expansion
        (volatile, good for directional moves) or compression (low volatility,
        confusing signals).

        Args:
            opens, highs, lows, closes: OHLC arrays

        Returns:
            {
                'level': Volatility enum,
                'score': float (0-1),  # 0=no volatility, 1=extreme
                'description': str,
                'avg_range_pct': float,
                'current_range_pct': float,
                'is_expansion': bool,
                'is_compression': bool
            }
        """
        if len(closes) < 3:
            return self._default_volatility()

        # Use recent candles
        recent_closes = closes[-self.lookback:] if len(closes) >= self.lookback else closes
        recent_opens = opens[-self.lookback:] if len(opens) >= self.lookback else opens
        recent_highs = highs[-self.lookback:] if len(highs) >= self.lookback else highs
        recent_lows = lows[-self.lookback:] if len(lows) >= self.lookback else lows

        # Calculate range percentages for each candle
        ranges = []
        for i in range(len(recent_closes)):
            candle_range = recent_highs[i] - recent_lows[i]
            range_pct = (candle_range / recent_closes[i]) * 100 if recent_closes[i] > 0 else 0
            ranges.append(range_pct)

        avg_range_pct = np.mean(ranges)
        std_range_pct = np.std(ranges)
        current_range_pct = ranges[-1] if ranges else 0

        # Volatility ratio: current vs average
        if avg_range_pct > 0:
            volatility_ratio = current_range_pct / avg_range_pct
        else:
            volatility_ratio = 1.0

        # Determine volatility level
        if volatility_ratio > 2.0:
            level = Volatility.EXTREME
            score = min(1.0, volatility_ratio / 3.0)
        elif volatility_ratio > 1.3:
            level = Volatility.HIGH
            score = min(1.0, volatility_ratio / 2.0)
        elif volatility_ratio < 0.7:
            level = Volatility.LOW
            score = volatility_ratio / 2.0
        else:
            level = Volatility.NORMAL
            score = 0.5 + (volatility_ratio - 1.0) * 0.25

        # Determine phase
        is_expansion = volatility_ratio > 1.3
        is_compression = volatility_ratio < 0.8

        description = f"{level.value.upper()} volatility ({current_range_pct:.2f}% current vs {avg_range_pct:.2f}% avg)"

        return {
            'level': level,
            'score': score,
            'description': description,
            'avg_range_pct': avg_range_pct,
            'current_range_pct': current_range_pct,
            'volatility_ratio': volatility_ratio,
            'is_expansion': is_expansion,
            'is_compression': is_compression,
            'std_deviation': std_range_pct
        }

    def calculate_momentum(self,
                          opens: np.ndarray,
                          highs: np.ndarray,
                          lows: np.ndarray,
                          closes: np.ndarray) -> Dict:
        """
        Calculate market momentum (trend direction and strength)

        Analyzes price structure (highs/lows pattern) and closing prices to
        determine if market is trending up, down, or sideways.

        Args:
            opens, highs, lows, closes: OHLC arrays

        Returns:
            {
                'momentum': Momentum enum,
                'score': float (-1 to +1),  # -1=strong down, 0=neutral, +1=strong up
                'description': str,
                'direction': str ('UP', 'DOWN', 'NEUTRAL'),
                'higher_highs_count': int,
                'lower_lows_count': int,
                'consecutive_up_candles': int,
                'consecutive_down_candles': int
            }
        """
        if len(closes) < 5:
            return self._default_momentum()

        # Use recent candles
        recent_closes = closes[-self.lookback:] if len(closes) >= self.lookback else closes
        recent_highs = highs[-self.lookback:] if len(highs) >= self.lookback else highs
        recent_lows = lows[-self.lookback:] if len(lows) >= self.lookback else lows

        # Count higher highs and lower lows
        higher_highs_count = 0
        lower_lows_count = 0

        for i in range(1, len(recent_highs)):
            if recent_highs[i] > recent_highs[i-1]:
                higher_highs_count += 1
            if recent_lows[i] < recent_lows[i-1]:
                lower_lows_count += 1

        # Count consecutive candles direction
        consecutive_up = 0
        consecutive_down = 0

        for i in range(len(recent_closes) - 1, 0, -1):
            if recent_closes[i] > recent_closes[i-1]:
                consecutive_up += 1
            else:
                break

        for i in range(len(recent_closes) - 1, 0, -1):
            if recent_closes[i] < recent_closes[i-1]:
                consecutive_down += 1
            else:
                break

        # Determine momentum
        total_highs = len(recent_highs) - 1
        total_lows = len(recent_lows) - 1

        higher_highs_pct = (higher_highs_count / total_highs * 100) if total_highs > 0 else 0
        lower_lows_pct = (lower_lows_count / total_lows * 100) if total_lows > 0 else 0

        # Momentum score: +1 = strong up, -1 = strong down, 0 = neutral
        momentum_score = (higher_highs_pct - lower_lows_pct) / 100

        # Recent price action (last 5 candles)
        recent_closes_small = recent_closes[-5:]
        direction_up = recent_closes_small[-1] > recent_closes_small[0]
        direction_down = recent_closes_small[-1] < recent_closes_small[0]

        # Determine momentum enum
        if momentum_score > 0.5 and direction_up:
            momentum = Momentum.STRONG_UP
            direction = "UP"
        elif momentum_score > 0.2:
            momentum = Momentum.MODERATE_UP
            direction = "UP"
        elif momentum_score < -0.5 and direction_down:
            momentum = Momentum.STRONG_DOWN
            direction = "DOWN"
        elif momentum_score < -0.2:
            momentum = Momentum.MODERATE_DOWN
            direction = "DOWN"
        else:
            momentum = Momentum.NEUTRAL
            direction = "NEUTRAL"

        description = f"{momentum.value.upper()} - {higher_highs_pct:.0f}% HH vs {lower_lows_pct:.0f}% LL"

        return {
            'momentum': momentum,
            'score': momentum_score,
            'description': description,
            'direction': direction,
            'higher_highs_count': higher_highs_count,
            'lower_lows_count': lower_lows_count,
            'higher_highs_pct': higher_highs_pct,
            'lower_lows_pct': lower_lows_pct,
            'consecutive_up_candles': consecutive_up,
            'consecutive_down_candles': consecutive_down
        }

    def _default_volatility(self) -> Dict:
        """Return default volatility when insufficient data"""
        return {
            'level': Volatility.NORMAL,
            'score': 0.5,
            'description': 'Normal volatility (insufficient data)',
            'avg_range_pct': 0.0,
            'current_range_pct': 0.0,
            'volatility_ratio': 1.0,
            'is_expansion': False,
            'is_compression': False,
            'std_deviation': 0.0
        }

    def _default_momentum(self) -> Dict:
        """Return default momentum when insufficient data"""
        return {
            'momentum': Momentum.NEUTRAL,
            'score': 0.0,
            'description': 'Neutral momentum (insufficient data)',
            'direction': 'NEUTRAL',
            'higher_highs_count': 0,
            'lower_lows_count': 0,
            'higher_highs_pct': 0.0,
            'lower_lows_pct': 0.0,
            'consecutive_up_candles': 0,
            'consecutive_down_candles': 0
        }

    def get_market_context(self,
                          opens: np.ndarray,
                          highs: np.ndarray,
                          lows: np.ndarray,
                          closes: np.ndarray) -> Dict:
        """
        Get complete market context: volatility + momentum + description

        Args:
            opens, highs, lows, closes: OHLC arrays

        Returns:
            Complete market analysis with both volatility and momentum
        """
        volatility = self.calculate_volatility(opens, highs, lows, closes)
        momentum = self.calculate_momentum(opens, highs, lows, closes)

        # Build context description
        context_desc = f"Market: {momentum['direction']} with {volatility['level'].value} volatility"

        return {
            'volatility': volatility,
            'momentum': momentum,
            'context': context_desc
        }
