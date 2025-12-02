#!/usr/bin/env python3
"""
MULTITIMEFRAME ADAPTER - Integración con el bot actual
=======================================================
Adapta el análisis multi-timeframe para usarse con el bot existente.
Mantiene compatibilidad backward mientras agrega análisis jerárquico completo.

USO SIMPLE:
    adapter = MultitimeframeAdapter(exchange, symbol='BTC/USDT')
    context = adapter.load_and_analyze()
    # Pasar context a GatekeeperV2
"""

from typing import Dict, Optional
import ccxt
import logging
from .multi_timeframe_data_loader import MultiTimeframeDataLoader
from .multitimeframe_correlator import MultitimeframeCorrelator

logger = logging.getLogger(__name__)


class MultitimeframeAdapter:
    """
    Adapter que integra DataLoader + Correlator
    API simple para el bot
    """

    def __init__(self, exchange: ccxt.Exchange, symbol: str = 'BTC/USDT'):
        self.exchange = exchange
        self.symbol = symbol

        # Inicializar módulos
        self.loader = MultiTimeframeDataLoader(exchange, symbol)
        self.correlator = MultitimeframeCorrelator()

        logger.info(f"✅ MultitimeframeAdapter initialized for {symbol}")

    def load_and_analyze(self, limit: int = 100) -> Dict:
        """
        Carga datos de todos los timeframes, calcula indicadores,
        y correlaciona todo en un solo llamado.

        Returns:
            Dict con toda la información lista para GatekeeperV2:
            {
                'multitimeframe': {
                    'daily': {'rsi': ..., 'momentum': ..., 'phase': ...},
                    '4h': {...},
                    '1h': {...},
                    '15m': {...},
                    '5m': {...},
                    '1m': {...}
                },
                'alignment_score': 0-100,
                'primary_direction': 'BULLISH'|'BEARISH'|'NEUTRAL',
                'volatility_context': 'LOW'|'MODERATE'|'HIGH',
                'opportunity_score': 0-100,
                'risk_factors': [str],
                'entry_recommendation': str,
                'structure_context': str,
                'confidence': 0.0-1.0
            }
        """
        try:
            # 1. Cargar datos OHLCV de todos los timeframes
            logger.debug("Loading multi-timeframe OHLCV data...")
            all_ohlcv = self.loader.load_all_timeframes(limit)

            # 2. Calcular análisis individual de cada timeframe
            logger.debug("Analyzing each timeframe...")
            timeframe_analyses = {}

            for tf in MultiTimeframeDataLoader.TIMEFRAMES:
                analysis = self.loader.get_timeframe_analysis(tf, limit)
                timeframe_analyses[tf] = analysis

            # 3. Correlacionar todos los timeframes
            logger.debug("Correlating timeframes...")
            correlation = self.correlator.correlate(timeframe_analyses)

            # 4. Compilar contexto completo para GatekeeperV2
            complete_context = self._build_complete_context(
                timeframe_analyses,
                correlation
            )

            logger.info(
                f"✓ MTF Analysis: Direction={complete_context['primary_direction']} "
                f"Alignment={complete_context['alignment_score']}% "
                f"Opportunity={complete_context['opportunity_score']}/100"
            )

            return complete_context

        except Exception as e:
            logger.error(f"Error in load_and_analyze: {e}")
            return self._empty_context()

    def _build_complete_context(self, tf_analyses: Dict, correlation: Dict) -> Dict:
        """
        Construye contexto completo combinando análisis + correlación
        """
        # Extraer detalles simplificados de cada timeframe para Claude
        multitimeframe_details = {}

        for tf, analysis in tf_analyses.items():
            indicators = analysis.get('indicators', {})
            multitimeframe_details[tf] = {
                'rsi': round(indicators.get('rsi', 50), 2),
                'momentum': analysis.get('momentum', 'NEUTRAL'),
                'phase': analysis.get('phase', 'CONSOLIDATION'),
                'volatility': round(indicators.get('volatility', 0), 2),
                'last_close': round(indicators.get('last_close', 0), 2),
                'support': round(indicators.get('support', 0), 2),
                'resistance': round(indicators.get('resistance', 0), 2)
            }

        # Combinar todo
        return {
            # Multi-timeframe details
            'multitimeframe': multitimeframe_details,

            # Correlation results
            'alignment_score': correlation['alignment_score'],
            'primary_direction': correlation['primary_direction'],
            'confidence': correlation['confidence'],
            'volatility_context': correlation['volatility_context'],
            'opportunity_score': correlation['opportunity_score'],
            'risk_factors': correlation['risk_factors'],
            'entry_recommendation': correlation['entry_recommendation'],
            'structure_context': correlation['structure_context'],

            # Metadata
            'timeframe_count': len(tf_analyses),
            'symbol': self.symbol
        }

    def get_quick_signal(self) -> Optional[str]:
        """
        Obtiene señal rápida (LONG/SHORT/WAIT) sin análisis completo
        Útil para monitoreo continuo lightweight
        """
        try:
            context = self.load_and_analyze(limit=50)  # Menos velas = más rápido

            recommendation = context.get('entry_recommendation', 'WAIT')

            if 'STRONG_LONG' in recommendation:
                return 'LONG'
            elif 'STRONG_SHORT' in recommendation:
                return 'SHORT'
            elif 'MODERATE_LONG' in recommendation:
                return 'LONG'
            elif 'MODERATE_SHORT' in recommendation:
                return 'SHORT'
            else:
                return 'WAIT'

        except Exception as e:
            logger.error(f"Error in get_quick_signal: {e}")
            return 'WAIT'

    def get_alignment_summary(self) -> str:
        """
        Retorna resumen legible de la alineación actual
        Para logging y debugging
        """
        try:
            context = self.load_and_analyze(limit=50)

            direction = context.get('primary_direction', 'NEUTRAL')
            alignment = context.get('alignment_score', 0)
            opportunity = context.get('opportunity_score', 0)
            risks = context.get('risk_factors', [])

            summary = f"Direction: {direction} | Alignment: {alignment}% | Opportunity: {opportunity}/100"

            if len(risks) > 0:
                summary += f" | Risks: {len(risks)}"

            return summary

        except Exception as e:
            return f"Error: {e}"

    def should_enter_now(self, gatekeeper_level: int = 3) -> bool:
        """
        Decisión rápida: ¿Debería entrar AHORA?

        Args:
            gatekeeper_level: 1-5 (permissive to selective)

        Returns:
            True si debería considerar entrada, False si esperar
        """
        try:
            context = self.load_and_analyze(limit=50)

            alignment = context.get('alignment_score', 0)
            opportunity = context.get('opportunity_score', 0)
            risks = context.get('risk_factors', [])

            # Thresholds basados en gatekeeper level
            if gatekeeper_level == 1:
                # Permissive
                return alignment >= 50 and opportunity >= 30 and len(risks) < 5

            elif gatekeeper_level == 2:
                return alignment >= 60 and opportunity >= 40 and len(risks) < 4

            elif gatekeeper_level == 3:
                # Balanced (default)
                return alignment >= 70 and opportunity >= 50 and len(risks) < 3

            elif gatekeeper_level == 4:
                # Selective
                return alignment >= 80 and opportunity >= 60 and len(risks) < 2

            else:  # Level 5
                # Maximum selective
                return alignment >= 85 and opportunity >= 70 and len(risks) == 0

        except Exception as e:
            logger.error(f"Error in should_enter_now: {e}")
            return False

    def _empty_context(self) -> Dict:
        """Contexto vacío para casos de error"""
        return {
            'multitimeframe': {},
            'alignment_score': 0,
            'primary_direction': 'NEUTRAL',
            'confidence': 0.0,
            'volatility_context': 'MODERATE',
            'opportunity_score': 0,
            'risk_factors': ['ERROR_LOADING_DATA'],
            'entry_recommendation': 'WAIT_ERROR',
            'structure_context': 'Error loading data',
            'timeframe_count': 0,
            'symbol': self.symbol
        }

    def print_current_analysis(self):
        """
        Imprime análisis actual en formato legible
        Para debugging
        """
        context = self.load_and_analyze()

        print("\n" + "="*80)
        print(f"MULTI-TIMEFRAME ANALYSIS - {self.symbol}")
        print("="*80)
        print(f"Direction:    {context['primary_direction']}")
        print(f"Alignment:    {context['alignment_score']}%")
        print(f"Opportunity:  {context['opportunity_score']}/100")
        print(f"Confidence:   {context['confidence']:.2f}")
        print(f"Volatility:   {context['volatility_context']}")
        print(f"Structure:    {context['structure_context']}")
        print(f"Recommendation: {context['entry_recommendation']}")

        if len(context['risk_factors']) > 0:
            print(f"\n⚠️  Risk Factors ({len(context['risk_factors'])}):")
            for risk in context['risk_factors']:
                print(f"  - {risk}")

        print("\nTimeframe Details:")
        for tf, details in context.get('multitimeframe', {}).items():
            print(f"  {tf:>4}: RSI={details['rsi']:>5.1f} | "
                  f"{details['momentum']:>8} | "
                  f"{details['phase']:>15} | "
                  f"Vol={details['volatility']:.2f}%")

        print("="*80 + "\n")
