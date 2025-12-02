# TRAD Bot v3.4 - Project Structure

## Root Directory
```
TRAD/
├── main.py                      # Bot entry point
├── requirements.txt             # Dependencies
├── .gitignore                   # Git configuration
│
├── config/                      # Configuration files
│   ├── config.json             # Main bot configuration
│   ├── permissiveness_config.txt # Trading modes (1-5)
│   ├── gatekeeper_config.json   # Claude GatekeeperV2 config
│   └── .env                    # Secrets (NOT in git)
│
├── src/                        # Source code
│   ├── bot.py                 # Main bot logic
│   ├── strategy/              # Trading strategies
│   │   ├── hybrid.py          # HybridStrategy implementation
│   │   └── __init__.py
│   ├── trading/               # Trading modules
│   │   ├── gatekeeper_v2.py   # Claude decision engine (349 lines)
│   │   ├── hybrid_gatekeeper_adapter.py # Integration (153 lines)
│   │   └── __init__.py
│   ├── analysis/              # Market analysis
│   │   ├── indicators.py
│   │   └── __init__.py
│   ├── monitoring/            # Monitoring & recovery
│   │   ├── recovery.py        # Crash recovery system
│   │   └── __init__.py
│   └── __init__.py
│
├── docs/                      # Documentation
│   ├── PROJECT_STRUCTURE_v3.4.md # This file
│   ├── QUICK_START.md
│   ├── STRATEGY_HYBRID.md
│   ├── RECOVERY_SYSTEM.md
│   ├── DEPLOYMENT.md
│   └── README.md
│
├── logs/                      # Logs and monitoring
│   ├── current/               # Active session logs
│   ├── trades/                # Trade execution logs
│   ├── health/                # Bot health logs
│   └── archive/               # Old logs (archived)
│
├── scripts/                   # Utility scripts
│   ├── setup/                 # Setup scripts
│   ├── bot/                   # Bot management
│   └── monitor/               # Monitoring scripts
│
├── archive/                   # Versioned backups
│   ├── v3.2/                  # Previous versions
│   ├── v3.3/
│   ├── tests/                 # Test files
│   └── logs/
│
└── venv/                      # Python virtual environment
```

## Key Modules

### src/trading/gatekeeper_v2.py (349 lines)
- Claude-based intelligent trading gatekeeper
- Replaces hardcoded MODE rules (1-5)
- Prompt caching for token optimization
- Decision statistics tracking

### src/trading/hybrid_gatekeeper_adapter.py (153 lines)
- Integration layer between HybridStrategy and GatekeeperV2
- No breaking changes to existing strategy
- Detailed decision logging
- Token usage tracking

### config/gatekeeper_config.json
- GATEKEEPER_LEVEL: 2 (PERMISSIVE)
- Risk management parameters
- Trading parameters

### config/permissiveness_config.txt
- MODE: 2 (currently active)
- AUTO_DETECT: false (explicitly disabled)
- RSI thresholds for each mode

## Log Files

### Current Logs
- `logs/current/` - Active session logs

### Trade Logs
- `logs/trades/` - Trade execution records

### Health Logs
- `logs/health/` - Bot health and status

### Archive
- `logs/archive/` - Historical logs

## Version Control

### Active Version: v3.4
- GatekeeperV2 integrated
- HybridStrategy + Claude intelligence
- Prompt caching enabled
- Recovery system integrated

### Previous Versions
- v3.3: Previous stable release
- v3.2: Earlier release (in archive)

