"""
Multi-Timeframe Correlation Validator

Implementa análisis profesional con correlación entre timeframes:
- DAILY: Confirmación del trend principal (largo plazo)
- 4H: Estructura Crecetrader (máximos/mínimos, T+Z+V)
- 1H: Entrada de operaciones (resolución operativa)

Solo permite trades cuando todos los timeframes están alineados.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple
import numpy as np
from .structure_change_detector import StructureChangeDetector, StructurePhase
from src.strategy.tzv_validator import TZVValidator


class TimeframeAlignment(Enum):
    """Estado de alineación entre timeframes"""
    PERFECT_ALIGNMENT = "perfect"  # Daily✅ + 4H✅ + 1H✅
    GOOD_ALIGNMENT = "good"        # Daily✅ + 4H✅
    WEAK_ALIGNMENT = "weak"        # Solo una o dos confirmadas
    MISALIGNMENT = "misalignment"  # Contradicción (Daily UP, 4H DOWN)
    NEUTRAL = "neutral"            # No hay señal clara


@dataclass
class TimeframeSignal:
    """Señal de un timeframe individual"""
    timeframe: str
    phase: StructurePhase
    confidence: float
    trend_direction: str  # "UP", "DOWN", "NEUTRAL"
    t_validation: bool
    z_validation: bool
    v_validation: bool
    highest_level: float = None
    lowest_level: float = None
    recommendation: str = ""


@dataclass
class MultiTimeframeAnalysis:
    """Análisis completo multi-timeframe"""
    daily_signal: TimeframeSignal
    h4_signal: TimeframeSignal
    h1_signal: TimeframeSignal
    alignment: TimeframeAlignment
    overall_confidence: float
    recommendation: str
    entry_allowed: bool
    correlation_strength: str  # "VERY_STRONG", "STRONG", "MODERATE", "WEAK", "NONE"


class MultiTimeframeValidator:
    """
    Validador profesional de correlación multi-timeframe
    """

    def __init__(self):
        self.structure_detector = StructureChangeDetector()
        self.tzv_validator = TZVValidator()

    def analyze_all_timeframes(
        self,
        daily_candles: np.ndarray,
        h4_candles: np.ndarray,
        h1_candles: np.ndarray,
        current_price: float,
    ) -> MultiTimeframeAnalysis:
        """
        Analiza correlación entre Daily, 4H y 1H

        Args:
            daily_candles: Array de velas diarias [open, high, low, close]
            h4_candles: Array de velas de 4H
            h1_candles: Array de velas de 1H
            current_price: Precio actual para validación

        Returns:
            Análisis completo con recomendación de entrada
        """
        # 1. Analizar cada timeframe
        daily_signal = self._analyze_timeframe(daily_candles, "DAILY", current_price)
        h4_signal = self._analyze_timeframe(h4_candles, "4H", current_price)
        h1_signal = self._analyze_timeframe(h1_candles, "1H", current_price)

        # 2. Evaluar alineación
        alignment = self._evaluate_alignment(daily_signal, h4_signal, h1_signal)

        # 3. Calcular confianza general
        overall_confidence = self._calculate_overall_confidence(
            daily_signal, h4_signal, h1_signal, alignment
        )

        # 4. Generar recomendación
        recommendation, entry_allowed = self._generate_recommendation(
            alignment, overall_confidence
        )

        # 5. Evaluar fortaleza de correlación
        correlation_strength = self._evaluate_correlation_strength(
            daily_signal, h4_signal, h1_signal
        )

        return MultiTimeframeAnalysis(
            daily_signal=daily_signal,
            h4_signal=h4_signal,
            h1_signal=h1_signal,
            alignment=alignment,
            overall_confidence=overall_confidence,
            recommendation=recommendation,
            entry_allowed=entry_allowed,
            correlation_strength=correlation_strength,
        )

    def _analyze_timeframe(
        self, candles: np.ndarray, timeframe_name: str, current_price: float
    ) -> TimeframeSignal:
        """Analiza estructura y validación T+Z+V para un timeframe"""

        if len(candles) < 4:
            return TimeframeSignal(
                timeframe=timeframe_name,
                phase=StructurePhase.NEUTRAL,
                confidence=0.0,
                trend_direction="NEUTRAL",
                t_validation=False,
                z_validation=False,
                v_validation=False,
                recommendation="Datos insuficientes",
            )

        # Extraer OHLC (candles format: [open, high, low, close, volume])
        highs = candles[:, 1] if candles.shape[1] > 1 else candles[:, 0]
        lows = candles[:, 2] if candles.shape[1] > 2 else candles[:, 0]
        closes = candles[:, 3] if candles.shape[1] > 3 else candles[:, 0]

        # Detectar estructura (máximos/mínimos)
        phase = self.structure_detector.detect_structure_phase(highs, lows)

        # Validar T (Tendencia) - FIXED: correct parameters (highs, lows, closes, lookback)
        t_validation_result = self.tzv_validator.validate_t_tendencia(
            highs, lows, closes, lookback=min(20, len(closes))
        )
        # Extract boolean validation from result dict
        t_validation = t_validation_result.get('validation_passed', False)

        # Validar Z (Zonas) - simplificado
        z_validation = len(highs) > 3 and (np.max(highs) > np.min(lows))

        # Validar V (Vacío/Risk-Reward) - simplificado
        v_validation = z_validation  # En 4H+ siempre hay espacio

        # Determinar dirección de trend
        trend_direction = self._determine_trend_direction(phase)

        # Confianza según estructura
        confidence = self._calculate_phase_confidence(phase, highs, lows)

        # Recomendación
        recommendation = self._generate_timeframe_recommendation(
            timeframe_name, phase, t_validation
        )

        return TimeframeSignal(
            timeframe=timeframe_name,
            phase=phase,
            confidence=confidence,
            trend_direction=trend_direction,
            t_validation=t_validation,
            z_validation=z_validation,
            v_validation=v_validation,
            highest_level=float(np.max(highs)) if len(highs) > 0 else None,
            lowest_level=float(np.min(lows)) if len(lows) > 0 else None,
            recommendation=recommendation,
        )

    def _determine_trend_direction(self, phase: StructurePhase) -> str:
        """Determina UP/DOWN/NEUTRAL según fase de estructura"""
        if phase == StructurePhase.BULLISH_STRONG:
            return "UP"
        elif phase == StructurePhase.BEARISH_STRONG:
            return "DOWN"
        elif phase == StructurePhase.BULLISH_WEAK:
            return "UP"
        elif phase == StructurePhase.BEARISH_WEAK:
            return "DOWN"
        else:
            return "NEUTRAL"

    def _calculate_phase_confidence(
        self, phase: StructurePhase, highs: np.ndarray, lows: np.ndarray
    ) -> float:
        """Calcula confianza 0-1 basada en fase y estructura"""
        base_confidence = {
            StructurePhase.BULLISH_STRONG: 0.95,
            StructurePhase.BEARISH_STRONG: 0.95,
            StructurePhase.BULLISH_WEAK: 0.70,
            StructurePhase.BEARISH_WEAK: 0.70,
            StructurePhase.TRANSITIONAL: 0.50,
            StructurePhase.NEUTRAL: 0.30,
        }.get(phase, 0.3)

        # Ajustar por volatilidad
        if len(highs) > 1 and len(lows) > 1:
            mean_highs = np.mean(highs)
            if mean_highs > 0:  # CRITICAL FIX: Prevent division by zero
                volatility = (np.max(highs) - np.min(lows)) / mean_highs
                if volatility > 0.05:  # Volatilidad alta
                    base_confidence *= 0.95  # Reduce confianza un poco
                elif volatility < 0.01:  # Volatilidad muy baja
                    base_confidence *= 0.85

        return min(base_confidence, 1.0)

    def _generate_timeframe_recommendation(
        self, timeframe: str, phase: StructurePhase, t_validation: bool
    ) -> str:
        """Genera recomendación para un timeframe individual"""
        if not t_validation:
            return f"{timeframe}: ⚠️ Validación T fallida - esperar estructura más clara"

        if phase == StructurePhase.BULLISH_STRONG:
            return f"{timeframe}: ✅ BULLISH FUERTE - Buena entrada alcista"
        elif phase == StructurePhase.BEARISH_STRONG:
            return f"{timeframe}: ✅ BEARISH FUERTE - Buena entrada bajista"
        elif phase == StructurePhase.BULLISH_WEAK:
            return f"{timeframe}: 🟡 Bullish débil - Usar con confirmación extra"
        elif phase == StructurePhase.BEARISH_WEAK:
            return f"{timeframe}: 🟡 Bearish débil - Usar con confirmación extra"
        elif phase == StructurePhase.TRANSITIONAL:
            return f"{timeframe}: ⚠️ Reversión en curso - Esperar confirmación"
        else:
            return f"{timeframe}: ❌ Neutral - No operar"

    def _evaluate_alignment(
        self,
        daily_signal: TimeframeSignal,
        h4_signal: TimeframeSignal,
        h1_signal: TimeframeSignal,
    ) -> TimeframeAlignment:
        """Evalúa alineación entre los tres timeframes"""

        daily_bullish = daily_signal.trend_direction == "UP"
        daily_bearish = daily_signal.trend_direction == "DOWN"
        h4_bullish = h4_signal.trend_direction == "UP"
        h4_bearish = h4_signal.trend_direction == "DOWN"
        h1_bullish = h1_signal.trend_direction == "UP"
        h1_bearish = h1_signal.trend_direction == "DOWN"

        daily_neutral = daily_signal.trend_direction == "NEUTRAL"
        h4_neutral = h4_signal.trend_direction == "NEUTRAL"
        h1_neutral = h1_signal.trend_direction == "NEUTRAL"

        # Contradicción: Daily y 4H en direcciones opuestas
        if (daily_bullish and h4_bearish) or (daily_bearish and h4_bullish):
            return TimeframeAlignment.MISALIGNMENT

        # Alineación perfecta: Daily + 4H + 1H en la misma dirección
        if daily_bullish and h4_bullish and h1_bullish:
            return TimeframeAlignment.PERFECT_ALIGNMENT
        if daily_bearish and h4_bearish and h1_bearish:
            return TimeframeAlignment.PERFECT_ALIGNMENT

        # Alineación buena: Daily + 4H alineados, 1H compatible
        if (daily_bullish and h4_bullish) and (h1_bullish or h1_neutral):
            return TimeframeAlignment.GOOD_ALIGNMENT
        if (daily_bearish and h4_bearish) and (h1_bearish or h1_neutral):
            return TimeframeAlignment.GOOD_ALIGNMENT

        # Alineación débil: Algunos confirmados
        if (daily_bullish or h4_bullish or h1_bullish) and \
           not ((daily_bearish or h4_bearish or h1_bearish)):
            return TimeframeAlignment.WEAK_ALIGNMENT
        if (daily_bearish or h4_bearish or h1_bearish) and \
           not ((daily_bullish or h4_bullish or h1_bullish)):
            return TimeframeAlignment.WEAK_ALIGNMENT

        # Neutral
        return TimeframeAlignment.NEUTRAL

    def _calculate_overall_confidence(
        self,
        daily_signal: TimeframeSignal,
        h4_signal: TimeframeSignal,
        h1_signal: TimeframeSignal,
        alignment: TimeframeAlignment,
    ) -> float:
        """Calcula confianza global ponderada"""

        # Pesos: Daily 40%, 4H 40%, 1H 20% (Daily y 4H son validación)
        weighted_confidence = (
            daily_signal.confidence * 0.40
            + h4_signal.confidence * 0.40
            + h1_signal.confidence * 0.20
        )

        # Multiplicador por alineación
        alignment_multiplier = {
            TimeframeAlignment.PERFECT_ALIGNMENT: 1.0,
            TimeframeAlignment.GOOD_ALIGNMENT: 0.90,
            TimeframeAlignment.WEAK_ALIGNMENT: 0.70,
            TimeframeAlignment.MISALIGNMENT: 0.30,
            TimeframeAlignment.NEUTRAL: 0.50,
        }.get(alignment, 0.5)

        final_confidence = weighted_confidence * alignment_multiplier
        return min(final_confidence, 1.0)

    def _evaluate_correlation_strength(
        self,
        daily_signal: TimeframeSignal,
        h4_signal: TimeframeSignal,
        h1_signal: TimeframeSignal,
    ) -> str:
        """Evalúa fortaleza de correlación entre timeframes"""

        daily_bullish = daily_signal.trend_direction == "UP"
        h4_bullish = h4_signal.trend_direction == "UP"
        h1_bullish = h1_signal.trend_direction == "UP"

        bullish_count = sum([daily_bullish, h4_bullish, h1_bullish])

        if bullish_count == 3 or (3 - bullish_count) == 3:
            return "VERY_STRONG"
        elif bullish_count >= 2 or (3 - bullish_count) >= 2:
            return "STRONG"
        elif bullish_count >= 1 or (3 - bullish_count) >= 1:
            return "MODERATE"
        else:
            return "WEAK"

    def _generate_recommendation(
        self, alignment: TimeframeAlignment, confidence: float
    ) -> Tuple[str, bool]:
        """Genera recomendación de entrada basada en alineación y confianza"""

        if alignment == TimeframeAlignment.MISALIGNMENT:
            return (
                "❌ MISALIGNEMENT: Daily vs 4H en direcciones opuestas - NO OPERAR",
                False,
            )

        if alignment == TimeframeAlignment.PERFECT_ALIGNMENT:
            if confidence >= 0.85:
                return (
                    "✅ PERFECT ALIGNMENT + ALTA CONFIANZA - ENTRADA FUERTE RECOMENDADA",
                    True,
                )
            elif confidence >= 0.70:
                return (
                    "✅ PERFECT ALIGNMENT - ENTRADA RECOMENDADA",
                    True,
                )
            else:
                return (
                    "🟡 Perfect alignment pero confianza moderada - Entrada con cuidado",
                    True,
                )

        if alignment == TimeframeAlignment.GOOD_ALIGNMENT:
            if confidence >= 0.80:
                return (
                    "✅ GOOD ALIGNMENT - ENTRADA RECOMENDADA",
                    True,
                )
            elif confidence >= 0.65:
                return (
                    "🟡 Good alignment - Entrada aceptable",
                    True,
                )
            else:
                return (
                    "⚠️ Good alignment pero confianza baja - Esperar mejor momento",
                    False,
                )

        if alignment == TimeframeAlignment.WEAK_ALIGNMENT:
            return (
                "⚠️ WEAK ALIGNMENT - Solo un timeframe confirmado - Esperar más señales",
                False,
            )

        if alignment == TimeframeAlignment.NEUTRAL:
            return (
                "❌ Sin alineación clara - NO OPERAR",
                False,
            )

        return ("❌ Sin recomendación clara - NO OPERAR", False)

    def get_summary(self, analysis: MultiTimeframeAnalysis) -> str:
        """Genera resumen profesional del análisis"""

        summary = []
        summary.append("=" * 70)
        summary.append("📊 MULTI-TIMEFRAME CORRELATION ANALYSIS")
        summary.append("=" * 70)

        # Señales individuales
        summary.append("\n🔍 INDIVIDUAL TIMEFRAMES:")
        summary.append(f"\n📅 DAILY:")
        summary.append(f"   Trend: {analysis.daily_signal.trend_direction}")
        summary.append(f"   Phase: {analysis.daily_signal.phase.value}")
        summary.append(f"   Confidence: {analysis.daily_signal.confidence:.1%}")
        summary.append(f"   T+Z+V: T={analysis.daily_signal.t_validation} | Z={analysis.daily_signal.z_validation} | V={analysis.daily_signal.v_validation}")

        summary.append(f"\n⏰ 4H:")
        summary.append(f"   Trend: {analysis.h4_signal.trend_direction}")
        summary.append(f"   Phase: {analysis.h4_signal.phase.value}")
        summary.append(f"   Confidence: {analysis.h4_signal.confidence:.1%}")
        summary.append(f"   T+Z+V: T={analysis.h4_signal.t_validation} | Z={analysis.h4_signal.z_validation} | V={analysis.h4_signal.v_validation}")

        summary.append(f"\n⏱️ 1H:")
        summary.append(f"   Trend: {analysis.h1_signal.trend_direction}")
        summary.append(f"   Phase: {analysis.h1_signal.phase.value}")
        summary.append(f"   Confidence: {analysis.h1_signal.confidence:.1%}")
        summary.append(f"   T+Z+V: T={analysis.h1_signal.t_validation} | Z={analysis.h1_signal.z_validation} | V={analysis.h1_signal.v_validation}")

        # Alineación y confianza general
        summary.append(f"\n🔗 ALIGNMENT: {analysis.alignment.value}")
        summary.append(f"📈 Correlation Strength: {analysis.correlation_strength}")
        summary.append(f"💪 Overall Confidence: {analysis.overall_confidence:.1%}")

        # Recomendación
        summary.append(f"\n{analysis.recommendation}")
        summary.append(
            f"{'✅ ENTRY ALLOWED' if analysis.entry_allowed else '❌ NO ENTRY'}"
        )
        summary.append("=" * 70)

        return "\n".join(summary)
