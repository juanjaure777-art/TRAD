#!/usr/bin/env python3
"""
TRAD Bot v3.5+ Real-Time Monitor
Monitorea el bot en tiempo real leyendo los eventos de trading
"""

import json
import os
import time
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# Timezone configuration for Argentina
try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Fallback for Python < 3.9
    ZoneInfo = None

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

class LiveMonitor:
    def __init__(self, log_file="trades_testnet.log"):
        self.log_file = log_file
        self.last_position = 0
        self.cycles_seen = set()
        self.stats = {
            'total_cycles': 0,
            'signal_detections': 0,
            'tzv_validations': 0,
            'tzv_failed': 0,
            'tzv_passed': 0,
            'entries': 0,
            'exits': 0,
            'entries_by_side': defaultdict(int),
            'exits_by_reason': defaultdict(int),
            'pnl_total': 0.0,
            'pnl_trades': [],
            'current_position': None,
            'gatekeeper_rejections': 0,
            'last_event': None,
        }

    def parse_log(self):
        """Lee nuevos eventos del log"""
        if not os.path.exists(self.log_file):
            return []

        with open(self.log_file, 'r') as f:
            f.seek(self.last_position)
            new_lines = f.readlines()
            self.last_position = f.tell()

        events = []
        for line in new_lines:
            try:
                event = json.loads(line.strip())
                events.append(event)
            except:
                pass

        return events

    def process_events(self, events):
        """Procesa eventos y actualiza estadísticas"""
        for event in events:
            event_type = event.get('type')
            self.stats['last_event'] = event

            # Contar ciclos únicos
            cycle = event.get('cycle')
            if cycle and cycle not in self.cycles_seen:
                self.cycles_seen.add(cycle)
                self.stats['total_cycles'] = len(self.cycles_seen)

            # Procesar por tipo
            if event_type == 'OPEN':
                self.stats['entries'] += 1
                side = event.get('side')
                self.stats['entries_by_side'][side] += 1
                self.stats['current_position'] = {
                    'type': 'OPEN',
                    'side': side,
                    'entry_price': event.get('entry_price'),
                    'sl': event.get('sl'),
                    'tp1': event.get('tp1'),
                    'tp2': event.get('tp2'),
                    'confidence': event.get('confidence'),
                    'cycle': cycle,
                }

            elif event_type == 'CLOSE':
                self.stats['exits'] += 1
                reason = event.get('reason', 'unknown')
                self.stats['exits_by_reason'][reason] += 1
                pnl = event.get('pnl', 0)
                self.stats['pnl_total'] += pnl
                self.stats['pnl_trades'].append(pnl)
                self.stats['current_position'] = None

            elif event_type == 'TZV_VALIDATION':
                self.stats['tzv_validations'] += 1
                if event.get('all_passed'):
                    self.stats['tzv_passed'] += 1
                else:
                    self.stats['tzv_failed'] += 1

            elif event_type == 'GATEKEEPER_REJECT':
                self.stats['gatekeeper_rejections'] += 1

    def print_dashboard(self):
        """Imprime dashboard en tiempo real"""
        os.system('clear') if os.name == 'posix' else os.system('cls')

        print(f"\n{'='*100}")
        print(f"🤖 TRAD BOT v3.5+ - LIVE MONITOR")
        print(f"{'='*100}")
        print(f"⏰ {get_local_time().strftime('%Y-%m-%d %H:%M:%S')}")

        # Stats principales
        print(f"\n📊 OPERACIÓN:")
        print(f"   Ciclos ejecutados: {self.stats['total_cycles']}")
        print(f"   Posición activa: {'✅ SÍ' if self.stats['current_position'] else '❌ NO'}")

        # T+Z+V Stats
        print(f"\n🧠 CRECETRADER T+Z+V VALIDATION:")
        print(f"   Total validaciones: {self.stats['tzv_validations']}")
        print(f"   ✅ Aprobadas: {self.stats['tzv_passed']}")
        print(f"   ❌ Rechazadas: {self.stats['tzv_failed']}")
        if self.stats['tzv_validations'] > 0:
            pass_rate = (self.stats['tzv_passed'] / self.stats['tzv_validations']) * 100
            print(f"   Pass rate: {pass_rate:.1f}%")

        # Entrada/Salida
        print(f"\n📈 OPERACIONES:")
        print(f"   Entradas totales: {self.stats['entries']}")
        if self.stats['entries_by_side']:
            for side, count in self.stats['entries_by_side'].items():
                print(f"      {side}: {count}")
        print(f"   Salidas totales: {self.stats['exits']}")
        if self.stats['exits_by_reason']:
            for reason, count in sorted(self.stats['exits_by_reason'].items(), key=lambda x: x[1], reverse=True):
                print(f"      {reason}: {count}")

        # P&L
        print(f"\n💰 P&L:")
        print(f"   Total P&L: {self.stats['pnl_total']:.2f}%")
        if self.stats['pnl_trades']:
            wins = sum(1 for pnl in self.stats['pnl_trades'] if pnl > 0)
            losses = sum(1 for pnl in self.stats['pnl_trades'] if pnl < 0)
            print(f"   Trades ganadores: {wins}")
            print(f"   Trades perdedores: {losses}")
            if self.stats['entries'] > 0:
                win_rate = (wins / self.stats['entries'] * 100) if self.stats['entries'] > 0 else 0
                print(f"   Win rate: {win_rate:.1f}%")

        # Rechazo Gatekeeper
        print(f"\n🛡️  VALIDACIONES:")
        print(f"   GatekeeperV2 rechazos: {self.stats['gatekeeper_rejections']}")

        # Posición actual
        if self.stats['current_position']:
            pos = self.stats['current_position']
            emoji = "🟢" if pos['side'] == 'LONG' else "🔴"
            print(f"\n🔓 POSICIÓN ABIERTA:")
            print(f"   {emoji} {pos['side']} @ ${pos['entry_price']:.2f}")
            print(f"   SL: ${pos['sl']:.2f} | TP1: ${pos['tp1']:.2f} | TP2: ${pos['tp2']:.2f}")
            print(f"   Confianza: {pos['confidence']:.0f}%")
            print(f"   Ciclo: #{pos['cycle']}")

        # Último evento
        if self.stats['last_event']:
            event = self.stats['last_event']
            print(f"\n📍 ÚLTIMO EVENTO:")
            print(f"   Tipo: {event.get('type')}")
            print(f"   Ciclo: #{event.get('cycle')}")
            if event.get('type') == 'TZV_VALIDATION':
                desc = event.get('description', '')
                print(f"   Estado: {desc}")
            print(f"   Timestamp: {event.get('timestamp')}")

        print(f"\n{'='*100}")
        print(f"Presiona Ctrl+C para salir | Actualizando cada 10 segundos...")

    def watch(self, interval=10):
        """Monitorea continuamente"""
        print(f"🔄 Iniciando monitor en vivo...")
        print(f"📁 Log: {self.log_file}")
        print(f"⏳ Intervalo de actualización: {interval}s")

        try:
            while True:
                events = self.parse_log()
                if events:
                    self.process_events(events)

                self.print_dashboard()
                time.sleep(interval)

        except KeyboardInterrupt:
            print(f"\n\n⏸️  Monitor detenido")
            print(f"📊 Resumen final:")
            print(f"   Total ciclos: {self.stats['total_cycles']}")
            print(f"   Total entradas: {self.stats['entries']}")
            print(f"   Total salidas: {self.stats['exits']}")
            print(f"   P&L total: {self.stats['pnl_total']:.2f}%")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    monitor = LiveMonitor()
    monitor.watch(interval=10)
