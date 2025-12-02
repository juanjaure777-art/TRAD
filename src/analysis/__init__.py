"""
Market analysis modules - Crecetrader implementation with structure detection and scenario analysis
Full integration of Esteban Pérez methodology
"""

from .market_analyzer import MarketAnalyzer, Volatility, Momentum
from .crecetrader import CrecetraderAnalysis, CandleLocation, CandleType, VolatilityPhase
from .referentes_calculator import ReferentesCalculator, ReferenteType
from .structure_change_detector import StructureChangeDetector, StructurePhase
from .scenario_manager import ScenarioManager, Scenario
from .bitcoin_context import BitcoinContext, FearGreedLevel
from .audit_crecetrader import CrecetraderAudit
from .multitimeframe_validator import (
    MultiTimeframeValidator,
    MultiTimeframeAnalysis,
    TimeframeSignal,
    TimeframeAlignment
)

__all__ = [
    # Market Analysis
    'MarketAnalyzer', 'Volatility', 'Momentum',
    # Crecetrader Price Action
    'CrecetraderAnalysis', 'CandleLocation', 'CandleType', 'VolatilityPhase',
    # Referentes (Support/Resistance)
    'ReferentesCalculator', 'ReferenteType',
    # Structure Change Detection (Core Esteban concept)
    'StructureChangeDetector', 'StructurePhase',
    # Scenario Management (A/B/C logic)
    'ScenarioManager', 'Scenario',
    # Bitcoin-specific context and Fear-Greed
    'BitcoinContext', 'FearGreedLevel',
    # Multi-Timeframe Correlation
    'MultiTimeframeValidator', 'MultiTimeframeAnalysis', 'TimeframeSignal', 'TimeframeAlignment',
    # Audit tools
    'CrecetraderAudit'
]
