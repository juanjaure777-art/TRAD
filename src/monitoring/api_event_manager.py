"""
API EVENT MANAGER - Sistema de Notificación de Eventos Críticos
===============================================================

Responsabilidad: Monitorear y notificar eventos críticos de APIs.
Evita fallos silenciosos - SIEMPRE notifica lo que está pasando.

Eventos monitoreados:
1. API Health (Binance, Anthropic)
2. Authentication failures
3. Rate limit warnings
4. Network timeouts/retries
5. Trade execution events
6. Errors críticos
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

class APIEventManager:
    """Gestor centralizado de eventos críticos de APIs"""

    def __init__(self, log_dir: str = "logs/api_events"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Archivos de log
        self.events_log = self.log_dir / "api_events.jsonl"
        self.critical_log = self.log_dir / "critical_events.log"
        self.health_status_file = self.log_dir / "api_health_status.json"

        # En-memoria
        self.event_buffer: List[Dict[str, Any]] = []
        self.api_health: Dict[str, Dict[str, Any]] = {
            "binance": {
                "status": "UNKNOWN",
                "last_check": None,
                "consecutive_failures": 0,
                "last_error": None
            },
            "anthropic": {
                "status": "UNKNOWN",
                "last_check": None,
                "consecutive_failures": 0,
                "last_error": None
            }
        }

        self.logger = logging.getLogger(__name__)

    def log_event(self,
                  event_type: str,
                  severity: str,  # CRITICAL, WARNING, INFO
                  api_name: str,  # binance, anthropic
                  message: str,
                  details: Optional[Dict] = None) -> None:
        """
        Log evento crítico con timestamp UTC

        event_type: API_HEALTH, AUTH_ERROR, RATE_LIMIT, TIMEOUT, TRADE_EVENT, etc.
        severity: CRITICAL (❌), WARNING (⚠️), INFO (ℹ️)
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        event = {
            "timestamp": timestamp,
            "event_type": event_type,
            "severity": severity,
            "api_name": api_name,
            "message": message,
            "details": details or {}
        }

        # En-memoria
        self.event_buffer.append(event)

        # JSONL (parseable)
        with open(self.events_log, "a") as f:
            f.write(json.dumps(event) + "\n")

        # Notificar crítico INMEDIATAMENTE
        if severity == "CRITICAL":
            self._notify_critical(event)
            with open(self.critical_log, "a") as f:
                f.write(f"\n[{timestamp}] {severity} | {api_name} | {event_type}\n")
                f.write(f"Message: {message}\n")
                f.write(f"Details: {json.dumps(details, indent=2)}\n")
                f.write("─" * 80 + "\n")

        # Print console
        emoji = {"CRITICAL": "❌", "WARNING": "⚠️", "INFO": "ℹ️"}.get(severity, "📝")
        print(f"{emoji} [{api_name.upper()}] {event_type}: {message}")

    def update_api_health(self,
                         api_name: str,
                         status: str,  # HEALTHY, DEGRADED, DOWN
                         error: Optional[str] = None) -> None:
        """Actualiza estado de salud de API"""
        timestamp = datetime.now(timezone.utc).isoformat()

        self.api_health[api_name]["status"] = status
        self.api_health[api_name]["last_check"] = timestamp

        if error:
            self.api_health[api_name]["last_error"] = error
            self.api_health[api_name]["consecutive_failures"] += 1
            severity = "CRITICAL" if self.api_health[api_name]["consecutive_failures"] > 3 else "WARNING"
            self.log_event(
                event_type="API_HEALTH_CHECK",
                severity=severity,
                api_name=api_name,
                message=f"API {status}: {error}",
                details={
                    "consecutive_failures": self.api_health[api_name]["consecutive_failures"],
                    "error": error
                }
            )
        else:
            self.api_health[api_name]["consecutive_failures"] = 0
            self.log_event(
                event_type="API_HEALTH_CHECK",
                severity="INFO",
                api_name=api_name,
                message=f"API {status}",
                details={}
            )

        # Guardar estado
        self._save_health_status()

    def log_authentication_error(self,
                                api_name: str,
                                error_msg: str,
                                will_exit: bool = False) -> None:
        """Log error de autenticación"""
        severity = "CRITICAL" if will_exit else "WARNING"
        self.log_event(
            event_type="AUTHENTICATION_ERROR",
            severity=severity,
            api_name=api_name,
            message=f"Invalid credentials - {error_msg}",
            details={
                "action": "EXIT" if will_exit else "RETRY",
                "error": error_msg
            }
        )

    def log_rate_limit_warning(self,
                              api_name: str,
                              remaining: int,
                              reset_time: Optional[str] = None) -> None:
        """Log warning de rate limit"""
        severity = "CRITICAL" if remaining < 10 else "WARNING"
        self.log_event(
            event_type="RATE_LIMIT_WARNING",
            severity=severity,
            api_name=api_name,
            message=f"Rate limit approaching - {remaining} requests remaining",
            details={
                "remaining_requests": remaining,
                "reset_time": reset_time
            }
        )

    def log_timeout(self,
                   api_name: str,
                   endpoint: str,
                   timeout_seconds: int,
                   retry_count: int) -> None:
        """Log timeout en API call"""
        severity = "CRITICAL" if retry_count > 2 else "WARNING"
        self.log_event(
            event_type="TIMEOUT",
            severity=severity,
            api_name=api_name,
            message=f"Timeout on {endpoint} after {timeout_seconds}s (retry {retry_count})",
            details={
                "endpoint": endpoint,
                "timeout_seconds": timeout_seconds,
                "retry_count": retry_count
            }
        )

    def log_trade_event(self,
                       event_type: str,  # ENTRY_EXECUTED, TP_HIT, SL_HIT, etc.
                       trade_id: str,
                       entry_price: float,
                       symbol: str,
                       details: Optional[Dict] = None) -> None:
        """Log evento de trading importante"""
        self.log_event(
            event_type=f"TRADE_{event_type}",
            severity="INFO",
            api_name="trading",
            message=f"{event_type} on {symbol} @ ${entry_price:.2f}",
            details={
                "trade_id": trade_id,
                "entry_price": entry_price,
                "symbol": symbol,
                **(details or {})
            }
        )

    def log_signal_generation(self,
                             signal_type: str,  # BULLISH, BEARISH
                             entry_price: float,
                             quality_score: float,
                             confidence: float,
                             timeframe: str = "4h") -> None:
        """Log señal generada"""
        self.log_event(
            event_type="SIGNAL_GENERATED",
            severity="INFO",
            api_name="strategy",
            message=f"{signal_type} signal @ ${entry_price:.2f} (quality: {quality_score:.0f}%)",
            details={
                "signal_type": signal_type,
                "entry_price": entry_price,
                "quality_score": quality_score,
                "confidence": confidence,
                "timeframe": timeframe
            }
        )

    def log_gatekeeper_validation(self,
                                 trade_id: str,
                                 approved: bool,
                                 reasoning: str,
                                 confidence_score: float) -> None:
        """Log validación GatekeeperV2"""
        self.log_event(
            event_type="GATEKEEPER_VALIDATION",
            severity="INFO",
            api_name="anthropic",
            message=f"Entry {'APPROVED' if approved else 'REJECTED'} - {reasoning[:60]}...",
            details={
                "trade_id": trade_id,
                "approved": approved,
                "reasoning": reasoning,
                "confidence_score": confidence_score
            }
        )

    def log_error(self,
                 error_type: str,
                 message: str,
                 api_name: str = "bot",
                 exception_details: Optional[str] = None,
                 is_fatal: bool = False) -> None:
        """Log error con traceback"""
        severity = "CRITICAL" if is_fatal else "WARNING"
        self.log_event(
            event_type=f"ERROR_{error_type}",
            severity=severity,
            api_name=api_name,
            message=message,
            details={
                "exception": exception_details,
                "is_fatal": is_fatal
            }
        )

    def get_health_summary(self) -> Dict[str, Any]:
        """Retorna resumen de salud de APIs"""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "apis": self.api_health,
            "total_events": len(self.event_buffer),
            "critical_events": sum(1 for e in self.event_buffer if e["severity"] == "CRITICAL"),
            "warnings": sum(1 for e in self.event_buffer if e["severity"] == "WARNING")
        }

    def print_health_status(self) -> None:
        """Imprime estado de salud en terminal"""
        summary = self.get_health_summary()
        print("\n" + "═" * 80)
        print("🔍 API HEALTH STATUS")
        print("═" * 80)
        print(f"Timestamp: {summary['timestamp']}")
        print()

        for api_name, health in summary["apis"].items():
            status_icon = "✅" if health["status"] == "HEALTHY" else "⚠️" if health["status"] == "DEGRADED" else "❌"
            print(f"{status_icon} {api_name.upper()}")
            print(f"   Status: {health['status']}")
            print(f"   Last Check: {health['last_check']}")
            print(f"   Consecutive Failures: {health['consecutive_failures']}")
            if health['last_error']:
                print(f"   Last Error: {health['last_error'][:60]}...")
            print()

        print(f"Total Events: {summary['total_events']}")
        print(f"Critical Events: {summary['critical_events']}")
        print(f"Warnings: {summary['warnings']}")
        print("═" * 80 + "\n")

    def _notify_critical(self, event: Dict[str, Any]) -> None:
        """Notifica evento crítico (hook para notificaciones externas)"""
        # TODO: Integrar con webhook, email, telegram, etc.
        # Por ahora solo printea de forma destacada
        print("\n" + "!" * 80)
        print(f"!!! CRITICAL EVENT: {event['api_name'].upper()} - {event['event_type']}")
        print(f"!!! {event['message']}")
        print("!" * 80 + "\n")

    def _save_health_status(self) -> None:
        """Guarda estado de salud en JSON"""
        with open(self.health_status_file, "w") as f:
            json.dump(self.get_health_summary(), f, indent=2)


# Global instance
_manager = None

def get_event_manager() -> APIEventManager:
    """Retorna instancia global del gestor"""
    global _manager
    if _manager is None:
        _manager = APIEventManager()
    return _manager
