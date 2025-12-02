#!/usr/bin/env python3
"""
Adapter to integrate HybridStrategy with GatekeeperV2
Replaces MODE-based decision logic with Claude-based validation.

Flow:
1. HybridStrategy generates technical signal
2. If signal meets minimum criteria, pass to GatekeeperV2
3. GatekeeperV2 makes final decision based on configured level
"""

import json
from typing import Dict, Any, Tuple, Optional
from src.strategy.hybrid import HybridSignal
from src.trading.gatekeeper_v2 import GatekeeperV2


class HybridGatekeeperAdapter:
    """Integrates HybridStrategy with GatekeeperV2 for intelligent entry decisions"""

    def __init__(self, gatekeeper_level: int = 2, mode: str = "testnet"):
        """
        Args:
            gatekeeper_level: 1-5 (1=permissive, 5=restrictive)
            mode: 'testnet' or 'live'
        """
        self.gatekeeper = GatekeeperV2(level=gatekeeper_level, mode=mode)
        self.mode = mode
        self.log_file = f"logs/hybrid_gatekeeper_{mode}.log"
        self.last_signal: Optional[HybridSignal] = None

    def should_enter(self, signal: HybridSignal, market_phase: str = "NEUTRAL",
                    additional_context: Dict[str, Any] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate HybridStrategy signal through GatekeeperV2.

        Args:
            signal: HybridSignal from HybridStrategy.analyze()
            market_phase: Current market phase (IMPULSE, CORRECTIVE, REVERSAL, NEUTRAL)
            additional_context: Additional market data (volatility, momentum, etc)

        Returns:
            (should_enter: bool, decision_details: dict)
        """

        self.last_signal = signal

        # Quick reject if technical signal already says no
        if not signal.should_trade:
            return False, {
                'approved': False,
                'reason': 'Technical signal rejected',
                'gatekeeper_decision': None
            }

        # If technical signal is weak, check gatekeeper confidence threshold
        min_confidence_threshold = {
            1: 0.3,  # Level 1: Very permissive, low threshold
            2: 0.4,  # Level 2: Permissive
            3: 0.5,  # Level 3: Balanced
            4: 0.6,  # Level 4: Selective
            5: 0.75  # Level 5: Maximum selective
        }

        # Pass to Claude for intelligent validation
        decision = self.gatekeeper.should_enter(
            rsi=signal.rsi_value,
            price=signal.entry_price,
            ema_fast=signal.ema_9,
            ema_slow=signal.ema_21,
            market_phase=market_phase,
            open_positions=0,  # TODO: Get from bot state
            reward_risk_ratio=self._calculate_rr_ratio(signal),
            additional_context=additional_context or {}
        )

        # Get threshold for current level
        min_conf = min_confidence_threshold.get(self.gatekeeper.level, 0.5)

        # Approval logic
        approved = (
            decision['should_enter'] and
            decision['confidence'] >= min_conf
        )

        result = {
            'approved': approved,
            'technical_signal': signal.should_trade,
            'gatekeeper_level': self.gatekeeper.level,
            'claude_decision': decision['should_enter'],
            'claude_confidence': decision['confidence'],
            'claude_reason': decision['reason'],
            'side': signal.side if approved else None,
            'entry_price': signal.entry_price if approved else None,
            'stop_loss': signal.stop_loss if approved else None,
            'take_profit_1': signal.take_profit_1 if approved else None,
            'take_profit_2': signal.take_profit_2 if approved else None,
            'tokens_used': decision.get('tokens_used', {})
        }

        self._log_decision(approved, result)
        return approved, result

    def _calculate_rr_ratio(self, signal: HybridSignal) -> float:
        """Calculate risk:reward ratio from signal"""
        try:
            if signal.side == "LONG":
                risk = signal.entry_price - signal.stop_loss
                reward = signal.take_profit_2 - signal.entry_price
            else:  # SHORT
                risk = signal.stop_loss - signal.entry_price
                reward = signal.entry_price - signal.take_profit_2

            if risk <= 0:
                return 1.0
            return reward / risk
        except:
            return 1.0

    def set_level(self, level: int):
        """Change gatekeeper level dynamically (1-5)"""
        self.gatekeeper.set_level(level)

    def get_stats(self) -> Dict[str, Any]:
        """Get decision statistics"""
        stats = self.gatekeeper.get_stats()
        stats['last_signal_side'] = self.last_signal.side if self.last_signal else None
        stats['last_signal_confidence'] = self.last_signal.confidence if self.last_signal else None
        return stats

    def _log_decision(self, approved: bool, details: Dict[str, Any]):
        """Log decision details"""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            status = "✅ APPROVED" if approved else "❌ REJECTED"

            log_entry = f"[{timestamp}] {status} | Level: {details['gatekeeper_level']} | "
            log_entry += f"Tech: {details['technical_signal']} | "
            log_entry += f"Claude: {details['claude_decision']} ({details['claude_confidence']:.2f}) | "
            log_entry += f"{details['claude_reason']}\n"

            with open(self.log_file, 'a') as f:
                f.write(log_entry)
        except:
            pass

    def clear_logs(self):
        """Clear decision logs"""
        try:
            open(self.log_file, 'w').close()
        except:
            pass
