#!/usr/bin/env python3
"""
TRAD Bot - Hybrid Strategy
Combina RSI (filtro) + Price Action (entrada) + Crecetrader (contexto)

Esto es el MERGE de dos estrategias profesionales:
1. RSI v2.0 (indicadores técnicos)
2. Scalping Crecetrader (price action puro + localization + wick analysis + volatility phases)
"""

import numpy as np
from typing import Tuple, Optional, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.strategy.indicators import TechnicalIndicators
from src.strategy.candle_patterns import CandlePatterns
from src.analysis.crecetrader import CrecetraderAnalysis, CandleLocation, VolatilityPhase
from src.analysis.panic_detector import PanicDumpDetector, PanicDumpSignal
from src.strategy.modes import PermissivenessManager, TradingMode, MODES_CONFIG

@dataclass
class HybridSignal:
    """Señal de entrada híbrida enriquecida con análisis Crecetrader"""
    should_trade: bool
    side: str  # "LONG" o "SHORT"
    confidence: float  # 0-100
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    reason: str
    price_action: str  # Patrón de velas detectado
    rsi_value: float
    ema_9: float
    ema_21: float
    # Crecetrader Analysis
    candle_location: str = "unknown"  # AT_SUPPORT, AT_RESISTANCE, FLUID_SPACE
    volatility_phase: str = "neutral"  # CONTRACTION, EXPANSION
    entry_quality_crecetrader: float = 0.0  # 0-100 score from Crecetrader analysis
    wick_analysis: Optional[Dict] = None  # upper/lower wick ratios and absorption type
    # Position Sizing (NEW v3.2)
    position_size_pct: float = 1.5  # Tamaño de posición (1.0-2.5%)
    timeframe_confirmations: int = 0  # Número de timeframes que confirman (0-3)


