# 📊 TRAD Bot v2.0 - Monitoreo en Vivo

**Enfoque**: Backtesting MIENTRAS el bot corre, estudiando su comportamiento en tiempo real.

---

## 🎯 Objetivo

**NO esperar 7 días para empezar a analizar**. Comenzar ahora con el bot corriendo y:

1. Ver CADA ciclo que ejecuta
2. Analizar por qué toma (o no) cada decisión
3. Ajustar parámetros en tiempo real si es necesario
4. Recopilar datos MIENTRAS aprendemos

---

## 📺 Sistema de Monitoreo (4 Niveles)

### Nivel 1: Dashboard Web (Interfaz Básica)
```
URL: http://localhost:8000
├─ Status del bot (corriendo/detenido)
├─ Precio actual BTC/USDT
├─ RSI actual
├─ Órdenes abiertas
└─ Historial de trades (últimos 10)
```

### Nivel 2: Gráficos RSI en Vivo
```
URL: http://localhost:8000/rsi_chart.html
├─ Gráfico RSI (últimas 100 velas)
├─ Línea de tendencia EMA(50)
├─ Zonas de sobrecompra/sobreventa
└─ Puntos de entrada/salida marcados
```

### Nivel 3: Logs en Tiempo Real
```bash
# Ver CADA ciclo del bot (cada 1 minuto)
tail -f /home/juan/Escritorio/osiris/proyectos/TRAD/trades_testnet.log

# Ver proceso corriendo
ps aux | grep bot_v2
```

### Nivel 4: Análisis Profundo (Script Custom)
Crear script que analice:
- Señales rechazadas vs aceptadas
- Motivo de cada entrada/salida
- Métricas en tiempo real (win rate, P&L)
- Anomalías o errores

---

## ⏰ Cronograma de Monitoreo

### HOY (Primeras 2 horas)
```
✅ Observar bot en vivo
✅ Ver primeros 2-3 ciclos
✅ Verificar que calcula indicadores correctamente
✅ Revisar que logs se generan
✅ Confirmar dashboard funciona
```

### PRÓXIMAS 24 HORAS
```
✅ Monitoreo contínuo (al menos 1 hora cada 4 horas)
✅ Buscar primeras oportunidades (RSI < 25)
✅ Verificar confirmaciones (EMA, Stochastic)
✅ Documentar cada señal detectada
```

### PRÓXIMOS 7 DÍAS
```
✅ Monitoreo intenso (1-2 horas diarias)
✅ Acumular datos reales (7,000+ candles)
✅ Analizar comportamiento del bot
✅ Identificar falsos positivos/negativos
✅ Ajustar parámetros si es necesario
```

### PRÓXIMOS 30 DÍAS
```
✅ Backtesting contra datos históricos recolectados
✅ Validar si estrategia es rentable
✅ Optimizar umbrales (RSI, EMA, etc)
✅ Decisión: continuar o mejorar
```

---

## 🔍 Qué Observar En Cada Ciclo

### Cada 1 minuto, el bot ejecuta un ciclo:

```
[HH:MM:SS] #CICLO | Price: $XXXXX | RSI(7): XX.X | EMA(50): $XXXXX | Stoch: XX.X
```

**Preguntas a hacerse**:

1. **¿RSI está bajando?**
   - Sí → Esperar a que baje más (< 25)
   - No → Esperar siguiente oportunidad

2. **¿RSI está en sobreventa (< 25)?**
   - Sí → Verificar otras condiciones
   - No → No hay entrada posible

3. **¿Precio está por encima de EMA(50)?**
   - Sí → Buena, sigue la tendencia
   - No → No compraría (contra-tendencia)

4. **¿Stochastic %K < 20?**
   - Sí → Confirmación, entrada FUERTE
   - No → Sin confirmación, débil

5. **¿Hay soporte cerca?**
   - Sí → Punto óptimo para entrar
   - No → Riesgoso, esperar mejor momento

6. **¿Claude AI valida?**
   - Sí → ✅ COMPRA
   - No → ❌ Rechaza (decisión inteligente)

---

## 📝 Análisis a Registrar (Template)

Crear documento: `ANALISIS_DIARIO.md`

```markdown
## ANÁLISIS - [FECHA]

### Ciclos Observados
- Total ciclos: XXX
- Oportunidades encontradas (RSI < 25): XX
- Órdenes ejecutadas: XX
- Órdenes rechazadas por Claude: XX

### Señales Interesantes
1. [HH:MM] Señal en BTC $XXXXX
   - RSI: X.X (¿bien?)
   - EMA: $XXXXX (¿arriba del precio?)
   - Stoch: X.X (¿< 20?)
   - Soporte: $XXXXX (¿cerca?)
   - Resultado: ✅ Entrada / ❌ Rechazada (por qué?)

### Parámetros a Revisar
- RSI(7) threshold: 25 (¿bueno o muy estricto?)
- EMA(50): ¿funciona bien?
- Stochastic: ¿confirmación valiosa?

### Ajustes Sugeridos
- Cambiar RSI a 20? (más estricto)
- Cambiar RSI a 30? (menos estricto)
- Modificar EMA a 40 o 60?
```

---

## 🛠️ Herramientas de Análisis Rápido

