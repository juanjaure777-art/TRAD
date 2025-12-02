#!/usr/bin/env python3
"""
T+Z+V Validator - Crecetrader Core Trading Formula

Implements the MASTER EQUATION of Crecetrader:
T + Z + V = PLAN DE TRADING

Where:
- T (Tendencia): Clear trend identification (Tf + Tpa)
- Z (Zonas): Support/Resistance levels identified
- V (Vacío): Sufficient gap for favorable risk/reward

This is the GATEKEEPER for all trading decisions.
NO TRADE POSSIBLE without all 3 components validated.

Trading Rules:
1. Validate T first (does trend exist?)
2. Then validate Z (are levels clear?)
3. Then validate V (is space sufficient?)
4. If all 3 YES → Look for Entry Event
5. If any NO → WAIT or SKIP this opportunity
"""

from enum import Enum
from typing import Dict, Optional
import numpy as np
from src.analysis.structure_change_detector import StructureChangeDetector


class TendencyStrength(Enum):
    """Trend strength evaluation"""
    CLEAR_UP = "clear_uptrend"          # Clear uptrend, multiple HH/HL
    MODERATE_UP = "moderate_uptrend"    # Some HH/HL, not all
    WEAK_UP = "weak_uptrend"            # Barely up
    UNCLEAR = "unclear"                 # No clear direction (FLAT)
    WEAK_DOWN = "weak_downtrend"        # Barely down
    MODERATE_DOWN = "moderate_downtrend"  # Some LL/LH, not all
    CLEAR_DOWN = "clear_downtrend"      # Clear downtrend, multiple LL/LH


class ZoneClarity(Enum):
    """Zone identification clarity"""
    VERY_CLEAR = "very_clear"      # Multiple confirmed levels (>3)
    CLEAR = "clear"                # Confirmed levels (2-3)
    UNCLEAR = "unclear"            # Only 1 level or unclear
    VERY_UNCLEAR = "very_unclear"  # No clear levels


class VacioValidity(Enum):
    """Vacío (gap) validity for risk/reward"""
    EXCELLENT = "excellent"  # > 3:1 ratio
    GOOD = "good"            # 2.5:1 - 3:1
    ACCEPTABLE = "acceptable"  # 2:1 - 2.5:1
    MARGINAL = "marginal"      # 1.5:1 - 2:1
    POOR = "poor"            # < 1.5:1 (REJECT)


