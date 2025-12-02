# 📈 TRAD - Trading Bot con IA

**Versión:** v3.0
**Estado:** Producción
**Última actualización:** 2025-11-19

---

## 📋 Descripción

TRAD es un bot de trading automatizado que utiliza **análisis técnico** e **indicadores de IA** para ejecutar operaciones en mercados financieros. Incluye monitoreo en tiempo real, backtesting y dashboard web.

### Características
- ✅ Bot de trading autónomo 24/7
- ✅ Análisis técnico avanzado (RSI, Bollinger, MACD)
- ✅ Estrategia híbrida con machine learning
- ✅ Dashboard web en tiempo real
- ✅ Backtesting y simulación
- ✅ Integración con Crecetrader API
- ✅ Sistema de detección de pánico

---

## 📁 Estructura del Proyecto

```
proyectos/TRAD/
├── bot_v3.py                    # Bot principal (versión 3)
├── monitor_bot.py               # Monitor en vivo
├── strategy_hybrid.py            # Estrategia híbrida
├── indicators_lib.py             # Librería de indicadores
├── crecetrader_context.py        # Integración Crecetrader
├── data_collector.py             # Recolector de datos
├── candle_patterns.py            # Patrones de velas
├── backtest.py                   # Sistema de backtesting
├── launch_bot.sh                 # Script de inicio
├── monitor_live.sh               # Monitor en vivo
├── config.json                   # Configuración
├── dashboard.html                # Dashboard web
├── logs/                         # Registros de ejecución
├── data/                         # Datos de mercado
├── venv/                         # Virtual environment
└── requirements.txt              # Dependencias Python
```

---

## 🚀 Guía Rápida

### Instalación

```bash
cd /home/juan/Escritorio/osiris/proyectos/TRAD

# Crear virtual environment
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### Configuración

Editar `config.json`:

```json
{
  "exchange": "binance",
  "symbols": ["BTC/USDT", "ETH/USDT"],
  "timeframe": "1m",
  "strategy": "hybrid",
  "max_trades": 5,
  "risk_percent": 2.0
}
```

### Ejecutar Bot

```bash
# Iniciar bot
bash launch_bot.sh

# Monitorear en vivo (otra terminal)
bash monitor_live.sh

# Ver dashboard
open http://localhost:8000
```

---

## 📊 Características Principales

### Estrategia Híbrida
- Análisis técnico clásico (RSI, Bollinger, MACD)
- Patrones de velas japonesas
- Machine Learning para predicciones
- Sistema de stop-loss dinámico

### Monitoreo
- Dashboard web en tiempo real
- Alertas por email/Telegram
- Registro detallado de operaciones
- Análisis de rendimiento

### Backtesting
```bash
python backtest.py --symbol BTC/USDT --days 30
```

---

## 📊 Estado del Proyecto

- ✅ Bot v3: Producción
- ✅ Estrategia híbrida: Optimizada
- ✅ Monitoreo: En vivo
- ✅ Dashboard: Funcional
- ✅ Backtesting: Completo
- 🔄 IA mejorada: En desarrollo
- 🔄 Detección de pánico: Experimental

---

## 🔗 Documentación

- **BITACORA Global:** `/home/juan/Escritorio/osiris/sistema/BITACORA.md`
- **Documentación Bot:** `/home/juan/Escritorio/osiris/core/PROJECT_MEMORY/TRAD.md` (si existe)
- **Guía Inicio Rápido:** `00-INICIO-RAPIDO.md`
- **Integración Crecetrader:** `CRECETRADER_INTEGRATION_GUIDE.md`
- **Estrategia Explicada:** `ESTRATEGIA_HYBRID_EXPLICADA.md`

---

## ⚠️ Disclaimer

Este bot es para propósitos educativos y de demostración.

**El trading es riesgoso.** Use con capital que pueda permitirse perder.

---

## 🛠️ Requisitos

- Python 3.10+
- Conexión a internet estable
- API keys de exchange (Binance, Crecetrader, etc)
- Mínimo: $100 USD para trading real

---

**Este proyecto está versionado en Git. Todos los cambios se registran automáticamente.**

