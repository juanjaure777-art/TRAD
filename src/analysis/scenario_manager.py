#!/usr/bin/env python3
"""
Scenario Manager - Esteban Pérez Crecetrader Three-Scenario Logic
Implements the three operational scenarios based on market conditions

From ANALISIS_BITCOIN_HOY.md:

ESCENARIO A: "Líquidez Sigue Entrando" ✅
- CONDICIONES: Precio > 90.823, máximos crecientes, distribución sigue disminuyendo
- PROYECCIÓN: 91.381 → 92.286 → 93.347 (weekly objective)
- PLAN: Comprar en 90.823-91.381, vender parcial en 91.719-92.286
- RIESGO: Bajo si se mantiene la estructura

ESCENARIO B: "Líquidez Se Retira" ⚠️
- CONDICIONES: Precio no aguanta 90.823, corrección sin liquidez
- PROYECCIÓN: Caída controlada a 89.199 → 88.666 → 84.12
- PLAN: NO OPERAR si hay indecisión, esperar reversión nuevamente
- RIESGO: Alto, estructura se quiebra

ESCENARIO C: "Zona Neutral" (Esteban lo prevé) 🟡
- CONDICIONES: Precio oscila 90.476-91.381, sin dirección clara
- PROYECCIÓN: Se queda en banda neutral, breakout tras Thanksgiving
- PLAN: Operar intradiario, NO posiciones largas
- RIESGO: Bajo reward, time decay, no ideal

This manager tracks which scenario we're in and recommends position management accordingly.
"""

import numpy as np
from typing import Dict, Optional, List
from enum import Enum


class Scenario(Enum):
    """Market scenarios based on Esteban's analysis"""
    LIQUIDITY_ENTERING = "A_liquidity_entering"      # Strong bullish
    LIQUIDITY_RETREATING = "B_liquidity_retreating"  # Bearish reversal
    NEUTRAL_ZONE = "C_neutral_zone"                  # Choppy/sideways


