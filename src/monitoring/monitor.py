#!/usr/bin/env python3
"""
TRAD Bot - Monitor en Vivo
Analiza el comportamiento del bot en tiempo real
"""

import json
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict

class BotMonitor:
    def __init__(self, log_file="trades_testnet.log"):
        self.log_file = log_file
        self.trades = []
        self.load_trades()

    def load_trades(self):
        """Cargar todos los trades desde el archivo"""
        if not os.path.exists(self.log_file):
            print(f"⚠️  Archivo no encontrado: {self.log_file}")
            return

        self.trades = []
        try:
            with open(self.log_file) as f:
                for line in f:
                    if line.strip():
                        try:
                            self.trades.append(json.loads(line))
                        except:
                            pass
        except Exception as e:
            print(f"❌ Error leyendo archivo: {e}")

    def get_statistics(self):
        """Calcular estadísticas en vivo"""
        if not self.trades:
            return {
                'total_cycles': 0,
                'total_opens': 0,
                'total_closes': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'avg_pnl': 0,
                'best_trade': 0,
                'worst_trade': 0,
                'errors': 0
            }

        opens = [t for t in self.trades if t.get('type') == 'OPEN']
        closes = [t for t in self.trades if t.get('type') == 'CLOSE']
        errors = [t for t in self.trades if t.get('type') == 'ERROR']

        if not closes:
            return {
                'total_cycles': max([t.get('cycle', 0) for t in self.trades]),
                'total_opens': len(opens),
                'total_closes': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'avg_pnl': 0,
                'best_trade': 0,
                'worst_trade': 0,
                'errors': len(errors)
            }

        winners = [c for c in closes if c.get('pnl_pct', 0) > 0]
        pnl_values = [c.get('pnl_pct', 0) for c in closes]

        return {
            'total_cycles': max([t.get('cycle', 0) for t in self.trades]),
            'total_opens': len(opens),
            'total_closes': len(closes),
            'wins': len(winners),
            'losses': len(closes) - len(winners),
            'win_rate': (len(winners) / len(closes)) * 100 if closes else 0,
            'total_pnl': sum(pnl_values),
            'avg_pnl': sum(pnl_values) / len(closes) if closes else 0,
            'best_trade': max(pnl_values) if pnl_values else 0,
            'worst_trade': min(pnl_values) if pnl_values else 0,
            'errors': len(errors)
        }

    def print_report(self):
        """Imprimir reporte detallado"""
        stats = self.get_statistics()

        print("\n" + "="*70)
        print("📊 REPORTE EN VIVO - TRAD Bot v2.0")
        print("="*70)
        print(f"Timestamp:             {datetime.now().isoformat()}")
        print()

        print("📈 ESTADÍSTICAS")
        print("-"*70)
        print(f"Ciclos ejecutados:     {stats['total_cycles']}")
        print(f"Órdenes abiertas:      {stats['total_opens']}")
        print(f"Órdenes cerradas:      {stats['total_closes']}")
        print(f"Ganancias (Wins):      {stats['wins']}")
        print(f"Pérdidas (Losses):     {stats['losses']}")
        print(f"Errores:               {stats['errors']}")

        print()
        print("💰 RENDIMIENTO")
        print("-"*70)
        print(f"Win Rate:              {stats['win_rate']:.1f}%")
        print(f"P&L Total:             {stats['total_pnl']:+.2f}%")
        print(f"P&L Promedio/trade:    {stats['avg_pnl']:+.2f}%")
        print(f"Mejor trade:           {stats['best_trade']:+.2f}%")
        print(f"Peor trade:            {stats['worst_trade']:+.2f}%")

        print()
        print("="*70)

    def show_recent_trades(self, limit=10):
        """Mostrar últimos trades"""
        closes = [t for t in self.trades if t.get('type') == 'CLOSE']

        if not closes:
            print("❌ No hay trades cerrados aún")
            return

        print("\n" + "="*70)
        print("📋 ÚLTIMOS TRADES CERRADOS")
        print("="*70)

        for i, trade in enumerate(closes[-limit:], 1):
            emoji = "🟢" if trade.get('pnl_pct', 0) > 0 else "🔴"
            print(f"\n{i}. {emoji} Trade #{trade.get('cycle', '?')}")
            print(f"   Entry:  ${trade.get('entry', 0):.2f}")
            print(f"   Exit:   ${trade.get('exit', 0):.2f}")
            print(f"   P&L:    {trade.get('pnl_pct', 0):+.2f}%")
            print(f"   Reason: {trade.get('reason', '?')}")

        print("\n" + "="*70)

    def show_open_signals(self, limit=5):
        """Mostrar últimas señales de entrada"""
        opens = [t for t in self.trades if t.get('type') == 'OPEN']

        if not opens:
            print("⏳ Sin órdenes abiertas aún")
            return

        print("\n" + "="*70)
        print("📈 ÚLTIMAS ÓRDENES ABIERTAS")
        print("="*70)

        for i, trade in enumerate(opens[-limit:], 1):
            print(f"\n{i}. 📊 Orden #{trade.get('cycle', '?')}")
            print(f"   Entry Price:  ${trade.get('price', 0):.2f}")
            print(f"   SL:           ${trade.get('sl', 0):.2f}")
            print(f"   TP:           ${trade.get('tp', 0):.2f}")
            print(f"   RSI:          {trade.get('rsi', 0):.1f}")
            print(f"   Reason:       {trade.get('reason', '?')}")

        print("\n" + "="*70)

    def analyze_rejection_rate(self):
        """Analizar tasa de rechazo de Claude AI"""
        print("\n" + "="*70)
        print("🤖 ANÁLISIS DE DECISIONES DE CLAUDE AI")
        print("="*70)

        opens = [t for t in self.trades if t.get('type') == 'OPEN']
        total_cycles = max([t.get('cycle', 0) for t in self.trades])

        # Ciclos donde hubo oportunidad pero Claude rechazó
        print(f"\nCiclos totales:        {total_cycles}")
        print(f"Órdenes ejecutadas:    {len(opens)}")
        print(f"Tasa de ejecución:     {(len(opens)/total_cycles*100):.2f}% (1 de cada {total_cycles//len(opens) if opens else '?'} ciclos)")

        if opens:
            print("\n✅ Claude ACEPTÓ estas condiciones:")
            print(f"   • RSI promedio al entrada: {sum([t.get('rsi', 0) for t in opens]) / len(opens):.1f}")
        else:
            print("\n⚠️  Claude aún no ha aceptado ninguna señal")
            print("   (Posibles razones: RSI nunca < 25, o parámetros muy estrictos)")

        print("\n" + "="*70)

    def print_summary(self):
        """Resumen ejecutivo"""
        stats = self.get_statistics()

        summary = f"""
════════════════════════════════════════════════════════════════════════════════
🎯 RESUMEN EJECUTIVO - TRAD Bot v2.0
════════════════════════════════════════════════════════════════════════════════

⏱️  ACTIVIDAD
   • Ciclos ejecutados:    {stats['total_cycles']}
   • Órdenes abiertas:     {stats['total_opens']}
   • Órdenes cerradas:     {stats['total_closes']}
   • Errores:              {stats['errors']}

📊 RESULTADOS
   • Win Rate:             {stats['win_rate']:.1f}%
   • P&L Total:            {stats['total_pnl']:+.2f}%
   • P&L Promedio:         {stats['avg_pnl']:+.2f}%
   • Mejor Trade:          {stats['best_trade']:+.2f}%
   • Peor Trade:           {stats['worst_trade']:+.2f}%

🔍 ANÁLISIS
   • Trades ganadores:     {stats['wins']}
   • Trades perdedores:    {stats['losses']}
   • Ratio ganador/total:  1 de cada {stats['total_opens']//stats['wins'] if stats['wins'] > 0 else '?'} intentos

════════════════════════════════════════════════════════════════════════════════
"""
        print(summary)

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Monitor TRAD Bot en tiempo real")
    parser.add_argument('--report', action='store_true', help='Mostrar reporte completo')
    parser.add_argument('--recent', type=int, default=5, help='Mostrar últimos N trades')
    parser.add_argument('--opens', type=int, default=3, help='Mostrar últimas N órdenes abiertas')
    parser.add_argument('--watch', action='store_true', help='Modo watch (actualizar cada 30s)')
    parser.add_argument('--summary', action='store_true', help='Mostrar solo resumen')

    args = parser.parse_args()

    monitor = BotMonitor()

    if not monitor.trades:
        print("⚠️  Sin datos aún. El bot aún no ha generado trades.")
        print(f"Verificar: {monitor.log_file}")
        return

    if args.watch:
        import time
        while True:
            os.system('clear')
            monitor.load_trades()
            monitor.print_summary()
            monitor.print_report()
            print("\n⏳ Actualizando en 30 segundos... (Ctrl+C para salir)")
            try:
                time.sleep(30)
            except KeyboardInterrupt:
                print("\n✅ Monitor detenido")
                break
    elif args.summary:
        monitor.print_summary()
    else:
        monitor.print_summary()
        monitor.print_report()
        monitor.show_open_signals(args.opens)
        monitor.show_recent_trades(args.recent)
        monitor.analyze_rejection_rate()

if __name__ == "__main__":
    main()