### Ver ciclos en tiempo real CON contexto
```bash
# Ver las últimas 3 líneas del bot cada 10 segundos
watch -n 10 'tmux capture-pane -t trad-v2:0 -p -S -3'
```

### Contar ciclos por hora
```bash
# ¿Cuántos ciclos corrió en las últimas 2 horas?
grep '"cycle"' trades_testnet.log | tail -120 | wc -l
```

### Analizar señales rechazadas vs aceptadas
```bash
# Órdenes ejecutadas
grep -c '"type": "OPEN"' trades_testnet.log

# Órdenes rechazadas (intentadas pero no confirmadas por Claude)
grep -c "REJECTED" trades_testnet.log
```

### Ver cada entrada en detalle
```bash
# Filtrar solo OPEN trades
grep '"type": "OPEN"' trades_testnet.log | jq .

# Filtrar solo CLOSE trades
grep '"type": "CLOSE"' trades_testnet.log | jq .
```

---

## 📊 Dashboard Personalizado para Monitoreo

Crear script: `monitor_bot.py`

```python
#!/usr/bin/env python3
import json
import os
from datetime import datetime
from collections import deque

class BotMonitor:
    def __init__(self):
        self.trades = []
        self.cycles = deque(maxlen=60)  # Últimos 60 ciclos
        self.load_trades()

    def load_trades(self):
        """Cargar trades desde archivo"""
        log_file = "trades_testnet.log"
        if os.path.exists(log_file):
            with open(log_file) as f:
                for line in f:
                    try:
                        self.trades.append(json.loads(line))
                    except:
                        pass

    def get_statistics(self):
        """Calcular estadísticas en vivo"""
        opens = [t for t in self.trades if t.get('type') == 'OPEN']
        closes = [t for t in self.trades if t.get('type') == 'CLOSE']

        if not closes:
            return {
                'total_trades': len(opens),
                'trades_closed': 0,
                'win_rate': 0,
                'total_pnl': 0
            }

        winners = [c for c in closes if c.get('pnl_pct', 0) > 0]

        return {
            'total_trades': len(opens),
            'trades_closed': len(closes),
            'wins': len(winners),
            'losses': len(closes) - len(winners),
            'win_rate': (len(winners) / len(closes)) * 100 if closes else 0,
            'total_pnl': sum([c.get('pnl_pct', 0) for c in closes]),
            'avg_pnl': sum([c.get('pnl_pct', 0) for c in closes]) / len(closes) if closes else 0
        }

    def print_report(self):
        """Imprimir reporte en tiempo real"""
        stats = self.get_statistics()

        print("\n" + "="*60)
        print("📊 REPORTE EN VIVO - TRAD Bot v2.0")
        print("="*60)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()
        print(f"Trades Ejecutados:     {stats['total_trades']}")
        print(f"Trades Cerrados:       {stats['trades_closed']}")
        print(f"Ganancias (Wins):      {stats['wins']}")
        print(f"Pérdidas (Losses):     {stats['losses']}")
        print(f"Win Rate:              {stats['win_rate']:.1f}%")
        print(f"P&L Total:             {stats['total_pnl']:.2f}%")
        print(f"P&L Promedio/trade:    {stats['avg_pnl']:.2f}%")
        print("="*60)

if __name__ == "__main__":
    monitor = BotMonitor()
    monitor.print_report()
```

---

## 🎯 Plan de Acción AHORA

### Hoy (Primeras 2 horas)
```bash
# 1. Abrir en una terminal
tmux attach -t trad-v2:0

# 2. En otra terminal, monitorear logs
tail -f trades_testnet.log | jq .

# 3. En otra, ver gráficos
open http://localhost:8000/rsi_chart.html

# 4. Estudiar comportamiento
# Observar:
# - ¿Qué ciclos genera signals?
# - ¿Qué rechaza Claude AI?
# - ¿Los parámetros son correctos?
```

### Próximas 24 horas
```bash
# Ejecutar análisis cada 4 horas
python3 monitor_bot.py

# Grabar observaciones
echo "[HH:MM] Observación importante..." >> ANALISIS_DIARIO.md
```

### Próximos 7 días
```bash
# Monitoreo diario (1-2 horas)
# Documentar anomalías
# Ajustar parámetros si es necesario
# Acumular datos
```

---

## ⚠️ Señales de Alerta

Detenerse y revisar si:

1. **Bot no genera signals en 6+ horas**
   - RSI nunca baja < 25
   - Parámetros muy estrictos?

2. **Claude rechaza todas las señales**
   - ¿Demasiado restrictivo?
   - ¿Parámetros inconsistentes?

3. **Bot entra pero siempre pierde**
   - ¿Estrategia no funciona?
   - ¿Parámetros mal calibrados?

4. **Errores en logs**
   - Revisar API keys
   - Revisar conexión Binance

---

## 🎓 Qué Aprenderás (Backtesting en Vivo)

✅ Cómo se comportan los indicadores en tiempo real
✅ Qué parámetros funcionan vs cuáles no
✅ Cuándo Claude AI rechaza correctamente
✅ Patrones de mercado en 1m
✅ Cómo optimizar la estrategia dinámicamente

---

**IMPORTANTE**: No esperes 7 días. Empieza AHORA a estudiar cada ciclo.

El backtesting es mientras el bot corre. Eso es aprendizaje real.
