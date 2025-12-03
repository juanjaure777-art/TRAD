#!/bin/bash
#################################################
# TRAD Bot - Testnet Safe Startup Script
# Version: 3.6+
# Para probar el bot de forma segura antes de mainnet
#################################################

set -e  # Exit on any error

echo "=========================================="
echo "🤖 TRAD Bot v3.6+ - TESTNET STARTUP"
echo "=========================================="
echo ""

# 1. Verificar directorio
if [ ! -f "main.py" ]; then
    echo "❌ ERROR: No estás en el directorio correcto"
    echo "   Ejecuta desde: /home/juan/Escritorio/osiris/proyectos/TRAD"
    exit 1
fi

# 2. Activar virtualenv
echo "📦 Activando virtualenv..."
if [ ! -d "venv" ]; then
    echo "❌ ERROR: virtualenv no encontrado. Ejecuta: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi
source venv/bin/activate

# 3. Verificar dependencias críticas
echo "🔍 Verificando dependencias..."
python3 -c "import ccxt, anthropic, numpy, dotenv" 2>/dev/null || {
    echo "❌ ERROR: Faltan dependencias. Ejecuta: pip install -r requirements.txt"
    exit 1
}
echo "✅ Dependencias OK"

# 4. Verificar API keys
echo "🔑 Verificando API keys..."
if [ ! -f "config/.env" ]; then
    echo "❌ ERROR: Archivo config/.env no encontrado"
    echo "   Crea el archivo con: BINANCE_API_KEY, BINANCE_API_SECRET, ANTHROPIC_API_KEY"
    exit 1
fi
echo "✅ API keys configuradas"

# 5. Cambiar a modo testnet
echo "⚙️  Configurando modo TESTNET..."
export BOT_MODE=testnet

# 6. Verificar sintaxis
echo "🔍 Verificando sintaxis de código..."
python3 -m py_compile src/bot.py || {
    echo "❌ ERROR: Errores de sintaxis en bot.py"
    exit 1
}
echo "✅ Sintaxis OK"

# 7. Crear backup de logs
echo "💾 Creando backup de logs anteriores..."
timestamp=$(date +%Y%m%d_%H%M%S)
mkdir -p logs/backups
if [ -f "logs/trades/trade_journal.txt" ]; then
    cp logs/trades/trade_journal.txt logs/backups/trade_journal_${timestamp}.txt
fi

# 8. Limpiar logs de sesión anterior (opcional)
read -p "¿Limpiar logs de sesión anterior? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    > logs/bot_session.log
    > logs/gatekeeper_mainnet.log
    echo "🧹 Logs limpiados"
fi

# 9. Mostrar configuración actual
echo ""
echo "=========================================="
echo "📊 CONFIGURACIÓN ACTUAL"
echo "=========================================="
echo "Modo: TESTNET"
echo "Par: $(grep -A 1 '"symbol"' config/config.json | tail -1 | cut -d'"' -f4)"
echo "Timeframe: $(grep -A 1 '"timeframe"' config/config.json | tail -1 | cut -d'"' -f4)"
echo "Leverage: $(grep -A 1 '"leverage"' config/config.json | tail -1)"
echo "Order Size: $(grep -A 1 '"order_size_usdt"' config/config.json | tail -1)"
echo "SL: $(grep -A 1 '"sl_pct"' config/config.json | tail -1)"
echo "TP1: $(grep -A 1 '"tp1_pct"' config/config.json | tail -1)"
echo "=========================================="
echo ""

# 10. Confirmar inicio
read -p "✅ ¿Iniciar bot en TESTNET? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Inicio cancelado"
    exit 0
fi

# 11. Iniciar bot
echo ""
echo "🚀 Iniciando TRAD Bot en TESTNET..."
echo "   (Presiona Ctrl+C para detener)"
echo ""
sleep 2

python3 main.py

echo ""
echo "=========================================="
echo "🛑 Bot detenido"
echo "=========================================="
