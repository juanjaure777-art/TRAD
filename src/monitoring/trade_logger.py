"""
TRADE LOGGER - Módulo de logging detallado de trades
======================================================

Responsabilidad: Registrar CADA evento de trading con precisión absoluta.

Estados de un trade:
1. SIGNAL_DETECTED      - Patrón técnico identificado
2. ORDER_REQUESTED      - Orden solicitada a exchange
3. ORDER_PLACED         - Orden colocada en exchange
4. TRADE_FILLED         - Posición abierta (orden ejecutada)
5. TP1_HIT              - Primer take profit (50% posición)
6. TP2_HIT              - Segundo take profit (25% posición)
7. STOP_LOSS_HIT        - Stop loss ejecutado
8. TRAILING_STOP_HIT    - Trailing stop ejecutado
9. TRADE_CLOSED         - Posición completamente cerrada
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

class TradeLogger:
    """Logger centralizado para tracking detallado de trades."""

    def __init__(self, log_dir: str = "logs/trades"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Archivos de log
        self.journal_file = self.log_dir / "trade_journal.txt"
        self.json_file = self.log_dir / "trades.json"
        self.stats_file = self.log_dir / "trade_stats.json"

        # En-memoria
        self.trades: Dict[str, Dict[str, Any]] = {}
        self.stats = {
            "total_signals": 0,
            "total_orders_requested": 0,
            "total_orders_placed": 0,
            "total_trades_filled": 0,
            "total_trades_closed": 0,
            "total_wins": 0,
            "total_losses": 0,
            "total_pnl": 0.0
        }

        self._load_stats()

    def log_signal_detected(self, signal_id: str, signal_type: str, price: float,
                           rsi: float, timeframe: str = "4h", metadata: Dict = None):
        """
        Log: Patrón técnico detectado (pero sin ejecución aún)

        Esta es la PRIMERA etapa - indica que el algoritmo encontró una señal,
        pero NO significa que una orden fue colocada.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        self.stats["total_signals"] += 1

        trade_info = {
            "signal_id": signal_id,
            "signal_type": signal_type,  # BULLISH, BEARISH
            "entry_price": price,
            "rsi": rsi,
            "timeframe": timeframe,
            "status": "SIGNAL_DETECTED",
            "timestamp_detected": timestamp,
            "metadata": metadata or {}
        }

        self.trades[signal_id] = trade_info
        self._write_journal(f"[SIGNAL_DETECTED] {signal_id} | {signal_type} @ ${price:.2f} RSI:{rsi:.1f}")
        print(f"📍 [SIGNAL DETECTED] {signal_id} | {signal_type} @ ${price:.2f}")

    def log_order_requested(self, signal_id: str, order_type: str, quantity: float,
                           position_size: float, leverage: float, metadata: Dict = None):
        """
        Log: Orden SOLICITADA a exchange (pero no confirmada aún)

        Segunda etapa - indica que el bot intentó colocar una orden.
        """
        if signal_id not in self.trades:
            return False

        self.stats["total_orders_requested"] += 1
        timestamp = datetime.now(timezone.utc).isoformat()

        self.trades[signal_id].update({
            "status": "ORDER_REQUESTED",
            "order_type": order_type,  # BUY, SELL
            "quantity": quantity,
            "position_size_usdt": position_size,
            "leverage": leverage,
            "timestamp_order_requested": timestamp,
            "metadata": metadata or {}
        })

        self._write_journal(f"[ORDER_REQUESTED] {signal_id} | {order_type} {quantity} @ {leverage}x")
        print(f"📊 [ORDER REQUESTED] {signal_id} | Qty: {quantity} | Size: ${position_size:.2f}")
        return True

    def log_order_placed(self, signal_id: str, order_id: str, exchange: str = "binance"):
        """
        Log: Orden COLOCADA en exchange (confirmada por exchange)

        Tercera etapa - exchange confirmó que la orden está en los libros.
        """
        if signal_id not in self.trades:
            return False

        self.stats["total_orders_placed"] += 1
        timestamp = datetime.now(timezone.utc).isoformat()

        self.trades[signal_id].update({
            "status": "ORDER_PLACED",
            "order_id": order_id,
            "exchange": exchange,
            "timestamp_order_placed": timestamp
        })

        self._write_journal(f"[ORDER_PLACED] {signal_id} | Exchange:{exchange} Order:{order_id}")
        print(f"✅ [ORDER PLACED] {signal_id} | Exchange: {exchange}")
        return True

    def log_trade_filled(self, signal_id: str, actual_entry_price: float,
                        actual_quantity: float, fill_time: Optional[str] = None):
        """
        Log: TRADE FILLED - Posición abierta, orden ejecutada

        Cuarta etapa - LA ORDEN FUE EJECUTADA. Posición abierta en el mercado.
        """
        if signal_id not in self.trades:
            return False

        self.stats["total_trades_filled"] += 1
        timestamp = fill_time or datetime.now(timezone.utc).isoformat()

        self.trades[signal_id].update({
            "status": "TRADE_FILLED",
            "actual_entry_price": actual_entry_price,
            "actual_quantity": actual_quantity,
            "timestamp_trade_filled": timestamp,
            "pnl": None,  # Aún no hay P&L
            "pnl_percent": None
        })

        self._write_journal(f"[TRADE_FILLED] {signal_id} | Entry: ${actual_entry_price:.2f} Qty: {actual_quantity}")
        print(f"💰 [TRADE FILLED] {signal_id} | Entry: ${actual_entry_price:.2f} | Qty: {actual_quantity}")
        return True

    def log_tp_hit(self, signal_id: str, tp_level: int, exit_price: float,
                  pnl: float, pnl_percent: float, filled_percent: float = 0.5):
        """
        Log: Take Profit ejecutado

        TP1: 50% de la posición
        TP2: 25% de la posición
        """
        if signal_id not in self.trades:
            return False

        timestamp = datetime.now(timezone.utc).isoformat()
        tp_key = f"TP{tp_level}_hit"

        self.trades[signal_id].update({
            f"tp{tp_level}_price": exit_price,
            f"tp{tp_level}_filled_percent": filled_percent,
            f"tp{tp_level}_timestamp": timestamp,
            f"tp{tp_level}_pnl": pnl,
            f"tp{tp_level}_pnl_percent": pnl_percent
        })

        self._write_journal(f"[TP{tp_level}_HIT] {signal_id} | Exit: ${exit_price:.2f} | P&L: ${pnl:.2f} ({pnl_percent:.2f}%)")
        print(f"✅ [TP{tp_level} HIT] {signal_id} | P&L: ${pnl:.2f}")
        return True

    def log_stop_loss_hit(self, signal_id: str, stop_price: float, loss: float, loss_percent: float):
        """Log: Stop loss ejecutado"""
        if signal_id not in self.trades:
            return False

        timestamp = datetime.now(timezone.utc).isoformat()
        self.stats["total_losses"] += 1

        self.trades[signal_id].update({
            "status": "STOP_LOSS_HIT",
            "stop_loss_price": stop_price,
            "pnl": -loss,
            "pnl_percent": -loss_percent,
            "timestamp_closed": timestamp
        })

        self._write_journal(f"[STOP_LOSS] {signal_id} | Stop: ${stop_price:.2f} | Loss: -${loss:.2f} (-{loss_percent:.2f}%)")
        print(f"❌ [STOP LOSS] {signal_id} | Loss: -${loss:.2f}")
        return True

    def log_trailing_stop_hit(self, signal_id: str, exit_price: float, pnl: float, pnl_percent: float):
        """Log: Trailing stop ejecutado"""
        if signal_id not in self.trades:
            return False

        timestamp = datetime.now(timezone.utc).isoformat()
        if pnl > 0:
            self.stats["total_wins"] += 1
        else:
            self.stats["total_losses"] += 1

        self.trades[signal_id].update({
            "status": "TRAILING_STOP_HIT",
            "trailing_stop_price": exit_price,
            "pnl": pnl,
            "pnl_percent": pnl_percent,
            "timestamp_closed": timestamp
        })

        self._write_journal(f"[TRAILING_STOP] {signal_id} | Exit: ${exit_price:.2f} | P&L: ${pnl:.2f} ({pnl_percent:.2f}%)")
        print(f"🔴 [TRAILING STOP] {signal_id} | P&L: ${pnl:.2f}")
        return True

    def log_trade_closed(self, signal_id: str, final_pnl: float, final_pnl_percent: float,
                        close_reason: str = "manual"):
        """Log: Trade COMPLETAMENTE CERRADO"""
        if signal_id not in self.trades:
            return False

        timestamp = datetime.now(timezone.utc).isoformat()
        self.stats["total_trades_closed"] += 1
        self.stats["total_pnl"] += final_pnl

        if final_pnl > 0:
            self.stats["total_wins"] += 1
        elif final_pnl < 0:
            self.stats["total_losses"] += 1

        self.trades[signal_id].update({
            "status": "TRADE_CLOSED",
            "final_pnl": final_pnl,
            "final_pnl_percent": final_pnl_percent,
            "close_reason": close_reason,
            "timestamp_closed": timestamp
        })

        self._write_journal(f"[TRADE_CLOSED] {signal_id} | Final P&L: ${final_pnl:.2f} ({final_pnl_percent:.2f}%) | Reason: {close_reason}")
        print(f"🏁 [TRADE CLOSED] {signal_id} | Final P&L: ${final_pnl:.2f}")

        self._save_json()
        return True

    def _write_journal(self, message: str):
        """Escribe en journal.txt con timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {message}\n"
        with open(self.journal_file, "a") as f:
            f.write(line)

    def _save_json(self):
        """Guarda trades en formato JSON"""
        with open(self.json_file, "w") as f:
            json.dump(self.trades, f, indent=2)

    def _save_stats(self):
        """Guarda estadísticas en JSON"""
        with open(self.stats_file, "w") as f:
            json.dump(self.stats, f, indent=2)

    def _load_stats(self):
        """Carga estadísticas previas"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, "r") as f:
                    self.stats = json.load(f)
            except (IOError, OSError, json.JSONDecodeError) as e:
                # CRITICAL FIX: Specific exception handling instead of bare except
                print(f"⚠️ Warning: Failed to load stats file: {e}")
                # Continue with default stats

    def get_summary(self) -> Dict[str, Any]:
        """Retorna resumen de estadísticas"""
        total_closed = self.stats["total_trades_closed"]
        win_rate = 0
        if total_closed > 0:
            win_rate = (self.stats["total_wins"] / total_closed) * 100

        return {
            "total_signals": self.stats["total_signals"],
            "total_trades_filled": self.stats["total_trades_filled"],
            "total_trades_closed": total_closed,
            "wins": self.stats["total_wins"],
            "losses": self.stats["total_losses"],
            "win_rate_percent": win_rate,
            "total_pnl": self.stats["total_pnl"]
        }

    def print_summary(self):
        """Imprime resumen en terminal"""
        summary = self.get_summary()
        print("\n" + "="*60)
        print("📊 TRADE STATISTICS SUMMARY")
        print("="*60)
        print(f"Signals Detected:      {summary['total_signals']}")
        print(f"Trades Filled:         {summary['total_trades_filled']}")
        print(f"Trades Closed:         {summary['total_trades_closed']}")
        print(f"Wins:                  {summary['wins']}")
        print(f"Losses:                {summary['losses']}")
        print(f"Win Rate:              {summary['win_rate_percent']:.1f}%")
        print(f"Total P&L:             ${summary['total_pnl']:.2f}")
        print("="*60 + "\n")


# Global instance
_logger = None

def get_trade_logger() -> TradeLogger:
    """Retorna instancia global del logger"""
    global _logger
    if _logger is None:
        _logger = TradeLogger()
    return _logger
