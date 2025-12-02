#!/bin/bash

# TRAD Bot v3.2 Launcher
# Multi-Timeframe Confirmation + Dynamic Position Sizing

PROJECT_DIR="/home/juan/Escritorio/osiris/proyectos/TRAD"
cd "$PROJECT_DIR"

# Activate virtual environment
source venv/bin/activate

# Create logs directory if not exists
mkdir -p logs

# Get timestamp for this session
TIMESTAMP=$(date '+%Y-%m-%d_%H-%M-%S')
LOG_FILE="logs/bot_v3.2_${TIMESTAMP}.log"

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🚀 LANZANDO TRAD BOT v3.2 - Multi-Timeframe + Dynamic Position Sizing"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "⏱️  Timestamp: ${TIMESTAMP}"
echo "📁 Log file: ${LOG_FILE}"
echo "🔧 Modo: $(python3 -c 'import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv("BOT_MODE", "testnet"))')"
echo ""

# Launch bot in new tmux session
tmux new-session -d -s trad -x 200 -y 50

# Send startup command
tmux send-keys -t trad "cd $PROJECT_DIR && source venv/bin/activate && python3 bot_v3.py 2>&1 | tee $LOG_FILE" Enter

# Wait for bot to start
sleep 2

echo "✅ Bot iniciado en sesión tmux 'trad'"
echo ""
echo "Para ver el bot en vivo:"
echo "  tmux attach -t trad"
echo ""
echo "Para ver logs:"
echo "  tail -f $LOG_FILE"
echo ""
echo "Para detener bot:"
echo "  tmux kill-session -t trad"
echo ""

