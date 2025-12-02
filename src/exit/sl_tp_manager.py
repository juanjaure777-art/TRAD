#!/usr/bin/env python3
"""
Stop Loss and Take Profit Manager

Manages multi-level exit strategy:
1. Stop Loss (SL): Close 100% if price hits
2. Take Profit 1 (TP1): Close 50% at first target, move SL to breakeven, ACTIVATE TRAILING STOP
3. Trailing Stop: Manages remaining 50% - Trail below (LONG) or above (SHORT) current price

NEW v3.6+: TP1 now activates trailing stop immediately for remaining 50%.
TP2 is deprecated (not used).

This implements partial profit taking with risk management.
"""

from typing import Tuple, Dict, Optional
from src.constants import TRAILING_STOP_PCT, TP_PARTIAL_FILL


class SLTPManager:
    """Manages stop loss, take profit, and trailing stop logic"""

    def __init__(self):
        """Initialize position exit tracking"""
        self.tp1_closed = False
        self.tp2_closed = False
        self.trailing_stop_active = False
        self.trailing_stop_price = None
        self.max_price = None
        self.max_price_time = None

    def check_stop_loss(self,
                       current_price: float,
                       stop_loss_price: float,
                       side: str) -> Tuple[bool, Optional[str]]:
        """
        Check if stop loss has been hit

        Args:
            current_price: Current market price
            stop_loss_price: Stop loss level
            side: "LONG" or "SHORT"

        Returns:
            Tuple of (hit: bool, reason: str if hit)
        """
        if side == "LONG":
            if current_price <= stop_loss_price:
                return True, f"STOP_LOSS: ${current_price:.2f} <= ${stop_loss_price:.2f}"
        else:  # SHORT
            if current_price >= stop_loss_price:
                return True, f"STOP_LOSS: ${current_price:.2f} >= ${stop_loss_price:.2f}"

        return False, None

    def check_take_profit_1(self,
                           current_price: float,
                           tp1_price: float,
                           side: str) -> Tuple[bool, Optional[str]]:
        """
        Check if TP1 (first profit target) has been hit

        NEW v3.6+: Activates trailing stop immediately after closing 50%

        Args:
            current_price: Current market price
            tp1_price: First take profit level
            side: "LONG" or "SHORT"

        Returns:
            Tuple of (hit: bool, reason: str if hit)
        """
        if self.tp1_closed:
            return False, None

        if side == "LONG":
            if current_price >= tp1_price:
                self.tp1_closed = True
                self.trailing_stop_active = True  # ✅ Activate trailing stop for remaining 50%
                return True, f"TP1: ${current_price:.2f} >= ${tp1_price:.2f} | Close {TP_PARTIAL_FILL*100:.0f}% | Activate trailing for {TP_PARTIAL_FILL*100:.0f}%"
        else:  # SHORT
            if current_price <= tp1_price:
                self.tp1_closed = True
                self.trailing_stop_active = True  # ✅ Activate trailing stop for remaining 50%
                return True, f"TP1: ${current_price:.2f} <= ${tp1_price:.2f} | Close {TP_PARTIAL_FILL*100:.0f}% | Activate trailing for {TP_PARTIAL_FILL*100:.0f}%"

        return False, None

    def check_take_profit_2(self,
                           current_price: float,
                           tp2_price: float,
                           side: str) -> Tuple[bool, Optional[str]]:
        """
        Check if TP2 (second profit target) has been hit

        DEPRECATED v3.6+: TP2 is no longer used.
        Trailing stop is now activated at TP1, managing the remaining 50%.
        This method is kept for backward compatibility but always returns False.

        Args:
            current_price: Current market price
            tp2_price: Second take profit level
            side: "LONG" or "SHORT"

        Returns:
            Tuple of (hit: bool, reason: str if hit) - Always (False, None)
        """
        # DEPRECATED: TP2 no longer used in v3.6+
        # Trailing stop is activated at TP1
        return False, None

    def check_trailing_stop(self,
                           current_price: float,
                           stop_loss_price: float,
                           side: str) -> Tuple[bool, Optional[str]]:
        """
        Check if trailing stop has been hit

        NEW v3.6+: Trailing stop trails below (LONG) or above (SHORT) the highest point reached
        after TP1 is hit (manages remaining 50% of position).

        Args:
            current_price: Current market price
            stop_loss_price: Original stop loss (fallback)
            side: "LONG" or "SHORT"

        Returns:
            Tuple of (hit: bool, reason: str if hit)
        """
        if not self.trailing_stop_active:
            return False, None

        # Initialize max_price on first call after TP1
        if self.max_price is None:
            self.max_price = current_price
            if side == "LONG":
                self.trailing_stop_price = current_price * (1 - TRAILING_STOP_PCT)
            else:
                self.trailing_stop_price = current_price * (1 + TRAILING_STOP_PCT)
            return False, None

        # Update max_price if new high/low reached
        if side == "LONG":
            if current_price > self.max_price:
                self.max_price = current_price
                self.trailing_stop_price = current_price * (1 - TRAILING_STOP_PCT)

            # Check if trailing stop hit
            if current_price <= self.trailing_stop_price:
                return True, (f"TRAILING_STOP: ${current_price:.2f} <= "
                             f"${self.trailing_stop_price:.2f} (trail {TRAILING_STOP_PCT*100:.1f}% from max ${self.max_price:.2f})")
        else:  # SHORT
            if current_price < self.max_price:
                self.max_price = current_price
                self.trailing_stop_price = current_price * (1 + TRAILING_STOP_PCT)

            # Check if trailing stop hit
            if current_price >= self.trailing_stop_price:
                return True, (f"TRAILING_STOP: ${current_price:.2f} >= "
                             f"${self.trailing_stop_price:.2f} (trail {TRAILING_STOP_PCT*100:.1f}% from min ${self.max_price:.2f})")

        return False, None

    def reset(self):
        """Reset state for new position"""
        self.tp1_closed = False
        self.tp2_closed = False
        self.trailing_stop_active = False
        self.trailing_stop_price = None
        self.max_price = None
        self.max_price_time = None

    def get_status(self) -> Dict:
        """Get current exit status for logging"""
        return {
            'tp1_closed': self.tp1_closed,
            'tp2_closed': self.tp2_closed,
            'trailing_stop_active': self.trailing_stop_active,
            'trailing_stop_price': self.trailing_stop_price,
            'max_price': self.max_price
        }

    def should_move_sl_to_breakeven(self) -> bool:
        """
        Check if SL should be moved to breakeven (after TP1 hit)

        Returns:
            True if TP1 has been hit (and SL should be moved)
        """
        return self.tp1_closed

    def get_breakeven_stop_loss(self, entry_price: float, side: str) -> float:
        """
        Calculate breakeven stop loss level

        Args:
            entry_price: Original entry price
            side: "LONG" or "SHORT"

        Returns:
            Stop loss price at breakeven (or entry price with tiny spread)
        """
        # Add tiny spread to avoid getting stopped out on noise
        spread = entry_price * 0.0005  # 0.05% spread

        if side == "LONG":
            return entry_price - spread
        else:  # SHORT
            return entry_price + spread
