#!/usr/bin/env python3
"""
MULTI-TIMEFRAME DATA LOADER
============================
Descarga datos de OHLCV para múltiples timeframes simultáneamente.
Usa la misma conexión CCXT para eficiencia.
Timeframes: 1m, 5m, 15m, 1h, 4h, 1d
"""

import ccxt
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class MultiTimeframeDataLoader:
    """
    Carga datos OHLCV de múltiples timeframes simultáneamente
    """

    TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h', '1d']

    def __init__(self, exchange: ccxt.Exchange, symbol: str = 'BTC/USDT'):
        self.exchange = exchange
        self.symbol = symbol
        self.cache = {}  # Cache para evitar llamadas API repetidas

    def load_all_timeframes(self, limit: int = 100) -> Dict[str, np.ndarray]:
        """
        Carga OHLCV de todos los timeframes

        Returns:
            Dict con estructura:
            {
                '1m': np.array([[timestamp, o, h, l, c, v], ...]),
                '5m': np.array([[timestamp, o, h, l, c, v], ...]),
                ...
            }
        """
        result = {}

        for tf in self.TIMEFRAMES:
            try:
                ohlcv = self._fetch_ohlcv(tf, limit)
                if ohlcv is not None and len(ohlcv) > 0:
                    result[tf] = np.array(ohlcv)
                    logger.debug(f"✓ Loaded {len(ohlcv)} candles for {tf}")
                else:
                    logger.warning(f"⚠ No data for {tf}")
                    result[tf] = np.array([])
            except Exception as e:
                logger.error(f"✗ Error loading {tf}: {e}")
                result[tf] = np.array([])

        return result

    def _fetch_ohlcv(self, timeframe: str, limit: int) -> Optional[List]:
        """Fetch OHLCV con retry logic"""
        max_retries = 3

        for attempt in range(max_retries):
            try:
                ohlcv = self.exchange.fetch_ohlcv(
                    self.symbol,
                    timeframe=timeframe,
                    limit=limit
                )
                return ohlcv
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.debug(f"Retry {attempt+1}/{max_retries} for {timeframe}")
                    continue
                else:
                    raise e

        return None

    def calculate_indicators(self, ohlcv: np.ndarray, timeframe: str) -> Dict:
        """
        Calcula indicadores técnicos para un timeframe

        Returns:
            {
                'rsi': float,
                'ema_fast': float,
                'ema_slow': float,
                'atr': float,
                'volatility': float,
                'last_close': float,
                'support': float,
                'resistance': float
            }
        """
        if len(ohlcv) < 20:
            return self._empty_indicators()

        closes = ohlcv[:, 4]
        highs = ohlcv[:, 2]
        lows = ohlcv[:, 3]

        # RSI(7)
        rsi = self._calculate_rsi(closes, period=7)

        # EMA
        ema_fast = self._calculate_ema(closes, period=9)
        ema_slow = self._calculate_ema(closes, period=21)

        # ATR
        atr = self._calculate_atr(highs, lows, closes, period=14)

        # Volatility (ATR/Price ratio)
        last_close = float(closes[-1])
        volatility = (atr / last_close * 100) if last_close > 0 else 0

        # Support/Resistance (simple: recent lows/highs)
        support = float(np.min(lows[-20:]))
        resistance = float(np.max(highs[-20:]))

        return {
            'rsi': rsi,
            'ema_fast': ema_fast,
            'ema_slow': ema_slow,
            'atr': atr,
            'volatility': volatility,
            'last_close': last_close,
            'support': support,
            'resistance': resistance,
            'timeframe': timeframe
        }

    def _calculate_rsi(self, prices: np.ndarray, period: int = 7) -> float:
        """Calcula RSI"""
        if len(prices) < period + 1:
            return 50.0

        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return float(rsi)

    def _calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """Calcula EMA"""
        if len(prices) < period:
            return float(prices[-1])

        multiplier = 2 / (period + 1)
        ema = float(prices[0])

        for price in prices[1:]:
            ema = (price - ema) * multiplier + ema

        return ema

    def _calculate_atr(self, highs: np.ndarray, lows: np.ndarray,
                      closes: np.ndarray, period: int = 14) -> float:
        """Calcula Average True Range"""
        if len(highs) < period + 1:
            return 0.0

        tr_list = []
        for i in range(1, len(highs)):
            h_l = highs[i] - lows[i]
            h_pc = abs(highs[i] - closes[i-1])
            l_pc = abs(lows[i] - closes[i-1])
            tr = max(h_l, h_pc, l_pc)
            tr_list.append(tr)

        atr = np.mean(tr_list[-period:])
        return float(atr)

    def _empty_indicators(self) -> Dict:
        """Retorna indicadores vacíos"""
        return {
            'rsi': 50.0,
            'ema_fast': 0.0,
            'ema_slow': 0.0,
            'atr': 0.0,
            'volatility': 0.0,
            'last_close': 0.0,
            'support': 0.0,
            'resistance': 0.0
        }

    def get_timeframe_analysis(self, timeframe: str, limit: int = 100) -> Dict:
        """
        Obtiene análisis completo de un timeframe

        Returns:
            {
                'ohlcv': np.ndarray,
                'indicators': dict,
                'momentum': str (BULLISH/BEARISH/NEUTRAL),
                'phase': str (TRENDING/REVERSAL/CONSOLIDATION)
            }
        """
        try:
            ohlcv = self._fetch_ohlcv(timeframe, limit)
            if ohlcv is None or len(ohlcv) < 20:
                return self._empty_analysis(timeframe)

            ohlcv_array = np.array(ohlcv)
            indicators = self.calculate_indicators(ohlcv_array, timeframe)

            # Determinar momentum
            momentum = self._determine_momentum(indicators)

            # Determinar fase
            phase = self._determine_phase(indicators, ohlcv_array)

            return {
                'ohlcv': ohlcv_array,
                'indicators': indicators,
                'momentum': momentum,
                'phase': phase,
                'timeframe': timeframe
            }

        except Exception as e:
            logger.error(f"Error analyzing {timeframe}: {e}")
            return self._empty_analysis(timeframe)

    def _determine_momentum(self, indicators: Dict) -> str:
        """Determina momentum basado en indicadores"""
        rsi = indicators['rsi']
        ema_fast = indicators['ema_fast']
        ema_slow = indicators['ema_slow']

        # EMA alignment
        if ema_fast > ema_slow * 1.002:  # 0.2% above
            return 'BULLISH'
        elif ema_fast < ema_slow * 0.998:  # 0.2% below
            return 'BEARISH'
        else:
            return 'NEUTRAL'

    def _determine_phase(self, indicators: Dict, ohlcv: np.ndarray) -> str:
        """Determina fase del mercado"""
        rsi = indicators['rsi']
        volatility = indicators['volatility']

        # RSI extremes = potential reversal
        if rsi < 30 or rsi > 70:
            return 'REVERSAL'

        # High volatility = trending
        if volatility > 2.0:
            return 'TRENDING'

        # Low volatility = consolidation
        return 'CONSOLIDATION'

    def _empty_analysis(self, timeframe: str) -> Dict:
        """Retorna análisis vacío"""
        return {
            'ohlcv': np.array([]),
            'indicators': self._empty_indicators(),
            'momentum': 'NEUTRAL',
            'phase': 'CONSOLIDATION',
            'timeframe': timeframe
        }
