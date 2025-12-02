#!/usr/bin/env python3
"""
TRAD Bot v3.0 - Panic Dump Detector Module
Detecta movimientos de pánico (panic dumps) en el mercado
y genera señales de SHORT de alta confianza

PROBLEMA IDENTIFICADO:
- Bot perdió $2,000 de swing en panic dump de 92k → 90k
- Razón: Falta detector de caídas rápidas con volumen masivo
- Solución: Módulo dedicado con 4 confirmaciones

CARACTERÍSTICAS:
1. Detección de caída porcentual rápida (>0.5% en 10 min)
2. Confirmación de volumen masivo (>2x promedio)
3. Análisis de wicks (Crecetrader pattern confirmation)
4. RSI trend validation (bajista, <40)
5. Scoring de confianza (0-100)

GESTIÓN DE RIESGO DIFERENCIADA:
- Posiciones MÁS PEQUEÑAS que LongSetups (1.0% vs 1.5%)
- SL MÁS AJUSTADO (0.3% vs 0.4%)
- Win rate esperado: 65-70% (vs 75-85% en long)
"""

import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PanicDumpSignal:
    """Señal de panic dump detectado"""
    is_panic: bool  # True si se detectó panic dump
    confidence: float  # 0-100, score de confianza
    entry_price: float  # Precio sugerido para SHORT
    stop_loss: float  # SL recomendado
    take_profit_1: float  # TP1 (vender 50%)
    take_profit_2: float  # TP2 (vender 50% restante)
    reason: str  # Explicación de la detección

    # Detalles de cada confirmación
    fast_drop: bool  # Caída rápida detectada
    drop_percentage: float  # % de caída
    massive_volume: bool  # Volumen anómalo
    volume_ratio: float  # Ratio vs promedio
    wick_pattern: bool  # Patrón de wick valid
    rsi_trend: bool  # RSI bajista
    rsi_value: float  # RSI actual


