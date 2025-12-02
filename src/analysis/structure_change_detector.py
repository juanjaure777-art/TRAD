#!/usr/bin/env python3
"""
Structure Change Detector - Esteban Pérez Crecetrader Core Insight
Implements the PRIMARY TREND REVERSAL SIGNAL used by Esteban Pérez

KEY INSIGHT from Crecetrader:
"Las cosas no transurren de repente. El precio NO va a romper y subir..."
Translation: Market changes happen through STRUCTURE change, not just price movement.

STRUCTURE DEFINITION (Máximos y Mínimos):
- MÁXIMOS (Highs sequence): Are they CRECIENTES (increasing) or DECRECIENTES (decreasing)?
- MÍNIMOS (Lows sequence): Are they CRECIENTES (increasing) or DECRECIENTES (decreasing)?

TREND SIGNALS:
1. ALCISTA (Bullish) = Máximos CRECIENTES + Mínimos CRECIENTES
2. BAJISTA (Bearish) = Máximos DECRECIENTES + Mínimos DECRECIENTES
3. CORRECTIVE = Mixed or transitional structure
4. REVERSIÓN = Structure just changed (bearish→bullish or vice versa)

CRECETRADER RULE:
A REVERSIÓN is only CONFIRMED when:
1. Structure change is detected (REVERSIÓN DAY 1)
2. New structure persists (REVERSIÓN DAY 2 = CONFIRMATION)
3. Can then enter on scenario breakdown

This detector is more reliable than traditional trend indicators because
it uses RAW PRICE STRUCTURE, not calculations or oscillators.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from enum import Enum


class StructurePhase(Enum):
    """Market structure phase"""
    BULLISH_STRONG = "bullish_strong"        # HH + HL confirmed multiple times
    BULLISH_WEAK = "bullish_weak"            # HH + HL but inconsistent
    BEARISH_STRONG = "bearish_strong"        # LL + LH confirmed multiple times
    BEARISH_WEAK = "bearish_weak"            # LL + LH but inconsistent
    TRANSITIONAL = "transitional"            # Switching structures
    NEUTRAL = "neutral"                      # No clear structure


class StructureChangeDetector:
    """
    Detects trend changes through price structure analysis

    CRECETRADER METHODOLOGY:
    - Don't follow oscillators or complex calculations
    - Watch where price makes new highs/lows
    - When the pattern changes = MARKET IS SHIFTING
    """

    def __init__(self, lookback: int = 20):
        """
        Initialize detector

        Args:
            lookback: Number of candles to analyze for structure
        """
        self.lookback = lookback
        self.last_structure = None
        self.structure_change_detected = False

    def analyze_maximos_minimos(self,
                               highs: np.ndarray,
                               lows: np.ndarray) -> Dict:
        """
        Analyze MÁXIMOS (highs) and MÍNIMOS (lows) sequences

        This is the CORE of Crecetrader trend detection.
        We don't use calculations, just RAW STRUCTURE.

        Args:
            highs: Array of candle highs
            lows: Array of candle lows

        Returns:
            {
                'maximos_trend': 'crecientes' | 'decrecientes' | 'flat',
                'minimos_trend': 'crecientes' | 'decrecientes' | 'flat',
                'maximos_confirmed': int (how many confirmed?),
                'minimos_confirmed': int (how many confirmed?),
                'maximos_sequence': [list of highs],
                'minimos_sequence': [list of lows],
                'analysis': str
            }
        """
        if len(highs) < 3 or len(lows) < 3:
            return {
                'maximos_trend': 'unknown',
                'minimos_trend': 'unknown',
                'maximos_confirmed': 0,
                'minimos_confirmed': 0,
                'maximos_sequence': [],
                'minimos_sequence': [],
                'analysis': 'Insufficient data'
            }

        recent_highs = highs[-self.lookback:] if len(highs) >= self.lookback else highs
        recent_lows = lows[-self.lookback:] if len(lows) >= self.lookback else lows

        # Track MÁXIMOS (local highs) - SIMPLIFIED: just track obvious peaks
        maximos = []
        for i in range(len(recent_highs)):
            # A máximo is when high is greater than neighbors (or current is significant)
            if i == 0:
                maximos.append((i, recent_highs[i]))
            elif i == len(recent_highs) - 1:
                maximos.append((i, recent_highs[i]))
            elif recent_highs[i] >= recent_highs[i-1]:  # Current >= previous
                # Only if it's also >= next, or next hasn't reversed yet
                if i < len(recent_highs) - 1:
                    if recent_highs[i] >= recent_highs[i+1]:
                        maximos.append((i, recent_highs[i]))
                else:
                    maximos.append((i, recent_highs[i]))

        # Track MÍNIMOS (local lows) - SIMPLIFIED: just track obvious valleys
        minimos = []
        for i in range(len(recent_lows)):
            # A mínimo is when low is less than neighbors (or current is significant)
            if i == 0:
                minimos.append((i, recent_lows[i]))
            elif i == len(recent_lows) - 1:
                minimos.append((i, recent_lows[i]))
            elif recent_lows[i] <= recent_lows[i-1]:  # Current <= previous
                # Only if it's also <= next, or next hasn't reversed yet
                if i < len(recent_lows) - 1:
                    if recent_lows[i] <= recent_lows[i+1]:
                        minimos.append((i, recent_lows[i]))
                else:
                    minimos.append((i, recent_lows[i]))

        # Determine MÁXIMOS trend
        if len(maximos) >= 2:
            maximos_prices = [m[1] for m in maximos]
            maximos_increasing = all(
                maximos_prices[i] < maximos_prices[i+1]
                for i in range(len(maximos_prices)-1)
            )
            maximos_decreasing = all(
                maximos_prices[i] > maximos_prices[i+1]
                for i in range(len(maximos_prices)-1)
            )

            if maximos_increasing:
                maximos_trend = 'crecientes'
                maximos_confirmed = len(maximos)
            elif maximos_decreasing:
                maximos_trend = 'decrecientes'
                maximos_confirmed = len(maximos)
            else:
                maximos_trend = 'flat'
                maximos_confirmed = 0
        else:
            maximos_trend = 'unknown'
            maximos_confirmed = len(maximos)

        # Determine MÍNIMOS trend
        if len(minimos) >= 2:
            minimos_prices = [m[1] for m in minimos]
            minimos_increasing = all(
                minimos_prices[i] < minimos_prices[i+1]
                for i in range(len(minimos_prices)-1)
            )
            minimos_decreasing = all(
                minimos_prices[i] > minimos_prices[i+1]
                for i in range(len(minimos_prices)-1)
            )

            if minimos_increasing:
                minimos_trend = 'crecientes'
                minimos_confirmed = len(minimos)
            elif minimos_decreasing:
                minimos_trend = 'decrecientes'
                minimos_confirmed = len(minimos)
            else:
                minimos_trend = 'flat'
                minimos_confirmed = 0
        else:
            minimos_trend = 'unknown'
            minimos_confirmed = len(minimos)

        # Build analysis description
        analysis = f"Máximos {maximos_trend} ({maximos_confirmed} confirmed) | "
        analysis += f"Mínimos {minimos_trend} ({minimos_confirmed} confirmed)"

        return {
            'maximos_trend': maximos_trend,
            'minimos_trend': minimos_trend,
            'maximos_confirmed': maximos_confirmed,
            'minimos_confirmed': minimos_confirmed,
            'maximos_sequence': maximos_prices if len(maximos) >= 2 else [],
            'minimos_sequence': minimos_prices if len(minimos) >= 2 else [],
            'analysis': analysis
        }

    def detect_structure_phase(self, highs: np.ndarray, lows: np.ndarray) -> Dict:
        """
        Determine current STRUCTURE PHASE based on máximos/mínimos

        Returns:
            {
                'phase': StructurePhase enum,
                'description': str,
                'confidence': float (0-1),
                'maximos_minimos': {structure analysis}
            }
        """
        structure = self.analyze_maximos_minimos(highs, lows)
        maximos_trend = structure['maximos_trend']
        minimos_trend = structure['minimos_trend']

        # Determine phase based on structure
        if maximos_trend == 'crecientes' and minimos_trend == 'crecientes':
            phase = StructurePhase.BULLISH_STRONG
            description = "🟢 ALCISTA FUERTE - Máximos y Mínimos CRECIENTES"
            confidence = min(1.0, (structure['maximos_confirmed'] + structure['minimos_confirmed']) / 8)

        elif maximos_trend == 'decrecientes' and minimos_trend == 'decrecientes':
            phase = StructurePhase.BEARISH_STRONG
            description = "🔴 BAJISTA FUERTE - Máximos y Mínimos DECRECIENTES"
            confidence = min(1.0, (structure['maximos_confirmed'] + structure['minimos_confirmed']) / 8)

        elif maximos_trend == 'crecientes' and minimos_trend in ['crecientes', 'flat']:
            phase = StructurePhase.BULLISH_WEAK
            description = "🟡 ALCISTA DÉBIL - Máximos crecientes, mínimos inconstantes"
            confidence = 0.6

        elif maximos_trend == 'decrecientes' and minimos_trend in ['decrecientes', 'flat']:
            phase = StructurePhase.BEARISH_WEAK
            description = "🟠 BAJISTA DÉBIL - Máximos decrecientes, mínimos inconstantes"
            confidence = 0.6

        else:
            # Transitional or unclear
            if (maximos_trend == 'crecientes' and minimos_trend == 'decrecientes') or \
               (maximos_trend == 'decrecientes' and minimos_trend == 'crecientes'):
                phase = StructurePhase.TRANSITIONAL
                description = "⚡ TRANSITIONAL - Estructura cambiando"
                confidence = 0.4
            else:
                phase = StructurePhase.NEUTRAL
                description = "⚪ NEUTRAL - Sin estructura clara"
                confidence = 0.3

        return {
            'phase': phase,
            'description': description,
            'confidence': confidence,
            'maximos_minimos': structure
        }

    def detect_structure_reversal(self,
                                 highs: np.ndarray,
                                 lows: np.ndarray,
                                 previous_phase: Optional[str] = None) -> Dict:
        """
        Detect if REVERSIÓN (structure reversal) has occurred

        CRECETRADER RULE:
        Day 1: Structure changes (bearish→bullish detected)
        Day 2: Structure persists (confirmation = VALID REVERSIÓN)

        Args:
            highs: Array of candle highs
            lows: Array of candle lows
            previous_phase: Previous phase to compare against (from history)

        Returns:
            {
                'reversal_detected': bool,
                'reversal_type': 'bearish_to_bullish' | 'bullish_to_bearish' | 'none',
                'is_confirmed': bool (has persisted 2+ days?),
                'current_phase': str,
                'previous_phase': str,
                'days_since_reversal': int,
                'strength': str ('weak' | 'moderate' | 'strong'),
                'description': str
            }
        """
        current = self.detect_structure_phase(highs, lows)
        current_phase_str = current['phase'].value

        # If we don't have history, we can't detect change
        if self.last_structure is None:
            self.last_structure = current_phase_str
            return {
                'reversal_detected': False,
                'reversal_type': 'none',
                'is_confirmed': False,
                'current_phase': current_phase_str,
                'previous_phase': 'none',
                'days_since_reversal': 0,
                'strength': 'none',
                'description': 'Initializing structure tracking'
            }

        # Check for reversal
        previous = self.last_structure
        reversal_detected = False
        reversal_type = 'none'

        # Bullish reversal: bearish→bullish
        if 'bearish' in previous and 'bullish' in current_phase_str:
            reversal_detected = True
            reversal_type = 'bearish_to_bullish'

        # Bearish reversal: bullish→bearish
        elif 'bullish' in previous and 'bearish' in current_phase_str:
            reversal_detected = True
            reversal_type = 'bullish_to_bearish'

        # Update history
        if reversal_detected:
            self.structure_change_detected = True
        else:
            self.structure_change_detected = False

        self.last_structure = current_phase_str

        # Determine if confirmed (need to track days)
        is_confirmed = current['confidence'] >= 0.7

        strength = 'strong' if current['confidence'] >= 0.8 else \
                  'moderate' if current['confidence'] >= 0.6 else 'weak'

        description = current['description']
        if reversal_detected:
            description += f" | ⚡ REVERSIÓN DETECTADA ({reversal_type})"

        return {
            'reversal_detected': reversal_detected,
            'reversal_type': reversal_type,
            'is_confirmed': is_confirmed,
            'current_phase': current_phase_str,
            'previous_phase': previous,
            'days_since_reversal': 1 if reversal_detected else 0,
            'strength': strength,
            'description': description
        }

    def get_trend_direction_by_structure(self, highs: np.ndarray, lows: np.ndarray) -> Dict:
        """
        Get current trend direction based on STRUCTURE (not calculations)

        Returns:
            {
                'direction': 'UP' | 'DOWN' | 'NEUTRAL',
                'structure': StructurePhase,
                'is_bullish': bool,
                'is_bearish': bool,
                'confidence': float (0-1)
            }
        """
        phase_info = self.detect_structure_phase(highs, lows)
        phase = phase_info['phase']

        if 'bullish' in phase.value:
            return {
                'direction': 'UP',
                'structure': phase,
                'is_bullish': True,
                'is_bearish': False,
                'confidence': phase_info['confidence']
            }
        elif 'bearish' in phase.value:
            return {
                'direction': 'DOWN',
                'structure': phase,
                'is_bullish': False,
                'is_bearish': True,
                'confidence': phase_info['confidence']
            }
        else:
            return {
                'direction': 'NEUTRAL',
                'structure': phase,
                'is_bullish': False,
                'is_bearish': False,
                'confidence': phase_info['confidence']
            }