class HybridStrategy:
    """
    Estrategia Híbrida Profesional

    FILTROS (condiciones que DEBEN cumplirse):
    1. RSI(7) < 25 para LONG (sobreventa)
    2. RSI(7) > 75 para SHORT (sobrecompra)
    3. Horario óptimo (13:30-20:00 UTC)

    CONFIRMACIONES (patrón de entrada):
    1. Price Action: 2-3 velas consecutivas del color correcto
    2. Cierre por encima/debajo del máximo/mínimo anterior
    3. EMA 9 > EMA 21 para LONG, EMA 9 < EMA 21 para SHORT

    RIESGO/BENEFICIO:
    - SL: 0.3-0.5% (muy ajustado, crecetrader style)
    - TP1: 0.5% - Salir 50%
    - TP2: 1.0% - Salir 50% restante
    - Ratio: 1:2 aproximadamente
    """

    def __init__(self, config: dict):
        self.config = config

        # Parámetros RSI (defaults - serán sobrescritos por modo dinámico)
        self.rsi_period = 7
        self.rsi_oversold = 25  # Para LONG (será dinámico)
        self.rsi_overbought = 75  # Para SHORT (será dinámico)

        # Parámetros EMA (Crecetrader context)
        self.ema_fast = 9
        self.ema_slow = 21

        # Gestión de riesgo (Crecetrader)
        self.sl_pct = 0.4  # 0.4% SL (conservador-moderado)
        self.tp1_pct = 0.5  # 0.5% TP1
        self.tp2_pct = 1.0  # 1.0% TP2

        # Control de trades
        self.trades_today = 0
        self.max_trades_per_day = 8
        self.daily_loss_limit = 3.0  # 3% del capital
        self.last_trade_time = None

        # Crecetrader Analysis engine
        self.crecetrader = CrecetraderAnalysis()

        # Panic Dump Detector (NEW v3.1 - Captura swings de pánico)
        self.panic_detector = PanicDumpDetector()

        # NEW v3.3 - Dynamic Permissiveness Modes
        self.permissiveness_manager = PermissivenessManager()
        self.current_mode_config = MODES_CONFIG[TradingMode.BALANCED]

        # NEW v3.4 - RSI Lookback for trend change detection (Option C)
        # Mantener registro del RSI anterior para detectar cambios de tendencia
        self.rsi_prev = 50.0  # RSI inicial neutral
        self.rsi_change_detected = False
        self.rsi_change_side = None  # "LONG" o "SHORT"

    def update_mode_config(self, mode: TradingMode):
        """NEW v3.3 - Update RSI thresholds based on current permissiveness mode"""
        self.current_mode_config = MODES_CONFIG[mode]
        self.rsi_oversold = self.current_mode_config.rsi_lower
        self.rsi_overbought = self.current_mode_config.rsi_upper

    def is_optimal_trading_hours(self) -> bool:
        """
        Verificar si es hora óptima para scalping
        Óptimo: 13:30-20:00 UTC (Sesión US)
        """
        now = datetime.utcnow().time()
        start = datetime.strptime("13:30", "%H:%M").time()
        end = datetime.strptime("20:00", "%H:%M").time()

        return start <= now <= end

    def validate_multi_timeframe(self, side: str, rsi_4h: float,
                                 rsi_daily: Optional[float] = None) -> Tuple[bool, int]:
        """
        Validar señal de 4H con confirmación de Daily

        Para estrategia 4H, solo necesitamos validación en Daily (superior timeframe)

        Retorna: (is_confirmed, number_of_confirmations)

        LONG (rsi_4h < 25):
        - Daily: RSI < 35 (tendencia bajista en Daily confirma setup)

        SHORT (rsi_4h > 75):
        - Daily: RSI > 65 (tendencia alcista en Daily confirma setup)
        """
        confirmations = 1  # 4H siempre cuenta como confirmación base

        if side == "LONG":
            # Para LONG en 4H, necesitamos Daily bajista (RSI < 35) como confirmación
            if rsi_daily is not None and rsi_daily < 35:
                confirmations += 1

        elif side == "SHORT":
            # Para SHORT en 4H, necesitamos Daily alcista (RSI > 65) como confirmación
            if rsi_daily is not None and rsi_daily > 65:
                confirmations += 1

        # Para 4H: con 2 timeframes, confirmaciones >= 2 significa "4H + Daily"
        is_confirmed = confirmations >= 2

        return is_confirmed, confirmations

    def calculate_dynamic_position_size(self, side: str, confidence: float,
                                       crecetrader_quality: float,
                                       timeframe_confirmations: int = 1) -> float:
        """
        Calcular tamaño de posición dinámico basado en múltiples confirmaciones

        Base:
        - Panic dumps: 1.0%
        - Técnico: 1.5%

        Ajuste por confirmaciones:
        - 1 confirmación: base (1.0-1.5%)
        - 2 confirmaciones: +0.5% (1.5-2.0%)
        - 3 confirmaciones: +1.0% (2.0-2.5%)

        Límite máximo: 2.5%
        """
        # Determinar base según tipo de setup
        if side == "SHORT" and crecetrader_quality == 0.0:
            # Panic dump
            base_size = 1.0
        else:
            # Técnico o LONG
            base_size = 1.5

        # Ajuste por confirmaciones multiples (para 4H: solo 2 timeframes posibles)
        confirmation_bonus = {
            1: 0.0,     # Solo 4H (sin Daily confirmación)
            2: 0.5      # 4H + Daily confirmado
            # REMOVED: 3 confirmations (4H strategy solo tiene 2 timeframes: 4H + Daily)
        }

        bonus = confirmation_bonus.get(timeframe_confirmations, 0.0)
        dynamic_size = base_size + bonus

        # Ajuste adicional por confianza extrema
        if confidence > 85:
            dynamic_size = min(2.5, dynamic_size + 0.25)
        elif confidence < 60:
            dynamic_size = max(1.0, dynamic_size - 0.25)

        # Limitar a rango permitido
        return min(2.5, max(1.0, dynamic_size))

    def calculate_sl_tp_distances(self, entry_price: float, side: str) -> Tuple[float, float, float]:
        """
        Calcular Stop Loss y Take Profit levels para una entrada

        NEW v3.3 - Estándares para todas las sesiones

        LONG:
        - SL: 2% por debajo de entry
        - TP1: 1% arriba de entry (cierra 50%)
        - TP2: 2% arriba de entry (cierra 25%, inicia trailing 25%)

        SHORT:
        - SL: 2% por encima de entry
        - TP1: 1% debajo de entry (cierra 50%)
        - TP2: 2% debajo de entry (cierra 25%, inicia trailing 25%)

        Retorna: (stop_loss, take_profit_1, take_profit_2)
        """
        if side == "LONG":
            sl_price = entry_price * (1 - 0.02)    # -2%
            tp1_price = entry_price * (1 + 0.01)   # +1%
            tp2_price = entry_price * (1 + 0.02)   # +2%
        else:  # SHORT
            sl_price = entry_price * (1 + 0.02)    # +2%
            tp1_price = entry_price * (1 - 0.01)   # -1%
            tp2_price = entry_price * (1 - 0.02)   # -2%

        return sl_price, tp1_price, tp2_price

    def check_pre_conditions(self) -> Tuple[bool, str]:
        """
        Verificar condiciones previas antes de analizar
        """
        # CRITICAL FIX v3.4.3: Removed is_optimal_trading_hours() check
        # This was blocking ALL entries after 20:00 UTC on testnet (24/7 trading)
        # 1. Horario óptimo - DISABLED FOR TESTNET 24/7 TRADING
        # if not self.is_optimal_trading_hours():
        #     return False, "❌ Fuera de horario óptimo"

        # 2. Máximo de trades/día
        if self.trades_today >= self.max_trades_per_day:
            return False, f"❌ Máximo {self.max_trades_per_day} trades/día alcanzado"

        # 3. Espera entre trades (cooldown)
        if self.last_trade_time:
            elapsed = (datetime.utcnow() - self.last_trade_time).total_seconds()
            if elapsed < 300:  # 5 minutos entre trades
                return False, f"⏳ Esperar {300 - elapsed:.0f}s entre trades"

        return True, "✅ Condiciones previas OK"

    def analyze(self, opens: np.ndarray, highs: np.ndarray,
                lows: np.ndarray, closes: np.ndarray,
                volumes: Optional[np.ndarray] = None,
                opens_daily: Optional[np.ndarray] = None,
                highs_daily: Optional[np.ndarray] = None,
                lows_daily: Optional[np.ndarray] = None,
                closes_daily: Optional[np.ndarray] = None,
                mode: Optional[TradingMode] = None) -> HybridSignal:
        """
        Análisis híbrido completo
        Retorna señal de entrada con confianza calculada
        NEW v3.3 - Accepts dynamic permissiveness mode
        """
        # Update RSI thresholds based on current mode
        if mode is not None:
            self.update_mode_config(mode)
        else:
            # Default to BALANCED if no mode provided
            self.update_mode_config(TradingMode.BALANCED)

        # Validar datos
        if len(closes) < 50:
            return HybridSignal(
                should_trade=False,
                side="NONE",
                confidence=0,
                entry_price=0,
                stop_loss=0,
                take_profit_1=0,
                take_profit_2=0,
                reason="Datos insuficientes",
                price_action="none",
                rsi_value=50,
                ema_9=closes[-1],
                ema_21=closes[-1]
            )

        # Precondiciones
        pre_ok, pre_msg = self.check_pre_conditions()
        if not pre_ok:
            return HybridSignal(
                should_trade=False,
                side="NONE",
                confidence=0,
                entry_price=0,
                stop_loss=0,
                take_profit_1=0,
                take_profit_2=0,
                reason=pre_msg,
                price_action="none",
                rsi_value=TechnicalIndicators.rsi(closes, self.rsi_period),
                ema_9=TechnicalIndicators.ema(closes, self.ema_fast),
                ema_21=TechnicalIndicators.ema(closes, self.ema_slow)
            )

        # Calcular indicadores
        rsi = TechnicalIndicators.rsi(closes, self.rsi_period)
        ema_9 = TechnicalIndicators.ema(closes, self.ema_fast)
        ema_21 = TechnicalIndicators.ema(closes, self.ema_slow)

        current_price = closes[-1]

        # NEW v3.4 - RSI Lookback Detection (Option C)
        # Detectar cambios de tendencia comparando RSI anterior vs actual
        # ============================================================
        self.rsi_change_detected = False
        self.rsi_change_side = None

        # Caso 1: RSI WAS overbought (>75) pero NOW bajó = SHORT reversal opportunity
        if self.rsi_prev > self.rsi_overbought and rsi <= self.rsi_overbought:
            self.rsi_change_detected = True
            self.rsi_change_side = "SHORT"
            print(f"[RSI CHANGE DETECTED] SHORT Reversal: RSI {self.rsi_prev:.1f} → {rsi:.1f} (threshold: {self.rsi_overbought})")

        # Caso 2: RSI WAS oversold (<25) pero NOW subió = LONG reversal opportunity
        elif self.rsi_prev < self.rsi_oversold and rsi >= self.rsi_oversold:
            self.rsi_change_detected = True
            self.rsi_change_side = "LONG"
            print(f"[RSI CHANGE DETECTED] LONG Reversal: RSI {self.rsi_prev:.1f} → {rsi:.1f} (threshold: {self.rsi_oversold})")

        # Guardar RSI actual para próximo ciclo
        self.rsi_prev = rsi

        # 0️⃣ DETECTOR DE PANIC DUMP (NEW v3.1 - Detecta caídas rápidas con volumen)
        # =====================================================
        # Este es un análisis SEPARADO del filtro RSI normal
        # Captura oportunidades de SHORT en panic dumps
        if volumes is not None and len(volumes) >= 20:
            panic_signal = self.panic_detector.detect_panic_dump(
                opens=opens,
                highs=highs,
                lows=lows,
                closes=closes,
                volumes=volumes,
                rsi_value=rsi
            )

            # Si hay panic dump confirmado, generar SHORT signal
            if panic_signal.is_panic and panic_signal.confidence >= 50:  # Mínimo 50% confianza
                return HybridSignal(
                    should_trade=True,
                    side="SHORT",
                    confidence=panic_signal.confidence * 0.9,  # Slightly lower confidence than technical shorts
                    entry_price=panic_signal.entry_price,
                    stop_loss=panic_signal.stop_loss,
                    take_profit_1=panic_signal.take_profit_1,
                    take_profit_2=panic_signal.take_profit_2,
                    reason=f"🚨 PANIC DUMP DETECTED: {panic_signal.reason} | Risk/Reward: 1:3+",
                    price_action="panic_dump",
                    rsi_value=rsi,
                    ema_9=ema_9,
                    ema_21=ema_21
                )

        # 1️⃣ FILTRO RSI (condición necesaria)
        # =====================================================
        # NEW v3.4: Aceptar también cambios de RSI, no solo extremos
        rsi_filter_passed = (rsi < self.rsi_oversold or rsi > self.rsi_overbought) or self.rsi_change_detected

        # CRITICAL FIX v3.5.1: Reset RSI change flag AFTER using it to prevent duplicate entries
        # The flag is used in rsi_filter_passed above, then immediately reset for next cycle
        if self.rsi_change_detected:
            self.rsi_change_detected = False

        if not rsi_filter_passed:
            # RSI en zona normal y sin cambio detectado - sin entrada
            return HybridSignal(
                should_trade=False,
                side="NONE",
                confidence=0,
                entry_price=0,
                stop_loss=0,
                take_profit_1=0,
                take_profit_2=0,
                reason=f"RSI {rsi:.1f} en zona normal (no en extremo, no cambio detectado)",
                price_action="none",
                rsi_value=rsi,
                ema_9=ema_9,
                ema_21=ema_21
            )

        # 2️⃣ DETECCIÓN DE PATRÓN DE VELAS
        # =====================================================
        candles_info = CandlePatterns.get_candle_info(opens, highs, lows, closes)

        # LONG: RSI < 25 (sobreventa) + Velas verdes
        if rsi < self.rsi_oversold:
            bullish_entry, bullish_type, bullish_data = CandlePatterns.detect_bullish_entry(candles_info)

            # CRITICAL FIX v3.4.2: Respect mode configuration for EMA alignment requirement
            ema_check_passed = (not self.current_mode_config.ema_strength_required) or (ema_9 > ema_21)
            if bullish_entry and ema_check_passed:
                # ✅ ENTRADA LONG CONFIRMADA - Análisis Crecetrader adicional
                confidence = self._calculate_confidence("LONG", rsi, ema_9, ema_21, bullish_data)
                sl = current_price - (current_price * self.sl_pct / 100)
                tp1 = current_price + (current_price * self.tp1_pct / 100)
                tp2 = current_price + (current_price * self.tp2_pct / 100)

                # Crecetrader Analysis - Localization + Volatility + Wick Analysis
                candle_current = candles_info[-1]
                crecetrader_analysis = self.crecetrader.comprehensive_analysis(
                    candle_current,
                    candles_info,
                    support=sl,
                    resistance=tp2
                )

                # Mejorar confianza con análisis Crecetrader
                enhanced_confidence = confidence
                if crecetrader_analysis['entry_quality'] > 70:
                    enhanced_confidence = min(100, confidence + 5)

                # 🔍 Multi-Timeframe Confirmation: 4H + Daily
                # ====================================================
                timeframe_confirmations = 1  # 4H siempre cuenta
                if closes_daily is not None and len(closes_daily) >= 20:
                    rsi_daily = TechnicalIndicators.rsi(closes_daily, self.rsi_period)
                    is_confirmed, timeframe_confirmations = self.validate_multi_timeframe(
                        "LONG", rsi, rsi_daily=rsi_daily
                    )
                    if not is_confirmed:
                        # Penalidad si Daily no confirma LONG
                        enhanced_confidence = max(40, enhanced_confidence - 15)
                # REMOVED: 5m and 15m validation (not applicable to 4H strategy)

                # 📊 Dynamic Position Sizing (NEW v3.2)
                # ====================================================
                position_size = self.calculate_dynamic_position_size(
                    "LONG", enhanced_confidence,
                    crecetrader_analysis['entry_quality'],
                    timeframe_confirmations
                )

                # Reset RSI change flag after using it for entry (NEW v3.5 - Fix duplicate entries)
                self.rsi_change_detected = False

                return HybridSignal(
                    should_trade=True,
                    side="LONG",
                    confidence=enhanced_confidence,
                    entry_price=current_price,
                    stop_loss=sl,
                    take_profit_1=tp1,
                    take_profit_2=tp2,
                    reason=f"RSI{rsi:.1f}+Bullish+EMA{ema_9:.0f}>{ema_21:.0f}+Crecetrader+MTF({timeframe_confirmations})",
                    price_action=bullish_type,
                    rsi_value=rsi,
                    ema_9=ema_9,
                    ema_21=ema_21,
                    # Crecetrader enrichment
                    candle_location=crecetrader_analysis['location'],
                    volatility_phase=crecetrader_analysis['volatility']['phase'],
                    entry_quality_crecetrader=crecetrader_analysis['entry_quality'],
                    wick_analysis=crecetrader_analysis['wick_analysis'],
                    # Position Sizing enrichment
                    position_size_pct=position_size,
                    timeframe_confirmations=timeframe_confirmations
                )

        # SHORT: Overbought RSI OR Downtrend + Velas rojas
        # =====================================================================
        # Condición 1: RSI > 75 (sobrecompra clásica)
        # Condición 2: Downtrend detectado (EMA 9 < 21) + Velas rojas
        # Esto permite operar SHORT en downtrends sin esperar overbought
        is_overbought = rsi > self.rsi_overbought
        is_downtrend = ema_9 < ema_21

        if is_overbought or is_downtrend:
            bearish_entry, bearish_type, bearish_data = CandlePatterns.detect_bearish_entry(candles_info)

            # CRITICAL FIX v3.5: Allow RSI reversals in PERMISSIVE mode without strict candle patterns
            # In PERMISSIVE mode with overbought RSI, allow SHORT without waiting for red candles
            if self.current_mode_config.mode == TradingMode.PERMISSIVE and is_overbought and not bearish_entry:
                # RSI is overbought but candles don't yet show bearish pattern
                # In PERMISSIVE mode, accept RSI reversal as signal
                bearish_entry = True
                bearish_type = "rsi_overbought_reversal"
                bearish_data = {'pattern': 'rsi_reversal_permissive', 'rsi': rsi}

            # CRITICAL FIX v3.4.3: Respect mode configuration AND allow SHORT in downtrends
            ema_check_passed_short = (not self.current_mode_config.ema_strength_required) or is_downtrend
            if bearish_entry and ema_check_passed_short:
                # ✅ ENTRADA SHORT CONFIRMADA - Análisis Crecetrader adicional
                confidence = self._calculate_confidence("SHORT", rsi, ema_9, ema_21, bearish_data)
                sl = current_price + (current_price * self.sl_pct / 100)
                tp1 = current_price - (current_price * self.tp1_pct / 100)
                tp2 = current_price - (current_price * self.tp2_pct / 100)

                # Crecetrader Analysis - Localization + Volatility + Wick Analysis
                candle_current = candles_info[-1]
                crecetrader_analysis = self.crecetrader.comprehensive_analysis(
                    candle_current,
                    candles_info,
                    support=tp2,
                    resistance=sl
                )

                # Mejorar confianza con análisis Crecetrader
                enhanced_confidence = confidence
                if crecetrader_analysis['entry_quality'] > 70:
                    enhanced_confidence = min(100, confidence + 5)

                # 🔍 Multi-Timeframe Confirmation: 4H + Daily
                # ====================================================
                timeframe_confirmations = 1  # 4H siempre cuenta
                if closes_daily is not None and len(closes_daily) >= 20:
                    rsi_daily = TechnicalIndicators.rsi(closes_daily, self.rsi_period)
                    is_confirmed, timeframe_confirmations = self.validate_multi_timeframe(
                        "SHORT", rsi, rsi_daily=rsi_daily
                    )
                    if not is_confirmed:
                        # Penalidad si Daily no confirma SHORT
                        enhanced_confidence = max(40, enhanced_confidence - 15)
                # REMOVED: 5m and 15m validation (not applicable to 4H strategy)

                # 📊 Dynamic Position Sizing (NEW v3.2)
                # ====================================================
                position_size = self.calculate_dynamic_position_size(
                    "SHORT", enhanced_confidence,
                    crecetrader_analysis['entry_quality'],
                    timeframe_confirmations
                )

                # Reset RSI change flag after using it for entry (NEW v3.5 - Fix duplicate entries)
                self.rsi_change_detected = False

                return HybridSignal(
                    should_trade=True,
                    side="SHORT",
                    confidence=enhanced_confidence,
                    entry_price=current_price,
                    stop_loss=sl,
                    take_profit_1=tp1,
                    take_profit_2=tp2,
                    reason=f"RSI{rsi:.1f}+Bearish+EMA{ema_9:.0f}<{ema_21:.0f}+Crecetrader+MTF({timeframe_confirmations})",
                    price_action=bearish_type,
                    rsi_value=rsi,
                    ema_9=ema_9,
                    ema_21=ema_21,
                    # Crecetrader enrichment
                    candle_location=crecetrader_analysis['location'],
                    volatility_phase=crecetrader_analysis['volatility']['phase'],
                    entry_quality_crecetrader=crecetrader_analysis['entry_quality'],
                    wick_analysis=crecetrader_analysis['wick_analysis'],
                    # Position Sizing enrichment
                    position_size_pct=position_size,
                    timeframe_confirmations=timeframe_confirmations
                )

        # Sin patrón de confirmación
        return HybridSignal(
            should_trade=False,
            side="NONE",
            confidence=0,
            entry_price=0,
            stop_loss=0,
            take_profit_1=0,
            take_profit_2=0,
            reason=f"RSI extremo ({rsi:.1f}) pero sin patrón de velas de confirmación",
            price_action="no_pattern",
            rsi_value=rsi,
            ema_9=ema_9,
            ema_21=ema_21
        )

    def _calculate_confidence(self, side: str, rsi: float, ema_9: float,
                            ema_21: float, pattern_data: dict) -> float:
        """
        Calcular confianza de la señal (0-100)
        Basado en: RSI extremo, distancia EMA, fuerza patrón
        """
        score = 50.0  # Base

        # RSI extremo (0-20 puntos)
        if side == "LONG":
            if rsi < 10:
                score += 20
            elif rsi < 20:
                score += 15
            else:
                score += 10
        else:  # SHORT
            if rsi > 90:
                score += 20
            elif rsi > 80:
                score += 15
            else:
                score += 10

        # Divergencia EMA (0-15 puntos)
        ema_distance = abs(ema_9 - ema_21) / ema_21 * 100
        if ema_distance > 1.0:
            score += 15
        elif ema_distance > 0.5:
            score += 10
        else:
            score += 5

        # Fuerza del patrón (0-15 puntos)
        body_strength = pattern_data.get('body_strength', 0)
        if body_strength > 0.7:
            score += 15
        elif body_strength > 0.5:
            score += 10
        else:
            score += 5

        return min(100, max(0, score))

    def record_trade(self, side: str):
        """Registrar que se ejecutó un trade"""
        self.trades_today += 1
        self.last_trade_time = datetime.utcnow()
