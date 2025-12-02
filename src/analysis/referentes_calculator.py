#!/usr/bin/env python3
"""
Referentes Calculator - Crecetrader Methodology Implementation

Implements the Crecetrader concept of "Referentes" (Support & Resistance levels)
using BOTH historical and calculated (Fibonacci) methods.

Key Crecetrader Principles:
- Referentes = Any point of price reference that acts as obstacle
- Historical: Previous highs/lows, pivots, consolidation levels
- Calculated: Fibonacci ratios (38.2%, 50%, 61.8% for corrections, 125%-261.8% for extensions)
- ALWAYS combine both historical AND calculated for complete price mapping
- Problema: Assets at all-time highs need calculated levels, not historical

Fibonacci Levels:
- Correcciones (retrocesos): 38.2%, 50%, 61.8% of previous impulse
- Extensiones (objetivos Phase III): 125%, 150%, 161.8%, 261.8% of Phase I impulse
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from enum import Enum


class ReferenteType(Enum):
    """Types of referentes"""
    HISTORICAL_HIGH = "historical_high"     # Previous high
    HISTORICAL_LOW = "historical_low"       # Previous low
    PIVOT_HIGH = "pivot_high"               # Pivot turning point (high)
    PIVOT_LOW = "pivot_low"                 # Pivot turning point (low)
    FIBONACCI_CORRECTION = "fibonacci_correction"  # Retroceso
    FIBONACCI_EXTENSION = "fibonacci_extension"    # Objetivo
    PAA_CENTER = "paa_center"               # Precio apertura anual
    PAA_UPPER = "paa_upper"                 # PAA + 10%
    PAA_LOWER = "paa_lower"                 # PAA - 10%


class ReferentesCalculator:
    """
    Calculates Crecetrader referentes using historical and Fibonacci methods

    Maps Crecetrader concepts:
    - Z (Zonas) = Main referente obstacles
    - V (Vacío) = Space between entry and first referente
    """

    def __init__(self, paa: Optional[float] = None):
        """
        Initialize calculator

        Args:
            paa: Precio de Apertura Anual (Annual Opening Price) for medium-term refuge calculation
        """
        self.paa = paa
        self.fibonacci_ratios = {
            'correction_shallow': 0.382,    # 38.2% - Corrección profunda
            'correction_medium': 0.500,      # 50% - Corrección media (más común)
            'correction_deep': 0.618,        # 61.8% - Corrección normal (menos común)
            'extension_conservative': 1.25,  # 125% - Objetivo conservador
            'extension_medium': 1.50,        # 150% - Objetivo medio
            'extension_standard': 1.618,     # 161.8% - Objetivo con fuerza (Phase III target)
            'extension_extreme': 2.618,      # 261.8% - Extensión extrema (Phase V)
        }

    def calculate_historical_referentes(self,
                                       highs: np.ndarray,
                                       lows: np.ndarray) -> Dict[str, List[Dict]]:
        """
        Calculate historical referentes from price data

        Identifies:
        - Most recent high (closest resistance)
        - Most recent low (closest support)
        - Farthest high (major resistance)
        - Farthest low (major support)
        - Pivot turning points (where price reversed)

        Args:
            highs: Array of high prices
            lows: Array of low prices

        Returns:
            {
                'resistances': [{'price': float, 'type': str, 'distance': int}, ...],
                'supports': [{'price': float, 'type': str, 'distance': int}, ...],
            }
        """
        if len(highs) < 3 or len(lows) < 3:
            return {'resistances': [], 'supports': []}

        resistances = []
        supports = []

        # Most recent high (closest resistance)
        closest_high = highs[-1]
        closest_high_idx = len(highs) - 1
        for i in range(len(highs) - 2, -1, -1):
            if highs[i] > closest_high:
                closest_high = highs[i]
                closest_high_idx = i

        if closest_high > highs[-1]:  # Only if it's actually higher than current
            resistances.append({
                'price': closest_high,
                'type': ReferenteType.HISTORICAL_HIGH.value,
                'distance': len(highs) - 1 - closest_high_idx,
                'strength': 'primary'
            })

        # Most recent low (closest support)
        closest_low = lows[-1]
        closest_low_idx = len(lows) - 1
        for i in range(len(lows) - 2, -1, -1):
            if lows[i] < closest_low:
                closest_low = lows[i]
                closest_low_idx = i

        if closest_low < lows[-1]:  # Only if it's actually lower than current
            supports.append({
                'price': closest_low,
                'type': ReferenteType.HISTORICAL_LOW.value,
                'distance': len(lows) - 1 - closest_low_idx,
                'strength': 'primary'
            })

        # Farthest high (yearly high, major resistance)
        farthest_high = np.max(highs)
        if farthest_high > closest_high and farthest_high != highs[-1]:
            resistances.append({
                'price': farthest_high,
                'type': ReferenteType.HISTORICAL_HIGH.value,
                'distance': len(highs),
                'strength': 'secondary'
            })

        # Farthest low (yearly low, major support)
        farthest_low = np.min(lows)
        if farthest_low < closest_low and farthest_low != lows[-1]:
            supports.append({
                'price': farthest_low,
                'type': ReferenteType.HISTORICAL_LOW.value,
                'distance': len(lows),
                'strength': 'secondary'
            })

        return {
            'resistances': resistances,
            'supports': supports
        }

    def calculate_fibonacci_levels(self,
                                  impulse_high: float,
                                  impulse_low: float,
                                  is_correction: bool = True) -> Dict[str, float]:
        """
        Calculate Fibonacci referentes

        Crecetrader Rule: Different ratios for different pauta phases
        - Correcciones: 38.2%, 50%, 61.8% (retroceso)
        - Extensiones: 125%, 150%, 161.8%, 261.8% (objetivos)

        Args:
            impulse_high: High of the impulse move
            impulse_low: Low of the impulse move
            is_correction: True = correction ratios, False = extension ratios

        Returns:
            {
                'level_name': price,
                ...
            }
        """
        impulse_range = impulse_high - impulse_low

        if is_correction:
            # Correction levels (retrocesos) - for Phase II/IV
            return {
                'fib_38.2%': impulse_high - (impulse_range * self.fibonacci_ratios['correction_shallow']),
                'fib_50%': impulse_high - (impulse_range * self.fibonacci_ratios['correction_medium']),
                'fib_61.8%': impulse_high - (impulse_range * self.fibonacci_ratios['correction_deep']),
            }
        else:
            # Extension levels (extensiones) - for Phase III targets
            return {
                'ext_125%': impulse_low + (impulse_range * self.fibonacci_ratios['extension_conservative']),
                'ext_150%': impulse_low + (impulse_range * self.fibonacci_ratios['extension_medium']),
                'ext_161.8%': impulse_low + (impulse_range * self.fibonacci_ratios['extension_standard']),
                'ext_261.8%': impulse_low + (impulse_range * self.fibonacci_ratios['extension_extreme']),
            }

    def calculate_paa_levels(self) -> Dict[str, float]:
        """
        Calculate PAA (Precio de Apertura Anual) refuge levels

        Crecetrader Medium-Term Refuge:
        - PAA = Annual opening price
        - PAA ± 10% = Zone of medium-term support/resistance
        - Valid throughout the year
        - Critical obstacle level

        Returns:
            {
                'paa': price,
                'paa_upper': price,  # PAA + 10%
                'paa_lower': price,  # PAA - 10%
            }
        """
        if not self.paa:
            return {'paa': 0, 'paa_upper': 0, 'paa_lower': 0}

        paa_range = self.paa * 0.10  # 10% buffer

        return {
            'paa_center': self.paa,
            'paa_upper': self.paa + paa_range,
            'paa_lower': self.paa - paa_range,
        }

    def get_complete_referentes_map(self,
                                   highs: np.ndarray,
                                   lows: np.ndarray,
                                   closes: np.ndarray,
                                   phase_1_low: Optional[float] = None,
                                   phase_1_high: Optional[float] = None) -> Dict:
        """
        Get COMPLETE referentes map combining historical + Fibonacci + PAA

        Crecetrader Rule: NEVER use only one method
        - ALWAYS combine historical (where price has been) with
        - Calculated Fibonacci (where price mathematically should go)
        - Result: Complete price map for planning entries/exits

        Args:
            highs, lows, closes: OHLC arrays
            phase_1_low: Low of Phase I impulse (for calculating Phase III targets)
            phase_1_high: High of Phase I impulse (for calculating correction levels)

        Returns:
            Complete referentes analysis
        """
        # 1. Historical referentes (where price HAS been)
        historical = self.calculate_historical_referentes(highs, lows)

        # 2. Fibonacci correction levels (where price MAY pullback to)
        fib_corrections = {}
        if phase_1_high is not None and phase_1_low is not None:
            fib_corrections = self.calculate_fibonacci_levels(
                phase_1_high,
                phase_1_low,
                is_correction=True
            )

        # 3. Fibonacci extension levels (where Phase III targets)
        fib_extensions = {}
        if phase_1_high is not None and phase_1_low is not None:
            fib_extensions = self.calculate_fibonacci_levels(
                phase_1_high,
                phase_1_low,
                is_correction=False
            )

        # 4. PAA levels (medium-term refuge)
        paa_levels = self.calculate_paa_levels()

        # 5. Build complete map with all referentes sorted
        all_resistances = historical['resistances'].copy()
        all_supports = historical['supports'].copy()

        # Add Fibonacci levels to appropriate list
        for level_name, price in fib_extensions.items():
            all_resistances.append({
                'price': price,
                'type': ReferenteType.FIBONACCI_EXTENSION.value,
                'level': level_name,
                'strength': 'calculated'
            })

        for level_name, price in fib_corrections.items():
            all_supports.append({
                'price': price,
                'type': ReferenteType.FIBONACCI_CORRECTION.value,
                'level': level_name,
                'strength': 'calculated'
            })

        # Add PAA levels
        if self.paa:
            all_supports.append({
                'price': paa_levels['paa_lower'],
                'type': ReferenteType.PAA_LOWER.value,
                'strength': 'medium_term'
            })
            all_resistances.append({
                'price': paa_levels['paa_upper'],
                'type': ReferenteType.PAA_UPPER.value,
                'strength': 'medium_term'
            })

        # Sort by price
        all_resistances.sort(key=lambda x: x['price'], reverse=True)
        all_supports.sort(key=lambda x: x['price'], reverse=False)

        return {
            'current_price': closes[-1] if len(closes) > 0 else 0,
            'resistances': all_resistances,
            'supports': all_supports,
            'fib_corrections': fib_corrections,
            'fib_extensions': fib_extensions,
            'paa': paa_levels,
            'complete_referentes': {
                'resistances_count': len(all_resistances),
                'supports_count': len(all_supports),
                'methods_used': ['historical', 'fibonacci', 'paa']
            }
        }

    def get_first_obstacle_above(self, price: float, all_referentes: List[Dict]) -> Optional[Dict]:
        """
        Get the FIRST obstacle ABOVE current price (resistance)

        This is critical for Crecetrader's "V (Vacío)" calculation:
        - V = Space between entry and first referente above
        - V determines if risk/reward is favorable

        Args:
            price: Current price
            all_referentes: All resistances sorted

        Returns:
            First referente above price, or None
        """
        for ref in all_referentes:
            if ref['price'] > price:
                return ref
        return None

    def get_first_obstacle_below(self, price: float, all_referentes: List[Dict]) -> Optional[Dict]:
        """
        Get the FIRST obstacle BELOW current price (support)

        Used for placing Stop Loss in correct location

        Args:
            price: Current price
            all_referentes: All supports sorted

        Returns:
            First referente below price, or None
        """
        for ref in reversed(all_referentes):  # Reverse to get from top down
            if ref['price'] < price:
                return ref
        return None

    def calculate_vacio(self, entry_price: float,
                       first_obstacle_above: float,
                       first_obstacle_below: float) -> Dict:
        """
        Calculate VACÍO (available gap)

        Critical Crecetrader Concept:
        - Vacío = Space between entry and first referente
        - Wide vacío = Confidence price moves before obstacle
        - Narrow vacío = High risk for low reward (REJECT ENTRY)
        - Rule: Must have 2:1 minimum (2× reward vs risk)

        Args:
            entry_price: Entry price
            first_obstacle_above: First resistance above entry
            first_obstacle_below: First support below entry (SL)

        Returns:
            {
                'vacio_above': float (pips to resistance),
                'vacio_below': float (pips to SL),
                'ratio': float (reward / risk),
                'is_valid': bool (True if ratio > 2.0),
                'description': str
            }
        """
        vacio_above = first_obstacle_above - entry_price
        vacio_below = entry_price - first_obstacle_below

        if vacio_below > 0:
            ratio = vacio_above / vacio_below
        else:
            ratio = 0.0

        is_valid = ratio >= 2.0  # Minimum 2:1

        description = f"Risk: {vacio_below:.2f} | Reward: {vacio_above:.2f} | Ratio: {ratio:.2f}:1"
        if not is_valid:
            description += " ❌ REJECT - Vacío insuficiente"
        else:
            description += " ✅ VALID - Vacío amplio"

        return {
            'vacio_above': vacio_above,
            'vacio_below': vacio_below,
            'ratio': ratio,
            'is_valid': is_valid,
            'description': description
        }