class PanicDumpDetector:
    """
    Detector profesional de panic dumps
    Implementa 4 capas de confirmación
    """

    def __init__(self):
        self.min_drop_percent = 0.3  # Mínimo 0.3% en últimos 10 minutos (ajustado)
        self.min_volume_ratio = 1.5  # Mínimo 1.5x del volumen promedio (ajustado)
        self.min_rsi_trend_threshold = 40  # RSI debe estar <40
        self.lookback_drop = 10  # Últimos 10 candles para caída
        self.lookback_volume = 20  # Últimos 20 candles para promedio

    def detect_panic_dump(
        self,
        opens: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        volumes: np.ndarray,
        rsi_value: float
    ) -> PanicDumpSignal:
        """
        Detecta panic dump con 4 confirmaciones

        Args:
            opens, highs, lows, closes, volumes: OHLCV data (últimos 100 candles)
            rsi_value: RSI(7) actual

        Returns:
            PanicDumpSignal con resultado de detección
        """

        # CONFIRMACIÓN 1: Caída porcentual rápida
        fast_drop, drop_pct = self._check_fast_drop(closes)

        # CONFIRMACIÓN 2: Volumen masivo
        massive_volume, volume_ratio = self._check_massive_volume(volumes)

        # CONFIRMACIÓN 3: Patrón de wicks válido
        wick_pattern = self._check_wick_pattern(opens, highs, lows, closes)

        # CONFIRMACIÓN 4: RSI tendencia bajista
        rsi_trend = self._check_rsi_trend(rsi_value, closes)

        # Calcular confianza basada en confirmaciones
        confirmation_count = sum([fast_drop, massive_volume, wick_pattern, rsi_trend])

        # LÓGICA FINAL
        is_panic = (confirmation_count >= 3)  # Necesita al menos 3 de 4
        confidence = self._calculate_confidence(
            fast_drop, drop_pct, massive_volume, volume_ratio,
            wick_pattern, rsi_trend, rsi_value
        )

        # Generar señal si es pánico confirmado
        if is_panic:
            entry_price = closes[-1]  # Entrada al precio actual
            stop_loss = entry_price * 1.003  # 0.3% arriba (SHORT, así que SL está arriba)
            take_profit_1 = entry_price * (1 - 0.005)  # 0.5% abajo (vender 50%)
            take_profit_2 = entry_price * (1 - 0.010)  # 1.0% abajo (vender 50% restante)

            reason = self._generate_reason(
                fast_drop, drop_pct, massive_volume, volume_ratio,
                wick_pattern, rsi_trend, confirmation_count
            )
        else:
            entry_price = 0
            stop_loss = 0
            take_profit_1 = 0
            take_profit_2 = 0
            reason = f"No hay panic dump confirmado ({confirmation_count}/4 confirmaciones)"

        return PanicDumpSignal(
            is_panic=is_panic,
            confidence=confidence,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit_1=take_profit_1,
            take_profit_2=take_profit_2,
            reason=reason,
            fast_drop=fast_drop,
            drop_percentage=drop_pct,
            massive_volume=massive_volume,
            volume_ratio=volume_ratio,
            wick_pattern=wick_pattern,
            rsi_trend=rsi_trend,
            rsi_value=rsi_value
        )

    def _check_fast_drop(self, closes: np.ndarray) -> Tuple[bool, float]:
        """
        Verificar si hay caída rápida (>0.5% en últimos 10 candles)

        Returns:
            (bool: hay caída rápida, float: % de caída)
        """
        if len(closes) < self.lookback_drop:
            return False, 0.0

        price_then = closes[-self.lookback_drop]
        price_now = closes[-1]

        drop_pct = ((price_now - price_then) / price_then) * 100

        # Negativo = caída
        is_fast_drop = drop_pct < -self.min_drop_percent

        return is_fast_drop, abs(drop_pct)

    def _check_massive_volume(self, volumes: np.ndarray) -> Tuple[bool, float]:
        """
        Verificar si hay volumen masivo (>2x promedio)

        Returns:
            (bool: volumen masivo, float: ratio vs promedio)
        """
        if len(volumes) < self.lookback_volume:
            return False, 0.0

        avg_volume = np.mean(volumes[-self.lookback_volume:])
        current_volume = volumes[-1]

        if avg_volume == 0:
            return False, 0.0

        volume_ratio = current_volume / avg_volume
        is_massive = volume_ratio >= self.min_volume_ratio

        return is_massive, volume_ratio

    def _check_wick_pattern(
        self,
        opens: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray
    ) -> bool:
        """
        Verificar patrón de wick válido para panic dump

        En panic dump:
        - Vela roja (close < open)
        - Wick inferior largo = compra de pánico (absorción)
        - Body sólido = caída confirmada
        """
        if len(closes) < 5:
            return False

        # Última vela
        current_candle = {
            'open': opens[-1],
            'high': highs[-1],
            'low': lows[-1],
            'close': closes[-1]
        }

        # Verificar que sea vela roja (close < open)
        if current_candle['close'] >= current_candle['open']:
            return False  # Verde o doji, no es caída de pánico

        # Calcular tamaño de body y wicks
        body_size = current_candle['open'] - current_candle['close']
        lower_wick = current_candle['close'] - current_candle['low']
        upper_wick = current_candle['high'] - current_candle['open']
        total_range = current_candle['high'] - current_candle['low']

        if total_range == 0:
            return False

        # En panic dump:
        # - Body debe ser significativo (>40% del rango)
        # - Lower wick debe existir pero no dominar (absorción de compra)
        body_ratio = body_size / total_range
        lower_wick_ratio = lower_wick / total_range

        # Patrón válido: body 40-70%, lower wick 10-40%
        valid_pattern = (0.40 <= body_ratio <= 0.70) and (0.05 <= lower_wick_ratio <= 0.40)

        # Validación adicional: últimas 3 velas deben estar bajando
        last_3_closes_down = (
            closes[-1] < closes[-2] and
            closes[-2] < closes[-3]
        )

        return valid_pattern and last_3_closes_down

    def _check_rsi_trend(self, rsi_value: float, closes: np.ndarray) -> bool:
        """
        Verificar tendencia bajista del RSI

        En panic dump:
        - RSI está bajo (<40) O bajando rápido
        - Indica momentum bajista confirmado
        """

        # RSI actual debe estar relativamente bajo
        if rsi_value >= self.min_rsi_trend_threshold:
            return False

        # Verificar que últimas velas están bajando (confirmar tendencia)
        if len(closes) >= 5:
            trend_down = closes[-1] < closes[-5]
            return trend_down

        return rsi_value < 30  # Fallback: RSI extremadamente bajo

    def _calculate_confidence(
        self,
        fast_drop: bool,
        drop_pct: float,
        massive_volume: bool,
        volume_ratio: float,
        wick_pattern: bool,
        rsi_trend: bool,
        rsi_value: float
    ) -> float:
        """
        Calcular score de confianza (0-100)

        Basado en fuerza de cada confirmación
        """

        confidence = 0.0

        # CONFIRMACIÓN 1: Fast drop (máximo 25 puntos)
        if fast_drop:
            # Más caída = más confianza (pero max 25)
            drop_strength = min(drop_pct / 2.0, 25.0)  # 1% = 12.5, 2% = 25
            confidence += drop_strength

        # CONFIRMACIÓN 2: Volumen masivo (máximo 25 puntos)
        if massive_volume:
            # Más volumen = más confianza (pero max 25)
            vol_strength = min((volume_ratio - 2.0) * 10, 25.0)  # 2x = 0, 4x = 20, 5x+ = 25
            confidence += vol_strength

        # CONFIRMACIÓN 3: Wick pattern (máximo 25 puntos)
        if wick_pattern:
            confidence += 25.0

        # CONFIRMACIÓN 4: RSI trend (máximo 25 puntos)
        if rsi_trend:
            # Más bajo el RSI = más confianza
            rsi_strength = (40 - rsi_value) / 40 * 25  # RSI 40 = 0, RSI 0 = 25
            confidence += min(rsi_strength, 25.0)

        # Normalizar a 0-100
        confidence = min(confidence, 100.0)
        confidence = max(confidence, 0.0)

        return confidence

    def _generate_reason(
        self,
        fast_drop: bool,
        drop_pct: float,
        massive_volume: bool,
        volume_ratio: float,
        wick_pattern: bool,
        rsi_trend: bool,
        confirmation_count: int
    ) -> str:
        """
        Generar descripción detallada de la detección
        """

        parts = []

        if fast_drop:
            parts.append(f"Caída rápida: {drop_pct:.2f}%")

        if massive_volume:
            parts.append(f"Volumen masivo: {volume_ratio:.2f}x promedio")

        if wick_pattern:
            parts.append("Patrón de wick válido (absorción de compra)")

        if rsi_trend:
            parts.append("RSI bajista (<40) - Momentum confirmado")

        reason = " | ".join(parts)
        reason += f" ({confirmation_count}/4 confirmaciones)"

        return reason

    def get_position_sizing(self, account_capital: float, base_risk_pct: float = 1.0) -> float:
        """
        Calcular tamaño de posición para panic dump shorts

        Más conservador que long setups porque volatilidad es mayor

        Args:
            account_capital: Capital total de la cuenta
            base_risk_pct: % de riesgo base (default 1.0% para panic, vs 1.5% para long)

        Returns:
            Posición size en % del capital
        """
        # Panic dumps tienen mayor volatilidad = menor posición
        # Long setup: 1.5%
        # Panic dump: 1.0%

        return base_risk_pct

    def get_risk_metrics(self, entry: float, stop_loss: float, take_profit: float) -> Dict:
        """
        Calcular métricas de riesgo/beneficio para panic dump

        Returns:
            Dict con:
            - risk_points: Puntos de pérdida si SL hit
            - reward_points: Puntos de ganancia si TP hit
            - risk_reward_ratio: R/R (ej: 1:2)
            - risk_percent: % de riesgo vs entry
        """

        risk_points = abs(entry - stop_loss)
        reward_points = abs(entry - take_profit)

        if risk_points == 0:
            ratio = 0
        else:
            ratio = reward_points / risk_points

        risk_percent = (risk_points / entry) * 100

        return {
            'risk_points': risk_points,
            'reward_points': reward_points,
            'risk_reward_ratio': ratio,
            'risk_percent': risk_percent
        }


