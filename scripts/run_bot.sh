#!/bin/bash
# Wrapper script para ejecutar el bot con paths correctos

cd "$(dirname "$0")"

# Establecer PYTHONPATH para que pueda encontrar los módulos
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Ejecutar el bot
python3 src/bot.py
