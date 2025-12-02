#!/usr/bin/env python3
"""
MULTITIMEFRAME CORRELATOR - Análisis jerárquico correlacionado
==============================================================
Correlaciona análisis de múltiples timeframes con jerarquía clara:

JERARQUÍA:
- DAILY (1d): Tendencia principal del día - Máximo peso
- 4HOUR (4h): Velas principales para las próximas 16 horas
- 1HOUR (1h): Confirmación dentro de 4H
- 15MIN (15m): Entrada fina dentro de 1H
- 5MIN (5m): Micro-confirmación
- 1MIN (1m): Ejecución precisa

LÓGICA OPERATIVA:
El bot NO opera en un timeframe específico.
El bot opera 24/7 buscando oportunidades cuando:
1. Daily/4H/1H muestran alineación (contexto favorable)
2. 15m/5m/1m dan señal de entrada
3. GatekeeperV2 valida con toda la información
"""

from typing import Dict, List, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


class MultitimeframeCorrelator:
    """
    Correlaciona múltiples timeframes con análisis jerárquico
    """

    # Pesos para cada timeframe (más alto = más importante)
    WEIGHTS = {
        '1d': 40,   # Daily define tendencia principal
        '4h': 25,   # 4H define estructura
        '1h': 20,   # 1H confirma
        '15m': 10,  # 15m para entrada
        '5m': 3,    # 5m micro-confirmación
        '1m': 2     # 1m ejecución
    }

    def __init__(self):
        self.last_analysis = None

    def correlate(self, timeframe_data: Dict[str, Dict]) -> Dict:
        """
        Correlaciona datos de múltiples timeframes

        Args:
            timeframe_data: Dict con análisis de cada timeframe
            Estructura esperada:
            {
                '1d': {'indicators': {...}, 'momentum': 'BULLISH', 'phase': 'TRENDING'},
                '4h': {...},
                ...
            }

        Returns:
            {
                'alignment_score': 0-100 (% de alineación entre timeframes),
                'primary_direction': 'BULLISH'|'BEARISH'|'NEUTRAL',
                'confidence': 0.0-1.0,
                'volatility_context': 'LOW'|'MODERATE'|'HIGH',
                'opportunity_score': 0-100,
                'risk_factors': [str],
                'entry_recommendation': 'STRONG_LONG'|'WEAK_LONG'|'WAIT'|...,
                'structure_context': str,
                'timeframe_details': {...}
            }
        """
        if not timeframe_data or len(timeframe_data) == 0:
            return self._empty_correlation()

        # 1. Calcular dirección primaria (Daily tiene más peso)
        primary_direction = self._calculate_primary_direction(timeframe_data)

        # 2. Calcular alignment score
        alignment_score = self._calculate_alignment_score(timeframe_data, primary_direction)

        # 3. Analizar volatilidad
        volatility_context = self._analyze_volatility(timeframe_data)

        # 4. Detectar factores de riesgo
        risk_factors = self._detect_risk_factors(timeframe_data, alignment_score)

        # 5. Calcular opportunity score
        opportunity_score = self._calculate_opportunity_score(
            alignment_score, timeframe_data, risk_factors
        )

        # 6. Generar recomendación de entrada
        entry_recommendation = self._generate_entry_recommendation(
            primary_direction, alignment_score, opportunity_score, timeframe_data
        )

        # 7. Contexto de estructura
        structure_context = self._build_structure_context(timeframe_data)

        # 8. Confianza general
        confidence = self._calculate_confidence(alignment_score, opportunity_score, risk_factors)

        result = {
            'alignment_score': alignment_score,
            'primary_direction': primary_direction,
            'confidence': confidence,
            'volatility_context': volatility_context,
            'opportunity_score': opportunity_score,
            'risk_factors': risk_factors,
            'entry_recommendation': entry_recommendation,
            'structure_context': structure_context,
            'timeframe_details': self._extract_timeframe_details(timeframe_data)
        }

        self.last_analysis = result
        return result

    def _calculate_primary_direction(self, tf_data: Dict) -> str:
        """
        Calcula dirección primaria usando pesos jerárquicos
        Daily tiene el mayor peso
        """
        bullish_score = 0
        bearish_score = 0
        neutral_score = 0

        for tf, data in tf_data.items():
            if tf not in self.WEIGHTS:
                continue

            weight = self.WEIGHTS[tf]
            momentum = data.get('momentum', 'NEUTRAL')

            if momentum == 'BULLISH':
                bullish_score += weight
            elif momentum == 'BEARISH':
                bearish_score += weight
            else:
                neutral_score += weight

        # Threshold: necesita 60% para ser direccional
        total = bullish_score + bearish_score + neutral_score
        if total == 0:
            return 'NEUTRAL'

        bullish_pct = bullish_score / total
        bearish_pct = bearish_score / total

        if bullish_pct > 0.6:
            return 'BULLISH'
        elif bearish_pct > 0.6:
            return 'BEARISH'
        else:
            return 'NEUTRAL'

    def _calculate_alignment_score(self, tf_data: Dict, primary_direction: str) -> int:
        """
        Calcula % de alineación con la dirección primaria
        100 = todos los timeframes alineados
        0 = ninguno alineado
        """
        if primary_direction == 'NEUTRAL':
            return 50  # Neutral baseline

        aligned_weight = 0
        total_weight = 0

        for tf, data in tf_data.items():
            if tf not in self.WEIGHTS:
                continue

            weight = self.WEIGHTS[tf]
            momentum = data.get('momentum', 'NEUTRAL')

            total_weight += weight

            if momentum == primary_direction:
                aligned_weight += weight

        if total_weight == 0:
            return 50

        score = int((aligned_weight / total_weight) * 100)
        return max(0, min(100, score))

    def _analyze_volatility(self, tf_data: Dict) -> str:
        """
        Analiza volatilidad promedio de los timeframes
        """
        volatilities = []

        for tf, data in tf_data.items():
            indicators = data.get('indicators', {})
            vol = indicators.get('volatility', 0)
            if vol > 0:
                volatilities.append(vol)

        if len(volatilities) == 0:
            return 'MODERATE'

        avg_vol = np.mean(volatilities)

        if avg_vol > 2.5:
            return 'HIGH'
        elif avg_vol < 1.0:
            return 'LOW'
        else:
            return 'MODERATE'

    def _detect_risk_factors(self, tf_data: Dict, alignment_score: int) -> List[str]:
        """
        Detecta factores de riesgo automáticamente
        """
        risks = []

        # Riesgo 1: Baja alineación
        if alignment_score < 50:
            risks.append(f"LOW_ALIGNMENT: {alignment_score}% - Timeframes conflictivos")

        # Riesgo 2: Daily vs 4H divergencia
        if '1d' in tf_data and '4h' in tf_data:
            daily_mom = tf_data['1d'].get('momentum', 'NEUTRAL')
            h4_mom = tf_data['4h'].get('momentum', 'NEUTRAL')

            if daily_mom != h4_mom and daily_mom != 'NEUTRAL' and h4_mom != 'NEUTRAL':
                risks.append(f"DAILY_4H_DIVERGENCE: Daily={daily_mom} vs 4H={h4_mom}")

        # Riesgo 3: Volatilidad extrema
        for tf, data in tf_data.items():
            indicators = data.get('indicators', {})
            vol = indicators.get('volatility', 0)

            if vol > 4.0:
                risks.append(f"EXTREME_VOLATILITY: {tf} = {vol:.2f}%")

        # Riesgo 4: RSI extremos en múltiples timeframes (riesgo de reversión)
        extreme_rsi_count = 0
        for tf, data in tf_data.items():
            indicators = data.get('indicators', {})
            rsi = indicators.get('rsi', 50)

            if rsi < 20 or rsi > 80:
                extreme_rsi_count += 1

        if extreme_rsi_count >= 3:
            risks.append(f"MULTI_TF_EXTREME_RSI: {extreme_rsi_count} timeframes en extremos")

        return risks

    def _calculate_opportunity_score(self, alignment_score: int,
                                    tf_data: Dict, risk_factors: List[str]) -> int:
        """
        Calcula score de oportunidad (0-100)
        Mayor = mejor oportunidad
        """
        score = alignment_score  # Base score

        # Bonus: Si Daily + 4H + 1H alineados perfectamente
        if '1d' in tf_data and '4h' in tf_data and '1h' in tf_data:
            daily_mom = tf_data['1d'].get('momentum', 'NEUTRAL')
            h4_mom = tf_data['4h'].get('momentum', 'NEUTRAL')
            h1_mom = tf_data['1h'].get('momentum', 'NEUTRAL')

            if daily_mom == h4_mom == h1_mom and daily_mom != 'NEUTRAL':
                score += 15  # Perfect alignment bonus

        # Penalty: Por cada risk factor
        penalty = len(risk_factors) * 10
        score -= penalty

        # Bonus: RSI oversold/overbought en timeframes bajos con alineación alta
        if alignment_score > 70:
            for tf in ['15m', '5m', '1m']:
                if tf in tf_data:
                    indicators = tf_data[tf].get('indicators', {})
                    rsi = indicators.get('rsi', 50)
                    if rsi < 25 or rsi > 75:
                        score += 5  # Extreme RSI bonus

        return max(0, min(100, score))

    def _generate_entry_recommendation(self, direction: str, alignment: int,
                                      opportunity: int, tf_data: Dict) -> str:
        """
        Genera recomendación de entrada basada en todo el análisis
        """
        # WAIT si alineación muy baja
        if alignment < 40:
            return 'WAIT_NO_ALIGNMENT'

        # WAIT si opportunity muy bajo
        if opportunity < 30:
            return 'WAIT_LOW_OPPORTUNITY'

        # Buscar señales en timeframes bajos (15m, 5m, 1m)
        entry_signal = self._check_entry_signals(tf_data)

        if direction == 'BULLISH':
            if alignment >= 80 and opportunity >= 70:
                return f'STRONG_LONG_{entry_signal}'
            elif alignment >= 60 and opportunity >= 50:
                return f'MODERATE_LONG_{entry_signal}'
            else:
                return f'WEAK_LONG_{entry_signal}'

        elif direction == 'BEARISH':
            if alignment >= 80 and opportunity >= 70:
                return f'STRONG_SHORT_{entry_signal}'
            elif alignment >= 60 and opportunity >= 50:
                return f'MODERATE_SHORT_{entry_signal}'
            else:
                return f'WEAK_SHORT_{entry_signal}'

        else:  # NEUTRAL
            return 'WAIT_NEUTRAL_MARKET'

    def _check_entry_signals(self, tf_data: Dict) -> str:
        """
        Verifica si hay señales de entrada en timeframes bajos
        """
        signals = []

        for tf in ['15m', '5m', '1m']:
            if tf not in tf_data:
                continue

            indicators = tf_data[tf].get('indicators', {})
            rsi = indicators.get('rsi', 50)

            # Oversold (potential long entry)
            if rsi < 30:
                signals.append(f'{tf}_OVERSOLD')

            # Overbought (potential short entry)
            if rsi > 70:
                signals.append(f'{tf}_OVERBOUGHT')

        if len(signals) == 0:
            return 'NO_SIGNAL'

        return '_'.join(signals[:2])  # Max 2 señales

    def _build_structure_context(self, tf_data: Dict) -> str:
        """
        Construye descripción de la estructura del mercado
        """
        parts = []

        if '1d' in tf_data:
            daily_mom = tf_data['1d'].get('momentum', 'NEUTRAL')
            daily_phase = tf_data['1d'].get('phase', 'CONSOLIDATION')
            parts.append(f"Daily: {daily_mom} {daily_phase}")

        if '4h' in tf_data:
            h4_mom = tf_data['4h'].get('momentum', 'NEUTRAL')
            h4_phase = tf_data['4h'].get('phase', 'CONSOLIDATION')
            parts.append(f"4H: {h4_mom} {h4_phase}")

        if '1h' in tf_data:
            h1_mom = tf_data['1h'].get('momentum', 'NEUTRAL')
            parts.append(f"1H: {h1_mom}")

        return ' | '.join(parts) if parts else 'No structure data'

    def _calculate_confidence(self, alignment: int, opportunity: int,
                             risk_factors: List[str]) -> float:
        """
        Calcula confianza general (0.0-1.0)
        """
        # Base confidence from alignment
        base = alignment / 100.0

        # Adjust by opportunity
        base = (base + opportunity / 100.0) / 2

        # Penalize by risk factors
        penalty = len(risk_factors) * 0.1
        base -= penalty

        return max(0.0, min(1.0, base))

    def _extract_timeframe_details(self, tf_data: Dict) -> Dict:
        """
        Extrae detalles clave de cada timeframe para Claude
        """
        details = {}

        for tf, data in tf_data.items():
            indicators = data.get('indicators', {})
            details[tf] = {
                'rsi': indicators.get('rsi', 50),
                'momentum': data.get('momentum', 'NEUTRAL'),
                'phase': data.get('phase', 'CONSOLIDATION'),
                'volatility': indicators.get('volatility', 0),
                'ema_alignment': 'BULLISH' if indicators.get('ema_fast', 0) > indicators.get('ema_slow', 0) else 'BEARISH'
            }

        return details

    def _empty_correlation(self) -> Dict:
        """Retorna correlación vacía"""
        return {
            'alignment_score': 50,
            'primary_direction': 'NEUTRAL',
            'confidence': 0.0,
            'volatility_context': 'MODERATE',
            'opportunity_score': 0,
            'risk_factors': ['NO_DATA'],
            'entry_recommendation': 'WAIT_NO_DATA',
            'structure_context': 'No data available',
            'timeframe_details': {}
        }
