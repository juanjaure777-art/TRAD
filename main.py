#!/usr/bin/env python3
"""
TRAD Bot v3.6 - Main Entry Point
Execute this to start the trading bot with API Health Check
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# CRITICAL FIX: Use absolute path instead of relative path
SCRIPT_DIR = Path(__file__).parent
ENV_PATH = SCRIPT_DIR / 'config' / '.env'

# Load environment variables from config/.env FIRST
load_dotenv(str(ENV_PATH))

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from bot import TRADBot_v3
from api_health import inject_api_health

if __name__ == "__main__":
    bot = TRADBot_v3(config_path="config/config.json")

    # ✅ INYECTAR API HEALTH CHECK (CRÍTICO)
    print("\n🔧 Inyectando API Health Check...")
    bot = inject_api_health(bot)

    # ✅ VERIFICAR CONECTIVIDAD API ANTES DE EMPEZAR
    print("\n📡 Verificando conectividad API...")
    if not bot.api_health.wait_for_api(max_wait_seconds=30):
        print("❌ API NO DISPONIBLE - El bot no puede iniciarse sin conexión")
        sys.exit(1)

    print("✅ API OK - Iniciando bot...\n")
    bot.run()