class TZVValidator:
    """
    Validates the T+Z+V formula before allowing trades

    Crecetrader Philosophy:
    "Context matters more than patterns"
    - Same price action has different meaning in different locations
    - T+Z+V ensures we trade ONLY with high probability setups
    """

    def __init__(self):
        """Initialize validator"""
        self.last_validation = None
        self.validation_history = []
        self.structure_detector = StructureChangeDetector(lookback=20)
        self.max_history_size = 1000  # CRITICAL FIX v3.5.1: Prevent memory leak from unbounded history

    def validate_t_tendencia(self,
                            highs: np.ndarray,
                            lows: np.ndarray,
                            closes: np.ndarray,
                            lookback: int = 20) -> Dict:
        """
        Validate T (Tendencia) - Trend identification

        PRIMARY METHOD (Esteban Pérez Crecetrader):
        - Analyze MÁXIMOS (highs) sequence: crecientes or decrecientes?
        - Analyze MÍNIMOS (lows) sequence: crecientes or decrecientes?
        - Clear trend = máximos + mínimos BOTH crecientes (bullish) OR BOTH decrecientes (bearish)

        SECONDARY METHOD (Traditional HH/HL counting):
        - Confirms primary structure analysis
        - Count higher highs vs lower highs
        - Count higher lows vs lower lows

        REVERSIÓN DETECTION:
        - When structure changes (bearish→bullish or vice versa)
        - Esteban emphasizes: "El precio NO va a romper y subir de golpe"
        - Structure change takes time, must be confirmed by persistence

        Args:
            highs, lows, closes: OHLC arrays
            lookback: How many candles to analyze

        Returns:
            {
                'strength': TendencyStrength enum,
                'is_uptrend': bool,
                'is_downtrend': bool,
                'hh_count': int (higher highs),
                'lh_count': int (lower highs),
                'hl_count': int (higher lows),
                'll_count': int (lower lows),
                'hh_pct': float,
                'hl_pct': float,
                'validation_passed': bool (trend is CLEAR),
                'structure_phase': str (PRIMARY signal),
                'reversal_detected': bool,
                'description': str
            }
        """
        if len(highs) < lookback:
            lookback = len(highs)

        recent_highs = highs[-lookback:]
        recent_lows = lows[-lookback:]
        recent_closes = closes[-lookback:]

        # ========================================
        # PRIMARY METHOD: Structure Change Detection
        # ========================================
        structure_info = self.structure_detector.detect_structure_phase(recent_highs, recent_lows)
        structure_phase = structure_info['phase'].value
        structure_confidence = structure_info['confidence']

        # Check for reversal
        reversal_info = self.structure_detector.detect_structure_reversal(recent_highs, recent_lows)
        reversal_detected = reversal_info['reversal_detected']

        # ========================================
        # SECONDARY METHOD: Traditional HH/HL counting
        # ========================================
        # Count HH (higher highs) and LH (lower highs)
        hh_count = 0
        lh_count = 0
        for i in range(1, len(recent_highs)):
            if recent_highs[i] > recent_highs[i-1]:
                hh_count += 1
            else:
                lh_count += 1

        # Count HL (higher lows) and LL (lower lows)
        hl_count = 0
        ll_count = 0
        for i in range(1, len(recent_lows)):
            if recent_lows[i] > recent_lows[i-1]:
                hl_count += 1
            else:
                ll_count += 1

        # Calculate percentages
        total_highs = hh_count + lh_count
        total_lows = hl_count + ll_count

        hh_pct = (hh_count / total_highs * 100) if total_highs > 0 else 0
        hl_pct = (hl_count / total_lows * 100) if total_lows > 0 else 0

        # ========================================
        # DETERMINE TREND STRENGTH (PRIMARY is structure)
        # ========================================

        # PRIMARY: Use structure to determine uptrend/downtrend
        is_uptrend = 'bullish' in structure_phase
        is_downtrend = 'bearish' in structure_phase

        # SECONDARY: Validate with HH/HL percentages
        hh_confirms_up = hh_pct > 60 and hl_pct > 60
        hh_confirms_down = lh_count > hh_count * 2 and ll_count > hl_count * 2

        # Classify trend based on structure PRIMARY, with HH/HL as confirmation
        if is_uptrend:
            if structure_confidence >= 0.8 and hh_confirms_up:
                strength = TendencyStrength.CLEAR_UP
            elif structure_confidence >= 0.6:
                strength = TendencyStrength.MODERATE_UP
            elif structure_confidence >= 0.4:
                strength = TendencyStrength.WEAK_UP
            else:
                strength = TendencyStrength.UNCLEAR
        elif is_downtrend:
            if structure_confidence >= 0.8 and hh_confirms_down:
                strength = TendencyStrength.CLEAR_DOWN
            elif structure_confidence >= 0.6:
                strength = TendencyStrength.MODERATE_DOWN
            elif structure_confidence >= 0.4:
                strength = TendencyStrength.WEAK_DOWN
            else:
                strength = TendencyStrength.UNCLEAR
        else:
            strength = TendencyStrength.UNCLEAR

        # Validation: CLEAR, MODERATE, or WEAK are acceptable if confidence >= 0.4
        validation_passed = strength in [
            TendencyStrength.CLEAR_UP,
            TendencyStrength.MODERATE_UP,
            TendencyStrength.WEAK_UP,
            TendencyStrength.CLEAR_DOWN,
            TendencyStrength.MODERATE_DOWN,
            TendencyStrength.WEAK_DOWN
        ] and structure_confidence >= 0.4

        # Build comprehensive description
        description = (
            f"[ESTRUCTURA] {structure_info['description']} | "
            f"[HH/HL] {hh_pct:.0f}% HH, {hl_pct:.0f}% HL | "
            f"[FUERZA] {strength.value}"
        )

        if reversal_detected:
            description += f" | ⚡ REVERSIÓN: {reversal_info['reversal_type']}"

        return {
            'strength': strength,
            'is_uptrend': is_uptrend,
            'is_downtrend': is_downtrend,
            'hh_count': hh_count,
            'lh_count': lh_count,
            'hl_count': hl_count,
            'll_count': ll_count,
            'hh_pct': hh_pct,
            'hl_pct': hl_pct,
            'validation_passed': validation_passed,
            'structure_phase': structure_phase,
            'structure_confidence': structure_confidence,
            'reversal_detected': reversal_detected,
            'reversal_info': reversal_info,
            'description': description
        }

    def validate_z_zonas(self,
                        supports: Dict,
                        resistances: Dict,
                        current_price: float) -> Dict:
        """
        Validate Z (Zonas) - Support/Resistance clarity

        Rules (from Crecetrader):
        - Multiple referentes (historical + calculated) define zones
        - Clear zones = At least 2 confirmed levels below and above price
        - Without clear zones, can't plan entry/exit properly

        Args:
            supports: Support levels {'resistances': [...], 'supports': [...]}
            resistances: Resistance levels (same structure)
            current_price: Current market price

        Returns:
            {
                'clarity': ZoneClarity enum,
                'supports_count': int,
                'resistances_count': int,
                'first_support': float,
                'first_resistance': float,
                'support_distance': float (pips from price),
                'resistance_distance': float (pips from price),
                'validation_passed': bool (zones are CLEAR),
                'description': str
            }
        """
        # Count levels above and below current price
        supports_list = supports.get('supports', [])
        resistances_list = resistances.get('resistances', [])

        # Find first support below and first resistance above
        first_support = None
        first_resistance = None

        for sup in supports_list:
            if sup['price'] < current_price:
                first_support = sup['price']
                break

        for res in resistances_list:
            if res['price'] > current_price:
                first_resistance = res['price']
                break

        # Calculate distances
        support_distance = current_price - first_support if first_support else None
        resistance_distance = first_resistance - current_price if first_resistance else None

        # Determine clarity
        if first_support and first_resistance:
            # Both levels exist
            if len(supports_list) >= 3 and len(resistances_list) >= 3:
                clarity = ZoneClarity.VERY_CLEAR
            elif len(supports_list) >= 2 and len(resistances_list) >= 2:
                clarity = ZoneClarity.CLEAR
            else:
                clarity = ZoneClarity.UNCLEAR
        elif first_support or first_resistance:
            clarity = ZoneClarity.UNCLEAR
        else:
            clarity = ZoneClarity.VERY_UNCLEAR

        # Validation: VERY_CLEAR or CLEAR are acceptable
        validation_passed = clarity in [ZoneClarity.VERY_CLEAR, ZoneClarity.CLEAR]

        description = (
            f"Support: {first_support:.2f} ({support_distance:.2f}p below) | "
            f"Resistance: {first_resistance:.2f} ({resistance_distance:.2f}p above) | "
            f"Clarity: {clarity.value}"
        )

        return {
            'clarity': clarity,
            'supports_count': len(supports_list),
            'resistances_count': len(resistances_list),
            'first_support': first_support,
            'first_resistance': first_resistance,
            'support_distance': support_distance,
            'resistance_distance': resistance_distance,
            'validation_passed': validation_passed,
            'description': description
        }

    def validate_v_vacio(self,
                        entry_price: float,
                        first_resistance: float,
                        first_support: float,
                        min_ratio: float = 2.0) -> Dict:
        """
        Validate V (Vacío) - Available gap for risk/reward

        Critical Rule: VACÍO determines if trade is viable
        - V = Space between entry and first obstacle
        - Rule: Min 2:1 ratio (reward ÷ risk ≥ 2)
        - If V too small → REJECT TRADE

        Args:
            entry_price: Entry price
            first_resistance: First obstacle above
            first_support: First obstacle below (where SL goes)
            min_ratio: Minimum ratio required (default 2.0)

        Returns:
            {
                'validity': VacioValidity enum,
                'vacio_up': float (pips to resistance),
                'vacio_down': float (pips to SL),
                'ratio': float (reward / risk),
                'validation_passed': bool (ratio >= min_ratio),
                'description': str
            }
        """
        # CRITICAL FIX: Validate entry price is within support-resistance range
        if not (first_support < entry_price < first_resistance):
            return {
                'validity': VacioValidity.POOR,
                'vacio_up': 0,
                'vacio_down': 0,
                'ratio': 0,
                'validation_passed': False,
                'description': 'Entry price outside support-resistance range'
            }

        vacio_up = first_resistance - entry_price
        vacio_down = entry_price - first_support

        if vacio_down > 0 and vacio_up > 0:
            ratio = vacio_up / vacio_down
        else:
            ratio = 0.0

        # Determine validity
        if ratio > 3.0:
            validity = VacioValidity.EXCELLENT
        elif ratio > 2.5:
            validity = VacioValidity.GOOD
        elif ratio > 2.0:
            validity = VacioValidity.ACCEPTABLE
        elif ratio > 1.5:
            validity = VacioValidity.MARGINAL
        else:
            validity = VacioValidity.POOR

        validation_passed = ratio >= min_ratio

        description = (
            f"Risk: {vacio_down:.2f}p | Reward: {vacio_up:.2f}p | "
            f"Ratio: {ratio:.2f}:1 | Validity: {validity.value}"
        )

        return {
            'validity': validity,
            'vacio_up': vacio_up,
            'vacio_down': vacio_down,
            'ratio': ratio,
            'validation_passed': validation_passed,
            'description': description
        }

    def validate_tzv_complete(self,
                             t_validation: Dict,
                             z_validation: Dict,
                             v_validation: Dict) -> Dict:
        """
        Validate COMPLETE T+Z+V formula

        Crecetrader Rule: ALL THREE must be VALID
        If any fails → NO TRADE

        Args:
            t_validation: Output from validate_t_tendencia()
            z_validation: Output from validate_z_zonas()
            v_validation: Output from validate_v_vacio()

        Returns:
            {
                't_passed': bool,
                'z_passed': bool,
                'v_passed': bool,
                'all_passed': bool (overall validation),
                'failed_components': [str, ...] (which failed),
                'confidence': float (0-1),
                'description': str,
                'can_trade': bool (True if all 3 pass)
            }
        """
        t_passed = t_validation.get('validation_passed', False)
        z_passed = z_validation.get('validation_passed', False)
        v_passed = v_validation.get('validation_passed', False)

        all_passed = t_passed and z_passed and v_passed

        failed_components = []
        if not t_passed:
            failed_components.append("Tendencia")
        if not z_passed:
            failed_components.append("Zonas")
        if not v_passed:
            failed_components.append("Vacío")

        # Calculate confidence score
        confidence = 0.0
        if t_passed:
            confidence += 0.35
        if z_passed:
            confidence += 0.35
        if v_passed:
            v_ratio = v_validation.get('ratio', 0)
            if v_ratio >= 3.0:
                confidence += 0.35
            elif v_ratio >= 2.0:
                confidence += 0.25
            else:
                confidence += 0.15

        description = (
            f"T:{t_validation['strength'].value if t_passed else '❌ FAIL'} | "
            f"Z:{z_validation['clarity'].value if z_passed else '❌ FAIL'} | "
            f"V:{v_validation['validity'].value if v_passed else '❌ FAIL'}"
        )

        # Store validation history
        self.last_validation = {
            't': t_validation,
            'z': z_validation,
            'v': v_validation,
            'complete': {
                't_passed': t_passed,
                'z_passed': z_passed,
                'v_passed': v_passed,
                'all_passed': all_passed,
                'confidence': confidence
            }
        }
        # CRITICAL FIX v3.5.1: Apply size limit to prevent memory leak
        self.validation_history.append(self.last_validation)
        if len(self.validation_history) > self.max_history_size:
            # Remove oldest entry (FIFO circular buffer pattern)
            self.validation_history.pop(0)

        return {
            't_passed': t_passed,
            'z_passed': z_passed,
            'v_passed': v_passed,
            'all_passed': all_passed,
            'failed_components': failed_components,
            'confidence': confidence,
            'description': description,
            'can_trade': all_passed  # Main decision
        }
