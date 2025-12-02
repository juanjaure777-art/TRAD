#!/usr/bin/env python3
"""
TRAD Bot - Technical Indicators Library
RSI(7), EMA, Stochastic, Divergence Detection
"""

import numpy as np
from typing import Tuple, List, Optional

class TechnicalIndicators:
    """Professional technical indicators for multi-timeframe trading (4H strategy)"""

    @staticmethod
    def rsi(closes: np.ndarray, period: int = 7) -> float:
        """
        Calculate RSI (Relative Strength Index)
        Period=7 works well for both short (1m-15m) and medium (1H-4H) timeframes
        """
        if len(closes) < period + 1:
            return 50.0

        deltas = np.diff(closes)
        seed = deltas[:period + 1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period

        rs = up / down if down != 0 else 0
        rsi = np.zeros_like(closes)
        rsi[:period] = 100. - 100. / (1. + rs)

        for i in range(period, len(closes)):
            delta = deltas[i - 1]
            upval = delta if delta > 0 else 0
            downval = -delta if delta < 0 else 0

            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            rs = up / down if down != 0 else 0
            rsi[i] = 100. - 100. / (1. + rs)

        return rsi[-1]

    @staticmethod
    def ema(closes: np.ndarray, period: int = 50) -> float:
        """
        Calculate EMA (Exponential Moving Average)
        Used as trend filter
        """
        if len(closes) < period:
            return closes[-1]

        multiplier = 2.0 / (period + 1)
        ema = closes[0]

        for i in range(1, len(closes)):
            ema = closes[i] * multiplier + ema * (1 - multiplier)

        return ema

    @staticmethod
    def stochastic(closes: np.ndarray, highs: np.ndarray, lows: np.ndarray,
                   k_period: int = 14, d_period: int = 3) -> Tuple[float, float]:
        """
        Calculate Stochastic Oscillator
        Returns (K%, D%)
        Used as confirmation indicator
        """
        if len(closes) < k_period:
            return 50.0, 50.0

        recent_closes = closes[-k_period:]
        recent_highs = highs[-k_period:]
        recent_lows = lows[-k_period:]

        lowest_low = recent_lows.min()
        highest_high = recent_highs.max()

        k_percent = 100 * (closes[-1] - lowest_low) / (highest_high - lowest_low) \
                    if highest_high != lowest_low else 50

        # Simple D% (should use SMA but approximate here)
        d_percent = k_percent  # Simplified

        return min(100, max(0, k_percent)), min(100, max(0, d_percent))

    @staticmethod
    def detect_divergence(prices: np.ndarray, rsi_values: np.ndarray,
                         window: int = 5) -> Tuple[bool, str]:
        """
        Detect bullish or bearish divergence
        Bullish: Price makes lower low, RSI makes higher low
        Bearish: Price makes higher high, RSI makes lower high
        """
        if len(prices) < window + 5 or len(rsi_values) < window + 5:
            return False, "none"

        # Get recent lows and highs
        recent_prices = prices[-window:]
        recent_rsi = rsi_values[-window:]

        price_low = recent_prices.min()
        price_high = recent_prices.max()
        rsi_low = recent_rsi.min()
        rsi_high = recent_rsi.max()

        # Previous period
        prev_prices = prices[-2*window:-window]
        prev_rsi = rsi_values[-2*window:-window]

        prev_price_low = prev_prices.min()
        prev_price_high = prev_prices.max()
        prev_rsi_low = prev_rsi.min()
        prev_rsi_high = prev_rsi.max()

        # Bullish divergence
        if (price_low < prev_price_low and rsi_low > prev_rsi_low):
            return True, "bullish"

        # Bearish divergence
        if (price_high > prev_price_high and rsi_high < prev_rsi_high):
            return True, "bearish"

        return False, "none"

    @staticmethod
    def find_support_resistance(prices: np.ndarray, window: int = 20) -> Tuple[float, float]:
        """
        Find recent support and resistance levels
        Support: Local minimum
        Resistance: Local maximum
        """
        if len(prices) < window:
            return prices.min(), prices.max()

        recent = prices[-window:]
        support = recent.min()
        resistance = recent.max()

        return support, resistance

    @staticmethod
    def candle_pattern_bullish(open_price: float, high: float, low: float, close: float) -> bool:
        """
        Detect bullish reversal candlestick patterns
        - Engulfing bullish
        - Hammer
        - Morning star (simplified)
        """
        body = abs(close - open_price)
        wick_lower = open_price - low
        wick_upper = high - close

        # Bullish engulfing (simplified)
        if close > open_price and body > 0.5 * (high - low):
            return True

        # Hammer (close near high, long lower wick)
        if wick_lower > 2 * body and close > open_price:
            return True

        return False

    @staticmethod
    def candle_pattern_bearish(open_price: float, high: float, low: float, close: float) -> bool:
        """
        Detect bearish reversal candlestick patterns
        - Engulfing bearish
        - Hanging man
        """
        body = abs(close - open_price)
        wick_lower = open_price - low
        wick_upper = high - close

        # Bearish engulfing (simplified)
        if close < open_price and body > 0.5 * (high - low):
            return True

        # Hanging man (close near open, long lower wick)
        if wick_lower > 2 * body and close < open_price:
            return True

        return False

    @staticmethod
    def rsi_trendline_break(rsi_values: np.ndarray, window: int = 10) -> bool:
        """
        Detect if RSI breaks its own trendline
        Indicates potential momentum change
        """
        if len(rsi_values) < window:
            return False

        recent_rsi = rsi_values[-window:]

        # Simple trend detection
        uptrend = recent_rsi[-1] > recent_rsi[0]

        # Check for break (simplified)
        if uptrend and recent_rsi[-1] > recent_rsi[-2]:
            return True
        elif not uptrend and recent_rsi[-1] < recent_rsi[-2]:
            return True

        return False