class ScenarioManager:
    """
    Manages three scenarios and recommends position management

    Key Crecetrader principle:
    "ESTO es un NEGOCIO, funciona como cualquier otro negocio.
     Entiende LAS FASES, y puedes APROVECHARTE."

    Esteban emphasizes the PHASES of price movement:
    - Not all prices are equal
    - Not all times are equal
    - Each scenario has appropriate entries/exits
    """

    def __init__(self,
                 pivot_level: float = 90.823,
                 level_1_buy: float = 90.823,
                 level_2_buy: float = 91.381,
                 level_3_buy: float = 91.719,
                 target_1: float = 92.286,
                 target_2: float = 93.347,
                 support_strong: float = 89.199,
                 support_major: float = 88.666,
                 support_deep: float = 84.12):
        """
        Initialize scenario manager with specific referentes levels

        Args:
            pivot_level: Central support/resistance level
            level_1_buy, level_2_buy, level_3_buy: Accumulation zones
            target_1, target_2: Distribution/take-profit zones
            support_strong, support_major, support_deep: Fallback levels
        """
        self.pivot_level = pivot_level
        self.level_1_buy = level_1_buy
        self.level_2_buy = level_2_buy
        self.level_3_buy = level_3_buy
        self.target_1 = target_1
        self.target_2 = target_2
        self.support_strong = support_strong
        self.support_major = support_major
        self.support_deep = support_deep

        self.current_scenario = None
        self.scenario_history = []
        self.scenario_start_time = None

    def analyze_scenario(self,
                        current_price: float,
                        maximos_trend: str,
                        minimos_trend: str,
                        distribution_level: str,
                        volatility_level: str) -> Dict:
        """
        Analyze current market conditions and determine scenario

        Args:
            current_price: Current BTC price
            maximos_trend: 'crecientes' | 'decrecientes' | 'flat'
            minimos_trend: 'crecientes' | 'decrecientes' | 'flat'
            distribution_level: 'mayuscula' (strong) | 'minuscula' (weak)
            volatility_level: 'high' | 'normal' | 'low'

        Returns:
            {
                'scenario': Scenario enum,
                'confidence': float (0-1),
                'recommendations': {
                    'entry_zone': (float, float),
                    'entry_strategy': str,
                    'tp_levels': [float, float, ...],
                    'sl_level': float,
                    'position_size': str ('FULL' | 'PARTIAL' | 'NONE'),
                    'holding_time': str,
                    'risk_level': str ('LOW' | 'MEDIUM' | 'HIGH')
                },
                'description': str
            }
        """

        # SCENARIO A: Liquidity Entering
        if (current_price > self.pivot_level and
            maximos_trend == 'crecientes' and
            minimos_trend == 'crecientes' and
            distribution_level == 'minuscula'):

            scenario = Scenario.LIQUIDITY_ENTERING
            confidence = 0.9

            recommendations = {
                'entry_zone': (self.level_1_buy, self.level_2_buy),
                'entry_strategy': 'BUY en 90.823-91.381 (acumulación)',
                'tp_levels': [self.target_1, self.target_2],
                'sl_level': self.support_strong,
                'position_size': 'FULL',
                'holding_time': 'Medio-Largo Plazo (días)',
                'risk_level': 'LOW',
                'partial_profit_1': f'Vender 50% en {self.target_1}',
                'partial_profit_2': f'Vender resto en {self.target_2}'
            }

            description = (
                f"🟢 ESCENARIO A: LIQUIDEZ ENTRANDO\n"
                f"   Precio: {current_price:.2f} (>  {self.pivot_level})\n"
                f"   Máximos: CRECIENTES ✅\n"
                f"   Mínimos: CRECIENTES ✅\n"
                f"   Distribución: DÉBIL (minúscula) ✅\n"
                f"   → Continuación alcista probable hacia {self.target_2}"
            )

        # SCENARIO B: Liquidity Retreating
        elif (current_price < self.pivot_level and
              (maximos_trend == 'decrecientes' or minimos_trend == 'decrecientes') and
              distribution_level == 'mayuscula'):

            scenario = Scenario.LIQUIDITY_RETREATING
            confidence = 0.85

            recommendations = {
                'entry_zone': None,
                'entry_strategy': 'NO OPERAR - Esperar reversión confirmada',
                'tp_levels': [],
                'sl_level': None,
                'position_size': 'NONE',
                'holding_time': 'Esperar',
                'risk_level': 'HIGH',
                'fallback_1': f'Si cae, soporte en {self.support_strong}',
                'fallback_2': f'Luego soporte en {self.support_major}',
                'fallback_3': f'Acumulación posible en {self.support_deep}'
            }

            description = (
                f"🔴 ESCENARIO B: LIQUIDEZ RETIRÁNDOSE\n"
                f"   Precio: {current_price:.2f} (< {self.pivot_level})\n"
                f"   Máximos: {'DECRECIENTES' if maximos_trend == 'decrecientes' else maximos_trend}\n"
                f"   Mínimos: {'DECRECIENTES' if minimos_trend == 'decrecientes' else minimos_trend}\n"
                f"   Distribución: FUERTE (mayúscula) ⚠️\n"
                f"   → Corrección esperada, RIESGO ALTO"
            )

        # SCENARIO C: Neutral Zone
        else:
            scenario = Scenario.NEUTRAL_ZONE
            confidence = 0.6

            lower_band = self.level_2_buy - 0.5
            upper_band = self.level_3_buy + 0.5

            recommendations = {
                'entry_zone': (lower_band, upper_band),
                'entry_strategy': f'Operar intradiario en banda {lower_band:.2f}-{upper_band:.2f}',
                'tp_levels': [lower_band + 0.3, upper_band - 0.3],
                'sl_level': lower_band - 0.2,
                'position_size': 'SMALL',
                'holding_time': 'Intradiario (minutos-horas)',
                'risk_level': 'MEDIUM',
                'note': 'Thanksgiving afecta volumen, sin dirección clara'
            }

            description = (
                f"🟡 ESCENARIO C: ZONA NEUTRAL\n"
                f"   Precio: {current_price:.2f}\n"
                f"   Estructura: Indecisa o en transición\n"
                f"   Movimiento: Oscilación sin dirección\n"
                f"   → Mejor para trading intradiario, evitar posiciones largas"
            )

        return {
            'scenario': scenario,
            'confidence': confidence,
            'recommendations': recommendations,
            'description': description
        }

    def get_position_management(self, scenario: Scenario, entry_price: float) -> Dict:
        """
        Get position management plan for current scenario

        Args:
            scenario: Current scenario
            entry_price: Entry price of position

        Returns:
            Position management plan with SL/TP levels
        """
        if scenario == Scenario.LIQUIDITY_ENTERING:
            return {
                'scenario': 'A',
                'strategy': 'PYRAMIDING - Agregar posición en cada nivel',
                'initial_sl': self.support_strong,
                'take_profit_1': {
                    'level': self.target_1,
                    'action': 'Vender 50% (profit taking parcial)',
                    'move_sl': f'Llevar SL a {entry_price} (breakeven)'
                },
                'take_profit_2': {
                    'level': self.target_2,
                    'action': 'Vender resto (profit total)',
                    'risk_reward': '>> 2:1'
                },
                'trailing_stop': f'Después de TP1, usar trailing stop del 1%'
            }

        elif scenario == Scenario.LIQUIDITY_RETREATING:
            return {
                'scenario': 'B',
                'strategy': 'NO POSICIÓN ABIERTA - Esperar señal de reversión',
                'action': 'Si ya tiene posición: CERRAR o reducir al 25%',
                'wait_for': f'Reversión confirmada (máximos+mínimos crecientes nuevamente)',
                'stop_loss': 'INMEDIATO si estructura quiebra'
            }

        else:  # SCENARIO C
            return {
                'scenario': 'C',
                'strategy': 'RANGE TRADING - Compra en soporte, vende en resistencia',
                'buy_zone': f'{self.level_2_buy - 0.5:.2f}',
                'sell_zone': f'{self.level_3_buy + 0.5:.2f}',
                'stop_loss': f'{self.level_2_buy - 0.7:.2f} (fuera de rango)',
                'take_profit': f'Pequeñas ganancias (0.3-0.5 puntos)',
                'quick_exit': 'Si breakout ocurre, salir inmediatamente'
            }

    def evaluate_entry_timing(self,
                            current_price: float,
                            last_n_candles: List[Dict]) -> Dict:
        """
        Evaluate if THIS IS THE RIGHT MOMENT to enter (Esteban's timing emphasis)

        CRECETRADER RULE: "NO es solo el precio, es CUÁNDO ocurre"

        Args:
            current_price: Current price
            last_n_candles: Last N candles with OHLC data

        Returns:
            Timing evaluation for entry
        """
        if not last_n_candles or len(last_n_candles) < 2:
            return {
                'entry_timing': 'WAIT',
                'reason': 'Insufficient data',
                'confidence': 0.0
            }

        last_candle = last_n_candles[-1]
        prev_candle = last_n_candles[-2] if len(last_n_candles) >= 2 else None

        # Check candle quality
        last_body = abs(last_candle['close'] - last_candle['open'])
        last_range = last_candle['high'] - last_candle['low']
        body_ratio = last_body / last_range if last_range > 0 else 0

        # Strong body = good entry timing
        if body_ratio > 0.7:
            entry_timing = 'STRONG'
            timing_reason = 'Vela de tendencia fuerte, dominan compradores'
            confidence = 0.85
        elif body_ratio > 0.5:
            entry_timing = 'GOOD'
            timing_reason = 'Cuerpo moderado, buena dirección'
            confidence = 0.65
        elif body_ratio > 0.3:
            entry_timing = 'WEAK'
            timing_reason = 'Vela de rango, indecisión'
            confidence = 0.40
        else:
            entry_timing = 'POOR'
            timing_reason = 'Mechas largas, rechazos, evitar'
            confidence = 0.20

        # Check positioning
        close_pos = (last_candle['close'] - last_candle['low']) / last_range if last_range > 0 else 0
        if close_pos > 0.7:
            positioning = 'En máximo (alcista)'
        elif close_pos < 0.3:
            positioning = 'En mínimo (bajista)'
        else:
            positioning = 'En medio (indeciso)'

        return {
            'entry_timing': entry_timing,
            'reason': timing_reason,
            'confidence': confidence,
            'candle_quality': body_ratio,
            'positioning': positioning,
            'recommendation': f'Timing {entry_timing.lower()} para entrar'
        }
