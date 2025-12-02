#!/usr/bin/env python3
"""
TRAD Bot - Candle Pattern Recognition
Detección de patrones de velas para Price Action
"""

import numpy as np
from typing import Tuple, Optional

class CandlePatterns:
    """Detector de patrones de velas para scalping"""

    @staticmethod
    def get_candle_info(opens: np.ndarray, highs: np.ndarray,
                       lows: np.ndarray, closes: np.ndarray) -> list:
        """
        Extraer información de velas
        Retorna: [{tipo, color, tamaño, wick_superior, wick_inferior}, ...]
        """
        candles = []

        for i in range(len(opens)):
            o = opens[i]
            h = highs[i]
            l = lows[i]
            c = closes[i]

            # Color (verde=1, rojo=-1)
            color = 1 if c >= o else -1

            # Tamaño del cuerpo
            body_size = abs(c - o)

            # Wicks (mechas)
            wick_up = h - max(o, c)
            wick_down = min(o, c) - l

            # Tamaño total de la vela
            total_size = h - l

            candles.append({
                'index': i,
                'open': o,
                'high': h,
                'low': l,
                'close': c,
                'color': color,  # 1=verde, -1=rojo
                'body_size': body_size,
                'wick_up': wick_up,
                'wick_down': wick_down,
                'total_size': total_size,
                'type': None  # Se llena después
            })

        return candles

    @staticmethod
    def detect_consecutive_greens(candles: list, count: int = 3) -> Tuple[bool, int]:
        """
        Detectar N velas verdes consecutivas
        Retorna: (encontrado, índice_última_vela)
        """
        if len(candles) < count:
            return False, -1

        # Revisar últimas N velas
        for i in range(len(candles) - count, len(candles) - 1):
            if all(candles[j]['color'] == 1 for j in range(i, i + count)):
                return True, i + count - 1

        return False, -1

    @staticmethod
    def detect_consecutive_reds(candles: list, count: int = 3) -> Tuple[bool, int]:
        """
        Detectar N velas rojas consecutivas
        Retorna: (encontrado, índice_última_vela)
        """
        if len(candles) < count:
            return False, -1

        # Revisar últimas N velas
        for i in range(len(candles) - count, len(candles) - 1):
            if all(candles[j]['color'] == -1 for j in range(i, i + count)):
                return True, i + count - 1

        return False, -1

    @staticmethod
    def detect_higher_high_pattern(candles: list) -> Tuple[bool, str]:
        """
        Detectar patrón: Vela cierra por encima del máximo anterior
        Usado para COMPRA (LONG)
        """
        if len(candles) < 2:
            return False, "insufficient_data"

        prev_high = candles[-2]['high']
        curr_close = candles[-1]['close']

        if curr_close > prev_high:
            return True, "higher_high"

        return False, "no_pattern"

    @staticmethod
    def detect_lower_low_pattern(candles: list) -> Tuple[bool, str]:
        """
        Detectar patrón: Vela cierra por debajo del mínimo anterior
        Usado para VENTA (SHORT)
        """
        if len(candles) < 2:
            return False, "insufficient_data"

        prev_low = candles[-2]['low']
        curr_close = candles[-1]['close']

        if curr_close < prev_low:
            return True, "lower_low"

        return False, "no_pattern"

    @staticmethod
    def detect_bullish_entry(candles: list) -> Tuple[bool, str, dict]:
        """
        Detectar entrada BULLISH (LONG)
        Condiciones FIXED v3.4.2:
        - 2-3 velas verdes consecutivas (REQUIRED)
        - Última vela es VERDE (closing > opening) (REQUIRED)

        REMOVED: Higher high requirement (was too restrictive in consolidation)
        RSI + EMA filters will handle bad entries at strategy level
        """

        if len(candles) < 3:
            print(f"[BULLISH] FAILED: insufficient_data (len={len(candles)})")
            return False, "insufficient_data", {}

        # Verificar 2-3 velas verdes
        greens_found, green_idx = CandlePatterns.detect_consecutive_greens(candles, count=2)
        if not greens_found:
            last3 = candles[-3:] if len(candles) >= 3 else candles
            colors = [c['color'] for c in last3]
            print(f"[BULLISH] FAILED: no_greens | Last 3 colors: {colors}")
            return False, "no_greens", {}

        # FIXED: Última vela debe ser verde (cierre > apertura)
        last_candle = candles[-1]
        if last_candle['color'] != 1:  # Not green
            print(f"[BULLISH] FAILED: last_candle_not_green | Color:{last_candle['color']} O:{last_candle['open']:.2f} C:{last_candle['close']:.2f}")
            return False, "last_candle_not_green", {}

        prev_candle = candles[-2]

        confirmation_data = {
            'pattern': 'bullish_entry',
            'greens_count': 2,
            'body_strength': last_candle['body_size'] / last_candle['total_size'] if last_candle['total_size'] > 0 else 0,
            'close_vs_prev_open': last_candle['close'] - prev_candle['open'],
            'price': last_candle['close']
        }

        print(f"[BULLISH] SUCCESS: detected | Price:{last_candle['close']:.2f}")
        return True, "bullish_entry_detected", confirmation_data

    @staticmethod
    def detect_bearish_entry(candles: list) -> Tuple[bool, str, dict]:
        """
        Detectar entrada BEARISH (SHORT)
        Condiciones FIXED v3.4.2:
        - 2-3 velas rojas consecutivas (REQUIRED)
        - Última vela es ROJA (closing < opening) (REQUIRED)

        REMOVED: Lower low requirement (was too restrictive in consolidation)
        RSI + EMA filters will handle bad entries at strategy level
        """

        if len(candles) < 3:
            print(f"[BEARISH] FAILED: insufficient_data (len={len(candles)})")
            return False, "insufficient_data", {}

        # Verificar 2-3 velas rojas
        reds_found, red_idx = CandlePatterns.detect_consecutive_reds(candles, count=2)
        if not reds_found:
            last3 = candles[-3:] if len(candles) >= 3 else candles
            colors = [c['color'] for c in last3]
            print(f"[BEARISH] FAILED: no_reds | Last 3 colors: {colors}")
            return False, "no_reds", {}

        # FIXED: Última vela debe ser roja (cierre < apertura)
        last_candle = candles[-1]
        if last_candle['color'] != -1:  # Not red
            print(f"[BEARISH] FAILED: last_candle_not_red | Color:{last_candle['color']} O:{last_candle['open']:.2f} C:{last_candle['close']:.2f}")
            return False, "last_candle_not_red", {}

        prev_candle = candles[-2]

        confirmation_data = {
            'pattern': 'bearish_entry',
            'reds_count': 2,
            'body_strength': last_candle['body_size'] / last_candle['total_size'] if last_candle['total_size'] > 0 else 0,
            'close_vs_prev_open': prev_candle['open'] - last_candle['close'],
            'price': last_candle['close']
        }

        print(f"[BEARISH] SUCCESS: detected | Price:{last_candle['close']:.2f}")
        return True, "bearish_entry_detected", confirmation_data

    @staticmethod
    def is_strong_candle(candle: dict, body_threshold: float = 0.6) -> bool:
        """
        Verificar si una vela es "fuerte"
        Cuerpo debe ser >= 60% del tamaño total (baja influencia de wicks)
        """
        if candle['total_size'] == 0:
            return False

        body_ratio = candle['body_size'] / candle['total_size']
        return body_ratio >= body_threshold

    @staticmethod
    def detect_breakout(candles: list, resistance: float, support: float) -> Tuple[str, Optional[float]]:
        """
        Detectar ruptura de nivel (soporte/resistencia)
        Retorna: (tipo_ruptura, precio)
        """
        if len(candles) < 1:
            return "none", None

        last_close = candles[-1]['close']

        if last_close > resistance:
            return "bullish_breakout", last_close
        elif last_close < support:
            return "bearish_breakout", last_close

        return "none", None

def print_candle_analysis(candles: list):
    """Imprimir análisis de velas (para debugging)"""
    if not candles:
        return

    for candle in candles[-5:]:
        color = "🟢" if candle['color'] == 1 else "🔴"
        print(f"{color} O:{candle['open']:.2f} H:{candle['high']:.2f} L:{candle['low']:.2f} C:{candle['close']:.2f} | Body:{candle['body_size']:.2f}")
