#!/bin/bash
################################################################################
#                  💾 AUTOGUARDADO TRAD - CADA 1 MINUTO                       #
#             Guarda logs, journal y estado del bot automáticamente            #
################################################################################

set -euo pipefail

# Directorios
TRAD_DIR="/home/juan/Escritorio/osiris/proyectos/TRAD"
LOGS_DIR="$TRAD_DIR/logs"
BACKUP_DIR="$TRAD_DIR/.backups/autoguardado"
TIMESTAMP=$(date '+%Y-%m-%d_%H-%M-%S')
LOCK_FILE="/tmp/trad-autosave.lock"

# Evitar ejecuciones simultáneas
if [ -f "$LOCK_FILE" ] && [ $(( $(date +%s) - $(stat -c%Y "$LOCK_FILE" 2>/dev/null || echo 0) )) -lt 30 ]; then
    exit 0
fi
touch "$LOCK_FILE"

# Crear directorio de backup si no existe
mkdir -p "$BACKUP_DIR"

# Función para hacer backup de archivos críticos
backup_critical_files() {
    local backup_subdir="$BACKUP_DIR/$(date '+%Y%m%d')"
    mkdir -p "$backup_subdir"

    # Backup de logs críticos (solo si existen y no están vacíos)
    if [ -d "$LOGS_DIR/trades" ] && [ "$(ls -A $LOGS_DIR/trades 2>/dev/null)" ]; then
        [ -f "$LOGS_DIR/trades/trade_journal.txt" ] && cp "$LOGS_DIR/trades/trade_journal.txt" "$backup_subdir/trade_journal_$TIMESTAMP.txt" 2>/dev/null || true
    fi

    if [ -d "$LOGS_DIR" ]; then
        [ -f "$LOGS_DIR/gatekeeper_mainnet.log" ] && tail -500 "$LOGS_DIR/gatekeeper_mainnet.log" > "$backup_subdir/gatekeeper_$TIMESTAMP.log" 2>/dev/null || true
        [ -f "$LOGS_DIR/session.log" ] && tail -500 "$LOGS_DIR/session.log" > "$backup_subdir/session_$TIMESTAMP.log" 2>/dev/null || true
    fi

    # Limpiar backups antiguos (mantener solo últimos 7 días)
    find "$BACKUP_DIR" -type d -name "202*" -mtime +7 -exec rm -rf {} + 2>/dev/null || true
}

# Función para sincronizar datos importantes
sync_data() {
    cd "$TRAD_DIR"

    # Verificar si hay cambios en archivos de logs/trades
    if [ -d "$LOGS_DIR/trades" ]; then
        local changes=$(find "$LOGS_DIR/trades" -type f -mmin -2 2>/dev/null | wc -l)
        if [ "$changes" -gt 0 ]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] 💾 Autoguardado: $changes archivo(s) modificado(s) en trades" >> "$LOGS_DIR/autosave.log"
        fi
    fi

    # Sincronizar a disco (flush buffers)
    sync
}

# Función para registrar estado del sistema
log_system_state() {
    local state_file="$LOGS_DIR/system_state.log"

    # Verificar si el bot está corriendo
    if pgrep -f "main.py" > /dev/null; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Bot activo | PID: $(pgrep -f "main.py")" >> "$state_file"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  Bot inactivo" >> "$state_file"
    fi

    # Mantener solo últimas 1000 líneas del log de estado
    tail -1000 "$state_file" > "$state_file.tmp" 2>/dev/null && mv "$state_file.tmp" "$state_file" || true
}

# Ejecutar funciones
backup_critical_files
sync_data
log_system_state

# Limpiar lock
rm -f "$LOCK_FILE"

exit 0
