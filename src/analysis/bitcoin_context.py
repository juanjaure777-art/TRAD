#!/usr/bin/env python3
"""
Bitcoin Market Context - Integración de niveles específicos Bitcoin
y ponderación por sentimiento Fear-Greed

Basado en ANALISIS_BITCOIN_HOY.md del 27 Noviembre 2025
Implementa niveles clave y sentimiento del mercado
"""

import requests
from typing import Dict, Optional
from enum import Enum


class FearGreedLevel(Enum):
    """Fear & Greed Index levels"""
    EXTREME_FEAR = "extreme_fear"        # 0-24
    FEAR = "fear"                        # 25-44
    NEUTRAL = "neutral"                  # 45-55
    GREED = "greed"                      # 56-74
    EXTREME_GREED = "extreme_greed"      # 75-100


class BitcoinContext:
    """
    Manages Bitcoin-specific market context

    - Referentes levels for BTC/USD
    - Fear-Greed sentiment
    - Session optimization
    """

    # CRITICAL BITCOIN LEVELS (27 Nov 2025 Analysis)
    PIVOT_LEVEL = 90.823
    LEVEL_1_BUY = 90.823        # Accumulation zone 1
    LEVEL_2_BUY = 91.381        # Accumulation zone 2
    LEVEL_3_RESISTANCE = 91.719 # Resistance zone
    TARGET_1 = 92.286           # First take-profit
    TARGET_2 = 93.347           # Weekly objective

    SUPPORT_STRONG = 89.199     # First support below pivot
    SUPPORT_MAJOR = 88.666      # Secondary support
    SUPPORT_DEEP = 84.12        # Deep support

    # Session times (UTC)
    SESSIONS = {
        'ASIA_OPEN': (0, 8),           # 00:00-08:00 UTC
        'ASIA_CLOSE': (6, 14),         # 06:00-14:00 UTC (overlap)
        'EU_OPEN': (7, 16),            # 07:00-16:00 UTC
        'EU_CLOSE': (14, 17),          # 14:00-17:00 UTC (end of EU)
        'NY_OPEN': (13, 21),           # 13:00-21:00 UTC
        'NY_CLOSE': (20, 24),          # 20:00-24:00 UTC (evening)
    }

    def __init__(self):
        self.fear_greed_value = None
        self.fear_greed_level = None
        self.last_fg_update = None
        self.bitcoin_levels = self._get_bitcoin_levels()

    def _get_bitcoin_levels(self) -> Dict:
        """Get all Bitcoin referentes levels"""
        return {
            'accumulation_zones': {
                'level_1': self.LEVEL_1_BUY,
                'level_2': self.LEVEL_2_BUY,
                'level_3': self.LEVEL_3_RESISTANCE
            },
            'take_profit': {
                'tp_1': self.TARGET_1,
                'tp_2': self.TARGET_2
            },
            'support': {
                'strong': self.SUPPORT_STRONG,
                'major': self.SUPPORT_MAJOR,
                'deep': self.SUPPORT_DEEP
            },
            'pivot': self.PIVOT_LEVEL
        }

    def fetch_fear_greed_index(self) -> Dict:
        """
        Fetch Fear & Greed Index from crypto Fear & Greed Index API

        Returns:
            {
                'value': int (0-100),
                'level': FearGreedLevel,
                'description': str,
                'success': bool
            }
        """
        try:
            response = requests.get(
                'https://api.alternative.me/fng/?limit=1',
                timeout=5
            )
            data = response.json()

            if data.get('data') and len(data['data']) > 0:
                fg_value = int(data['data'][0]['value'])
                self.fear_greed_value = fg_value
                self.fear_greed_level = self._classify_fear_greed(fg_value)
                self.last_fg_update = data['data'][0]['timestamp']

                return {
                    'value': fg_value,
                    'level': self.fear_greed_level,
                    'description': self._get_fg_description(fg_value),
                    'success': True
                }
        except Exception as e:
            print(f"⚠️  Error fetching Fear-Greed: {e}")

        # Return cached value or default
        return {
            'value': self.fear_greed_value or 50,
            'level': self.fear_greed_level or FearGreedLevel.NEUTRAL,
            'description': 'Cached or default value',
            'success': False
        }

    def _classify_fear_greed(self, value: int) -> FearGreedLevel:
        """Classify Fear-Greed value into level"""
        if value < 25:
            return FearGreedLevel.EXTREME_FEAR
        elif value < 45:
            return FearGreedLevel.FEAR
        elif value < 55:
            return FearGreedLevel.NEUTRAL
        elif value < 75:
            return FearGreedLevel.GREED
        else:
            return FearGreedLevel.EXTREME_GREED

    def _get_fg_description(self, value: int) -> str:
        """Get description for Fear-Greed value"""
        if value < 11:
            return "🚨 Miedo extremo - Pánico en el mercado"
        elif value < 25:
            return "🔴 Miedo extremo"
        elif value < 45:
            return "🟠 Miedo - Depresión"
        elif value < 55:
            return "🟡 Neutral"
        elif value < 75:
            return "🟢 Codicia - Optimismo"
        else:
            return "🟢 Codicia extrema - Euforia"

    def get_position_size_multiplier(self, fear_greed_value: Optional[int] = None) -> float:
        """
        Get position size multiplier based on Fear-Greed sentiment

        Esteban principle: Market psychology affects position sizing

        Args:
            fear_greed_value: Optional override value (for testing)

        Returns:
            float: multiplier (0.5 to 1.5)
            - Extreme fear: 0.5x (too risky)
            - Neutral: 1.0x (normal)
            - Extreme greed: 0.7x (overheated)
        """
        value = fear_greed_value if fear_greed_value is not None else self.fear_greed_value

        if value is None:
            return 1.0

        if value < 11:
            return 0.5  # Extreme fear - too risky
        elif value < 25:
            return 0.6
        elif value < 45:
            return 0.8
        elif value < 55:
            return 1.0  # Neutral - normal
        elif value < 75:
            return 0.9
        else:
            return 0.7  # Extreme greed - overheated

    def get_confidence_boost(self) -> float:
        """
        Get confidence boost based on Fear-Greed

        Returns:
            float: confidence multiplier (0.7 to 1.3)
        """
        if self.fear_greed_value is None:
            return 1.0

        value = self.fear_greed_value

        if value < 25:
            return 0.9  # Slight reduction in extreme fear
        elif value < 45:
            return 0.95
        elif value < 55:
            return 1.0  # Neutral
        elif value < 75:
            return 1.1  # Slight boost in greed
        else:
            return 1.0  # Reduce in extreme greed (too risky)

    def is_good_entry_timing(self, session_hour: int) -> Dict:
        """
        Evaluate if this is good entry timing for Bitcoin

        Esteban: "NO es solo precio, es CUÁNDO ocurre"

        Args:
            session_hour: Current hour in UTC

        Returns:
            {
                'is_good': bool,
                'session': str,
                'liquidity': str ('HIGH' | 'MEDIUM' | 'LOW'),
                'session_quality': float (0-1),
                'reason': str
            }
        """

        # High liquidity sessions
        if 13 <= session_hour < 17:  # NY+EU overlap
            return {
                'is_good': True,
                'session': 'NY+EU OVERLAP',
                'liquidity': 'HIGH',
                'session_quality': 1.0,
                'reason': 'Máxima liquidez: NY y EU trading simultaneamente'
            }

        # Good sessions
        if (7 <= session_hour < 16) or (13 <= session_hour < 21):  # EU or NY
            return {
                'is_good': True,
                'session': 'EU or NY MAIN',
                'liquidity': 'HIGH',
                'session_quality': 0.85,
                'reason': 'Buena liquidez: EU o NY activos'
            }

        # Moderate sessions
        if (0 <= session_hour < 8) or (20 <= session_hour < 24):  # Asia or NY end
            return {
                'is_good': False,
                'session': 'ASIA or NY LATE',
                'liquidity': 'MEDIUM',
                'session_quality': 0.6,
                'reason': 'Liquidez moderada: afuera de horarios principales'
            }

        # Default
        return {
            'is_good': False,
            'session': 'UNKNOWN',
            'liquidity': 'LOW',
            'session_quality': 0.3,
            'reason': 'Horario no óptimo'
        }

    def evaluate_bitcoin_setup(self,
                               current_price: float,
                               scenario: str,
                               structure_confidence: float,
                               session_hour: int) -> Dict:
        """
        Complete Bitcoin-specific entry evaluation

        Combines:
        - Price location relative to Bitcoin levels
        - Market sentiment (Fear-Greed)
        - Trading session quality
        - Structure strength

        Args:
            current_price: Current BTC price
            scenario: 'A' | 'B' | 'C'
            structure_confidence: 0-1
            session_hour: Current hour (UTC)

        Returns:
            Complete setup evaluation
        """

        # Get Fear-Greed
        fg_data = self.fetch_fear_greed_index()

        # Get session quality
        session_data = self.is_good_entry_timing(session_hour)

        # Calculate composite score
        fg_multiplier = self.get_confidence_boost()
        session_quality = session_data['session_quality']
        composite_confidence = structure_confidence * fg_multiplier * session_quality

        # Position sizing
        base_multiplier = self.get_position_size_multiplier()

        # Determine if setup is valid for Bitcoin
        is_valid = (
            scenario == 'A' and
            composite_confidence > 0.6 and
            session_data['liquidity'] != 'LOW'
        )

        return {
            'current_price': current_price,
            'scenario': scenario,
            'structure_confidence': structure_confidence,
            'fear_greed': fg_data,
            'session': session_data,
            'composite_confidence': composite_confidence,
            'position_size_multiplier': base_multiplier,
            'is_valid_setup': is_valid,
            'levels': self.bitcoin_levels,
            'recommendation': self._build_recommendation(
                scenario, composite_confidence, is_valid, current_price
            )
        }

    def _build_recommendation(self,
                             scenario: str,
                             confidence: float,
                             is_valid: bool,
                             current_price: float) -> str:
        """Build human-readable recommendation"""

        if not is_valid:
            return f"❌ SETUP NO VÁLIDO - Esperar condiciones mejores"

        if scenario == 'A':
            if current_price > self.LEVEL_2_BUY:
                return f"🟢 STRONG BUY - Precio ({current_price:.2f}) en zona de acumulación 2"
            elif current_price > self.LEVEL_1_BUY:
                return f"🟢 BUY - Precio ({current_price:.2f}) en zona de acumulación 1"
            else:
                return f"🟡 WAIT - Precio ({current_price:.2f}) bajo nivel pivot, esperar rebound"

        elif scenario == 'B':
            return f"🔴 NO OPERAR - Escenario B (liquidez retirándose)"

        else:  # Scenario C
            return f"🟡 INTRADAY ONLY - Zona neutral, pequeñas posiciones"
