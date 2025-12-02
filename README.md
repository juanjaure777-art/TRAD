# 🤖 TRAD Bot v3.5+ - 4H Crecetrader Trading Bot

Professional trading bot implementing the **Crecetrader methodology** on **4H timeframe** with Daily validation.

## 📊 Current Status

- **Version:** v3.5+ (4H Crecetrader Edition)
- **Timeframe:** 4H with Daily multi-timeframe validation
- **Strategy:** Hybrid (RSI + Price Action + Crecetrader)
- **Leverage:** 10.0x
- **Mode:** Testnet (ready for mainnet)
- **Last Update:** 2025-11-28

## 🎯 Key Metrics

| Metric | 1H | 4H (Current) |
|--------|----|----|
| Noise | 80% | 15% |
| Crecetrader Effectiveness | 20% | 95% |
| Expected Win Rate | 35-40% | 65-75% |
| Trades/Day | 15-20+ | 0-4 |
| Signal Quality | Low | High |

## 📁 Project Structure

```
TRAD/
├── 📄 main.py                 # Bot entry point
├── 📄 requirements.txt         # Python dependencies
├── 📄 .gitignore              # Git ignore rules
│
├── 📁 config/                 # Configuration files
│   └── .env                   # API keys (not in git)
│   └── config.json            # Bot configuration
│
├── 📁 src/                    # Source code
│   ├── bot.py                 # Main bot logic
│   ├── constants.py           # Constants & thresholds
│   ├── analysis/              # Market analysis
│   │   ├── market_analyzer.py
│   │   ├── crecetrader.py
│   │   ├── multitimeframe_validator.py
│   │   └── referentes_calculator.py
│   ├── strategy/              # Trading strategies
│   │   ├── hybrid.py
│   │   ├── indicators.py
│   │   ├── candle_patterns.py
│   │   ├── modes.py
│   │   └── tzv_validator.py   # T+Z+V Crecetrader validation
│   ├── entry/                 # Entry management
│   │   └── entry_executor.py
│   ├── exit/                  # Exit management
│   │   ├── dead_trade_detector.py
│   │   └── sl_tp_manager.py
│   ├── risk_management/       # Risk calculation
│   │   └── risk_manager.py
│   ├── monitoring/            # Trade logging
│   │   └── trade_logger.py
│   ├── trading/               # Trading utilities
│   │   ├── sessions.py
│   │   ├── recovery.py
│   │   └── hybrid_gatekeeper_adapter.py
│   └── __init__.py
│
├── 📁 docs/                   # Documentation
│   ├── README.md              # Quick start guide
│   ├── ARCHITECTURE_ANALYSIS.md
│   ├── RULES.md               # Trading rules
│   ├── CRECETRADER_CONCEPTOS_CLAVE.md
│   ├── analysis/
│   │   ├── TIMEFRAME_ANALYSIS.md    # Why 4H > 1H
│   │   └── ANALISIS_BITCOIN_HOY.md
│   ├── migration/
│   │   └── MIGRATION_SUMMARY_4H.md  # Recent migration changes
│   └── reports/
│       ├── AUDIT_REPORT.txt
│       └── PROFESSIONAL_AUDIT_REPORT.md
│
├── 📁 scripts/                # Utility scripts
│   ├── health_monitor.py      # Bot health monitoring
│   ├── monitor.py             # General monitoring
│   ├── monitor_realtime.py    # Real-time monitoring
│   └── run_bot.sh             # Bot execution script
│
├── 📁 logs/                   # Log files
│   ├── bot_health_alerts.log
│   ├── trades_testnet.log
│   ├── .gatekeeper_stats_testnet.json
│   └── trades/                # Trade records & statistics
│
├── 📁 data/                   # Data files
│   └── (market data, cache)
│
├── 📁 archive/                # Old/archived files
│   └── (previous versions)
│
├── 📁 venv/                   # Python virtual environment
│   └── (dependencies)
│
└── 📁 __pycache__/            # Python cache (auto-generated)
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
cd /home/juan/Escritorio/osiris/proyectos/TRAD

# Create virtual environment (if needed)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Bot

Edit `config/config.json`:
```json
{
  "mode": "testnet",
  "trading": {
    "timeframe": "4h",
    "symbol": "BTC/USDT",
    "leverage": 10.0
  }
}
```

### 3. Set API Keys

Create `config/.env`:
```
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
```

### 4. Run Bot

**Testnet (Safe):**
```bash
export BOT_MODE=testnet
python3 main.py
```

**Mainnet (Real Trading):**
```bash
export BOT_MODE=mainnet
python3 main.py
```

## 📊 4H Strategy Overview

### Entry Conditions

**LONG Entry:**
- RSI(7) < 25 on 4H
- RSI < 35 on Daily (confirmation)
- Bullish price action or EMA signal
- T+Z+V validation passes

**SHORT Entry:**
- RSI(7) > 75 on 4H
- RSI > 65 on Daily (confirmation)
- Bearish price action
- T+Z+V validation passes

### Exit Targets

- **TP1:** +2.0% (closes 50%)
- **TP2:** +3.5% (closes remaining 50%, trailing starts)
- **SL:** -0.8% (below entry)

### Multi-Timeframe Validation

- **Primary:** 4H candles (entry timeframe)
- **Confirmation:** Daily trend validation
- **Structure:** T+Z+V Crecetrader formula

## 🔧 Monitoring Tools

### Real-time Monitor
```bash
python3 scripts/monitor_realtime.py
```

### Health Check
```bash
python3 scripts/health_monitor.py
```

### Trade History
```bash
tail -f logs/trades_testnet.log
```

## 📈 Recent Changes

### 4H Migration (2025-11-28)

Complete migration from 1H to 4H timeframe:

- ✅ Config updated (4h, leverage 10x, 24/7 hours)
- ✅ Bot.py: Fetch Daily+4H data
- ✅ Strategy: 4H+Daily validation
- ✅ Tests: 11/11 passed
- ✅ Ready for testnet

**Details:** See `docs/migration/MIGRATION_SUMMARY_4H.md`

## 🎓 Documentation

- **Getting Started:** `docs/README.md`
- **Strategy Details:** `docs/STRATEGY_HYBRID.md`
- **Architecture:** `docs/ARCHITECTURE_ANALYSIS.md`
- **Crecetrader:** `docs/CRECETRADER_CONCEPTOS_CLAVE.md`
- **Rules:** `docs/RULES.md`

## 🔍 Key Features

✅ **Crecetrader Methodology**
- T (Tendencia): Trend validation on Daily
- Z (Zonas): Support/resistance from Fibonacci
- V (Vacío): Risk/reward ratio enforcement

✅ **Multi-Timeframe Analysis**
- Daily for trend direction
- 4H for entry points
- MarketPhase detection (COMPRESSION/EXPANSION)

✅ **Intelligent Validation**
- GatekeeperV2: Claude AI validation
- Technical indicators: RSI, EMA
- Price action patterns: Wick analysis, candle localization

✅ **Risk Management**
- Position sizing based on confirmations
- Stop loss & take profit levels
- Dead trade detection
- Emergency closure on critical conditions

✅ **Monitoring & Logging**
- Trade journal with all details
- Health alerts system
- Statistics tracking
- Real-time monitoring

## 🛠️ Development

### Running Tests
```bash
python3 -m pytest tests/ -v
```

### Syntax Check
```bash
python3 -m py_compile src/*.py
```

### Code Quality
- Uses PEP 8 style
- Type hints in key functions
- Comprehensive error handling

## ⚠️ Important Notes

### Testnet First
Always test thoroughly in testnet before mainnet:
- Minimum 1-3 days of testnet trading
- Verify multi-timeframe correlation works
- Confirm T+Z+V validation is correct

### Patience Required
4H trading requires patience:
- May have 0 trades some days
- Better setups = higher probability
- **Don't force entries**

### Capital Management
- Start with small capital (1-5% of total)
- 10x leverage is conservative for 4H
- Can increase to 15-20x after validation

## 📞 Support & Issues

Check logs for errors:
```bash
tail -100 logs/bot_health_alerts.log
cat logs/trades_testnet.log
```

## 📜 License

Private project. All rights reserved.

---

**Version:** v3.5+ (4H Crecetrader Edition)
**Last Updated:** 2025-11-28
**Status:** ✅ Ready for Testnet Deployment
