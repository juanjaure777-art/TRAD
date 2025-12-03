#!/usr/bin/env python3
"""
TRAD Bot v3.5+ - Conscious Crecetrader Implementation
Hybrid Strategy (RSI + Price Action + Crecetrader Methodology)

CONSCIOUSNESS LEVEL: FULL CRECETRADER INTEGRATION
This bot now applies the COMPLETE Crecetrader methodology:

T+Z+V Formula (Core Trading Equation):
- T (Tendencia): Clear trend identification validated before entry
- Z (Zonas): Support/Resistance levels calculated (historical + Fibonacci)
- V (Vacío): Risk/Reward ratio minimum 2:1 ENFORCED

CHANGELOG v1.0 → v3.5+:
- v1.0: RSI simple (< 35)
- v2.0: RSI con multi-confirmación (RSI + EMA + Stochastic)
- v3.0: HYBRID - RSI (filtro) + Price Action + Crecetrader (contexto)
- v3.5: ✨ CONSCIOUS - Full T+Z+V validation, Fibonacci referentes, proper SL/TP placement
"""

import json
import time
import os
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict
import ccxt
from anthropic import Anthropic
from dotenv import load_dotenv

# Timezone configuration for Argentina
try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Fallback for Python < 3.9
    from datetime import timezone as tz
    ZoneInfo = None

from src.strategy.indicators import TechnicalIndicators
from src.strategy.candle_patterns import CandlePatterns
from src.strategy.hybrid import HybridStrategy
from src.trading.hybrid_gatekeeper_adapter import HybridGatekeeperAdapter
from src.trading.sessions import (
    get_active_session,
    get_session_by_name,
    is_off_hours,
    is_in_opening_hour,
    get_session_status
)
from src.strategy.modes import PermissivenessManager, TradingMode, MODES_CONFIG
from src.trading.recovery import StateRecovery, PositionState, EmergencyClosureManager
from src.monitoring.trade_logger import get_trade_logger
from src.constants import (
    DEAD_PRICE_THRESHOLD_PCT,
    DEAD_VOLUME_RATIO,
    DEAD_PRICE_COUNTER_MAX,
    DEAD_VOLUME_COUNTER_MAX,
    TRAILING_STOP_PCT,
    TRADE_COOLDOWN_SECONDS,
    TP_PARTIAL_FILL
)
from src.risk_management.risk_manager import RiskManager
from src.strategy.dynamic_mode_manager import DynamicModeManager
from src.analysis.market_analyzer import MarketAnalyzer
from src.analysis.referentes_calculator import ReferentesCalculator
from src.strategy.tzv_validator import TZVValidator
from src.analysis.multitimeframe_validator import MultiTimeframeValidator
# NEW v3.6+ - Multi-Timeframe Continuous Monitoring
from src.analysis.multi_timeframe_data_loader import MultiTimeframeDataLoader
from src.analysis.multitimeframe_correlator import MultitimeframeCorrelator
from src.analysis.multitimeframe_adapter import MultitimeframeAdapter
from src.analysis.multitimeframe_audit import MultitimeframeAudit

# Load environment variables from .env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

# Helper function to get current time in Argentina timezone
def get_local_time():
    """Get current time in America/Argentina/Buenos_Aires timezone"""
    try:
        if ZoneInfo:
            # Python 3.9+ with zoneinfo
            return datetime.now(ZoneInfo("America/Argentina/Buenos_Aires"))
    except Exception:
        pass

    # Fallback: use UTC-3 (Argentina standard time)
    try:
        tz_offset = timezone(timedelta(hours=-3))
        return datetime.now(tz_offset)
    except Exception:
        # Last resort: return local datetime (system timezone)
        return datetime.now()

