#!/usr/bin/env python3
"""
TRAD Bot Health Monitor - Monitoreo continuo de salud del bot
Detecta anomalías, errores y estado anormal
"""

import json
import time
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

def get_local_time():
    """Get current time in Argentina timezone"""
    try:
        if ZoneInfo:
            return datetime.now(ZoneInfo("America/Argentina/Buenos_Aires"))
    except Exception:
        pass
    try:
        tz_offset = timezone(timedelta(hours=-3))
        return datetime.now(tz_offset)
    except Exception:
        return datetime.now()

class BotHealthMonitor:
    def __init__(self, log_file="trades_testnet.log", check_interval=30):
        self.log_file = log_file
        self.check_interval = check_interval
        self.last_position = 0
        self.last_cycle_count = 0
        self.consecutive_errors = 0
        self.max_errors = 3
        self.alert_log = "bot_health_alerts.log"
        
    def is_bot_running(self):
        """Verifica si el bot está corriendo"""
        try:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return "python3 src/bot.py" in result.stdout and "grep" not in result.stdout
        except Exception:
            return False
    
    def read_new_events(self):
        """Lee nuevos eventos del log"""
        try:
            with open(self.log_file, 'r') as f:
                f.seek(self.last_position)
                new_lines = f.readlines()
                self.last_position = f.tell()
            
            events = []
            for line in new_lines:
                try:
                    event = json.loads(line.strip())
                    events.append(event)
                except json.JSONDecodeError:
                    pass
            
            return events
        except Exception as e:
            self.log_alert(f"ERROR reading log: {e}")
            return []
    
    def check_health(self):
        """Realiza chequeo de salud"""
        alerts = []
        
        # 1. Verificar que el bot está corriendo
        if not self.is_bot_running():
            alerts.append("🚨 CRÍTICO: Bot no está corriendo!")
            return alerts
        
        # 2. Leer nuevos eventos
        events = self.read_new_events()
        
        if not events:
            # Sin eventos nuevos en este ciclo
            return alerts
        
        # 3. Análisis de eventos
        for event in events:
            event_type = event.get('type')
            timestamp = event.get('timestamp')
            
            # Detectar errores
            if event_type == 'ERROR':
                error_msg = event.get('error', 'Unknown error')
                alerts.append(f"⚠️  ERROR REGISTRADO: {error_msg} @ {timestamp}")
                self.consecutive_errors += 1
            else:
                self.consecutive_errors = 0
            
            # Detectar ciclos sin avance
            cycle = event.get('cycle', 0)
            if cycle and cycle <= self.last_cycle_count:
                alerts.append(f"⚠️  Ciclo duplicado/regresivo: {cycle} @ {timestamp}")
            
            if cycle:
                self.last_cycle_count = cycle
        
        # 4. Alertas por errores consecutivos
        if self.consecutive_errors >= self.max_errors:
            alerts.append(f"🚨 {self.consecutive_errors} errores consecutivos detectados!")
        
        # 5. Verificar que los ciclos avanzan (no stuck)
        if len(events) == 0 and self.check_interval > 60:
            # Si no hay eventos en 60+ segundos, podría estar stuck
            alerts.append("⚠️  Sin eventos en últimos ciclos - verificar si está stuck")
        
        return alerts
    
    def log_alert(self, message):
        """Logguea alerta"""
        timestamp = get_local_time().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.alert_log, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")
        print(f"{message}")
    
    def run(self):
        """Loop de monitoreo continuo"""
        print(f"🔍 Iniciando Health Monitor (intervalo: {self.check_interval}s)")
        print(f"📁 Log: {self.log_file}")
        print(f"📋 Alertas: {self.alert_log}")
        
        try:
            iteration = 0
            while True:
                iteration += 1
                
                # Chequeo de salud
                alerts = self.check_health()
                
                # Log de alertas
                for alert in alerts:
                    self.log_alert(alert)
                
                # Status summary cada 10 iteraciones
                if iteration % 10 == 0:
                    try:
                        file_size = Path(self.log_file).stat().st_size
                        file_lines = sum(1 for _ in open(self.log_file))
                        status = "✅ OK" if not alerts else f"⚠️  {len(alerts)} alertas"
                        print(f"[{iteration*self.check_interval}s] {status} | Ciclos: {self.last_cycle_count} | Eventos: {file_lines}")
                    except Exception:
                        pass
                
                time.sleep(self.check_interval)
        
        except KeyboardInterrupt:
            print(f"\n⏸️  Monitor detenido")
        except Exception as e:
            self.log_alert(f"🚨 FATAL ERROR en monitor: {e}")

if __name__ == "__main__":
    monitor = BotHealthMonitor(check_interval=30)
    monitor.run()
