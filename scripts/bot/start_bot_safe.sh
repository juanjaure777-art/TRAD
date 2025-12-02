#!/bin/bash
#
# TRAD Bot v3.3 - Safe Startup Script
# Evita procesos duplicados y garantiza una sola instancia
#

set -e

BOT_DIR="/home/juan/Escritorio/osiris/proyectos/TRAD"
LOCK_FILE="$BOT_DIR/.bot_v33.lock"
SESSION_NAME="trad_v33"
BOT_SCRIPT="bot_v3.py"

cd "$BOT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}╔════════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║           TRAD Bot v3.3 - SAFE STARTUP (Previene Duplicados)                 ║${NC}"
echo -e "${YELLOW}╚════════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 1. Check for existing lock file and process
if [ -f "$LOCK_FILE" ]; then
    OLD_PID=$(cat "$LOCK_FILE")
    echo -e "${YELLOW}📋 Lock file encontrado con PID: $OLD_PID${NC}"
    
    # Check if process is still running
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Bot ya está ejecutándose (PID: $OLD_PID)${NC}"
        echo ""
        ps aux | grep "python3 main.py" | grep -v grep || echo "Verificando..."
        exit 0
    else
        echo -e "${YELLOW}⚠️  PID en lock file no existe. Limpiando...${NC}"
        rm -f "$LOCK_FILE"
    fi
fi

# 2. Kill any duplicate processes
echo ""
echo -e "${YELLOW}🔍 Buscando procesos duplicados...${NC}"
PROCESS_COUNT=$(ps aux | grep "python3 main.py" | grep -v grep | wc -l)

if [ "$PROCESS_COUNT" -gt 0 ]; then
    echo -e "${RED}❌ Encontrados $PROCESS_COUNT proceso(s) del bot${NC}"
    echo -e "${YELLOW}Matando procesos viejos...${NC}"
    pkill -f "python3 main.py" 2>/dev/null || true
    sleep 2
fi

# 3. Kill tmux session if exists
echo -e "${YELLOW}🔄 Limpiando sesión tmux vieja...${NC}"
tmux kill-session -t "$SESSION_NAME" 2>/dev/null || echo "No había sesión previa"
sleep 1

# 4. Create lock file with current timestamp
echo -e "${YELLOW}📝 Creando lock file...${NC}"
echo "$$" > "$LOCK_FILE"
echo "$(date)" >> "$LOCK_FILE"
chmod 600 "$LOCK_FILE"

# 5. Start bot in tmux
echo ""
echo -e "${YELLOW}🚀 Iniciando bot en tmux...${NC}"
tmux new-session -d -s "$SESSION_NAME" "cd $BOT_DIR && python3 main.py"

sleep 3

# 6. Verify bot started
if tmux list-sessions | grep -q "^$SESSION_NAME"; then
    echo -e "${GREEN}✅ Bot iniciado correctamente${NC}"
    echo ""
    tmux capture-pane -t "$SESSION_NAME" -p | head -10
else
    echo -e "${RED}❌ Error: Bot no se inició${NC}"
    rm -f "$LOCK_FILE"
    exit 1
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Bot v3.3 iniciado con seguridad (sin duplicados)${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════════════════════${NC}"

