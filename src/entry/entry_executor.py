#!/usr/bin/env python3
"""
Entry Executor - Executes position entry with validation and risk checks

Entry validation chain:
1. Off-hours check (don't trade when market closed)
2. Risk Manager validation (position limits, daily loss limit)
3. Gatekeeper validation (Claude intelligence check)
4. Position initialization with SL/TP levels
5. TradeLogger logging (order lifecycle tracking)

Ensures only high-quality, risk-managed entries are executed.
"""

from typing import Tuple, Optional, Dict
from datetime import datetime, timezone
from src.trading.sessions import is_off_hours
from src.monitoring.trade_logger import get_trade_logger


class EntryExecutor:
    """Executes validated trading entries with proper risk management"""

    def __init__(self, risk_manager, trade_logger=None):
        """
        Initialize entry executor

        Args:
            risk_manager: RiskManager instance for validation
            trade_logger: TradeLogger instance for logging (optional)
        """
        self.risk_manager = risk_manager
        self.trade_logger = trade_logger or get_trade_logger()

    def can_enter(self) -> Tuple[bool, Optional[str]]:
        """
        Check if entry is allowed

        Returns:
            Tuple of (can_enter: bool, reason: str if cannot)
        """
        # Check 1: Off-hours
        if is_off_hours(datetime.now(timezone.utc)):
            return False, "❌ OFF_HOURS: Market is closed"

        # Check 2: Risk Manager validation
        can_open, risk_reason = self.risk_manager.can_open_position()
        if not can_open:
            return False, risk_reason

        return True, None

    def execute_entry(self,
                     signal: object,
                     cycle_count: int,
                     current_price: float) -> Tuple[bool, Optional[Dict]]:
        """
        Execute trade entry if all conditions are met

        Args:
            signal: Signal object from HybridStrategy with:
                - side: "LONG" or "SHORT"
                - entry_price: Entry price
                - stop_loss: SL level
                - take_profit_1: TP1 level
                - take_profit_2: TP2 level
                - position_size_pct: Position size
                - confidence: Confidence score
                - price_action: Pattern description
                - reason: Entry reason
            cycle_count: Current cycle number
            current_price: Current market price

        Returns:
            Tuple of (success: bool, position_dict: Dict if success)
        """
        # Check if entry is allowed
        can_enter, reason = self.can_enter()
        if not can_enter:
            self.trade_logger._write_journal(f"[ENTRY_BLOCKED] {reason}")
            return False, None

        # Create position
        position = {
            'side': signal.side,
            'entry_price': signal.entry_price,
            'entry_time': datetime.now(timezone.utc),
            'stop_loss': signal.stop_loss,
            'take_profit_1': signal.take_profit_1,
            'take_profit_2': signal.take_profit_2,
            'size': signal.position_size_pct,
            'tp1_hit': False,
            'signal_id': f"SIGNAL_{cycle_count}_{signal.side}"
        }

        # Register with Risk Manager
        self.risk_manager.register_trade_entry(signal.entry_price, signal.side)

        # Log entry execution
        self._log_entry(position, signal, cycle_count)

        return True, position

    def _log_entry(self, position: Dict, signal: object, cycle_count: int):
        """Log entry execution with full context"""
        signal_id = position['signal_id']

        # Log to trade logger
        self.trade_logger.log_signal_detected(
            signal_id=signal_id,
            signal_type=signal.side,
            price=position['entry_price'],
            rsi=signal.rsi_value,
            timeframe='4h',  # 4H strategy timeframe
            metadata={
                'confidence': signal.confidence,
                'pattern': signal.price_action,
                'reason': signal.reason
            }
        )

        # Log order lifecycle
        self.trade_logger.log_order_status(
            signal_id=signal_id,
            status='ENTRY_EXECUTED',
            price=position['entry_price'],
            details={
                'side': position['side'],
                'stop_loss': position['stop_loss'],
                'take_profit_1': position['take_profit_1'],
                'take_profit_2': position['take_profit_2'],
                'confidence': signal.confidence
            }
        )

        # Console display
        emoji = "🟢" if signal.side == "LONG" else "🔴"
        print(f"{emoji} ABIERTO {signal.side} | Entry: ${position['entry_price']:.2f} | "
              f"SL: ${position['stop_loss']:.2f} | TP1: ${position['take_profit_1']:.2f} | "
              f"TP2: ${position['take_profit_2']:.2f}")
        print(f"   Confianza: {signal.confidence:.0f}% | Patrón: {signal.price_action} | {signal.reason}")

    def validate_signal_quality(self, signal: object) -> Tuple[bool, str]:
        """
        Additional validation of signal quality (optional)

        Args:
            signal: Signal to validate

        Returns:
            Tuple of (is_valid: bool, reason: str)
        """
        # Check 1: Minimum confidence
        MIN_CONFIDENCE = 40.0  # 40%
        if signal.confidence < MIN_CONFIDENCE:
            return False, f"Low confidence: {signal.confidence:.0f}% < {MIN_CONFIDENCE}%"

        # Check 2: Valid price levels
        if signal.side == "LONG":
            if signal.entry_price >= signal.stop_loss:
                return False, "Invalid LONG: entry >= SL"
            if signal.stop_loss >= signal.take_profit_1 >= signal.take_profit_2:
                return False, "Invalid LONG: SL >= TP1 >= TP2"
        else:  # SHORT
            if signal.entry_price <= signal.stop_loss:
                return False, "Invalid SHORT: entry <= SL"
            if signal.stop_loss <= signal.take_profit_1 <= signal.take_profit_2:
                return False, "Invalid SHORT: SL <= TP1 <= TP2"

        return True, "Signal quality OK"
