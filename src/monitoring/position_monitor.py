#!/usr/bin/env python3
"""
Position Monitor - Tracks position state and session information

Monitors:
- Current position details (entry, targets, SL)
- Session information (active trading session)
- Performance metrics (P&L tracking)
- Position history
"""

from typing import Optional, Dict
from datetime import datetime, timezone
from src.trading.sessions import get_active_session


class PositionMonitor:
    """Monitors active position and session state"""

    def __init__(self):
        """Initialize position monitor"""
        self.position = None
        self.active_session = None
        self.session_start_time = None

    def open_position(self,
                     side: str,
                     entry_price: float,
                     stop_loss: float,
                     take_profit_1: float,
                     take_profit_2: float,
                     position_size: float,
                     signal_id: str) -> Dict:
        """
        Track new opened position

        Args:
            side: "LONG" or "SHORT"
            entry_price: Entry price
            stop_loss: Stop loss level
            take_profit_1: First take profit level
            take_profit_2: Second take profit level
            position_size: Position size percentage
            signal_id: Signal identifier for logging

        Returns:
            Position dict
        """
        self.position = {
            'side': side,
            'entry_price': entry_price,
            'entry_time': datetime.now(timezone.utc),
            'stop_loss': stop_loss,
            'take_profit_1': take_profit_1,
            'take_profit_2': take_profit_2,
            'size': position_size,
            'tp1_hit': False,
            'signal_id': signal_id
        }

        # Update session tracking
        current_time = datetime.now(timezone.utc)
        session = get_active_session(current_time)
        self.active_session = session.name if session else None
        self.session_start_time = current_time

        return self.position

    def close_position(self) -> Optional[Dict]:
        """
        Close current position

        Returns:
            Closed position dict, or None if no position
        """
        closed = self.position
        self.position = None
        self.active_session = None
        self.session_start_time = None
        return closed

    def get_position(self) -> Optional[Dict]:
        """Get current position (read-only)"""
        return self.position

    def has_position(self) -> bool:
        """Check if position is open"""
        return self.position is not None

    def update_stop_loss(self, new_stop_loss: float):
        """Update stop loss level (e.g., move to breakeven)"""
        if self.position:
            self.position['stop_loss'] = new_stop_loss

    def calculate_pnl(self, current_price: float) -> Dict:
        """
        Calculate current P&L

        Args:
            current_price: Current market price

        Returns:
            {
                'pnl_absolute': float,
                'pnl_percent': float,
                'is_profitable': bool,
                'position_age_seconds': float
            }
        """
        if not self.position:
            return {
                'pnl_absolute': 0.0,
                'pnl_percent': 0.0,
                'is_profitable': False,
                'position_age_seconds': 0.0
            }

        entry_price = self.position['entry_price']
        side = self.position['side']

        # Calculate P&L
        if side == "LONG":
            pnl_absolute = current_price - entry_price
        else:  # SHORT
            pnl_absolute = entry_price - current_price

        pnl_percent = (pnl_absolute / entry_price * 100) if entry_price > 0 else 0

        # Calculate position age
        position_age = (datetime.now(timezone.utc) - self.position['entry_time']).total_seconds()

        return {
            'pnl_absolute': pnl_absolute,
            'pnl_percent': pnl_percent,
            'is_profitable': pnl_absolute > 0,
            'position_age_seconds': position_age
        }

    def get_position_info(self, current_price: float) -> Dict:
        """
        Get comprehensive position information

        Args:
            current_price: Current market price

        Returns:
            Complete position info for display/logging
        """
        if not self.position:
            return {
                'has_position': False,
                'position': None
            }

        pnl = self.calculate_pnl(current_price)

        # Calculate distance to targets
        entry = self.position['entry_price']
        distance_to_tp1 = (
            self.position['take_profit_1'] - entry
            if self.position['side'] == 'LONG'
            else entry - self.position['take_profit_1']
        )
        distance_to_tp2 = (
            self.position['take_profit_2'] - entry
            if self.position['side'] == 'LONG'
            else entry - self.position['take_profit_2']
        )

        return {
            'has_position': True,
            'position': self.position,
            'current_price': current_price,
            'pnl': pnl,
            'distance_to_tp1': distance_to_tp1,
            'distance_to_tp2': distance_to_tp2,
            'active_session': self.active_session,
            'session_duration_seconds': (
                (datetime.now(timezone.utc) - self.session_start_time).total_seconds()
                if self.session_start_time else 0
            )
        }

    def get_status(self) -> Dict:
        """Get position monitor status"""
        return {
            'has_position': self.has_position(),
            'active_session': self.active_session,
            'session_start_time': self.session_start_time.isoformat() if self.session_start_time else None
        }
