#!/usr/bin/env python3
"""
Permissiveness Modes Module - v3.3 Dynamic Trading
Defines 5 modes of permissiveness based on market phases
Modes adapt dynamically to current market conditions
"""

from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class TradingMode(Enum):
    """Enum for 5 trading modes"""
    VERY_PERMISSIVE = 1      # Máximo volumen
    PERMISSIVE = 2            # Permisivo
    BALANCED = 3              # Equilibrado (default)
    SELECTIVE = 4             # Selectivo
    MAXIMUM_SELECTIVE = 5     # Máximo selectivo

class MarketPhase(Enum):
    """Market phases based on Crecetrader methodology"""
    IMPULSE = "IMPULSE"
    CORRECTIVE = "CORRECTIVE"
    REVERSAL = "REVERSAL"
    NEUTRAL = "NEUTRAL"

@dataclass
class ModeConfig:
    """Configuration for each permissiveness mode"""
    mode: TradingMode
    rsi_lower: int           # RSI threshold for SHORT signals
    rsi_upper: int           # RSI threshold for LONG signals
    ema_strength_required: bool  # EMA confirmation required?
    mtf_confirmations_needed: int  # How many timeframes needed (0=none, 1=weak, 2=medium, 3=strict)
    gate_keeper_required: bool     # Claude gate-keeper validation?
    description: str
    ideal_phase: str

# Define all 5 modes
MODES_CONFIG = {
    TradingMode.MAXIMUM_SELECTIVE: ModeConfig(
        mode=TradingMode.MAXIMUM_SELECTIVE,
        rsi_lower=20,
        rsi_upper=80,
        ema_strength_required=True,
        mtf_confirmations_needed=3,
        gate_keeper_required=True,
        description="MÁXIMO SELECTIVO - Solo lo ideal",
        ideal_phase="REVERSAL"
    ),
    TradingMode.SELECTIVE: ModeConfig(
        mode=TradingMode.SELECTIVE,
        rsi_lower=25,
        rsi_upper=75,
        ema_strength_required=True,
        mtf_confirmations_needed=2,
        gate_keeper_required=True,
        description="SELECTIVO - Impulso inicial",
        ideal_phase="IMPULSE"
    ),
    TradingMode.BALANCED: ModeConfig(
        mode=TradingMode.BALANCED,
        rsi_lower=30,
        rsi_upper=70,
        ema_strength_required=True,
        mtf_confirmations_needed=1,
        gate_keeper_required=True,
        description="EQUILIBRADO - Balance calidad-cantidad",
        ideal_phase="IMPULSE"
    ),
    TradingMode.PERMISSIVE: ModeConfig(
        mode=TradingMode.PERMISSIVE,
        rsi_lower=35,
        rsi_upper=65,
        ema_strength_required=False,
        mtf_confirmations_needed=0,
        gate_keeper_required=False,
        description="PERMISIVO - Correcciones y más trades",
        ideal_phase="CORRECTIVE"
    ),
    TradingMode.VERY_PERMISSIVE: ModeConfig(
        mode=TradingMode.VERY_PERMISSIVE,
        rsi_lower=40,
        rsi_upper=60,
        ema_strength_required=False,
        mtf_confirmations_needed=0,
        gate_keeper_required=False,
        description="MUY PERMISIVO - Máximo volumen",
        ideal_phase="NEUTRAL"
    ),
}

class PermissivenessManager:
    """Manages dynamic permissiveness modes based on market conditions"""

    def __init__(self):
        self.current_mode: TradingMode = TradingMode.BALANCED
        self.current_phase: MarketPhase = MarketPhase.NEUTRAL
        self.auto_detect: bool = True
        self.override_reason: Optional[str] = None

    def get_current_config(self) -> ModeConfig:
        """Get configuration for current mode"""
        return MODES_CONFIG[self.current_mode]

    def detect_phase(self,
                    closes: list,
                    atr: float,
                    ema9: float,
                    ema21: float,
                    current_price: float,
                    rsi: float) -> MarketPhase:
        """
        Detect market phase based on price action and indicators
        Uses Crecetrader methodology
        """
        if len(closes) < 20:
            return MarketPhase.NEUTRAL

        # Calculate metrics
        volatility = atr / current_price
        ema_distance = abs(ema9 - ema21) / current_price
        price_momentum = (closes[-1] - closes[-20]) / closes[-20]
        recent_move = (closes[-1] - closes[-5]) / closes[-5]

        # Phase detection logic (Crecetrader-based)

        # REVERSAL: Low momentum with extreme RSI - signal reversal
        if (price_momentum < 0.01) and (rsi < 20 or rsi > 80):
            return MarketPhase.REVERSAL

        # IMPULSE: Strong momentum, price trending, RSI extremes
        if (abs(price_momentum) > 0.02) and (abs(recent_move) > 0.01):
            if (rsi < 25 or rsi > 75):
                return MarketPhase.IMPULSE

        # CORRECTIVE: Price moving against recent trend, 50%+ correction
        if (price_momentum > 0 and recent_move < -0.01) or \
           (price_momentum < 0 and recent_move > 0.01):
            if abs(recent_move) > 0.005:
                return MarketPhase.CORRECTIVE

        return MarketPhase.NEUTRAL

    def suggest_mode_for_phase(self, phase: MarketPhase) -> TradingMode:
        """Suggest optimal mode based on detected phase"""
        phase_to_mode = {
            MarketPhase.REVERSAL: TradingMode.MAXIMUM_SELECTIVE,
            MarketPhase.IMPULSE: TradingMode.SELECTIVE,
            MarketPhase.CORRECTIVE: TradingMode.PERMISSIVE,
            MarketPhase.NEUTRAL: TradingMode.BALANCED,
        }
        return phase_to_mode.get(phase, TradingMode.BALANCED)

    def auto_adjust_mode(self,
                        closes: list,
                        atr: float,
                        ema9: float,
                        ema21: float,
                        current_price: float,
                        rsi: float) -> Tuple[TradingMode, MarketPhase]:
        """
        Auto-adjust mode based on current market conditions
        Returns (new_mode, detected_phase)
        """
        if not self.auto_detect:
            return self.current_mode, self.current_phase

        # Detect current phase
        phase = self.detect_phase(closes, atr, ema9, ema21, current_price, rsi)
        self.current_phase = phase

        # Suggest mode for phase
        suggested_mode = self.suggest_mode_for_phase(phase)

        # Only change if different
        if suggested_mode != self.current_mode:
            self.current_mode = suggested_mode
            self.override_reason = f"Auto-adjusted to {phase.value}"
            return suggested_mode, phase

        return self.current_mode, phase

    def manual_override(self, mode: TradingMode, reason: str):
        """Manually override mode with reason"""
        self.current_mode = mode
        self.override_reason = reason
        self.auto_detect = False

    def enable_auto_detect(self):
        """Re-enable automatic phase detection"""
        self.auto_detect = True
        self.override_reason = None

    def get_mode_info(self) -> Dict:
        """Get current mode information"""
        config = self.get_current_config()
        return {
            'mode': self.current_mode.value,
            'mode_name': self.current_mode.name,
            'description': config.description,
            'phase': self.current_phase.value,
            'auto_detect': self.auto_detect,
            'override_reason': self.override_reason,
            'rsi_lower': config.rsi_lower,
            'rsi_upper': config.rsi_upper,
            'ema_required': config.ema_strength_required,
            'mtf_needed': config.mtf_confirmations_needed,
            'gate_keeper': config.gate_keeper_required,
        }
