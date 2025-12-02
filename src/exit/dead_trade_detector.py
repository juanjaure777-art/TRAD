#!/usr/bin/env python3
"""
Dead Trade Detector - Identifies stalled positions that should be closed

A "dead trade" is one where price is not moving (price dead) or volume has dried up.
Using OPTION 3: Combined Price + Volume detection for accuracy.

Strategy:
- Track last 15 candles of price/volume
- DEAD_PRICE: If price range < 0.5% over period
- DEAD_VOLUME: If volume < 50% of average
- Close if: Both true for 3+ cycles OR one true for 5+ cycles
"""

from typing import Tuple, Optional
from collections import deque
from src.constants import (
    DEAD_PRICE_THRESHOLD_PCT,
    DEAD_VOLUME_RATIO,
    DEAD_PRICE_COUNTER_MAX,
    DEAD_VOLUME_COUNTER_MAX
)


class DeadTradeDetector:
    """Detects stalled positions that should be closed"""

    def __init__(self, history_limit: int = 15):
        """
        Initialize detector

        Args:
            history_limit: Number of candles to track for price/volume
        """
        self.history_limit = history_limit
        self.price_history = deque(maxlen=history_limit)
        self.volume_history = deque(maxlen=history_limit)

        # Counters for consecutive "dead" candles
        self.dead_price_counter = 0
        self.dead_volume_counter = 0

    def update_history(self, price: float, volume: float):
        """
        Add new candle data to history

        Args:
            price: Closing price
            volume: Trading volume for candle
        """
        self.price_history.append(price)
        self.volume_history.append(volume)

    def check_dead_trade(self, current_price: float, current_volume: float) -> Tuple[bool, str]:
        """
        Check if trade is dead (should be closed)

        Returns:
            Tuple of (is_dead: bool, reason: str)
        """
        if len(self.price_history) < 3:
            return False, "Insufficient history"

        # ANALYSIS 1: Price Movement Check
        price_range = max(self.price_history) - min(self.price_history)
        range_pct = (price_range / min(self.price_history)) * 100 if min(self.price_history) > 0 else 0

        is_price_dead = range_pct < DEAD_PRICE_THRESHOLD_PCT

        if is_price_dead:
            self.dead_price_counter += 1
        else:
            self.dead_price_counter = 0

        # ANALYSIS 2: Volume Check
        avg_volume = sum(self.volume_history) / len(self.volume_history)
        is_volume_dead = current_volume < (avg_volume * DEAD_VOLUME_RATIO)

        if is_volume_dead:
            self.dead_volume_counter += 1
        else:
            self.dead_volume_counter = 0

        # DECISION LOGIC
        # Option A: Both conditions true for N consecutive candles = definitely dead
        if is_price_dead and is_volume_dead:
            if (self.dead_price_counter >= DEAD_PRICE_COUNTER_MAX and
                self.dead_volume_counter >= DEAD_VOLUME_COUNTER_MAX):
                reason = (f"DEAD_TRADE: Price stalled ({range_pct:.2f}% < {DEAD_PRICE_THRESHOLD_PCT}%) + "
                         f"Volume dried ({current_volume:.0f} < {avg_volume * DEAD_VOLUME_RATIO:.0f})")
                return True, reason

        # Option B: One condition true for longer period = probably dead
        if self.dead_price_counter >= DEAD_PRICE_COUNTER_MAX + 2:  # 5 consecutive
            reason = (f"DEAD_TRADE: Price stalled for {self.dead_price_counter} candles "
                     f"({range_pct:.2f}% < {DEAD_PRICE_THRESHOLD_PCT}%)")
            return True, reason

        if self.dead_volume_counter >= DEAD_VOLUME_COUNTER_MAX + 2:  # 5 consecutive
            reason = (f"DEAD_TRADE: Volume dried for {self.dead_volume_counter} candles "
                     f"(avg: {avg_volume:.0f}, current: {current_volume:.0f})")
            return True, reason

        return False, "Trade active"

    def reset(self):
        """Reset detector state for new trade"""
        self.price_history.clear()
        self.volume_history.clear()
        self.dead_price_counter = 0
        self.dead_volume_counter = 0

    def get_status(self) -> dict:
        """Get detector status for logging/monitoring"""
        if len(self.price_history) == 0:
            return {
                'price_range_pct': 0.0,
                'volume_status': 'no data',
                'dead_price_counter': 0,
                'dead_volume_counter': 0
            }

        price_range = max(self.price_history) - min(self.price_history)
        range_pct = (price_range / min(self.price_history)) * 100 if min(self.price_history) > 0 else 0
        avg_volume = sum(self.volume_history) / len(self.volume_history)

        return {
            'price_range_pct': range_pct,
            'price_threshold': DEAD_PRICE_THRESHOLD_PCT,
            'price_dead': range_pct < DEAD_PRICE_THRESHOLD_PCT,
            'avg_volume': avg_volume,
            'volume_ratio': DEAD_VOLUME_RATIO,
            'dead_price_counter': self.dead_price_counter,
            'dead_volume_counter': self.dead_volume_counter,
            'candles_in_history': len(self.price_history)
        }
