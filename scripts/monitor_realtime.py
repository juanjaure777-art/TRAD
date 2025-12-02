#!/usr/bin/env python3
"""
TRAD Bot Monitor - Real-time Status Reporter
Monitorea el estado del bot en tiempo real y reporta eventos
"""

import os
import time
import json
import subprocess
import signal
from datetime import datetime
from pathlib import Path

class BotMonitor:
    def __init__(self):
        self.mode = 'testnet'  # Cambiar a 'live' si aplica
        self.log_file = f"trades_{self.mode}.log"
        self.last_position = None
        self.events_processed = 0
        self.cycles_count = 0
        self.trades_count = 0
        self.last_check_time = None

    def get_recent_events(self, lines=20):
        """Lee los últimos eventos del log"""
        try:
            if not os.path.exists(self.log_file):
                return []

            with open(self.log_file, 'r') as f:
                all_lines = f.readlines()

            recent = all_lines[-lines:] if len(all_lines) > lines else all_lines
            return recent
        except Exception as e:
            return [f"❌ Error reading log: {e}"]

    def parse_log_entry(self, line):
        """Parsea una línea del log JSON"""
        try:
            return json.loads(line.strip())
        except:
            return None

    def get_status_summary(self):
        """Obtiene resumen del estado actual"""
        events = self.get_recent_events(50)

        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_events': len(events),
            'last_event': None,
            'open_position': False,
            'recent_trades': [],
            'cycle_count': 0,
            'signal_detections': 0,
            'entries': 0,
            'exits': 0,
            'gatekeeper_rejections': 0,
            'tzv_validations': 0,
            'tzv_rejections': 0,
        }

        for line in events:
            entry = self.parse_log_entry(line)
            if not entry:
                continue

            event_type = entry.get('type')

            # Actualizar resumen
            summary['cycle_count'] = max(summary['cycle_count'], entry.get('cycle', 0))
            summary['last_event'] = entry

            # Contar eventos por tipo
            if event_type == 'OPEN':
                summary['entries'] += 1
                summary['open_position'] = True
                summary['recent_trades'].append({
                    'type': 'OPEN',
                    'side': entry.get('side'),
                    'entry_price': entry.get('entry_price'),
                    'sl': entry.get('sl'),
                    'tp1': entry.get('tp1'),
                    'confidence': entry.get('confidence'),
                    'cycle': entry.get('cycle'),
                    'crecetrader_location': entry.get('crecetrader_location'),
                    'crecetrader_quality': entry.get('crecetrader_quality'),
                })

            elif event_type == 'CLOSE':
                summary['exits'] += 1
                summary['open_position'] = False
                summary['recent_trades'].append({
                    'type': 'CLOSE',
                    'pnl': entry.get('pnl'),
                    'reason': entry.get('reason'),
                    'cycle': entry.get('cycle'),
                })

            elif event_type == 'SIGNAL_DETECTED':
                summary['signal_detections'] += 1

            elif event_type == 'GATEKEEPER_REJECT':
                summary['gatekeeper_rejections'] += 1

            elif event_type == 'TZV_VALIDATION':
                summary['tzv_validations'] += 1

            elif event_type == 'TZV_REJECTED':
                summary['tzv_rejections'] += 1

        summary['recent_trades'] = summary['recent_trades'][-5:]  # Últimas 5
        return summary

    def print_status(self):
        """Imprime estado en formato legible"""
        status = self.get_status_summary()

        print(f"\n{'='*80}")
        print(f"⏰ BOT STATUS - {status['timestamp']}")
        print(f"{'='*80}")

        print(f"\n📊 CICLOS & EVENTOS:")
        print(f"   Ciclos ejecutados: #{status['cycle_count']}")
        print(f"   Total eventos: {status['total_events']}")
        print(f"   Signals detectadas: {status['signal_detections']}")

        print(f"\n🔄 POSICIONES:")
        print(f"   Posición abierta: {'✅ SÍ' if status['open_position'] else '❌ NO'}")
        print(f"   Entradas totales: {status['entries']}")
        print(f"   Salidas totales: {status['exits']}")

        print(f"\n🧠 VALIDACIONES CRECETRADER:")
        print(f"   T+Z+V validaciones: {status['tzv_validations']}")
        print(f"   T+Z+V rechazos: {status['tzv_rejections']}")
        print(f"   GatekeeperV2 rechazos: {status['gatekeeper_rejections']}")

        print(f"\n📈 ÚLTIMAS OPERACIONES:")
        if status['recent_trades']:
            for i, trade in enumerate(status['recent_trades'][-3:]):
                if trade['type'] == 'OPEN':
                    emoji = "🟢" if trade['side'] == 'LONG' else "🔴"
                    print(f"   {emoji} ABIERTO {trade['side']} @ ${trade['entry_price']:.2f} | "
                          f"Conf:{trade.get('confidence', 0):.0f}% | "
                          f"Q:{trade.get('crecetrader_quality', 0):.0f}% | "
                          f"Loc:{trade.get('crecetrader_location', '?')}")
                elif trade['type'] == 'CLOSE':
                    emoji = "🟢" if trade['pnl'] > 0 else "🔴"
                    print(f"   {emoji} CERRADO - P&L: {trade['pnl']:.2f}% | "
                          f"Razón: {trade['reason']}")
        else:
            print(f"   (Sin operaciones aún)")

        if status['last_event']:
            print(f"\n⏱️  ÚLTIMO EVENTO:")
            event = status['last_event']
            print(f"   Tipo: {event.get('type')} | Ciclo: #{event.get('cycle')}")
            if event.get('type') == 'OPEN':
                print(f"   → Entry: ${event.get('entry_price'):.2f} | "
                      f"SL: ${event.get('sl'):.2f} | TP1: ${event.get('tp1'):.2f}")

        print(f"\n{'='*80}\n")

    def watch(self, interval=30):
        """Monitorea el bot continuamente"""
        print(f"👀 INICIANDO MONITOR - Intervalo de reporte: {interval}s")
        print(f"📁 Monitoreando: {self.log_file}")
        print(f"🔴 Presiona Ctrl+C para detener el monitor (el bot seguirá corriendo)")

        try:
            while True:
                self.print_status()
                time.sleep(interval)
        except KeyboardInterrupt:
            print(f"\n⏸️  Monitor pausado (bot aún está corriendo)")
        except Exception as e:
            print(f"❌ Error en monitor: {e}")

if __name__ == "__main__":
    monitor = BotMonitor()
    monitor.watch(interval=30)  # Reportar cada 30 segundos
