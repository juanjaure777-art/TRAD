#!/bin/bash
# TRAD Bot v3.0 - Live Monitoring Script
# Vigila el bot en tiempo real e imprime métricas actualizadas

BOT_DIR="/home/juan/Escritorio/osiris/proyectos/TRAD"
SESSION="trad"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🔍 TRAD BOT v3.0 - MONITOREO EN VIVO CONTINUO"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Comenzando monitoreo a: $TIMESTAMP"
echo "🤖 Sesión tmux: $SESSION"
echo "📁 Directorio: $BOT_DIR"
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Variables para tracking
prev_cycle=0
signal_count=0
total_p_l=0

while true; do
    clear

    CURRENT_TIME=$(date '+%H:%M:%S')
    UPTIME=$(tmux list-sessions | grep "$SESSION" | awk '{print $6}')

    echo "════════════════════════════════════════════════════════════════════════════════"
    echo "🔍 TRAD BOT v3.0 - MONITOREO EN VIVO"
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo ""
    echo "⏰ Hora actual: $CURRENT_TIME"
    echo "📡 Estado: 🟢 ACTIVO"
    echo "⬆️  Uptime: $UPTIME"
    echo ""

    # Capturar últimas líneas del bot
    echo "📊 ACTIVIDAD DEL BOT (Últimos ciclos):"
    echo ""

    tmux capture-pane -t "$SESSION" -p -S -15 | grep -E "ABIERTO|PARCIAL|CERRADO|Price:|RSI|RECHAZADO|Crecetrader" | tail -20 | sed 's/^/   /'

    echo ""
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo "📈 ESTADÍSTICAS"
    echo "════════════════════════════════════════════════════════════════════════════════"

    # Contar eventos en el output actual
    TOTAL_EVENTS=$(tmux capture-pane -t "$SESSION" -p | grep -c "ABIERTO\|CERRADO\|PARCIAL" 2>/dev/null || echo 0)
    SIGNALS_COUNT=$(tmux capture-pane -t "$SESSION" -p | grep -c "ABIERTO" 2>/dev/null || echo 0)

    echo "   🎯 Señales detectadas: $SIGNALS_COUNT"
    echo "   📊 Eventos totales: $TOTAL_EVENTS"
    echo "   ⏱️ Ciclos ejecutados: $(tmux capture-pane -t "$SESSION" -p | grep -o '#[0-9]*' | tail -1 | tr -d '#')"
    echo ""

    echo "════════════════════════════════════════════════════════════════════════════════"
    echo "🔄 PRÓXIMA ACTUALIZACIÓN EN 30 SEGUNDOS (Ctrl+C para salir)"
    echo "════════════════════════════════════════════════════════════════════════════════"

    sleep 30
done