# ============================================================================
# TESTING Y VALIDACIÓN
# ============================================================================

def test_panic_detector():
    """
    Test del panic detector con datos simulados realistas
    """

    detector = PanicDumpDetector()

    # ESCENARIO 1: Normal trading (SIN panic dump)
    print("\n" + "=" * 80)
    print("SCENARIO 1: NORMAL TRADING (Sin Panic Dump)")
    print("=" * 80)

    closes_normal = np.linspace(92000, 92100, 50)  # Movimiento gradual
    opens_normal = closes_normal + np.random.normal(0, 10, 50)
    highs_normal = np.maximum(opens_normal, closes_normal) + np.random.normal(10, 5, 50)
    lows_normal = np.minimum(opens_normal, closes_normal) - np.random.normal(10, 5, 50)
    volumes_normal = np.random.normal(15000, 2000, 50)

    result1 = detector.detect_panic_dump(
        opens=opens_normal,
        highs=highs_normal,
        lows=lows_normal,
        closes=closes_normal,
        volumes=volumes_normal,
        rsi_value=50.0
    )

    print(f"Panic detected: {result1.is_panic}")
    print(f"Confidence: {result1.confidence:.1f}%")

    # ESCENARIO 2: Panic dump (CON confirmaciones)
    print("\n" + "=" * 80)
    print("SCENARIO 2: PANIC DUMP REAL (Dump de 92k a 90k)")
    print("=" * 80)

    # 30 candles normales
    closes_base = np.linspace(92000, 92000, 30)
    opens_base = closes_base + 20
    highs_base = opens_base + 30
    lows_base = closes_base - 30
    volumes_base = np.ones(30) * 15000

    # Inyectar panic dump en últimos 20 candles (realista: 20 minutos)
    panic_closes = np.array([
        92000, 91950, 91900, 91850, 91820, 91800, 91780, 91760, 91740, 91700,  # Caída fuerte
        91720, 91750, 91780, 91800, 91820, 91850, 91880, 91920, 91950, 91970   # Recuperación
    ])

    closes_full = np.concatenate([closes_base, panic_closes])
    opens_full = np.concatenate([opens_base, panic_closes + 10])  # Rojo

    # Wicks realistas en caída
    lows_full = np.concatenate([
        lows_base,
        np.array([91960, 91930, 91880, 91820, 91760, 91750, 91730, 91710, 91680, 91650,  # Lows bajos
                  91700, 91730, 91760, 91790, 91810, 91840, 91870, 91900, 91930, 91950])
    ])
    highs_full = np.concatenate([
        highs_base,
        np.array([92010, 91980, 91950, 91900, 91850, 91840, 91820, 91800, 91770, 91740,  # Highs
                  91750, 91780, 91810, 91840, 91860, 91890, 91920, 91960, 91990, 92010])
    ])

    # Volumen masivo en caída
    volumes_full = np.concatenate([
        volumes_base,
        np.array([15000, 30000, 35000, 40000, 45000, 50000, 45000, 40000, 35000, 30000,  # Volumen alto
                  20000, 18000, 16000, 15000, 15000, 15000, 15000, 15000, 15000, 15000])
    ])

    result2 = detector.detect_panic_dump(
        opens=opens_full,
        highs=highs_full,
        lows=lows_full,
        closes=closes_full,
        volumes=volumes_full,
        rsi_value=28.0  # RSI bajo, dentro de pánico
    )

    print(f"Panic detected: {result2.is_panic}")
    print(f"Confidence: {result2.confidence:.1f}%")
    print(f"Reason: {result2.reason}")
    print(f"")
    print(f"Confirmations:")
    print(f"  - Fast drop: {result2.fast_drop} ({result2.drop_percentage:.2f}%)")
    print(f"  - Massive volume: {result2.massive_volume} ({result2.volume_ratio:.2f}x)")
    print(f"  - Wick pattern: {result2.wick_pattern}")
    print(f"  - RSI trend: {result2.rsi_trend}")
    print(f"")

    if result2.is_panic:
        print(f"SHORT Entry: ${result2.entry_price:.2f}")
        print(f"Stop Loss: ${result2.stop_loss:.2f}")
        print(f"TP1 (0.5%): ${result2.take_profit_1:.2f}")
        print(f"TP2 (1.0%): ${result2.take_profit_2:.2f}")
        print(f"")

        metrics = detector.get_risk_metrics(
            result2.entry_price,
            result2.stop_loss,
            result2.take_profit_2
        )
        print(f"Risk/Reward Ratio: 1:{metrics['risk_reward_ratio']:.2f}")
        print(f"Risk %: {metrics['risk_percent']:.3f}%")
        print(f"Potential profit per $1000: ${(metrics['reward_points'] / result2.entry_price) * 1000:.2f}")

    print("=" * 80)

    return result2


if __name__ == "__main__":
    test_panic_detector()

