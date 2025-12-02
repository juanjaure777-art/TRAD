#!/bin/bash
#
# Setup Automation - Configura monitoreo automático del bot
#

BOT_DIR="/home/juan/Escritorio/osiris/proyectos/TRAD"
CRON_JOB="*/5 * * * * cd $BOT_DIR && ./health_check.sh > /dev/null 2>&1"

echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║        Configurando Automatización - TRAD Bot v3.3                            ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "health_check.sh"; then
    echo "✅ Cron job ya está configurado"
    echo ""
    crontab -l | grep health_check
else
    echo "📝 Agregando cron job para health check cada 5 minutos..."
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Cron job agregado"
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "📊 RESUMEN DE PROTECCIONES:"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "1️⃣ start_bot_safe.sh"
echo "   └─ Lock file para evitar múltiples instancias"
echo "   └─ Mata procesos duplicados antes de iniciar"
echo "   └─ Verifica que solo hay 1 sesión tmux"
echo ""
echo "2️⃣ health_check.sh"
echo "   └─ Verifica sesión tmux"
echo "   └─ Verifica proceso único"
echo "   └─ Verifica logs actualizados"
echo "   └─ Verifica ciclos en ejecución"
echo "   └─ Reinicia automáticamente si hay problemas"
echo ""
echo "3️⃣ Cron Automation"
echo "   └─ Ejecuta health check cada 5 minutos"
echo "   └─ Detecta y repara problemas automáticamente"
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "🚀 COMANDOS ÚTILES:"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Iniciar bot (SEGURO):"
echo "   ./start_bot_safe.sh"
echo ""
echo "Verificar salud manual:"
echo "   ./health_check.sh"
echo ""
echo "Ver logs de salud:"
echo "   tail -f .bot_health.log"
echo ""
echo "Ver cron jobs:"
echo "   crontab -l"
echo ""
echo "Editar cron jobs:"
echo "   crontab -e"
echo ""

