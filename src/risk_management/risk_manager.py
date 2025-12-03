#!/usr/bin/env python3
"""
RISK MANAGER - v3.5 Risk Management Layer
Enforces position limits, daily loss limits, and trade cooldown
"""

from datetime import datetime, timedelta
from typing import Tuple, Dict, Optional
import json
from pathlib import Path


class RiskManager:
    """Professional risk management with strict enforcement"""

    def __init__(self, config: dict = None):
        self.config = config or {}

        # Risk parameters
        self.max_open_positions = self.config.get('max_open_positions', 3)
        self.max_daily_loss_pct = self.config.get('max_daily_loss_percent', 5.0)
        self.min_trade_cooldown_seconds = self.config.get('min_trade_cooldown_seconds', 30)

        # Session tracking
        self.session_start = datetime.utcnow()
        self.daily_pnl = 0.0  # Accumulated P&L in percentage
        self.open_positions = 0
        self.last_trade_time = None
        self.trades_today = 0

        # Risk stats
        self.risk_events = []
        self.stats_file = Path("logs/risk_management/stats.json")
        self.stats_file.parent.mkdir(parents=True, exist_ok=True)

        self._load_session_stats()

        # CRITICAL FIX: Sanitize loaded values to prevent -inf/nan errors
        self._sanitize_pnl_values()

    def _load_session_stats(self):
        """Load previous session stats if available"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    stats = json.load(f)
                    # Reset if new day
                    if self._is_new_trading_day(stats.get('last_update')):
                        self.daily_pnl = 0.0
                        self.trades_today = 0
                    else:
                        self.daily_pnl = stats.get('daily_pnl', 0.0)
                        self.trades_today = stats.get('trades_today', 0)
            except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
                # Stats file invalid or missing, use defaults
                pass

    def _is_new_trading_day(self, last_timestamp: Optional[str]) -> bool:
        """Check if it's a new trading day"""
        if not last_timestamp:
            return True
        try:
            last_time = datetime.fromisoformat(last_timestamp)
            return last_time.date() != datetime.utcnow().date()
        except (ValueError, TypeError):
            # Invalid timestamp format, treat as new day
            return True

    def _sanitize_pnl_values(self):
        """Sanitize P&L values to prevent inf/nan errors"""
        import math

        # Check for invalid values
        if math.isnan(self.daily_pnl) or math.isinf(self.daily_pnl):
            self._log_risk_event(f"⚠️ WARNING: Invalid daily_pnl detected ({self.daily_pnl}), resetting to 0.0")
            self.daily_pnl = 0.0

        # Ensure daily_pnl is within reasonable bounds (-100% to +1000%)
        if self.daily_pnl < -100.0:
            self._log_risk_event(f"⚠️ WARNING: daily_pnl too low ({self.daily_pnl}%), capping at -100%")
            self.daily_pnl = -100.0
        elif self.daily_pnl > 1000.0:
            self._log_risk_event(f"⚠️ WARNING: daily_pnl too high ({self.daily_pnl}%), capping at +1000%")
            self.daily_pnl = 1000.0

    def can_open_position(self) -> Tuple[bool, str]:
        """Check if new position can be opened"""

        # Check 1: Max open positions
        if self.open_positions >= self.max_open_positions:
            reason = f"❌ MAX_POSITIONS REACHED ({self.open_positions}/{self.max_open_positions})"
            self._log_risk_event(reason)
            return False, reason

        # Check 2: Daily loss limit (daily_pnl is in % already)
        if self.daily_pnl <= -self.max_daily_loss_pct:
            reason = f"❌ DAILY_LOSS_LIMIT HIT (Daily P&L: {self.daily_pnl:.2f}% / Limit: -{self.max_daily_loss_pct}%)"
            self._log_risk_event(reason)
            return False, reason

        # Check 3: Trade cooldown
        if self.last_trade_time:
            elapsed = (datetime.utcnow() - self.last_trade_time).total_seconds()
            if elapsed < self.min_trade_cooldown_seconds:
                reason = f"❌ TRADE_COOLDOWN ({elapsed:.0f}s < {self.min_trade_cooldown_seconds}s)"
                self._log_risk_event(reason)
                return False, reason

        return True, "✅ RISK_CHECK_PASSED"

    def register_trade_entry(self, price: float, side: str) -> Dict:
        """Register a new trade entry"""
        self.open_positions += 1
        self.last_trade_time = datetime.utcnow()
        self.trades_today += 1

        event = {
            "type": "TRADE_ENTRY",
            "timestamp": self.last_trade_time.isoformat(),
            "price": price,
            "side": side,
            "open_positions": self.open_positions,
            "trades_today": self.trades_today
        }

        self._log_risk_event(f"✅ TRADE_ENTRY: {side} @ ${price:.2f} | Open Pos: {self.open_positions}/{self.max_open_positions}")
        return event

    def register_trade_close(self, pnl: float, close_reason: str = "manual") -> Dict:
        """Register a trade close and update P&L"""
        if self.open_positions > 0:
            self.open_positions -= 1

        self.daily_pnl += pnl

        event = {
            "type": "TRADE_CLOSE",
            "timestamp": datetime.utcnow().isoformat(),
            "pnl": pnl,
            "daily_pnl": self.daily_pnl,
            "daily_pnl_pct": self.daily_pnl,  # Approximate (should track starting balance)
            "close_reason": close_reason,
            "open_positions": self.open_positions
        }

        status = "✅ WIN" if pnl > 0 else ("🔴 LOSS" if pnl < 0 else "⚪ BREAK_EVEN")
        self._log_risk_event(f"{status}: {close_reason} | P&L: ${pnl:.2f} | Daily: ${self.daily_pnl:.2f} | Open Pos: {self.open_positions}")

        # Check if daily loss limit breached
        if self.daily_pnl < (-self.max_daily_loss_pct):
            self._log_risk_event(f"⚠️ WARNING: Daily loss limit approaching ({self.daily_pnl:.2f}%)")

        return event

    def get_risk_status(self) -> Dict:
        """Get current risk status"""
        daily_loss_pct = (self.daily_pnl / self.max_daily_loss_pct) * 100 if self.max_daily_loss_pct > 0 else 0

        return {
            "open_positions": self.open_positions,
            "max_open_positions": self.max_open_positions,
            "position_usage": f"{self.open_positions}/{self.max_open_positions}",
            "daily_pnl": self.daily_pnl,
            "daily_pnl_limit": self.max_daily_loss_pct,
            "daily_loss_usage_pct": daily_loss_pct,
            "trades_today": self.trades_today,
            "last_trade_time": self.last_trade_time.isoformat() if self.last_trade_time else None,
            "session_duration": (datetime.utcnow() - self.session_start).total_seconds()
        }

    def _log_risk_event(self, message: str):
        """Log risk event"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message
        }
        self.risk_events.append(event)

        # Save to file
        log_file = Path("logs/risk_management/events.log")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, 'a') as f:
            f.write(f"[{event['timestamp']}] {message}\n")

    def save_session_stats(self):
        """Save session statistics"""
        stats = {
            "session_start": self.session_start.isoformat(),
            "last_update": datetime.utcnow().isoformat(),
            "daily_pnl": self.daily_pnl,
            "trades_today": self.trades_today,
            "open_positions": self.open_positions,
            "risk_events": len(self.risk_events)
        }

        with open(self.stats_file, 'w') as f:
            json.dump(stats, f, indent=2)

    def print_status(self):
        """Print current risk status"""
        status = self.get_risk_status()
        print("\n" + "="*70)
        print("📊 RISK MANAGEMENT STATUS")
        print("="*70)
        print(f"Open Positions:    {status['position_usage']}")
        print(f"Daily P&L:         ${status['daily_pnl']:.2f} ({status['daily_loss_usage_pct']:.1f}% of limit)")
        print(f"Trades Today:      {status['trades_today']}")
        print(f"Last Trade:        {status['last_trade_time'] or 'None'}")
        print(f"Session Duration:  {status['session_duration']:.0f} seconds")
        print("="*70 + "\n")
