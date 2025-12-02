#!/usr/bin/env python3
"""
Trading Sessions Manager - v3.3
Gestiona las tres sesiones globales de trading (ASIAN, EUROPEAN, AMERICAN)
Determina horarios activos, off-hours, y momentos de máxima liquidez
"""

from datetime import datetime, time, timedelta
from typing import Optional, List
from dataclasses import dataclass

@dataclass
class TradingSession:
    """Representa una sesión de trading global"""
    name: str  # "ASIAN", "EUROPEAN", "AMERICAN"
    start_utc: str  # "21:00"
    end_utc: str  # "06:00" (puede ser al día siguiente)
    opening_hour_start: str  # "21:00" - cuando abre
    opening_hour_end: str  # "22:00" - fin del pico de liquidez

    def is_active(self, current_time: datetime) -> bool:
        """
        Verifica si la sesión está activa en el horario actual (UTC)
        Maneja sesiones que cruzan medianoche (ASIAN: 21:00 día anterior -> 06:00 día actual)
        """
        current_hour = current_time.hour
        current_minute = current_time.minute
        current_time_minutes = current_hour * 60 + current_minute

        start_parts = self.start_utc.split(':')
        start_minutes = int(start_parts[0]) * 60 + int(start_parts[1])

        end_parts = self.end_utc.split(':')
        end_minutes = int(end_parts[0]) * 60 + int(end_parts[1])

        # Sesión que cruza medianoche (ASIAN: 21:00 -> 06:00 next day)
        if start_minutes > end_minutes:
            return current_time_minutes >= start_minutes or current_time_minutes < end_minutes

        # Sesión normal (EUROPEAN: 07:00 -> 16:00)
        return start_minutes <= current_time_minutes < end_minutes

    def is_opening_hour(self, current_time: datetime) -> bool:
        """
        Verifica si estamos en la hora de apertura de máxima liquidez
        Ejemplos:
        - ASIAN: 21:00-22:00 (Tokyo opening)
        - EUROPEAN: 08:00-09:00 (London opening)
        - AMERICAN: 13:30-14:30 (NY opening)
        """
        current_hour = current_time.hour
        current_minute = current_time.minute
        current_time_minutes = current_hour * 60 + current_minute

        opening_start_parts = self.opening_hour_start.split(':')
        opening_start_minutes = int(opening_start_parts[0]) * 60 + int(opening_start_parts[1])

        opening_end_parts = self.opening_hour_end.split(':')
        opening_end_minutes = int(opening_end_parts[0]) * 60 + int(opening_end_parts[1])

        return opening_start_minutes <= current_time_minutes < opening_end_minutes

    def get_closing_alert_time(self) -> str:
        """
        Retorna la hora en que debe alertar sobre cierre de sesión (30 min antes)
        Retorna en formato "HH:MM"
        """
        end_parts = self.end_utc.split(':')
        end_hour = int(end_parts[0])
        end_minute = int(end_parts[1])

        # Restar 30 minutos
        total_minutes = end_hour * 60 + end_minute - 30

        if total_minutes < 0:
            total_minutes += 24 * 60  # Day before

        alert_hour = (total_minutes // 60) % 24
        alert_minute = total_minutes % 60

        return f"{alert_hour:02d}:{alert_minute:02d}"

    def get_session_name(self) -> str:
        """Retorna nombre amigable de la sesión"""
        return self.name


# Configuración de las tres sesiones globales
TRADING_SESSIONS: List[TradingSession] = [
    TradingSession(
        name="ASIAN",
        start_utc="21:00",
        end_utc="06:00",  # Día siguiente
        opening_hour_start="21:00",
        opening_hour_end="22:00"
    ),
    TradingSession(
        name="EUROPEAN",
        start_utc="07:00",
        end_utc="16:00",
        opening_hour_start="08:00",  # London opening
        opening_hour_end="09:00"
    ),
    TradingSession(
        name="AMERICAN",
        start_utc="13:00",
        end_utc="22:00",
        opening_hour_start="13:30",  # NY opening
        opening_hour_end="14:30"
    )
]


def get_active_session(current_time: Optional[datetime] = None) -> Optional[TradingSession]:
    """
    Obtiene la sesión activa en el momento actual (UTC)
    Si current_time es None, usa datetime.now(timezone.utc)
    Retorna None si estamos en off-hours
    """
    if current_time is None:
        from datetime import timezone
        current_time = datetime.now(timezone.utc)

    for session in TRADING_SESSIONS:
        if session.is_active(current_time):
            return session

    return None


def get_session_by_name(name: str) -> Optional[TradingSession]:
    """Obtiene una sesión por nombre"""
    for session in TRADING_SESSIONS:
        if session.name == name:
            return session
    return None


def is_in_opening_hour(current_time: Optional[datetime] = None) -> bool:
    """
    Verifica si estamos en una hora de apertura de máxima liquidez
    """
    if current_time is None:
        from datetime import timezone
        current_time = datetime.now(timezone.utc)

    session = get_active_session(current_time)
    if session:
        return session.is_opening_hour(current_time)
    return False


def is_off_hours(current_time: Optional[datetime] = None) -> bool:
    """Verifica si estamos fuera de horario de trading"""
    if current_time is None:
        from datetime import timezone
        current_time = datetime.now(timezone.utc)

    return get_active_session(current_time) is None


def get_session_status() -> dict:
    """
    Retorna estado actual de todas las sesiones
    Útil para debugging y logging
    """
    from datetime import timezone
    now = datetime.now(timezone.utc)
    current_time_str = now.strftime("%H:%M")

    status = {
        "current_time_utc": current_time_str,
        "active_session": None,
        "is_opening_hour": False,
        "sessions": {}
    }

    active = get_active_session(now)
    if active:
        status["active_session"] = active.name
        status["is_opening_hour"] = active.is_opening_hour(now)

    for session in TRADING_SESSIONS:
        status["sessions"][session.name] = {
            "hours": f"{session.start_utc}-{session.end_utc}",
            "is_active": session.is_active(now),
            "is_opening": session.is_opening_hour(now)
        }

    return status
