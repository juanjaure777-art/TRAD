#!/bin/bash
# TRAD Bot v3.0 - Launch Script with Monitoring
# Lanza el bot en tmux y configura monitoreo continuo

set -e

BOT_DIR="/home/juan/Escritorio/osiris/proyectos/TRAD"
SESSION_NAME="trad-bot-v3"
TIMESTAMP=$(date '+%Y-%m-%d_%H-%M-%S')
LOG_DIR="$BOT_DIR/logs"

# Crear directorio de logs
mkdir -p "$LOG_DIR"
MAIN_LOG="$LOG_DIR/bot_$TIMESTAMP.log"
MONITOR_LOG="$LOG_DIR/monitor_$TIMESTAMP.log"

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🚀 TRAD BOT v3.0 - LANZAMIENTO COMPLETO"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📅 Timestamp: $TIMESTAMP"
echo "📁 Bot Directory: $BOT_DIR"
echo "📝 Main Log: $MAIN_LOG"
echo "📊 Monitor Log: $MONITOR_LOG"
echo ""

# Cambiar al directorio del bot
cd "$BOT_DIR"

# Verificar que .env existe
if [ ! -f ".env" ]; then
    echo "❌ ERROR: .env no encontrado en $BOT_DIR"
    exit 1
fi

# Verificar venv
if [ ! -d "venv" ]; then
    echo "❌ ERROR: venv no encontrado"
    exit 1
fi

# Limpiar sesión anterior si existe
if tmux list-sessions | grep -q "^$SESSION_NAME"; then
    echo "🧹 Limpiando sesión anterior..."
    tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true
    sleep 1
fi

# Crear nueva sesión tmux
echo "🔄 Creando sesión tmux: $SESSION_NAME"
tmux new-session -d -s "$SESSION_NAME" -x 160 -y 40

# Panel 1: Bot Principal
echo "🤖 Panel 1: Lanzando BOT PRINCIPAL..."
tmux send-keys -t "$SESSION_NAME:0" "
. venv/bin/activate
python3 main.py 2>&1 | tee -a '$MAIN_LOG'
" Enter

# Esperar a que el bot inicie
echo "⏳ Esperando 3 segundos para que el bot inicie..."
sleep 3

# Panel 2: Monitor en vivo
echo "📊 Panel 2: Lanzando MONITOR EN VIVO..."
tmux split-window -h -t "$SESSION_NAME:0"
tmux send-keys -t "$SESSION_NAME:0.1" "
cd '$BOT_DIR'
. venv/bin/activate
sleep 2
python3 monitor_bot.py --watch 2>&1 | tee -a '$MONITOR_LOG'
" Enter

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ TRAD BOT LANZADO CORRECTAMENTE"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "🔗 PARA CONECTARTE AL BOT:"
echo "   tmux attach -t $SESSION_NAME"
echo ""
echo "📝 PARA VER LOGS:"
echo "   Main log:    tail -f '$MAIN_LOG'"
echo "   Monitor log: tail -f '$MONITOR_LOG'"
echo ""
echo "🛑 PARA DETENER EL BOT:"
echo "   tmux kill-session -t $SESSION_NAME"
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Mostrar estado de sesión
echo "📡 Estado de sesión tmux:"
tmux list-sessions | grep "$SESSION_NAME"
echo ""

# Mostrar que está corriendo
echo "🟢 BOT CORRIENDO EN SEGUNDO PLANO"
echo ""
echo "Para vigilancia continua, ejecuta en otra terminal:"
echo "   tail -f '$MAIN_LOG'"
