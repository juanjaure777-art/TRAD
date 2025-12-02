# TRAD Bot v3.3 - Project Structure

## Overview
Professional Python trading bot with modular architecture and comprehensive monitoring.

## Directory Structure

```
TRAD/
├── src/                              # Core source code
│   ├── __init__.py
│   ├── bot.py                        # Main bot engine (TRADBot_v3 class)
│   ├── strategy/                     # Trading strategy modules
│   │   ├── __init__.py
│   │   ├── hybrid.py                 # Hybrid strategy (RSI + Price Action + Crecetrader)
│   │   ├── modes.py                  # Permissiveness modes (1-5 dynamic adjustment)
│   │   ├── market_phases.py          # Market phase detection
│   │   ├── indicators.py             # Technical indicators library
│   │   └── candle_patterns.py        # Candle pattern recognition
│   ├── analysis/                     # Market analysis modules
│   │   ├── __init__.py
│   │   ├── crecetrader.py            # Crecetrader methodology integration
│   │   └── panic_detector.py         # Panic/dump detection system
│   ├── trading/                      # Trading utilities
│   │   ├── __init__.py
│   │   ├── sessions.py               # Trading sessions (ASIAN, EUROPEAN, AMERICAN)
│   │   └── orders.py                 # Order management
│   └── monitoring/                   # Bot monitoring tools
│       ├── __init__.py
│       └── monitor.py                # Monitoring utilities
│
├── scripts/                          # Operational scripts
│   ├── bot/                          # Bot operation scripts
│   │   ├── start_bot_safe.sh         # Safe startup (prevents duplicates)
│   │   ├── health_check.sh           # Health verification (4-point check)
│   │   └── launch_bot.sh             # Basic launch script
│   ├── setup/                        # Setup and configuration
│   │   └── setup_automation.sh       # Cron job automation setup
│   └── monitor/                      # Monitoring scripts
│       └── monitor_live.sh           # Live monitoring output
│
├── config/                           # Configuration files
│   ├── config.json                   # Main bot configuration
│   ├── permissiveness_config.txt     # Dynamic mode configuration
│   └── .env                          # Environment variables (API keys, etc)
│
├── docs/                             # Documentation
│   ├── README.md                     # Main readme
│   ├── QUICK_START.md                # Quick start guide
│   ├── ARCHITECTURE.md               # Architecture overview
│   ├── PROJECT_STRUCTURE.md          # This file
│   ├── STRATEGY_HYBRID.md            # Strategy explanation
│   ├── CRECETRADER_INTEGRATION.md    # Crecetrader integration guide
│   ├── PANIC_DETECTOR.md             # Panic detector documentation
│   ├── MONITOR.md                    # Monitoring guide
│   ├── DEPLOYMENT.md                 # Deployment & audit guide
│   └── SESSION_SUMMARY.md            # Session history
│
├── logs/                             # Trading logs
│   └── trades_testnet.log            # Testnet trading log
│
├── tests/                            # Test suite
│   └── test_features.py              # Feature tests
│
├── archive/                          # Old/deprecated code
│   └── v3.2/                         # Previous version archive
│       └── bot_v32.sh
│
├── data/                             # Market data storage
│   └── (candles, market data, etc)
│
├── main.py                           # Entry point for the bot
├── requirements.txt                  # Python dependencies
├── .gitignore                        # Git ignore rules
├── venv/                             # Python virtual environment
└── README.md                         # Project readme (at root)
```

## Key Files

### Entry Point
- **main.py**: Start the bot here. Imports and executes `src/bot.py`

### Core
- **src/bot.py**: Main TRADBot_v3 class. Handles trading logic, API calls, and cycle management

### Strategies
- **src/strategy/hybrid.py**: Hybrid strategy combining RSI, Price Action, and Crecetrader
- **src/strategy/modes.py**: Dynamic permissiveness modes (1-5) for market adaptation
- **src/strategy/market_phases.py**: Market phase detection (IMPULSE, CORRECTIVE, etc)

### Analysis
- **src/analysis/crecetrader.py**: Crecetrader methodology for market context
- **src/analysis/panic_detector.py**: Detects panic selling/dumping

### Operations
- **scripts/bot/start_bot_safe.sh**: Safe startup with lock file (prevents duplicate processes)
- **scripts/bot/health_check.sh**: 4-point health verification with auto-restart
- **scripts/setup/setup_automation.sh**: Cron job configuration for continuous monitoring

## Execution

```bash
# Start the bot
python3 main.py

# Or use safe startup script
./scripts/bot/start_bot_safe.sh

# Check bot health
./scripts/bot/health_check.sh

# View logs
tail -f logs/trades_testnet.log
```

## Configuration

All configuration is centralized in `config/`:
- **config/config.json**: Order size, leverage, margin mode, trading pair, timeframe
- **config/permissiveness_config.txt**: Current trading mode (1-5)
- **config/.env**: Sensitive data (API keys, passwords)

## Monitoring

Three levels of monitoring:
1. **Live Monitoring**: Real-time cycle tracking via tmux
2. **Health Checks**: Automated every 5 minutes via cron
3. **Intelligent Agent**: Continuous analysis and reporting

## Development

When adding new modules:
1. Create in appropriate `src/` subdirectory
2. Add imports to `src/__init__.py`
3. Update imports in dependent files
4. Add tests in `tests/`
5. Document in `docs/`