class TRADBot_v3:
    """TRAD Bot v3.0 - Estrategia Híbrida Profesional"""

    def __init__(self, config_path: str = "config/config.json"):
        with open(config_path) as f:
            self.cfg = json.load(f)

        self.symbol = self.cfg['trading']['symbol']
        self.timeframe = self.cfg['trading']['timeframe']
        # Get mode from environment variable or config (env takes priority)
        self.mode = os.getenv('BOT_MODE', self.cfg.get('mode', 'testnet'))

        # Get API keys from environment variables (more secure than config.json)
        api_key = os.getenv('BINANCE_API_KEY') or self.cfg['exchange'].get('api_key')
        api_secret = os.getenv('BINANCE_API_SECRET') or self.cfg['exchange'].get('api_secret')

        if not api_key or not api_secret:
            raise ValueError("❌ API Keys no encontradas. Verifica .env o config.json")

        # Initialize exchange
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'testnet': self.mode == 'testnet',
            'enableRateLimit': True,
        })

        # Initialize Claude client (uses ANTHROPIC_API_KEY from env automatically)
        self.client = Anthropic()
        self.strategy = HybridStrategy(self.cfg)

        # NEW v3.4 - GatekeeperV2: Claude-based intelligent entry validation
        gatekeeper_level = 2  # PERMISSIVE (configurable: 1-5)
        self.gatekeeper_adapter = HybridGatekeeperAdapter(
            gatekeeper_level=gatekeeper_level,
            mode=self.mode
        )
        print(f"✅ GatekeeperV2 initialized - Level {gatekeeper_level} (PERMISSIVE)")

        self.position = None
        self.cycle_count = 0
        self.open_trades = {}

        # NEW v3.3 - Multi-Timezone Sessions
        self.active_session = None
        self.session_start_time = None

        # NEW v3.3 - Dead Trade Detection (OPTION 3: COMBINED price+volume)
        self.dead_price_counter = 0
        self.dead_volume_counter = 0
        self.price_history = []  # Last 15 candles for dead price detection
        self.volume_history = []  # Last 15 candles for dead volume detection
        self.trade_max_price = None  # For trailing stop tracking
        self.trade_max_price_time = None

        # NEW v3.3 - Partial position exits tracking
        self.position_tp1_closed = False
        self.position_tp2_closed = False
        self.trailing_stop_active = False
        self.trailing_stop_price = None

        # NEW v3.3 - METRICS TRACKING (CRITICAL for performance evaluation)
        self.trade_count = 0  # Total trades executed
        self.winning_trades = 0  # Number of profitable trades
        self.losing_trades = 0  # Number of unprofitable trades
        self.total_pnl = 0.0  # Cumulative P&L in %
        self.trades_log = []  # Store all trade details for analysis

        # Load order size from config (25 USDT)
        self.order_size_usdt = self.cfg['trading'].get('order_size_usdt', 25.0)
        self.leverage = self.cfg['trading'].get('leverage', 50.0)
        self.margin_mode = self.cfg['trading'].get('margin_mode', 'isolated')

        # NEW v3.3 - Dynamic Permissiveness Modes
        self.permissiveness_manager = PermissivenessManager()
        self.current_mode = TradingMode.BALANCED
        self.mode_last_logged = None
        self.mode_change_count = 0

        # CRITICAL FIX v3.4.1: Load permissiveness config and update strategy RSI thresholds
        self._load_permissiveness_config()
        self.strategy.update_mode_config(self.current_mode)

        # NEW v3.3 - Failure Recovery System
        self.recovery = StateRecovery(mode=self.mode)
        self.emergency_closure = EmergencyClosureManager(self.exchange, self.symbol, self.recovery)

        # NEW v3.4 - Trade Logger (CRITICAL for distinguishing signal detection from execution)
        self.trade_logger = get_trade_logger()
        print(f"✅ TradeLogger initialized - Detailed trade tracking ENABLED")

        # NEW v3.5 - Risk Manager & Dynamic Mode Manager Integration
        self.risk_manager = RiskManager(self.cfg)
        self.mode_manager = DynamicModeManager()
        print(f"✅ RiskManager initialized - Position limits & daily loss tracking ENABLED")
        print(f"✅ DynamicModeManager initialized - Automatic mode switching ENABLED")

        # NEW v3.5 - Market Analyzer for volatility & momentum (Crecetrader methodology)
        self.market_analyzer = MarketAnalyzer(lookback=20)
        print(f"✅ MarketAnalyzer initialized - Volatility & momentum calculation ENABLED")

        # NEW v3.5+ - Referentes Calculator (Historical + Fibonacci Crecetrader levels)
        self.referentes_calc = ReferentesCalculator(paa=None)  # PAA can be updated per asset

        # NEW v3.6 - Multi-Timeframe Correlation Validator (Daily + 4H + 1H)
        self.multitimeframe_validator = MultiTimeframeValidator()
        self.mtf_enabled = self.cfg.get('multitimeframe', {}).get('enabled', True)
        print(f"✅ MultiTimeframeValidator initialized - Professional correlation analysis ENABLED")
        print(f"✅ ReferentesCalculator initialized - Fibonacci + Historical referentes ENABLED")

        # NEW v3.5+ - T+Z+V Validator (Crecetrader core trading formula)
        self.tzv_validator = TZVValidator()
        print(f"✅ TZVValidator initialized - T+Z+V formula validation ENABLED")

        # NEW v3.6+ - Multi-Timeframe Adapter (CONTINUOUS 24/7 MONITORING)
        try:
            self.multitf_adapter = MultitimeframeAdapter(self.exchange, symbol=self.symbol)
            self.multitf_audit = MultitimeframeAudit()
            print(f"✅ MultitimeframeAdapter initialized - 6-timeframe hierarchical analysis (1m/5m/15m/1h/4h/1d)")
            print(f"✅ MultitimeframeAudit initialized - Data integrity & anomaly detection")
            print(f"🎯 OPERATIONAL MODE: Continuous 24/7 monitoring (NOT timeframe-bound)")
            print(f"   - Daily/4H/1H = CONTEXT (trend, structure)")
            print(f"   - 15m/5m/1m = ENTRY SIGNALS (execution)")
        except Exception as e:
            print(f"⚠️  MultitimeframeAdapter failed to initialize: {e}")
            self.multitf_adapter = None
            self.multitf_audit = None

    def _load_permissiveness_config(self):
        """NEW v3.3 - Load dynamic permissiveness mode from config file"""
        try:
            config_file = 'permissiveness_config.txt'
            if not os.path.exists(config_file):
                return  # File doesn't exist, use current mode

            with open(config_file) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    if line.startswith('MODE:'):
                        mode_num = int(line.split(':')[1].strip())
                        new_mode = TradingMode(mode_num)

                        # Log if mode changed
                        if new_mode != self.current_mode:
                            self.mode_change_count += 1
                            config = MODES_CONFIG[new_mode]
                            print(f"\n📊 MODE CHANGE #{self.mode_change_count}: {self.current_mode.value} → {new_mode.value}")
                            print(f"   {config.description}")
                            print(f"   RSI: < {config.rsi_lower} or > {config.rsi_upper} | MTF: {config.mtf_confirmations_needed}/3 | GateKeeper: {config.gate_keeper_required}")
                            self.current_mode = new_mode
                            # CRITICAL FIX v3.4.1: Update strategy RSI thresholds when mode changes
                            self.strategy.update_mode_config(new_mode)
                            self._log_event('MODE_CHANGE', mode=new_mode.value, change_num=self.mode_change_count)

                    elif line.startswith('AUTO_DETECT:'):
                        auto_detect = 'true' in line.lower()
                        self.permissiveness_manager.auto_detect = auto_detect

        except Exception as e:
            print(f"⚠️  Error loading permissiveness config: {e}")

    def _get_sleep_seconds(self) -> int:
        """
        NEW v3.6+: Return sleep interval for CONTINUOUS MONITORING

        El bot ya NO opera en un timeframe específico.
        Opera 24/7 buscando oportunidades cuando los timeframes alinean.

        Intervalo: 10 segundos
        - Permite detectar señales en 1m, 5m, 15m muy rápidamente
        - Daily/4H/1H se usan como CONTEXTO (no determina el ciclo)
        """
        return 10  # 10 segundos - monitoreo continuo AGRESIVO

    def _fetch_ohlcv(self, timeframe: str = None, limit: int = 100) -> tuple:
        """Fetch OHLCV data from exchange for specified timeframe"""
        if timeframe is None:
            timeframe = self.timeframe

        try:
            ohlcv = self.exchange.fetch_ohlcv(
                self.symbol,
                timeframe,
                limit=limit
            )
            closes = np.array([x[4] for x in ohlcv])
            highs = np.array([x[2] for x in ohlcv])
            lows = np.array([x[3] for x in ohlcv])
            opens = np.array([x[1] for x in ohlcv])
            volumes = np.array([x[5] for x in ohlcv])

            return opens, highs, lows, closes, volumes
        except Exception as e:
            print(f"❌ Fetch error ({timeframe}): {e}")
            return np.array([]), np.array([]), np.array([]), np.array([]), np.array([])

    def _fetch_multi_timeframe(self, limit: int = 100) -> dict:
        """Fetch OHLCV data for 4H strategy with Daily validation"""
        # Para estrategia 4H: necesitamos Daily como validación superior + 4H como entrada
        data = {
            'daily': self._fetch_ohlcv('1d', limit=30),   # 30 días de historia para tendencia
            '4h': self._fetch_ohlcv('4h', limit=100),     # 100 velas 4H (~16-17 días)
            # REMOVED: 1m, 5m, 15m (no aplicables a estrategia 4H)
        }
        return data

    def _fetch_correlation_timeframes(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        NEW v3.6 - Fetch Daily, 4H, and 1H data for multi-timeframe correlation

        Returns:
            Tuple of (daily_candles, h4_candles, h1_candles)
            Each is a numpy array of [open, high, low, close] for each candle
        """
        # Fetch sufficient historical data
        daily_data = self._fetch_ohlcv('1d', limit=30)  # Last 30 days
        h4_data = self._fetch_ohlcv('4h', limit=100)     # Last 100 x 4h = ~16 days
        h1_data = self._fetch_ohlcv('1h', limit=100)     # Last 100 hours ~4 days

        # Convert to numpy arrays [open, high, low, close]
        daily_candles = np.column_stack([daily_data[0], daily_data[1], daily_data[2], daily_data[3]])
        h4_candles = np.column_stack([h4_data[0], h4_data[1], h4_data[2], h4_data[3]])
        h1_candles = np.column_stack([h1_data[0], h1_data[1], h1_data[2], h1_data[3]])

        return daily_candles, h4_candles, h1_candles

    def _log_event(self, event_type: str, **kwargs):
        """Log trading events to file"""
        log_file = f"trades_{self.mode}.log"

        # Convert numpy types to Python native types for JSON serialization
        clean_kwargs = {}
        for k, v in kwargs.items():
            if isinstance(v, (np.bool_, np.integer, np.floating)):
                clean_kwargs[k] = v.item()
            elif isinstance(v, np.ndarray):
                clean_kwargs[k] = v.tolist()
            else:
                clean_kwargs[k] = v

        entry = {
            'timestamp': get_local_time().isoformat(),
            'cycle': self.cycle_count,
            'type': event_type,
            **clean_kwargs
        }

        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except (IOError, OSError):
            # Failed to write log, skip silently
            pass

    def _validate_tzv_formula(self, opens: np.ndarray, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, current_price: float) -> Dict:
        """
        NEW v3.5+ - Validate T+Z+V Formula (Crecetrader Core)

        This is the GATEKEEPER for all trading decisions.
        Applied BEFORE any entry logic.

        Rules (from Crecetrader):
        1. Validate T (Tendencia) - Must have clear trend
        2. Validate Z (Zonas) - Must have clear support/resistance levels
        3. Validate V (Vacío) - Must have favorable risk/reward (min 2:1)

        If ALL 3 pass → Proceed to entry
        If ANY fails → WAIT or SKIP this cycle

        Returns:
            {
                'all_passed': bool,
                'can_trade': bool,
                't_validation': dict,
                'z_validation': dict,
                'v_validation': dict,
                'complete_validation': dict,
                'referentes_map': dict
            }
        """
        # Step 1: Calculate market referentes (Z validation)
        # Using historical + Fibonacci to map all obstacles
        # CRITICAL FIX: Protect against empty arrays
        phase_1_low = np.min(lows[-50:]) if len(lows) >= 50 else (np.min(lows) if len(lows) > 0 else 0)
        phase_1_high = np.max(highs[-50:]) if len(highs) >= 50 else (np.max(highs) if len(highs) > 0 else 0)

        referentes_map = self.referentes_calc.get_complete_referentes_map(
            highs, lows, closes,
            phase_1_low=phase_1_low,
            phase_1_high=phase_1_high
        )

        # Step 2: Validate T (Tendencia)
        t_validation = self.tzv_validator.validate_t_tendencia(highs, lows, closes, lookback=20)

        # Step 3: Validate Z (Zonas) using referentes
        z_validation = self.tzv_validator.validate_z_zonas(
            referentes_map,  # Contains supports
            referentes_map,  # Contains resistances
            current_price
        )

        # Step 4: Validate V (Vacío) - requires entry point
        # For now, use current price as potential entry
        first_support = z_validation.get('first_support')
        first_resistance = z_validation.get('first_resistance')

        if first_support and first_resistance:
            v_validation = self.tzv_validator.validate_v_vacio(
                current_price,
                first_resistance,
                first_support,
                min_ratio=2.0  # Crecetrader minimum 2:1
            )
        else:
            v_validation = {
                'validity': 'poor',
                'vacio_up': 0,
                'vacio_down': 0,
                'ratio': 0,
                'validation_passed': False,
                'description': 'Cannot validate Vacío: missing support or resistance'
            }

        # Step 5: Complete T+Z+V validation
        complete_validation = self.tzv_validator.validate_tzv_complete(
            t_validation,
            z_validation,
            v_validation
        )

        # Log validation results
        self._log_event('TZV_VALIDATION',
            t_passed=t_validation.get('validation_passed'),
            z_passed=z_validation.get('validation_passed'),
            v_passed=v_validation.get('validation_passed'),
            all_passed=complete_validation.get('all_passed'),
            confidence=complete_validation.get('confidence'),
            description=complete_validation.get('description')
        )

        # NEW v3.6 - Log specifically when TZV passes (important milestone)
        if complete_validation.get('all_passed'):
            self._log_event('TZV_PASSED',
                confidence=complete_validation.get('confidence'),
                description=complete_validation.get('description'),
                t_details=t_validation.get('description', ''),
                z_details=z_validation.get('description', ''),
                v_details=v_validation.get('description', ''),
                risk_reward_ratio=v_validation.get('rr_ratio', 0)
            )

        return {
            'all_passed': complete_validation.get('all_passed'),
            'can_trade': complete_validation.get('can_trade'),
            't_validation': t_validation,
            'z_validation': z_validation,
            'v_validation': v_validation,
            'complete_validation': complete_validation,
            'referentes_map': referentes_map
        }

    def _update_metrics_on_close(self, entry_price: float, exit_price: float, side: str):
        """NEW v3.3 - Update metrics when a trade closes"""
        # Calculate P&L
        pnl = (exit_price - entry_price) if side == 'LONG' else (entry_price - exit_price)
        pnl_pct = (pnl / entry_price) * 100

        # Update trade metrics
        self.trade_count += 1
        if pnl_pct > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1

        self.total_pnl += pnl_pct

        # Store trade details for analysis
        trade_record = {
            'trade_num': self.trade_count,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'side': side,
            'pnl_pct': pnl_pct,
            'timestamp': get_local_time().isoformat()
        }
        self.trades_log.append(trade_record)

        # Calculate winrate
        winrate = (self.winning_trades / self.trade_count * 100) if self.trade_count > 0 else 0
        avg_pnl = (self.total_pnl / self.trade_count) if self.trade_count > 0 else 0

        # Log metrics to console
        print(f"\n📊 METRICS UPDATE:")
        print(f"   Trade #{self.trade_count} | Wins: {self.winning_trades} | Losses: {self.losing_trades}")
        print(f"   Winrate: {winrate:.1f}% | Avg P&L: {avg_pnl:.2f}% | Total P&L: {self.total_pnl:.2f}%")
        print()

    def _get_current_session(self) -> Optional[str]:
        """NEW v3.3 - Get current active trading session (ASIAN/EUROPEAN/AMERICAN)"""
        current_time = datetime.now(timezone.utc)
        session = get_active_session(current_time)
        return session.name if session else None

    def _update_price_volume_history(self, price: float, volume: float):
        """NEW v3.3 - Track price/volume history for dead trade detection (last 15 candles)"""
        self.price_history.append(price)
        self.volume_history.append(volume)

        # Keep only last 15 candles
        if len(self.price_history) > 15:
            self.price_history.pop(0)
        if len(self.volume_history) > 15:
            self.volume_history.pop(0)

    def _check_dead_trade(self, current_price: float, current_volume: float) -> Tuple[bool, str]:
        """
        NEW v3.3 - OPTION 3: Combined Price + Volume Dead Trade Detection

        DEAD_PRICE: Price doesn't move ±{DEAD_PRICE_THRESHOLD_PCT}% in last 15 candles
        DEAD_VOLUME: Volume < 50% of average of last 15 candles

        Close logic:
        - Both true for 3+ cycles → CLOSE
        - One true for 5+ cycles → CLOSE

        Returns: (should_close, reason)
        """
        if not self.price_history or len(self.price_history) < 3:
            return False, ""

        # Calculate price range
        price_min = min(self.price_history)
        price_max = max(self.price_history)
        entry_price = self.position['entry_price']
        price_range_pct = ((price_max - price_min) / entry_price) * 100

        # Check if price is dead (less than threshold movement)
        is_dead_price = price_range_pct < DEAD_PRICE_THRESHOLD_PCT
        if is_dead_price:
            self.dead_price_counter += 1
        else:
            self.dead_price_counter = 0

        # Check if volume is dead (less than threshold of average)
        if self.volume_history:
            avg_volume = np.mean(self.volume_history)
            is_dead_volume = current_volume < (avg_volume * DEAD_VOLUME_RATIO)
        else:
            is_dead_volume = False

        if is_dead_volume:
            self.dead_volume_counter += 1
        else:
            self.dead_volume_counter = 0

        # Close conditions
        # Both dead for N+ cycles (very confident it's dead)
        if is_dead_price and is_dead_volume and self.dead_price_counter >= DEAD_PRICE_COUNTER_MAX and self.dead_volume_counter >= DEAD_VOLUME_COUNTER_MAX:
            return True, f"DEAD TRADE - Both price and volume dead (price_range={price_range_pct:.3f}%, avg_vol={avg_volume:.0f}, current_vol={current_volume:.0f})"

        # One dead for 5+ cycles (probably dead)
        if (is_dead_price and self.dead_price_counter >= 5) or (is_dead_volume and self.dead_volume_counter >= 5):
            return True, f"DEAD TRADE - Single condition persistent (dead_price={self.dead_price_counter}, dead_volume={self.dead_volume_counter})"

        return False, ""

    def _check_position_sl_tp(self, current_price: float) -> Tuple[bool, str]:
        """
        NEW v3.3 - Monitor SL/TP levels and execute partial/full exits

        Returns: (should_close_position, exit_reason)
        """
        if not self.position:
            return False, ""

        side = self.position['side']
        entry_price = self.position['entry_price']
        sl_price = self.position['stop_loss']
        tp1_price = self.position['take_profit_1']
        tp2_price = self.position['take_profit_2']

        # Check Stop Loss
        if side == 'LONG' and current_price <= sl_price:
            pnl = ((current_price - entry_price) / entry_price) * 100
            return True, f"STOP LOSS HIT - Price: ${current_price:.2f}, P&L: {pnl:.2f}%"

        if side == 'SHORT' and current_price >= sl_price:
            pnl = ((entry_price - current_price) / entry_price) * 100
            return True, f"STOP LOSS HIT - Price: ${current_price:.2f}, P&L: {pnl:.2f}%"

        # Check TP1 (50% close)
        if not self.position_tp1_closed:
            if side == 'LONG' and current_price >= tp1_price:
                pnl = ((current_price - entry_price) / entry_price) * 100
                print(f"🟢 PARTIAL CLOSE (TP1) | Exit: ${current_price:.2f} | P&L: {pnl:.2f}% | 50% closed")

                # NEW v3.4 - Log TP1 hit to TradeLogger
                if self.position.get('signal_id'):
                    self.trade_logger.log_tp_hit(
                        signal_id=self.position['signal_id'],
                        tp_level=1,
                        exit_price=current_price,
                        pnl=pnl,
                        pnl_percent=pnl,
                        filled_percent=TP_PARTIAL_FILL
                    )

                self._log_event('TP1_HIT',
                    entry=entry_price,
                    exit=current_price,
                    pnl=pnl,
                    size_closed='50%'
                )
                self.position_tp1_closed = True
                self.position['stop_loss'] = entry_price * 1.001  # Move SL to breakeven + 0.1%
                self.trade_max_price = current_price  # Reset for TP2 trailing
                return False, ""

            if side == 'SHORT' and current_price <= tp1_price:
                pnl = ((entry_price - current_price) / entry_price) * 100
                print(f"🟢 PARTIAL CLOSE (TP1) | Exit: ${current_price:.2f} | P&L: {pnl:.2f}% | 50% closed")

                # NEW v3.4 - Log TP1 hit to TradeLogger
                if self.position.get('signal_id'):
                    self.trade_logger.log_tp_hit(
                        signal_id=self.position['signal_id'],
                        tp_level=1,
                        exit_price=current_price,
                        pnl=pnl,
                        pnl_percent=pnl,
                        filled_percent=TP_PARTIAL_FILL
                    )

                self._log_event('TP1_HIT',
                    entry=entry_price,
                    exit=current_price,
                    pnl=pnl,
                    size_closed='50%'
                )
                self.position_tp1_closed = True
                self.position['stop_loss'] = entry_price * 0.999  # Move SL to breakeven - 0.1%
                self.trade_max_price = current_price
                return False, ""

        # Check TP2 (25% close, 25% for trailing)
        if self.position_tp1_closed and not self.position_tp2_closed:
            if side == 'LONG' and current_price >= tp2_price:
                pnl = ((current_price - entry_price) / entry_price) * 100
                print(f"🟢 PARTIAL CLOSE (TP2) | Exit: ${current_price:.2f} | P&L: {pnl:.2f}% | 25% closed, 25% trailing")

                # NEW v3.4 - Log TP2 hit to TradeLogger
                if self.position.get('signal_id'):
                    self.trade_logger.log_tp_hit(
                        signal_id=self.position['signal_id'],
                        tp_level=2,
                        exit_price=current_price,
                        pnl=pnl,
                        pnl_percent=pnl,
                        filled_percent=0.25
                    )

                self._log_event('TP2_HIT',
                    entry=entry_price,
                    exit=current_price,
                    pnl=pnl,
                    size_closed='25%'
                )
                self.position_tp2_closed = True
                self.trailing_stop_active = True
                self.trade_max_price = current_price
                self.trailing_stop_price = current_price * (1 - TRAILING_STOP_PCT)  # Trail below current
                return False, ""

            if side == 'SHORT' and current_price <= tp2_price:
                pnl = ((entry_price - current_price) / entry_price) * 100
                print(f"🟢 PARTIAL CLOSE (TP2) | Exit: ${current_price:.2f} | P&L: {pnl:.2f}% | 25% closed, 25% trailing")

                # NEW v3.4 - Log TP2 hit to TradeLogger
                if self.position.get('signal_id'):
                    self.trade_logger.log_tp_hit(
                        signal_id=self.position['signal_id'],
                        tp_level=2,
                        exit_price=current_price,
                        pnl=pnl,
                        pnl_percent=pnl,
                        filled_percent=0.25
                    )

                self._log_event('TP2_HIT',
                    entry=entry_price,
                    exit=current_price,
                    pnl=pnl,
                    size_closed='25%'
                )
                self.position_tp2_closed = True
                self.trailing_stop_active = True
                self.trade_max_price = current_price
                self.trailing_stop_price = current_price * (1 + TRAILING_STOP_PCT)  # Trail above current
                return False, ""

        # Check Trailing Stop (remaining 25%)
        if self.trailing_stop_active:
            if side == 'LONG':
                # Update trailing stop if price goes higher
                if current_price > self.trade_max_price:
                    self.trade_max_price = current_price
                    self.trailing_stop_price = current_price * (1 - TRAILING_STOP_PCT)  # Trail below current
                # Check if trailing SL hit
                elif current_price <= self.trailing_stop_price:
                    pnl = ((current_price - entry_price) / entry_price) * 100
                    return True, f"TRAILING STOP HIT - Price: ${current_price:.2f}, P&L: {pnl:.2f}%"

            else:  # SHORT
                # Update trailing stop if price goes lower
                if current_price < self.trade_max_price:
                    self.trade_max_price = current_price
                    self.trailing_stop_price = current_price * (1 + TRAILING_STOP_PCT)  # Trail above current
                # Check if trailing SL hit
                elif current_price >= self.trailing_stop_price:
                    pnl = ((entry_price - current_price) / entry_price) * 100
                    return True, f"TRAILING STOP HIT - Price: ${current_price:.2f}, P&L: {pnl:.2f}%"

        return False, ""

    def _check_session_closing(self, current_time: datetime) -> Tuple[bool, str]:
        """NEW v3.3 - Check if approaching session end and close position 30 min before"""
        session = get_active_session(current_time)
        if not session:
            return False, ""

        # Get closing alert time (30 min before session end)
        closing_alert = session.get_closing_alert_time()
        current_time_str = current_time.strftime("%H:%M")

        # If we're past the alert time, close the position
        if current_time_str >= closing_alert:
            return True, f"SESSION CLOSING SOON ({closing_alert} UTC alert)"

        return False, ""

    def run_cycle(self):
        """Execute one trading cycle"""
        self.cycle_count += 1

        # NEW v3.3 - Load dynamic permissiveness mode
        self._load_permissiveness_config()

        # NEW v3.6 - GATEKEEPER #0: Multi-Timeframe Correlation (Daily + 4H + 1H)
        # =====================================================================
        # This is the PROFESSIONAL filter - only trade when all timeframes align
        if self.mtf_enabled:
            try:
                daily_candles, h4_candles, h1_candles = self._fetch_correlation_timeframes()

                # Get current price from h1 data
                current_price_h1 = h1_candles[-1, 3] if len(h1_candles) > 0 else None

                if current_price_h1 is not None and len(daily_candles) > 3 and len(h4_candles) > 3:
                    # Analyze correlation
                    mtf_analysis = self.multitimeframe_validator.analyze_all_timeframes(
                        daily_candles, h4_candles, h1_candles, current_price_h1
                    )

                    # Log MTF analysis
                    if mtf_analysis.alignment.value != "neutral":
                        summary = self.multitimeframe_validator.get_summary(mtf_analysis)
                        self.trade_logger._write_journal(f"\n{summary}\n")

                    # CRITICAL: Only proceed if entry is allowed by MTF correlation
                    if not mtf_analysis.entry_allowed:
                        self.trade_logger._write_journal(
                            f"[MTF_GATEKEEPER] BLOCKED - Alignment: {mtf_analysis.alignment.value} | "
                            f"Confidence: {mtf_analysis.overall_confidence:.0%} | "
                            f"Correlation: {mtf_analysis.correlation_strength}"
                        )
                        return  # Don't proceed with this cycle
            except Exception as e:
                # If MTF fails, log and continue (failsafe)
                self.trade_logger._write_journal(f"[MTF_ERROR] {str(e)} - Continuing with single timeframe")
                self.mtf_enabled = False  # Disable MTF temporarily

        # Fetch multi-timeframe data for 4H strategy
        # ============================================
        data_mtf = self._fetch_multi_timeframe(limit=100)
        opens, highs, lows, closes, volumes = data_mtf['4h']  # CHANGED: Use 4H as primary timeframe

        if len(closes) == 0:
            return

        current_price = closes[-1]

        # Extract Daily data for multi-timeframe validation (superior timeframe)
        opens_daily, highs_daily, lows_daily, closes_daily, _ = data_mtf['daily']
        # REMOVED: 5m and 15m extraction (not applicable to 4H strategy)

        # NEW v3.5+ - GATEKEEPER #1: Validate T+Z+V Formula (Crecetrader Core)
        # This GATEKEEPER runs AFTER multi-timeframe correlation check
        tzv_result = self._validate_tzv_formula(opens, highs, lows, closes, current_price)

        # Log T+Z+V validation (for consciousness tracking)
        if not tzv_result['all_passed']:
            failed = tzv_result['complete_validation'].get('failed_components', [])
            self.trade_logger._write_journal(
                f"[TZV_VALIDATION] FAILED Components: {', '.join(failed)} | "
                f"Confidence: {tzv_result['complete_validation'].get('confidence', 0):.0%}"
            )

        # Analyze with hybrid strategy using 4H + Daily for 4H timeframe strategy
        signal = self.strategy.analyze(
            opens, highs, lows, closes, volumes,
            opens_daily=opens_daily, highs_daily=highs_daily,
            lows_daily=lows_daily, closes_daily=closes_daily,
            mode=self.current_mode
            # REMOVED: 5m and 15m parameters (not needed for 4H strategy)
        )

        # NEW v3.4 - Validate signal through GatekeeperV2 (Claude intelligence layer)
        # NEW v3.5 - Calculate actual volatility & momentum using Crecetrader methodology
        market_context = self.market_analyzer.get_market_context(opens, highs, lows, closes)
        volatility_desc = market_context['volatility']['description']
        momentum_desc = market_context['momentum']['description']

        # NEW v3.6+ - Load Multi-Timeframe Analysis for complete market context
        multitf_context = {}
        if self.multitf_adapter is not None:
            try:
                multitf_context = self.multitf_adapter.load_and_analyze(limit=100)
                self.trade_logger._write_journal(
                    f"\n[MTF_ANALYSIS] Direction: {multitf_context['primary_direction']} | "
                    f"Alignment: {multitf_context['alignment_score']}% | "
                    f"Opportunity: {multitf_context['opportunity_score']}/100 | "
                    f"Confidence: {multitf_context['confidence']:.2f}"
                )
                # Si el alignment es muy bajo, podemos saltear el ciclo
                if multitf_context['alignment_score'] < 40:
                    self.trade_logger._write_journal(
                        f"[MTF_SKIP] Alignment {multitf_context['alignment_score']}% too low - skipping cycle"
                    )
                    return  # Skip this cycle
            except Exception as e:
                self.trade_logger._write_journal(f"[MTF_ERROR] {str(e)}")
                multitf_context = {}

        # Pass technical signal to Claude for intelligent validation
        # Merge basic context + multi-timeframe context
        enhanced_context = {
            'volatility': volatility_desc,
            'momentum': momentum_desc
        }
        if multitf_context:
            enhanced_context.update(multitf_context)

        # NEW v3.6+ - RSI es INFORMATIVO (no bloqueante) cuando MTF alignment > 80%
        # Si MTF tiene alta convicción, forzamos señal para que Gatekeeper decida
        if multitf_context.get('alignment_score', 0) > 80:
            if not signal.should_trade:
                self.trade_logger._write_journal(
                    f"[MTF_OVERRIDE] RSI filter bypassed (MTF alignment {multitf_context['alignment_score']}% > 80%) - "
                    f"Forcing signal for Gatekeeper evaluation"
                )
            signal.should_trade = True  # Force signal when MTF has high conviction
            signal.entry_price = current_price  # CRITICAL: Set entry price
            # Determine side based on MTF direction
            if multitf_context.get('primary_direction') == 'BEARISH':
                signal.side = 'SHORT'
            elif multitf_context.get('primary_direction') == 'BULLISH':
                signal.side = 'LONG'
            # Recalculate SL/TP based on current price
            if signal.side == 'SHORT':
                signal.stop_loss = current_price * (1 + self.sl_pct / 100)
                signal.take_profit_1 = current_price * (1 - self.tp1_pct / 100)
                signal.take_profit_2 = current_price * (1 - self.tp2_pct / 100)
            else:  # LONG
                signal.stop_loss = current_price * (1 - self.sl_pct / 100)
                signal.take_profit_1 = current_price * (1 + self.tp1_pct / 100)
                signal.take_profit_2 = current_price * (1 + self.tp2_pct / 100)

        try:
            gk_approved, gk_decision = self.gatekeeper_adapter.should_enter(
                signal=signal,
                market_phase=self.current_market_phase if hasattr(self, 'current_market_phase') else 'NEUTRAL',
                additional_context=enhanced_context,
                open_positions=self.risk_manager.open_positions  # FIXED: Pass real open positions count
            )

            # If GatekeeperV2 rejects, override the technical signal
            if not gk_approved and signal.should_trade:
                # Log the override
                self._log_event('GATEKEEPER_REJECT',
                    reason=gk_decision.get('claude_reason', 'Unknown'),
                    technical_confidence=signal.confidence,
                    claude_confidence=gk_decision.get('claude_confidence', 0),
                    gatekeeper_level=gk_decision.get('gatekeeper_level')
                )
                # NEW v3.5 - Log Gatekeeper rejection with trade_logger
                self.trade_logger._write_journal(
                    f"[GATEKEEPER_REJECT] Level:{gk_decision.get('gatekeeper_level')} | "
                    f"Reason:{gk_decision.get('claude_reason', 'Unknown')} | "
                    f"Tech:{signal.confidence:.0f}% vs Claude:{gk_decision.get('claude_confidence', 0):.0f}%"
                )
                signal.should_trade = False  # Override technical signal with Claude decision

            # NEW v3.6 - Log when Gatekeeper APPROVES (important milestone for visibility)
            elif gk_approved and signal.should_trade:
                self._log_event('GATEKEEPER_APPROVED',
                    reason=gk_decision.get('claude_reason', 'Setup quality confirmed'),
                    technical_confidence=signal.confidence,
                    claude_confidence=gk_decision.get('claude_confidence', 0),
                    gatekeeper_level=gk_decision.get('gatekeeper_level', 0),
                    signal_side=signal.side
                )
                self.trade_logger._write_journal(
                    f"[GATEKEEPER_APPROVED] Level:{gk_decision.get('gatekeeper_level')} | "
                    f"Reason:{gk_decision.get('claude_reason', 'Setup quality confirmed')} | "
                    f"Tech:{signal.confidence:.0f}% + Claude:{gk_decision.get('claude_confidence', 0):.0f}%"
                )

        except Exception as e:
            # Fallback: If gatekeeper fails, use technical signal (failsafe)
            self._log_event('GATEKEEPER_ERROR', error=str(e))
            pass

        # NEW v3.4 - Log signals even if not traded (to distinguish pattern detection from execution)
        if signal.should_trade:
            signal_id = f"SIGNAL_{self.cycle_count}_{signal.side}"
            self.trade_logger.log_signal_detected(
                signal_id=signal_id,
                signal_type=signal.side,
                price=current_price,
                rsi=signal.rsi_value,
                timeframe=self.timeframe,
                metadata={
                    'confidence': signal.confidence,
                    'pattern': signal.price_action,
                    'reason': signal.reason
                }
            )

        # Display status
        emoji_rsi = "🔴" if signal.rsi_value < 25 else ("🟡" if signal.rsi_value < 50 else "🟢")
        status = f"[{get_local_time().strftime('%H:%M:%S')}] #{self.cycle_count}"
        print(f"{status} | Price: ${current_price:.2f} | RSI(7):{emoji_rsi}{signal.rsi_value:.1f} | EMA: {signal.ema_9:.0f}vs{signal.ema_21:.0f}")

        # NEW v3.3 - Session Status Display
        current_time = datetime.now(timezone.utc)
        current_session = self._get_current_session()
        is_off = is_off_hours(current_time)

        # Check if we're in off-hours and should close position
        if is_off and self.position:
            pnl = (current_price - self.position['entry_price']) if self.position['side'] == 'LONG' else (self.position['entry_price'] - current_price)
            pnl_pct = (pnl / self.position['entry_price']) * 100
            emoji = "🟢" if pnl_pct > 0 else "🔴"
            print(f"{emoji} CERRADO (OFF-HOURS) | Exit: ${current_price:.2f} | P&L Total: {pnl_pct:.2f}%")
            self._update_metrics_on_close(self.position['entry_price'], current_price, self.position['side'])
            self._log_event('TRADE_CLOSED',
                side=self.position['side'],
                entry_price=self.position['entry_price'],
                exit_price=current_price,
                exit_type="OFF_HOURS",
                pnl=pnl,
                pnl_pct=pnl_pct,
                exit_reason="Market off-hours",
                duration_hours=((datetime.now(timezone.utc) - self.position['entry_time']).total_seconds() / 3600)
            )
            # NEW v3.5 - Register trade close with Risk Manager
            self.risk_manager.register_trade_close(pnl_pct, "OFF_HOURS")
            self.position = None

        # ENTRY LOGIC
        if signal.should_trade and self.position is None:
            # Check if we're in an active session
            if is_off:
                self._log_event('SKIPPED', reason="OFF_HOURS")
            # NEW v3.6+ - T+Z+V is now INFORMATIVE only (not blocking)
            # Gatekeeper with MTF is the primary decision maker
            else:
                # Log TZV result for information (but don't block)
                if not tzv_result.get('all_passed'):
                    failed_components = tzv_result['complete_validation'].get('failed_components', [])
                    self.trade_logger._write_journal(
                        f"[TZV_INFO] {', '.join(failed_components)} failed but continuing with GatekeeperV2 approval"
                    )
                    print(f"   ℹ️  TZV Note: {', '.join(failed_components)} failed (informative only)")
                else:
                    self.trade_logger._write_journal(f"[TZV_PASSED] All components passed")
                    print(f"   ✅ TZV: All components passed")
                # NEW v3.5 - Risk Manager check BEFORE entry
                can_open, risk_reason = self.risk_manager.can_open_position()
                if not can_open:
                    self._log_event('RISK_REJECTED', reason=risk_reason)
                    self.trade_logger._write_journal(f"[RISK_REJECTED] {risk_reason}")
                    print(f"   {risk_reason}")
                # NEW v3.6 - Log Risk Manager approval
                else:
                    self._log_event('RISK_MANAGER_APPROVED',
                        max_open_trades=self.risk_manager.max_open_positions,
                        current_open_trades=len([p for p in [self.position] if p]),
                        daily_loss_limit_pct=self.risk_manager.max_daily_loss_pct,
                        position_allowed=True
                    )
                    self.trade_logger._write_journal(f"[RISK_MANAGER_APPROVED] Position allowed (Risk Manager check passed)")

                # GatekeeperV2 already validated the signal, so proceed if risk manager approved
                if can_open:
                    # Use dynamic position sizing (NEW v3.2)
                    position_size = signal.position_size_pct

                    self.position = {
                        'side': signal.side,
                        'entry_price': signal.entry_price,
                        'entry_time': datetime.now(timezone.utc),
                        'stop_loss': signal.stop_loss,
                        'take_profit_1': signal.take_profit_1,
                        'take_profit_2': signal.take_profit_2,
                        'size': position_size,
                        'tp1_hit': False,
                        'signal_id': signal_id  # NEW v3.4 - Store signal_id for exit logging
                    }

                    # Initialize v3.3 position tracking
                    self.position_tp1_closed = False
                    self.position_tp2_closed = False
                    self.trailing_stop_active = False
                    self.dead_price_counter = 0
                    self.dead_volume_counter = 0
                    self.trade_max_price = current_price
                    self.session_start_time = datetime.now(timezone.utc)
                    self.active_session = current_session

                    emoji = "🟢" if signal.side == "LONG" else "🔴"
                    print(f"{emoji} ABIERTO {signal.side} | Entry: ${signal.entry_price:.2f} | SL: ${signal.stop_loss:.2f} | TP1: ${signal.take_profit_1:.2f} | TP2: ${signal.take_profit_2:.2f}")
                    print(f"   Confianza: {signal.confidence:.0f}% | Patrón: {signal.price_action} | {signal.reason}")
                    print(f"   📊 Position Size: {position_size:.1f}% | MTF Confirmations: {signal.timeframe_confirmations}")
                    print(f"   🔍 Crecetrader: Localización={signal.candle_location} | Volatilidad={signal.volatility_phase} | Calidad={signal.entry_quality_crecetrader:.0f}%")
                    print(f"   📍 Session: {current_session}")

                    # NEW v3.4 - Log trade FILLED (actual execution, not just signal detection)
                    signal_id = f"SIGNAL_{self.cycle_count}_{signal.side}"
                    self.trade_logger.log_order_requested(
                        signal_id=signal_id,
                        order_type=signal.side,
                        quantity=position_size,
                        position_size=self.order_size_usdt,
                        leverage=self.leverage,
                        metadata={'confidence': signal.confidence}
                    )
                    self.trade_logger.log_order_placed(
                        signal_id=signal_id,
                        order_id=f"ORDRX_{self.cycle_count}",
                        exchange="binance"
                    )
                    self.trade_logger.log_trade_filled(
                        signal_id=signal_id,
                        actual_entry_price=signal.entry_price,
                        actual_quantity=position_size
                    )

                    self._log_event('ENTRY_EXECUTED',
                        side=signal.side,
                        entry_price=signal.entry_price,
                        stop_loss=signal.stop_loss,
                        take_profit_1=signal.take_profit_1,
                        take_profit_2=signal.take_profit_2,
                        confidence=signal.confidence,
                        reason=signal.reason,
                        pattern=signal.price_action,
                        rsi=signal.rsi_value,
                        ema_9=signal.ema_9,
                        ema_21=signal.ema_21,
                        crecetrader_location=signal.candle_location,
                        crecetrader_volatility=signal.volatility_phase,
                        crecetrader_quality=signal.entry_quality_crecetrader,
                        position_size_pct=signal.position_size_pct,
                        mtf_confirmations=signal.timeframe_confirmations,
                        session=current_session,
                        order_id=f"ORDRX_{self.cycle_count}"
                    )

                    self.strategy.record_trade(signal.side)

                    # NEW v3.5 - Register trade entry with Risk Manager
                    self.risk_manager.register_trade_entry(signal.entry_price, signal.side)

        # NEW v3.3 - ADVANCED EXIT LOGIC with SL/TP/Trailing/Dead Trade Detection
        elif self.position:
            # Update price/volume history for dead trade detection
            self._update_price_volume_history(current_price, volumes[-1] if len(volumes) > 0 else 0)

            # 1. Check for dead trade (OPTION 3: Combined price+volume)
            is_dead, dead_reason = self._check_dead_trade(current_price, volumes[-1] if len(volumes) > 0 else 0)
            if is_dead:
                pnl = (current_price - self.position['entry_price']) if self.position['side'] == 'LONG' else (self.position['entry_price'] - current_price)
                pnl_pct = (pnl / self.position['entry_price']) * 100
                emoji = "🟢" if pnl_pct > 0 else "🔴"
                print(f"{emoji} CERRADO ({dead_reason}) | Exit: ${current_price:.2f} | P&L Total: {pnl_pct:.2f}%")

                # NEW v3.4 - Log trade closure to TradeLogger
                if self.position.get('signal_id'):
                    self.trade_logger.log_trade_closed(
                        signal_id=self.position['signal_id'],
                        final_pnl=pnl,
                        final_pnl_percent=pnl_pct,
                        close_reason="DEAD_TRADE"
                    )
                    self.trade_logger._save_stats()  # Persist stats to file

                self._update_metrics_on_close(self.position['entry_price'], current_price, self.position['side'])
                self._log_event('TRADE_CLOSED',
                    side=self.position['side'],
                    entry_price=self.position['entry_price'],
                    exit_price=current_price,
                    exit_type="DEAD_TRADE",
                    pnl=pnl,
                    pnl_pct=pnl_pct,
                    exit_reason=dead_reason,
                    duration_hours=((datetime.now(timezone.utc) - self.position['entry_time']).total_seconds() / 3600)
                )
                # NEW v3.5 - Register trade close with Risk Manager
                self.risk_manager.register_trade_close(pnl_pct, "DEAD_TRADE")
                self.position = None
                return

            # 2. Check for SL/TP hits
            should_close, exit_reason = self._check_position_sl_tp(current_price)
            if should_close:
                pnl = (current_price - self.position['entry_price']) if self.position['side'] == 'LONG' else (self.position['entry_price'] - current_price)
                pnl_pct = (pnl / self.position['entry_price']) * 100
                emoji = "🟢" if pnl_pct > 0 else "🔴"
                print(f"{emoji} CERRADO ({exit_reason}) | Exit: ${current_price:.2f} | P&L Total: {pnl_pct:.2f}%")

                # NEW v3.4 - Log exit events to TradeLogger
                if self.position.get('signal_id'):
                    # Differentiate between STOP LOSS and TRAILING STOP
                    if "STOP LOSS HIT" in exit_reason:
                        self.trade_logger.log_stop_loss_hit(
                            signal_id=self.position['signal_id'],
                            stop_price=current_price,
                            loss=abs(pnl),  # Absolute value for loss
                            loss_percent=abs(pnl_pct)  # Absolute value for loss %
                        )
                    elif "TRAILING STOP HIT" in exit_reason:
                        self.trade_logger.log_trailing_stop_hit(
                            signal_id=self.position['signal_id'],
                            exit_price=current_price,
                            pnl=pnl,
                            pnl_percent=pnl_pct
                        )

                    # Log final trade closure
                    self.trade_logger.log_trade_closed(
                        signal_id=self.position['signal_id'],
                        final_pnl=pnl,
                        final_pnl_percent=pnl_pct,
                        close_reason=exit_reason.split('-')[0].strip()
                    )
                    self.trade_logger._save_stats()  # Persist stats to file

                self._update_metrics_on_close(self.position['entry_price'], current_price, self.position['side'])

                # NEW v3.6 - Determine exit type for structured logging
                exit_type = "SL"
                if "TAKE PROFIT 1" in exit_reason:
                    exit_type = "TP1"
                elif "TAKE PROFIT 2" in exit_reason:
                    exit_type = "TP2"
                elif "TRAILING STOP" in exit_reason:
                    exit_type = "TRAILING_STOP"

                self._log_event('TRADE_CLOSED',
                    side=self.position['side'],
                    entry_price=self.position['entry_price'],
                    exit_price=current_price,
                    exit_type=exit_type,
                    pnl=pnl,
                    pnl_pct=pnl_pct,
                    exit_reason=exit_reason.split('-')[0].strip(),
                    duration_hours=((datetime.now(timezone.utc) - self.position['entry_time']).total_seconds() / 3600)
                )
                # NEW v3.5 - Register trade close with Risk Manager
                self.risk_manager.register_trade_close(pnl_pct, exit_reason.split('-')[0].strip())
                self.position = None
                return

            # 3. Check for session closing (15 min before session end)
            should_close_session, session_msg = self._check_session_closing(current_time)
            if should_close_session and self.position:
                pnl = (current_price - self.position['entry_price']) if self.position['side'] == 'LONG' else (self.position['entry_price'] - current_price)
                pnl_pct = (pnl / self.position['entry_price']) * 100
                emoji = "🟢" if pnl_pct > 0 else "🔴"
                print(f"{emoji} CERRADO ({session_msg}) | Exit: ${current_price:.2f} | P&L Total: {pnl_pct:.2f}%")

                # NEW v3.4 - Log session closing trade closure to TradeLogger
                if self.position.get('signal_id'):
                    self.trade_logger.log_trade_closed(
                        signal_id=self.position['signal_id'],
                        final_pnl=pnl,
                        final_pnl_percent=pnl_pct,
                        close_reason="SESSION_CLOSING"
                    )
                    self.trade_logger._save_stats()  # Persist stats to file

                self._update_metrics_on_close(self.position['entry_price'], current_price, self.position['side'])
                self._log_event('TRADE_CLOSED',
                    side=self.position['side'],
                    entry_price=self.position['entry_price'],
                    exit_price=current_price,
                    exit_type="SESSION_CLOSING",
                    pnl=pnl,
                    pnl_pct=pnl_pct,
                    exit_reason=session_msg,
                    duration_hours=((datetime.now(timezone.utc) - self.position['entry_time']).total_seconds() / 3600)
                )
                # NEW v3.5 - Register trade close with Risk Manager
                self.risk_manager.register_trade_close(pnl_pct, "SESSION_CLOSING")
                self.position = None
                return

        # NEW v3.5 - Dynamic Mode Manager: Determine optimal mode after every cycle
        if len(closes) > 5:
            new_mode, mode_reason = self.mode_manager.determine_mode(
                rsi=signal.rsi_value,
                atr=0.0,  # ATR not directly available, use 0
                recent_closes=list(closes[-20:])
            )
            # Update strategy mode if changed
            if new_mode != self.current_mode:
                self.current_mode = new_mode
                self.strategy.update_mode_config(new_mode)
                self.trade_logger._write_journal(f"[MODE_SWITCH] {mode_reason}")

        # NEW v3.5 - Print mode/risk status every 15 cycles (avoid spam)
        if self.cycle_count % 15 == 0:
            mode_status = self.mode_manager.get_status()
            risk_status = self.risk_manager.get_risk_status()
            print(f"\n   === PERIODIC STATUS (Cycle #{self.cycle_count}) ===")
            print(f"   Mode: {mode_status['current_mode']} | Volatility: {mode_status['volatility']:.1f}%")
            print(f"   Open Positions: {risk_status['position_usage']} | Daily P&L: {risk_status['daily_pnl']:.2f}%")
            print(f"   Trades Today: {risk_status['trades_today']} | Mode Switches: {mode_status['mode_switches_count']}")

    def _handle_crash_recovery(self):
        """NEW v3.3 - Handle recovery from bot crashes with open positions"""
        # Check if bot crashed with open positions
        if self.recovery.detect_crash_with_open_positions():
            open_positions = self.recovery.get_open_positions()
            print(f"\n⚠️  CRASH RECOVERY DETECTED: {len(open_positions)} open position(s) found")

            # Try to reconcile with API
            reconciliation = self.recovery.reconcile_with_api(self.exchange)

            if reconciliation['recovered']:
                print(f"✅ RECOVERED POSITIONS: {len(reconciliation['recovered'])}")
                for pos in reconciliation['recovered']:
                    print(f"   - {pos}")
                # Clear state after recovery
                self.recovery.clear_state()
                print(f"✅ Recovery completed and state cleared")

            elif reconciliation['lost']:
                print(f"❌ LOST POSITIONS (not found in API): {len(reconciliation['lost'])}")
                for pos in reconciliation['lost']:
                    print(f"   - {pos}")

                # Check if emergency closure is needed
                self.emergency_closure.record_failure()
                if self.emergency_closure.should_close_positions():
                    print(f"🚨 EMERGENCY CLOSURE TRIGGERED ({self.emergency_closure.failure_count} failures)")
                    if self.emergency_closure.close_all_positions():
                        print(f"✅ All positions closed via emergency mechanism")
                        self.recovery.clear_state()
                    else:
                        print(f"❌ Emergency closure failed")
                else:
                    print(f"⚠️  Keeping positions open for manual review")
                    print(f"   Failure count: {self.emergency_closure.failure_count}/{self.emergency_closure.max_failures}")
        else:
            print(f"✅ No crashed positions detected. Bot ready to trade.")

    def run(self):
        """Main loop"""
        sleep_seconds = self._get_sleep_seconds()
        sleep_minutes = sleep_seconds / 60

        print(f"🚀 TRAD Bot v3.6+ INICIADO - CONTINUOUS 24/7 MULTI-TIMEFRAME MONITORING")
        print(f"📊 Par: {self.symbol} | Modo: {self.mode}")
        print(f"⏳ Ciclo de monitoreo: Cada {sleep_minutes:.0f} minutos")
        print(f"📍 Estrategia: RSI + Price Action + FULL Crecetrader + Multi-Timeframe Correlation")
        print("="*70)
        print(f"🎯 OPERATIONAL MODEL: Continuous Opportunity Detection")
        print(f"   • NO opera en un timeframe fijo")
        print(f"   • Busca oportunidades 24/7 cuando todo alinea")
        print(f"   • Daily/4H/1H = CONTEXTO (pronóstico, tendencia)")
        print(f"   • 15m/5m/1m = SEÑALES DE ENTRADA (ejecución)")
        print("="*70)
        print(f"🧠 CONSCIOUSNESS LEVEL: FULL T+Z+V VALIDATION + MTF CORRELATION")
        print(f"   ✓ T (Tendencia): Trend validation across all timeframes")
        print(f"   ✓ Z (Zonas): Historical + Fibonacci referentes calculated")
        print(f"   ✓ V (Vacío): 2:1 minimum risk/reward ENFORCED")
        print(f"   ✓ MTF (Multi-TF): 6 timeframes analyzed and correlated")
        print("="*70)
        print(f"💰 TRADING CONFIG:")
        print(f"   Order Size: {self.order_size_usdt:.2f} USDT")
        print(f"   Leverage: {self.leverage:.1f}x")
        print(f"   Margin Mode: {self.margin_mode}")
        print(f"="*70)
        print(f"📊 METRICS TRACKING:")
        print(f"   Trades: 0 | Wins: 0 | Losses: 0 | Winrate: 0% | Total P&L: 0%")
        print("="*70)

        # NEW v3.3 - Crash Recovery
        print(f"\n🔄 CHECKING FOR CRASHED POSITIONS...")
        self._handle_crash_recovery()

        try:
            while True:
                self.run_cycle()
                time.sleep(sleep_seconds)
        except KeyboardInterrupt:
            print(f"\n⛔ Detenido por usuario")
        except Exception as e:
            print(f"❌ Error: {e}")
            self._log_event('ERROR', error=str(e))

if __name__ == "__main__":
    bot = TRADBot_v3()
    bot.run()
