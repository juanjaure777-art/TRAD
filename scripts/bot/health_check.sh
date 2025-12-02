#!/bin/bash
#
# TRAD Bot v3.3 - Health Check & Auto-Restart
# Monitorea la salud del bot y lo reinicia si es necesario
#

BOT_DIR="/home/juan/Escritorio/osiris/proyectos/TRAD"
SESSION_NAME="trad_v33"
LOCK_FILE="$BOT_DIR/.bot_v33.lock"
LOG_FILE="$BOT_DIR/trades_testnet.log"
HEALTH_LOG="$BOT_DIR/.bot_health.log"

cd "$BOT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_health() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$HEALTH_LOG"
}

check_bot_health() {
    echo -e "${YELLOW}🔍 Verificando salud del bot...${NC}"

    # Check 1: Is tmux session running?
    if ! tmux list-sessions 2>/dev/null | grep -q "^$SESSION_NAME"; then
        echo -e "${RED}❌ Sesión tmux no existe${NC}"
        log_health "ERROR: Sesión tmux no encontrada"
        return 1
    fi
    echo -e "${GREEN}✅ Sesión tmux activa${NC}"

    # Check 2: Is python process running?
    PROCESS_COUNT=$(ps aux | grep "python3 main.py" | grep -v grep | wc -l)
    if [ "$PROCESS_COUNT" -eq 0 ]; then
        echo -e "${RED}❌ Proceso del bot no encontrado${NC}"
        log_health "ERROR: Proceso del bot no existe"
        return 1
    elif [ "$PROCESS_COUNT" -gt 1 ]; then
        echo -e "${RED}❌ Múltiples procesos detectados ($PROCESS_COUNT)${NC}"
        log_health "ERROR: Procesos duplicados detectados ($PROCESS_COUNT)"
        return 1
    fi
    echo -e "${GREEN}✅ Proceso único activo (PID: $(ps aux | grep 'python3 main.py' | grep -v grep | awk '{print $2}'))${NC}"

    # Check 3: Is bot producing output? (log recently updated)
    if [ -f "$LOG_FILE" ]; then
        LAST_LOG=$(stat -c "%Y" "$LOG_FILE" 2>/dev/null || stat -f "%m" "$LOG_FILE" 2>/dev/null || date +%s)
        NOW=$(date +%s)
        DIFF=$((NOW - LAST_LOG))

        # If log not updated in 3 minutes, something is wrong
        if [ "$DIFF" -gt 180 ]; then
            echo -e "${RED}⚠️  Log no actualizado en ${DIFF}s (3 min = problema)${NC}"
            log_health "WARNING: Log not updated for ${DIFF}s"
            return 1
        fi
        echo -e "${GREEN}✅ Log actualizado hace ${DIFF}s${NC}"
    fi

    # Check 4: Is bot in a cycle? (check tmux output)
    LATEST_CYCLE=$(tmux capture-pane -t "$SESSION_NAME" -p | grep "^\[" | tail -1)
    if [ -z "$LATEST_CYCLE" ]; then
        echo -e "${RED}❌ No hay ciclos en tmux${NC}"
        log_health "ERROR: No cycles detected in tmux"
        return 1
    fi
    echo -e "${GREEN}✅ Bot ejecutando ciclos${NC}"
    echo "   Último: $LATEST_CYCLE"

    # Check 5: Check for recovery system issues
    RECOVERY_LOG="$BOT_DIR/logs/recovery_testnet.log"
    if [ -f "$RECOVERY_LOG" ]; then
        CRASH_DETECTED=$(tail -5 "$RECOVERY_LOG" | grep -i "CRASH DETECTED")
        if [ ! -z "$CRASH_DETECTED" ]; then
            echo -e "${RED}⚠️  Crash recovery triggered${NC}"
            log_health "WARNING: Crash recovery activated"
            return 1
        fi
    fi

    return 0
}

restart_bot() {
    echo ""
    echo -e "${YELLOW}🔄 REINICIANDO BOT...${NC}"
    log_health "ACTION: Reiniciando bot"

    # Kill old processes
    pkill -f "python3 main.py" 2>/dev/null || true
    sleep 1

    # Kill tmux session
    tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true
    sleep 1

    # Remove lock file
    rm -f "$LOCK_FILE"

    # Restart
    ./start_bot_safe.sh

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Bot reiniciado exitosamente${NC}"
        log_health "SUCCESS: Bot restarted successfully"
        return 0
    else
        echo -e "${RED}❌ Error al reiniciar el bot${NC}"
        log_health "ERROR: Failed to restart bot"
        return 1
    fi
}

check_emergency_closure() {
    """Check if bot is stuck in emergency closure mode"""
    RECOVERY_LOG="$BOT_DIR/logs/recovery_testnet.log"
    if [ -f "$RECOVERY_LOG" ]; then
        EMERGENCY=$(tail -3 "$RECOVERY_LOG" | grep -i "EMERGENCY CLOSURE TRIGGERED")
        if [ ! -z "$EMERGENCY" ]; then
            echo -e "${RED}🚨 EMERGENCY CLOSURE ACTIVE${NC}"
            log_health "ALERT: Emergency closure detected - manual intervention required"
            echo "   Check recovery_testnet.log for details"
            return 1
        fi
    fi
    return 0
}

# Main health check
echo ""
echo -e "${YELLOW}════════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Health Check - $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Check for emergency closure first
if ! check_emergency_closure; then
    echo ""
    echo -e "${RED}⚠️  Emergency closure detected - contact administrator${NC}"
    log_health "ALERT: Emergency closure requires manual intervention"
    exit 1
fi

if check_bot_health; then
    echo ""
    echo -e "${GREEN}✅ Bot en buena salud${NC}"
    log_health "STATUS: Bot healthy"
else
    echo ""
    echo -e "${RED}❌ Problema detectado - Reiniciando...${NC}"
    restart_bot
fi

echo ""

