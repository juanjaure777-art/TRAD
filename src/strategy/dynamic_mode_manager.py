#!/usr/bin/env python3
"""
DYNAMIC MODE MANAGER - v3.5 Automatic Mode Switching
Switches between 5 trading modes based on market volatility and conditions
"""

from typing import Tuple, Dict
from datetime import datetime
from src.strategy.modes import TradingMode, MODES_CONFIG
from src.strategy.indicators import TechnicalIndicators


class DynamicModeManager:
    """Intelligent mode switching based on market conditions"""

    def __init__(self):
        self.current_mode = TradingMode.PERMISSIVE  # Default: MODE 2
        self.volatility = 50.0  # Initial volatility (0-100)
        self.mode_switches = []
        self.last_mode_switch = datetime.utcnow()

    def determine_mode(self, rsi: float, atr: float, recent_closes: list) -> Tuple[TradingMode, str]:
        """
        Determine best mode based on market conditions

        Algorithm:
        - Calculate volatility (ATR based)
        - Classify market phase based on RSI and recent movement
        - Recommend mode accordingly
        """

        # Calculate volatility (simplified: use ATR if available, else use price movement)
        if recent_closes and len(recent_closes) >= 5:
            price_range = max(recent_closes[-5:]) - min(recent_closes[-5:])
            avg_price = sum(recent_closes[-5:]) / 5
            volatility_pct = (price_range / avg_price) * 100
            self.volatility = volatility_pct * 10  # Scale to 0-100
        else:
            self.volatility = 50.0

        self.volatility = max(0, min(100, self.volatility))  # Clamp to 0-100

        # Classify market phase
        if rsi < 25:
            phase = "OVERSOLD"
        elif rsi > 75:
            phase = "OVERBOUGHT"
        elif 35 < rsi < 65:
            phase = "NEUTRAL"
        else:
            phase = "TRENDING"

        # Recommend mode based on volatility and phase
        recommended_mode = self._get_mode_for_conditions(self.volatility, phase, rsi)

        # Check if mode changed
        reason = self._generate_reason(phase, rsi, self.volatility, recommended_mode)

        if recommended_mode != self.current_mode:
            self.current_mode = recommended_mode
            self.mode_switches.append({
                "timestamp": datetime.utcnow().isoformat(),
                "from": str(self.current_mode),
                "to": str(recommended_mode),
                "reason": reason
            })
            return recommended_mode, f"🔄 MODE SWITCH: {reason}"

        return recommended_mode, f"✅ Mode stable: {self.current_mode.name}"

    def _get_mode_for_conditions(self, volatility: float, phase: str, rsi: float) -> TradingMode:
        """Get recommended mode based on market conditions"""

        # HIGH VOLATILITY: Be more selective
        if volatility > 70:
            if phase == "OVERBOUGHT" or phase == "OVERSOLD":
                return TradingMode.MAXIMUM_SELECTIVE  # MODE 5: Maximum selectivity
            else:
                return TradingMode.SELECTIVE  # MODE 4: Selective

        # MODERATE VOLATILITY: Balanced approach
        elif 40 <= volatility <= 70:
            if phase == "NEUTRAL":
                return TradingMode.PERMISSIVE  # MODE 2: Take more opportunities
            elif phase == "TRENDING":
                return TradingMode.BALANCED  # MODE 3: Follow the trend
            else:
                return TradingMode.SELECTIVE  # MODE 4: Be careful at extremes

        # LOW VOLATILITY: Be permissive to capture micro-moves
        else:
            if phase == "NEUTRAL":
                return TradingMode.VERY_PERMISSIVE  # MODE 1: Take any good setup
            else:
                return TradingMode.PERMISSIVE  # MODE 2: Still be somewhat careful

    def _generate_reason(self, phase: str, rsi: float, volatility: float, new_mode: TradingMode) -> str:
        """Generate a human-readable reason for the mode"""
        volatility_desc = "HIGH" if volatility > 70 else ("MODERATE" if volatility > 40 else "LOW")
        return f"{phase} (RSI:{rsi:.0f}, Vol:{volatility_desc}%) → {new_mode.name}"

    def get_mode_config(self) -> dict:
        """Get current mode configuration"""
        return MODES_CONFIG.get(self.current_mode, MODES_CONFIG[TradingMode.BALANCED])

    def get_status(self) -> Dict:
        """Get current mode status"""
        config = self.get_mode_config()
        return {
            "current_mode": self.current_mode.name,
            "mode_number": self.current_mode.value,
            "volatility": self.volatility,
            "rsi_lower": config.rsi_lower,
            "rsi_upper": config.rsi_upper,
            "ema_strength_required": config.ema_strength_required,
            "mtf_confirmations": config.mtf_confirmations_needed,
            "gatekeeper_required": config.gate_keeper_required,
            "mode_switches_count": len(self.mode_switches),
            "description": config.description
        }

    def print_status(self):
        """Print current mode status"""
        status = self.get_status()
        print("\n" + "="*70)
        print("📊 DYNAMIC MODE STATUS")
        print("="*70)
        print(f"Current Mode:           {status['current_mode']} (#{status['mode_number']})")
        print(f"Description:            {status['description']}")
        print(f"Volatility:             {status['volatility']:.1f}%")
        print(f"RSI Thresholds:         < {status['rsi_lower']} / > {status['rsi_upper']}")
        print(f"EMA Required:           {status['ema_strength_required']}")
        print(f"Multi-TF Confirmations: {status['mtf_confirmations']}")
        print(f"Gatekeeper Required:    {status['gatekeeper_required']}")
        print(f"Mode Switches:          {status['mode_switches_count']}")
        print("="*70 + "\n")
