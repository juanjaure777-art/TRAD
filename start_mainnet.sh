#!/bin/bash
#################################################
# TRAD Bot - MAINNET Startup Script
# Version: 3.6+ con 10x leverage
# ⚠️  DINERO REAL - Usar con precaución
#################################################

set -e

echo "=========================================="
echo "🚀 TRAD Bot v3.6+ - MAINNET STARTUP"
echo "=========================================="
echo ""
echo "⚠️  ADVERTENCIA: DINERO REAL"
echo "⚠️  LEVERAGE: 10x"
echo ""

# 1. Verificar directorio
if [ ! -f "main.py" ]; then
    echo "❌ ERROR: No estás en el directorio correcto"
    exit 1
fi

# 2. Activar virtualenv
echo "📦 Activando virtualenv..."
source venv/bin/activate

# 3. Verificar dependencias
echo "🔍 Verificando dependencias..."
python3 -c "import ccxt, anthropic, numpy, dotenv" || {
    echo "❌ ERROR: Faltan dependencias"
    exit 1
}

# 4. Verificar API keys
if [ ! -f "config/.env" ]; then
    echo "❌ ERROR: config/.env no encontrado"
    exit 1
fi

# 5. Configurar modo mainnet
export BOT_MODE=mainnet

# 6. Mostrar configuración
echo ""
echo "=========================================="
echo "📊 CONFIGURACIÓN ACTUAL"
echo "=========================================="
python3 -c "
import json
with open('config/config.json') as f:
    cfg = json.load(f)
    print(f'Modo: MAINNET (dinero real)')
    print(f'Par: {cfg[\"trading\"][\"symbol\"]}')
    print(f'Order Size: {cfg[\"trading\"][\"order_size_usdt\"]} USDC')
    print(f'Leverage: {cfg[\"trading\"][\"leverage\"]}x')
    print(f'SL: {cfg[\"risk_management\"][\"sl_pct\"]}% (pérdida real: {cfg[\"risk_management\"][\"sl_pct\"] * cfg[\"trading\"][\"leverage\"]:.0f}%)')
    print(f'TP1: {cfg[\"risk_management\"][\"tp1_pct\"]}% (ganancia real: {cfg[\"risk_management\"][\"tp1_pct\"] * cfg[\"trading\"][\"leverage\"]:.0f}%)')
    print(f'Ratio R:R: {cfg[\"risk_management\"][\"tp1_pct\"] / cfg[\"risk_management\"][\"sl_pct\"]:.0f}:1')
"
echo "=========================================="
echo ""

# 7. Confirmación de seguridad
echo "⚠️  CONFIRMACIÓN REQUERIDA"
echo ""
read -p "¿Entiendes que usarás DINERO REAL con 10x leverage? (escribe SI): " confirm1
if [ "$confirm1" != "SI" ]; then
    echo "❌ Inicio cancelado"
    exit 0
fi

read -p "¿Confirmas iniciar en MAINNET? (escribe CONFIRMO): " confirm2
if [ "$confirm2" != "CONFIRMO" ]; then
    echo "❌ Inicio cancelado"
    exit 0
fi

# 8. Limpiar logs anteriores (opcional)
read -p "¿Limpiar logs de sesión anterior? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    > logs/bot_session.log
    > logs/gatekeeper_mainnet.log
    echo "🧹 Logs limpiados"
fi

# 9. Iniciar bot
echo ""
echo "🚀 INICIANDO BOT EN MAINNET..."
echo "   Par: SOL/USDC"
echo "   Leverage: 10x"
echo "   Order: 1 USDC"
echo ""
echo "📊 MONITOREO:"
echo "   Terminal 1: tail -f logs/gatekeeper_mainnet.log"
echo "   Terminal 2: tail -f logs/trades/trade_journal.txt"
echo ""
echo "🛑 Para detener: Ctrl+C"
echo ""
sleep 3

python3 main.py

echo ""
echo "=========================================="
echo "🛑 Bot detenido"
echo "=========================================="
