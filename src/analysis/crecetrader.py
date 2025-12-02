#!/usr/bin/env python3
"""
TRAD Bot - Crecetrader Context Analysis
Implementa conceptos avanzados del método Crecetrader:
- Análisis de localización (contexto de la vela)
- Análisis de mechas (absorción de compras/ventas)
- Volatility phases (contracción vs expansión)
- Vela de tendencia vs vela de rango
- Detección de rupturas fallidas
"""

import numpy as np
from typing import Tuple, Dict, Optional
from enum import Enum

class CandleLocation(Enum):
    """Localización de la vela en el gráfico"""
    AT_SUPPORT = "at_support"           # En zona de soporte
    AT_RESISTANCE = "at_resistance"     # En zona de resistencia
    FLUID_SPACE = "fluid_space"         # En vacío de movimiento fluido
    UNKNOWN = "unknown"                 # No determinada

class CandleType(Enum):
    """Tipo de vela según cuerpo y colas"""
    TREND_CANDLE = "trend"              # Gran cuerpo, pocas colas
    RANGE_CANDLE = "range"              # Pequeño cuerpo, grandes colas
    INDECISION = "indecision"           # Pequeño cuerpo, colas iguales
    FAILED_BREAKOUT = "failed_breakout" # Cola larga + pequeño cuerpo
    STRONG_CLOSE = "strong_close"       # Cierre fuerte alejado de extremo

class VolatilityPhase(Enum):
    """Fase de volatilidad del mercado"""
    CONTRACTION = "contraction"         # Rango estrecho, calma previa
    EXPANSION = "expansion"             # Rango amplio, volatilidad en explosión
    NEUTRAL = "neutral"                 # Volatilidad normal

