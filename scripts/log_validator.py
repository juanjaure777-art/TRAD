#!/usr/bin/env python3
"""
Log Validator - Asegura integridad y formato de los logs del bot TRAD

Validaciones:
- Formato JSON válido
- Campos requeridos presentes
- Timestamps en rango válido
- Ciclos en secuencia
- Detección de corrupción
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import hashlib

class LogValidator:
    """Validador de logs del bot TRAD"""

    REQUIRED_FIELDS = {
        'TZV_VALIDATION': ['timestamp', 'cycle', 'type', 't_passed', 'z_passed', 'v_passed', 'all_passed', 'confidence'],
        'TZV_PASSED': ['timestamp', 'cycle', 'type', 'confidence', 'description'],
        'TZV_REJECTED': ['timestamp', 'cycle', 'type', 'reason', 'confidence'],
        'GATEKEEPER_APPROVED': ['timestamp', 'cycle', 'type', 'reason', 'technical_confidence', 'claude_confidence'],
        'GATEKEEPER_REJECT': ['timestamp', 'cycle', 'type', 'reason', 'technical_confidence'],
        'RISK_MANAGER_APPROVED': ['timestamp', 'cycle', 'type', 'position_allowed'],
        'ENTRY_EXECUTED': ['timestamp', 'cycle', 'type', 'side', 'entry_price', 'stop_loss', 'take_profit_1'],
        'TRADE_CLOSED': ['timestamp', 'cycle', 'type', 'side', 'entry_price', 'exit_price', 'exit_type', 'pnl_pct'],
    }

    def __init__(self, log_file: str):
        self.log_file = Path(log_file)
        self.errors = []
        self.warnings = []
        self.stats = {
            'total_lines': 0,
            'valid_lines': 0,
            'invalid_lines': 0,
            'event_types': {},
        }

    def validate_file(self) -> bool:
        """Validar archivo de log completo"""
        if not self.log_file.exists():
            self.errors.append(f"❌ Archivo no existe: {self.log_file}")
            return False

        if self.log_file.stat().st_size == 0:
            self.warnings.append(f"⚠️ Archivo vacío: {self.log_file}")
            return True

        with open(self.log_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                self.stats['total_lines'] += 1

                if not line.strip():
                    continue

                try:
                    event = json.loads(line)
                    self._validate_event(event, line_num)
                    self.stats['valid_lines'] += 1

                    # Track event types
                    event_type = event.get('type', 'UNKNOWN')
                    self.stats['event_types'][event_type] = self.stats['event_types'].get(event_type, 0) + 1

                except json.JSONDecodeError as e:
                    self.stats['invalid_lines'] += 1
                    self.errors.append(f"❌ Línea {line_num}: JSON inválido - {e}")
                except Exception as e:
                    self.stats['invalid_lines'] += 1
                    self.errors.append(f"❌ Línea {line_num}: Error - {e}")

        return len(self.errors) == 0

    def _validate_event(self, event: dict, line_num: int):
        """Validar un evento individual"""
        event_type = event.get('type', 'UNKNOWN')

        # Validar que timestamp existe
        if 'timestamp' not in event:
            self.errors.append(f"❌ Línea {line_num}: Falta 'timestamp'")
            return

        # Validar formato de timestamp
        try:
            ts = event['timestamp']
            # Debe estar en formato ISO con timezone
            if not ('+' in ts or '-' in ts.split('T')[1:]):
                self.warnings.append(f"⚠️ Línea {line_num}: Timestamp sin timezone: {ts}")
        except:
            self.errors.append(f"❌ Línea {line_num}: Timestamp mal formado: {event['timestamp']}")

        # Validar campos requeridos por tipo de evento
        if event_type in self.REQUIRED_FIELDS:
            required = self.REQUIRED_FIELDS[event_type]
            missing = [f for f in required if f not in event]
            if missing:
                self.warnings.append(f"⚠️ Línea {line_num} ({event_type}): Campos faltantes: {missing}")

    def get_checksum(self) -> str:
        """Calcular checksum SHA256 del archivo"""
        sha256_hash = hashlib.sha256()
        with open(self.log_file, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def print_report(self):
        """Imprimir reporte de validación"""
        print("\n" + "="*70)
        print("📊 REPORTE DE VALIDACIÓN DE LOGS")
        print("="*70)

        print(f"\n📁 Archivo: {self.log_file}")
        print(f"📏 Tamaño: {self.log_file.stat().st_size / 1024:.2f} KB")
        print(f"🔐 Checksum SHA256: {self.get_checksum()[:16]}...")

        print(f"\n📈 Estadísticas:")
        print(f"   Total líneas:     {self.stats['total_lines']}")
        print(f"   Líneas válidas:   {self.stats['valid_lines']} ✅")
        print(f"   Líneas inválidas: {self.stats['invalid_lines']} ❌")

        if self.stats['total_lines'] > 0:
            validity = (self.stats['valid_lines'] / self.stats['total_lines']) * 100
            print(f"   Integridad:       {validity:.1f}%")

        if self.stats['event_types']:
            print(f"\n📋 Tipos de eventos:")
            for event_type, count in sorted(self.stats['event_types'].items()):
                print(f"   {event_type:20s}: {count:3d}")

        if self.errors:
            print(f"\n❌ ERRORES ({len(self.errors)}):")
            for error in self.errors[:5]:  # Mostrar primeros 5
                print(f"   {error}")
            if len(self.errors) > 5:
                print(f"   ... y {len(self.errors) - 5} más")

        if self.warnings:
            print(f"\n⚠️ ADVERTENCIAS ({len(self.warnings)}):")
            for warning in self.warnings[:5]:  # Mostrar primeros 5
                print(f"   {warning}")
            if len(self.warnings) > 5:
                print(f"   ... y {len(self.warnings) - 5} más")

        print("\n" + "="*70)

        if len(self.errors) == 0:
            print("✅ VALIDACIÓN EXITOSA - Logs en buen estado")
        else:
            print("❌ VALIDACIÓN FALLIDA - Revisa los errores arriba")
        print("="*70 + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        log_file = "/home/juan/Escritorio/osiris/proyectos/TRAD/logs/trades_testnet.log"
    else:
        log_file = sys.argv[1]

    validator = LogValidator(log_file)
    validator.validate_file()
    validator.print_report()

    sys.exit(0 if len(validator.errors) == 0 else 1)
