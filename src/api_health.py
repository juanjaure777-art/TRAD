"""
API Health Check & Optimizer para TRAD Bot v3.6
Resuelve bloqueos en llamadas a Binance con timeouts, retry, y caché
"""

import time
import ccxt
from typing import Tuple, Optional, Dict, Any
import logging
from datetime import datetime, timedelta, timezone
import numpy as np

class APIHealthCheck:
    """Verifica y optimiza la salud de la conexión API"""

    def __init__(self, exchange, max_retries: int = 3, timeout_seconds: int = 10):
        self.exchange = exchange
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.last_successful_call = datetime.now()
        self.consecutive_failures = 0
        self.data_cache = {}

    def is_api_healthy(self) -> bool:
        """Verifica rápidamente si la API responde"""
        try:
            # Test simple: obtener balance (muy rápido)
            self.exchange.request_timeout = self.timeout_seconds * 1000  # milliseconds
            self.exchange.fetch_balance()
            self.consecutive_failures = 0
            self.last_successful_call = datetime.now(timezone.utc)
            return True
        except Exception as e:
            self.consecutive_failures += 1
            print(f"⚠️ API HEALTH CHECK FAILED (attempt {self.consecutive_failures}): {type(e).__name__}")
            return False

    def wait_for_api(self, max_wait_seconds: int = 30) -> bool:
        """Espera a que la API esté disponible (con backoff)"""
        start_time = time.time()
        wait_time = 1

        print(f"🔄 Esperando API... (timeout: {max_wait_seconds}s)")
        while time.time() - start_time < max_wait_seconds:
            if self.is_api_healthy():
                print(f"✅ API disponible después de {time.time() - start_time:.1f}s")
                return True

            print(f"   ⏳ Reintentando en {wait_time}s...")
            time.sleep(wait_time)
            wait_time = min(wait_time * 2, 5)  # Backoff: max 5 segundos

        print(f"❌ API no respondió en {max_wait_seconds}s")
        return False

    def fetch_ohlcv_safe(self, symbol: str, timeframe: str, limit: int = 100) -> Optional[list]:
        """
        Fetch OHLCV con retry, timeout, y caché
        Retorna None si falla después de reintentos
        """
        cache_key = f"{symbol}_{timeframe}_{limit}"

        for attempt in range(self.max_retries):
            try:
                self.exchange.request_timeout = self.timeout_seconds * 1000
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

                # Cache exitoso
                self.data_cache[cache_key] = {
                    'data': ohlcv,
                    'timestamp': datetime.now(timezone.utc)
                }
                self.consecutive_failures = 0

                print(f"✅ fetch_ohlcv({symbol}, {timeframe}) OK - {len(ohlcv)} candles")
                return ohlcv

            except ccxt.RequestTimeout:
                print(f"⏱️ TIMEOUT en {symbol}/{timeframe} (attempt {attempt+1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    wait = (attempt + 1) * 2
                    print(f"   Esperando {wait}s antes de reintentar...")
                    time.sleep(wait)

            except ccxt.NetworkError as e:
                print(f"🌐 Network error: {e} (attempt {attempt+1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep((attempt + 1) * 2)

            except ccxt.AuthenticationError as e:
                # CRITICAL FIX: AuthenticationError should stop bot immediately
                print(f"❌ AUTHENTICATION ERROR: Invalid API keys - {e}")
                print(f"🛑 Bot cannot continue without valid credentials")
                import sys
                sys.exit(1)

            except Exception as e:
                print(f"❌ Error desconocido: {type(e).__name__}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep((attempt + 1) * 2)

        # Si todo falla, usar caché
        if cache_key in self.data_cache:
            cached = self.data_cache[cache_key]
            age_seconds = (datetime.now() - cached['timestamp']).total_seconds()
            print(f"⚠️ Usando CACHÉ para {symbol}/{timeframe} (edad: {age_seconds:.0f}s)")
            return cached['data']

        print(f"❌ {symbol}/{timeframe} FALLÓ después de {self.max_retries} intentos y sin caché")
        return None

    def get_status(self) -> Dict[str, Any]:
        """Retorna estado de la API"""
        return {
            'healthy': self.consecutive_failures < 3,
            'consecutive_failures': self.consecutive_failures,
            'last_success': self.last_successful_call.isoformat(),
            'cache_entries': len(self.data_cache),
            'timeout_seconds': self.timeout_seconds
        }


def inject_api_health(bot_instance):
    """
    Inyecta APIHealthCheck en la instancia del bot
    Reemplaza _fetch_ohlcv con versión segura
    """
    # Crear health check
    bot_instance.api_health = APIHealthCheck(
        bot_instance.exchange,
        max_retries=3,
        timeout_seconds=10
    )

    # Reemplazar método _fetch_ohlcv
    original_fetch = bot_instance._fetch_ohlcv

    def _fetch_ohlcv_safe(timeframe: str = None, limit: int = 100) -> tuple:
        """Versión segura de _fetch_ohlcv con retry y timeout"""
        if timeframe is None:
            timeframe = bot_instance.timeframe

        # Intentar fetch
        ohlcv = bot_instance.api_health.fetch_ohlcv_safe(
            bot_instance.symbol,
            timeframe,
            limit=limit
        )

        if ohlcv is None:
            print(f"⚠️ Retornando datos vacíos para {timeframe} - API no disponible")
            return (np.array([]), np.array([]), np.array([]), np.array([]), np.array([]))

        # Procesar como lo hace el original - EXTRAER 5 ELEMENTOS
        # OHLCV: [[timestamp, open, high, low, close, volume], ...]
        opens = np.array([x[1] for x in ohlcv])
        highs = np.array([x[2] for x in ohlcv])
        lows = np.array([x[3] for x in ohlcv])
        closes = np.array([x[4] for x in ohlcv])
        volumes = np.array([x[5] for x in ohlcv])

        return (opens, highs, lows, closes, volumes)

    # Monkey patch
    bot_instance._fetch_ohlcv = _fetch_ohlcv_safe

    print("✅ APIHealthCheck inyectado en bot")
    return bot_instance