class CrecetraderAnalysis:
    """
    Análisis Crecetrader: Localización + Mechas + Contexto + Volatility

    CONCEPTOS CLAVE DE CRECETRADER:
    1. LOCALIZACIÓN: Misma vela ≠ significado si está en soporte/resistencia/vacío
    2. MECHAS: Indican absorción de compras/ventas y puntos de rechazo
    3. VOLATILIDAD: Rango estrecho = próxima explosión, rango amplio = movimiento fuerte
    4. VELA DE TENDENCIA: Gran cuerpo = dominio, pequeño cuerpo + colas = indecisión
    5. RUPTURAS FALLIDAS: Colas largas son intentos fallidos de ruptura
    """

    def __init__(self):
        self.support_level = None
        self.resistance_level = None
        self.avg_range_20 = None  # Promedio de rango últimas 20 velas

    def set_levels(self, support: float, resistance: float):
        """Establecer niveles de soporte y resistencia"""
        self.support_level = support
        self.resistance_level = resistance

    def calculate_volatility_phase(self, closes: np.ndarray,
                                  highs: np.ndarray,
                                  lows: np.ndarray,
                                  period: int = 20) -> Tuple[VolatilityPhase, float]:
        """
        Determinar fase de volatilidad

        Contracción: Rango promedio bajo = calma previa a explosión
        Expansión: Rango promedio alto = volatilidad en aumento
        """
        if len(closes) < period:
            return VolatilityPhase.NEUTRAL, 0.0

        # Calcular rangos
        ranges = highs[-period:] - lows[-period:]
        avg_range = np.mean(ranges)
        current_range = highs[-1] - lows[-1]

        self.avg_range_20 = avg_range

        # Ratio actual vs promedio
        range_ratio = current_range / avg_range if avg_range > 0 else 1.0

        if range_ratio < 0.7:
            return VolatilityPhase.CONTRACTION, range_ratio
        elif range_ratio > 1.3:
            return VolatilityPhase.EXPANSION, range_ratio
        else:
            return VolatilityPhase.NEUTRAL, range_ratio

    def detect_candle_location(self, price: float,
                             support: float,
                             resistance: float,
                             margin_pct: float = 0.5) -> CandleLocation:
        """
        Detectar localización de la vela

        AT_SUPPORT: Precio cerca de soporte (dentro de margin_pct)
        AT_RESISTANCE: Precio cerca de resistencia (dentro de margin_pct)
        FLUID_SPACE: Precio entre soporte y resistencia, sin zona cercana
        """
        margin = support * (margin_pct / 100)

        if abs(price - support) <= margin:
            return CandleLocation.AT_SUPPORT

        if abs(price - resistance) <= margin:
            return CandleLocation.AT_RESISTANCE

        return CandleLocation.FLUID_SPACE

    def analyze_wick_absorption(self, candle: Dict) -> Dict:
        """
        Analizar absorción de compras/ventas por las mechas

        MECHA SUPERIOR LARGA:
        - Precio intentó subir pero fue rechazado (ventas)
        - Indica resistencia

        MECHA INFERIOR LARGA:
        - Precio intentó bajar pero fue rechazado (compras)
        - Indica soporte
        """
        total_range = candle['total_size']
        if total_range == 0:
            return {'upper_wick': 0, 'lower_wick': 0, 'absorption': 'none'}

        upper_wick_ratio = candle['wick_up'] / total_range
        lower_wick_ratio = candle['wick_down'] / total_range

        absorption = 'none'
        absorption_detail = ''

        # Mecha superior significativa (> 40% del rango)
        if upper_wick_ratio > 0.4:
            absorption = 'upper'
            absorption_detail = 'Venta rechazó la compra'

        # Mecha inferior significativa (> 40% del rango)
        elif lower_wick_ratio > 0.4:
            absorption = 'lower'
            absorption_detail = 'Compra rechazó la venta'

        return {
            'upper_wick_ratio': upper_wick_ratio,
            'lower_wick_ratio': lower_wick_ratio,
            'absorption': absorption,
            'detail': absorption_detail
        }

    def classify_candle_type(self, candle: Dict) -> Tuple[CandleType, str]:
        """
        Clasificar tipo de vela según cuerpo y colas

        TREND CANDLE: Cuerpo > 60% del rango, colas pequeñas
        RANGE CANDLE: Cuerpo < 40%, colas largas
        INDECISION: Cuerpo pequeño, colas iguales a ambos lados
        FAILED BREAKOUT: Cola larga + cuerpo pequeño (intento fallido)
        """
        total_range = candle['total_size']
        if total_range == 0:
            return CandleType.INDECISION, "Sin movimiento"

        body_ratio = candle['body_size'] / total_range
        upper_wick_ratio = candle['wick_up'] / total_range
        lower_wick_ratio = candle['wick_down'] / total_range

        # TREND CANDLE: Cuerpo fuerte, colas pequeñas
        if body_ratio > 0.6 and max(upper_wick_ratio, lower_wick_ratio) < 0.2:
            return CandleType.TREND_CANDLE, f"Dominio claro ({body_ratio*100:.0f}% cuerpo)"

        # RANGE CANDLE: Cuerpo pequeño, colas largas
        elif body_ratio < 0.4 and (upper_wick_ratio > 0.3 or lower_wick_ratio > 0.3):
            return CandleType.RANGE_CANDLE, "Indecisión del mercado"

        # INDECISION: Colas iguales
        elif body_ratio < 0.4 and abs(upper_wick_ratio - lower_wick_ratio) < 0.1:
            return CandleType.INDECISION, "Equilibrio de fuerzas"

        # FAILED BREAKOUT: Cola larga + cuerpo pequeño
        elif body_ratio < 0.4 and max(upper_wick_ratio, lower_wick_ratio) > 0.4:
            direction = "arriba" if upper_wick_ratio > lower_wick_ratio else "abajo"
            return CandleType.FAILED_BREAKOUT, f"Ruptura fallida hacia {direction}"

        # STRONG CLOSE: Cierre fuerte al extremo opuesto de apertura
        elif body_ratio > 0.5:
            return CandleType.STRONG_CLOSE, "Cierre fuerte"

        return CandleType.INDECISION, "Tipo indeterminado"

    def detect_trend_context(self, candles: list) -> Dict:
        """
        Detectar contexto de tendencia

        Small body in strong trend = parte de movimiento de tendencia
        Large body in sideways = vela de rango
        """
        if len(candles) < 5:
            return {'trend': 'unknown', 'strength': 0}

        # Analizar últimas 5 velas
        recent = candles[-5:]
        body_sizes = [c['body_size'] for c in recent]
        avg_body = np.mean(body_sizes)
        current_body = candles[-1]['body_size']

        # Trend detection: cuerpos progresivamente mayores = tendencia
        bodies_increasing = all(body_sizes[i] <= body_sizes[i+1] for i in range(len(body_sizes)-1))

        # Volatilidad
        ranges = [c['total_size'] for c in recent]
        volatility_increasing = ranges[-1] > np.mean(ranges)

        if bodies_increasing and current_body > avg_body:
            return {'trend': 'strong', 'strength': 80}
        elif current_body < avg_body:
            return {'trend': 'consolidation', 'strength': 30}
        else:
            return {'trend': 'normal', 'strength': 50}

    def comprehensive_analysis(self, candle: Dict,
                              candles: list,
                              support: float = None,
                              resistance: float = None) -> Dict:
        """
        Análisis COMPLETO Crecetrader de una vela
        Retorna todos los insights necesarios para decisión de entrada/salida
        """
        current_price = candle['close']

        # 1. VOLATILIDAD
        volatility_phase, vol_ratio = self.calculate_volatility_phase(
            np.array([c['close'] for c in candles]),
            np.array([c['high'] for c in candles]),
            np.array([c['low'] for c in candles])
        )

        # 2. LOCALIZACIÓN
        location = CandleLocation.UNKNOWN
        if support and resistance:
            location = self.detect_candle_location(current_price, support, resistance)

        # 3. TIPO DE VELA
        candle_type, type_detail = self.classify_candle_type(candle)

        # 4. ABSORCIÓN DE MECHAS
        wick_analysis = self.analyze_wick_absorption(candle)

        # 5. CONTEXTO DE TENDENCIA
        trend_context = self.detect_trend_context(candles)

        # 6. CALIDAD GENERAL DE ENTRADA
        entry_quality = self._calculate_entry_quality(
            candle_type, location, volatility_phase,
            wick_analysis, trend_context
        )

        return {
            'volatility': {
                'phase': volatility_phase.value,
                'ratio': vol_ratio,
                'interpretation': 'Calma previa a explosión' if volatility_phase == VolatilityPhase.CONTRACTION else 'Volatilidad en expansión'
            },
            'location': location.value,
            'candle_type': {
                'type': candle_type.value,
                'detail': type_detail
            },
            'wick_analysis': wick_analysis,
            'trend_context': trend_context,
            'entry_quality': entry_quality,
            'recommendation': self._generate_recommendation(
                candle_type, location, volatility_phase, entry_quality
            )
        }

    def _calculate_entry_quality(self, candle_type: CandleType,
                                location: CandleLocation,
                                volatility: VolatilityPhase,
                                wick_analysis: Dict,
                                trend_context: Dict) -> float:
        """
        Calcular score de calidad de entrada (0-100)
        Basado en todos los factores Crecetrader
        """
        score = 50.0

        # Type: Vela de tendencia = buena (20 puntos)
        if candle_type == CandleType.TREND_CANDLE:
            score += 20
        elif candle_type == CandleType.STRONG_CLOSE:
            score += 15
        elif candle_type == CandleType.FAILED_BREAKOUT:
            score -= 20  # ¡Malo! Evitar
        elif candle_type == CandleType.INDECISION:
            score -= 5

        # Location: En soporte/resistencia = buena (15 puntos)
        if location == CandleLocation.AT_SUPPORT:
            score += 15
        elif location == CandleLocation.AT_RESISTANCE:
            score -= 10  # Peor zona
        elif location == CandleLocation.FLUID_SPACE:
            score += 5

        # Volatility: Transición contracción→expansión = excelente (15 puntos)
        if volatility == VolatilityPhase.CONTRACTION:
            score += 15  # Próxima explosión
        elif volatility == VolatilityPhase.EXPANSION:
            score += 10

        # Trend context: Tendencia fuerte = buena (10 puntos)
        if trend_context['trend'] == 'strong':
            score += 10
        elif trend_context['trend'] == 'consolidation':
            score -= 5

        # Wick: Sin wick largo rechazo = buena (10 puntos)
        if wick_analysis['absorption'] == 'none':
            score += 10
        elif wick_analysis['absorption'] in ['upper', 'lower']:
            score += 5  # Hay rechazo

        return min(100, max(0, score))

    def _generate_recommendation(self, candle_type: CandleType,
                               location: CandleLocation,
                               volatility: VolatilityPhase,
                               entry_quality: float) -> str:
        """Generar recomendación de entrada basada en análisis"""
        if entry_quality >= 80:
            return "ENTRADA FUERTE - Condiciones excelentes"
        elif entry_quality >= 70:
            return "ENTRADA BUENA - Proceder con confianza"
        elif entry_quality >= 60:
            return "ENTRADA MODERADA - Puede operar con cuidado"
        elif entry_quality >= 50:
            return "ENTRADA DÉBIL - Esperar mejores oportunidades"
        else:
            return "EVITAR ENTRADA - Esperar mejores condiciones"
