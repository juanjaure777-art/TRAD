#!/usr/bin/env python3
"""
Exit Manager - Orchestrates all position exit logic

Coordinates:
1. Dead Trade Detection - Close stalled positions
2. Stop Loss / Take Profit - Multi-level exit strategy
3. Session Closing - Close positions before market closes
4. Trailing Stop - Lock in profits with trailing logic

Provides unified interface for checking exit conditions each cycle.
"""

from typing import Tuple, Optional, Dict
from datetime import datetime, timezone
from src.exit.dead_trade_detector import DeadTradeDetector
from src.exit.sl_tp_manager import SLTPManager
from src.trading.sessions import get_active_session, is_off_hours


class ExitManager:
    """Manages all position exit conditions"""

    def __init__(self):
        """Initialize exit managers"""
        self.dead_trade_detector = DeadTradeDetector()
        self.sl_tp_manager = SLTPManager()

    def open_new_position(self, current_price: float):
        """
        Called when opening a new position

        Args:
            current_price: Entry price
        """
        self.dead_trade_detector.reset()
        self.sl_tp_manager.reset()
        self.sl_tp_manager.max_price = current_price  # Start tracking max for trailing stop

    def update_candle(self, price: float, volume: float):
        """
        Update with new candle data

        Args:
            price: Closing price
            volume: Trading volume
        """
        self.dead_trade_detector.update_history(price, volume)

    def check_all_exits(self,
                       current_price: float,
                       position: Dict) -> Tuple[bool, str, Optional[str]]:
        """
        Check all exit conditions in order of priority

        Returns:
            Tuple of (should_exit: bool, exit_type: str, details: str)

        Exit types:
        - "DEAD_TRADE": Trade stalled
        - "STOP_LOSS": Hit SL
        - "TAKE_PROFIT_1": TP1 hit (partial close 50%)
        - "TAKE_PROFIT_2": TP2 hit (partial close 25%, activate trailing)
        - "TRAILING_STOP": Trailing stop hit
        - "SESSION_CLOSING": Market about to close
        - "OFF_HOURS": Market is closed
        - None: No exit conditions
        """
        side = position['side']

        # Priority 1: Stop Loss (hard exit)
        hit, reason = self.sl_tp_manager.check_stop_loss(
            current_price, position['stop_loss'], side
        )
        if hit:
            return True, "STOP_LOSS", reason

        # Priority 2: Dead Trade (position stalled)
        is_dead, reason = self.dead_trade_detector.check_dead_trade(current_price, 0)
        if is_dead:
            return True, "DEAD_TRADE", reason

        # Priority 3: Take Profit 1 (partial exit)
        hit, reason = self.sl_tp_manager.check_take_profit_1(
            current_price, position['take_profit_1'], side
        )
        if hit:
            # Move SL to breakeven
            new_sl = self.sl_tp_manager.get_breakeven_stop_loss(
                position['entry_price'], side
            )
            position['stop_loss'] = new_sl
            return True, "TAKE_PROFIT_1", reason

        # Priority 4: Take Profit 2 (partial exit + activate trailing)
        hit, reason = self.sl_tp_manager.check_take_profit_2(
            current_price, position['take_profit_2'], side
        )
        if hit:
            return True, "TAKE_PROFIT_2", reason

        # Priority 5: Trailing Stop (if active)
        hit, reason = self.sl_tp_manager.check_trailing_stop(
            current_price, position['stop_loss'], side
        )
        if hit:
            return True, "TRAILING_STOP", reason

        # Priority 6: Session Closing (soft warning before hard close at off_hours)
        should_close, reason = self._check_session_closing()
        if should_close:
            return True, "SESSION_CLOSING", reason

        # Priority 7: Off Hours (hard exit if market closed)
        if is_off_hours(datetime.now(timezone.utc)):
            return True, "OFF_HOURS", "Market closed"

        return False, None, None

    def _check_session_closing(self) -> Tuple[bool, str]:
        """
        Check if we're approaching session closing time

        Most sessions end with 30-minute closing bars where it's harder to exit
        Returns:
            Tuple of (should_close: bool, reason: str)
        """
        try:
            current_time = datetime.now(timezone.utc)
            session = get_active_session(current_time)

            if not session:
                return False, ""

            # Get session closing time
            closing_time = session.get_closing_alert_time()
            if not closing_time:
                return False, ""

            time_until_close = (closing_time - current_time).total_seconds() / 60  # minutes

            # Close position if within 30 minutes of session close
            if 0 < time_until_close < 30:
                return True, f"SESSION_CLOSING: {time_until_close:.0f} min until {session.name} close"

            return False, ""

        except Exception:
            # If error checking session, don't force close
            return False, ""

    def get_exit_status(self) -> Dict:
        """Get detailed exit status for logging/monitoring"""
        return {
            'dead_trade_detector': self.dead_trade_detector.get_status(),
            'sl_tp_manager': self.sl_tp_manager.get_status()
        }

    def reset(self):
        """Reset exit manager for new position"""
        self.dead_trade_detector.reset()
        self.sl_tp_manager.reset()
