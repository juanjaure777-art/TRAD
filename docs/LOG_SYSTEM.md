# 📋 Sistema de Logs - TRAD Bot v3.5+

## Overview

El sistema de logs del bot TRAD es **crítico** para:
- ✅ Auditoría de todas las operaciones
- ✅ Debugging de problemas
- ✅ Análisis de performance
- ✅ Recuperación ante fallos

## Estructura de Logs

### Archivo Principal: `logs/trades_testnet.log`

**Formato:** JSON (1 evento por línea)

**Campos Obligatorios (todos los eventos):**
```json
{
  "timestamp": "2025-11-28T13:05:36.623427-03:00",  // ISO 8601 con timezone
  "cycle": 13,                                        // Número de ciclo del bot
  "type": "EVENT_TYPE"                                // Tipo de evento
}
```

## Tipos de Eventos

### 1. TZV_VALIDATION
Análisis Crecetrader de tendencia, zonas y riesgo - resultado de validación completa.

```json
{
  "timestamp": "2025-11-28T13:05:36.623427-03:00",
  "cycle": 13,
  "type": "TZV_VALIDATION",
  "t_passed": true,
  "z_passed": true,
  "v_passed": true,
  "all_passed": true,
  "confidence": 1.05,
  "description": "T:moderate_downtrend | Z:very_clear | V:excellent"
}
```

**Campos:**
- `t_passed` (bool): Tendencia validada
- `z_passed` (bool): Zonas (soportes/resistencias) identificadas
- `v_passed` (bool): Vacío (risk/reward) aceptable
- `all_passed` (bool): Todos los requisitos pasaron
- `confidence` (float): Confianza 0-1 (>0.7 es bueno)

### 1.5. TZV_PASSED
Cuando T+Z+V validation pasa completamente (importante hito en decisión de entrada).

```json
{
  "timestamp": "2025-11-28T13:05:36.623427-03:00",
  "cycle": 13,
  "type": "TZV_PASSED",
  "confidence": 1.05,
  "description": "T:moderate_downtrend | Z:very_clear | V:excellent",
  "t_details": "Tendencia moderada a la baja en 4H",
  "z_details": "Zonas claras identificadas (S1: 94500, S2: 93200, R1: 96800)",
  "v_details": "Risk/Reward 2.5:1 - Excelente",
  "risk_reward_ratio": 2.5
}
```

**Propósito**: Marca el momento cuando T+Z+V validation PASA - este es un hito crítico en el flujo de decisión.

### 2. TZV_REJECTED
Cuando T+Z+V falló (no pasa validación).

```json
{
  "timestamp": "2025-11-28T02:05:05.887737-03:00",
  "cycle": 2,
  "type": "TZV_REJECTED",
  "reason": "T+Z+V validation failed: Tendencia",
  "confidence": 0.7,
  "technical_signal_confidence": 70.0
}
```

### 3. GATEKEEPER_APPROVED
Claude (Gatekeeper) aprobó el setup técnico después de validar calidad.

```json
{
  "timestamp": "2025-11-28T13:06:00.123456-03:00",
  "cycle": 13,
  "type": "GATEKEEPER_APPROVED",
  "reason": "Setup quality confirmed - RSI oversold, strong downtrend, excellent R/R",
  "technical_confidence": 85.0,
  "claude_confidence": 0.85,
  "gatekeeper_level": 2,
  "signal_side": "SHORT"
}
```

**Propósito**: Registra cuando Claude/Gatekeeper APRUEBA un setup (importante milestone).

**Campos:**
- `reason` (str): Razón de la aprobación
- `technical_confidence` (float): Confianza técnica del bot (0-100)
- `claude_confidence` (float): Confianza de Claude (0-1)
- `gatekeeper_level` (int): Nivel de Gatekeeper aplicado
- `signal_side` (str): LONG o SHORT

### 3.5. GATEKEEPER_REJECT
Claude (Gatekeeper) rechazó el setup.

```json
{
  "timestamp": "2025-11-28T12:05:35.095997-03:00",
  "cycle": 12,
  "type": "GATEKEEPER_REJECT",
  "reason": "RSI not oversold enough for Level 2 (needs <35), NEUTRAL phase",
  "technical_confidence": 85.0,
  "claude_confidence": 0.3,
  "gatekeeper_level": 2
}
```

### 3.7. RISK_MANAGER_APPROVED
Risk Manager aprobó abrir la posición (verificación final antes de entrada).

```json
{
  "timestamp": "2025-11-28T13:06:05.123456-03:00",
  "cycle": 13,
  "type": "RISK_MANAGER_APPROVED",
  "max_open_trades": 2,
  "current_open_trades": 0,
  "daily_loss_limit_pct": 2.0,
  "position_allowed": true
}
```

**Propósito**: Registra aprobación final de Risk Manager antes de ENTRY_EXECUTED.

**Campos:**
- `max_open_trades` (int): Máximo de operaciones simultáneas permitidas
- `current_open_trades` (int): Operaciones abiertas actualmente
- `daily_loss_limit_pct` (float): Límite de pérdida diaria en %
- `position_allowed` (bool): Posición permitida

### 4. ENTRY_EXECUTED ⭐
**TRADE EJECUTADO** - El bot entró en una posición.

```json
{
  "timestamp": "2025-11-28T15:30:45.123456-03:00",
  "cycle": 25,
  "type": "ENTRY_EXECUTED",
  "side": "LONG",
  "entry_price": 95432.50,
  "stop_loss": 94756.23,
  "take_profit_1": 97341.00,
  "take_profit_2": 98523.45,
  "confidence": 0.85,
  "reason": "RSI oversold + Downtrend + Excellent RR",
  "rsi": 28.5,
  "ema_9": 94823.45,
  "ema_21": 95234.21,
  "crecetrader_location": "SUPPORT",
  "crecetrader_volatility": "EXPANSION",
  "crecetrader_quality": 0.92,
  "position_size_pct": 2.5,
  "mtf_confirmations": 2,
  "session": "AMERICAN",
  "order_id": "ORDRX_25"
}
```

**Este es el evento que indicará el PRIMER TRADE.**

**Campos principales:**
- `side` (str): LONG o SHORT
- `entry_price` (float): Precio de entrada
- `stop_loss` (float): Nivel de Stop Loss
- `take_profit_1` (float): Primer objetivo de ganancia
- `take_profit_2` (float): Segundo objetivo de ganancia
- `confidence` (float): Confianza del bot (0-100)
- `order_id` (str): ID de la orden generada

### 5. TRADE_CLOSED ⭐
**TRADE CERRADO** - Trade cerrado por cualquier razón. **Evento crítico que marca el final de la operación.**

```json
{
  "timestamp": "2025-11-28T16:30:00.000000-03:00",
  "cycle": 26,
  "type": "TRADE_CLOSED",
  "side": "LONG",
  "entry_price": 95432.50,
  "exit_price": 97341.00,
  "exit_type": "TP1",
  "pnl": 1909.00,
  "pnl_pct": 1.98,
  "exit_reason": "TAKE PROFIT 1 HIT",
  "duration_hours": 1.0
}
```

**Campos principales:**
- `side` (str): LONG o SHORT
- `entry_price` (float): Precio de entrada
- `exit_price` (float): Precio de salida
- `exit_type` (str): Tipo de salida: **TP1**, **TP2**, **SL**, **DEAD_TRADE**, **SESSION_CLOSING**, **TRAILING_STOP**, **OFF_HOURS**
- `pnl` (float): P&L en dinero (USDT)
- `pnl_pct` (float): P&L en porcentaje (%)
- `exit_reason` (str): Razón detallada del cierre
- `duration_hours` (float): Duración de la operación en horas

**Tipos de salida posibles:**
- `TP1`: Take Profit 1 alcanzado (salida parcial)
- `TP2`: Take Profit 2 alcanzado (salida final)
- `SL`: Stop Loss alcanzado (pérdida)
- `DEAD_TRADE`: Trade muerto (sin movimiento de precio)
- `SESSION_CLOSING`: Cierre automático por fin de sesión
- `TRAILING_STOP`: Trailing stop alcanzado
- `OFF_HOURS`: Cierre manual por horario off-market

## Flujo Completo de un Trade (ENTRADA → SALIDA)

### Ciclo de Vida Completo en los Logs

```
┌─────────────────────────────────────────────────────────────────┐
│                    CICLO DE TRADING COMPLETO                     │
└─────────────────────────────────────────────────────────────────┘

[Ciclo N]
  ├─ TZV_VALIDATION (siempre se evalúa)
  │   ├─ T: Validar tendencia
  │   ├─ Z: Validar zonas (S/R)
  │   └─ V: Validar riesgo/reward
  │
  ├─ [¿Pasó T+Z+V?]
  │   ├─ NO  → TZV_REJECTED (fin del ciclo)
  │   └─ SÍ  → TZV_PASSED ✅ (importante hito)
  │            │
  │            ├─ Strategy.analyze()
  │            │   └─ Genera señal técnica
  │            │
  │            ├─ GatekeeperV2.should_enter()
  │            │   └─ Evalúa calidad del setup
  │            │
  │            ├─ [¿Aprobó Gatekeeper?]
  │            │   ├─ NO  → GATEKEEPER_REJECT (fin del ciclo)
  │            │   └─ SÍ  → GATEKEEPER_APPROVED ✅
  │            │
  │            ├─ RiskManager.can_open_position()
  │            │   └─ Valida límites de riesgo
  │            │
  │            ├─ [¿Aprobó RiskManager?]
  │            │   ├─ NO  → RISK_REJECTED (fin del ciclo)
  │            │   └─ SÍ  → RISK_MANAGER_APPROVED ✅
  │            │
  │            └─ ENTRY_EXECUTED 🎯 ← PRIMERA OPERACIÓN
  │               (Posición abierta)
  │
  └─ [Ciclos siguientes - GESTIÓN DE POSICIÓN ABIERTA]
     │
     ├─ Check dead trade?
     │   ├─ SÍ  → TRADE_CLOSED (exit_type: DEAD_TRADE)
     │   └─ NO  → continuar
     │
     ├─ Check SL/TP hits?
     │   ├─ SL Hit   → TRADE_CLOSED (exit_type: SL) 🔴
     │   ├─ TP1 Hit  → TRADE_CLOSED (exit_type: TP1) 🟢
     │   ├─ TP2 Hit  → TRADE_CLOSED (exit_type: TP2) 🟢
     │   └─ NO       → continuar
     │
     ├─ Check session closing?
     │   ├─ SÍ  → TRADE_CLOSED (exit_type: SESSION_CLOSING)
     │   └─ NO  → continuar
     │
     └─ Check off-hours?
         ├─ SÍ  → TRADE_CLOSED (exit_type: OFF_HOURS)
         └─ NO  → posición sigue abierta
```

### Ejemplo Completo en Logs

```json
[Ciclo 13 - T13:05:36]
{"timestamp":"2025-11-28T13:05:36.623427-03:00", "cycle":13, "type":"TZV_VALIDATION", "all_passed":true, "confidence":1.05}
{"timestamp":"2025-11-28T13:05:36.700000-03:00", "cycle":13, "type":"TZV_PASSED", "confidence":1.05, "description":"T:moderate_downtrend | Z:very_clear | V:excellent"}
{"timestamp":"2025-11-28T13:06:00.100000-03:00", "cycle":13, "type":"GATEKEEPER_APPROVED", "reason":"Setup quality confirmed", "technical_confidence":85, "claude_confidence":0.85}
{"timestamp":"2025-11-28T13:06:05.200000-03:00", "cycle":13, "type":"RISK_MANAGER_APPROVED", "position_allowed":true}
{"timestamp":"2025-11-28T13:06:10.300000-03:00", "cycle":13, "type":"ENTRY_EXECUTED", "side":"SHORT", "entry_price":95432.50, "stop_loss":94756.23, "take_profit_1":97341.00}

[Ciclos 14-26 - Posición abierta, sin events]

[Ciclo 27 - T16:30:00 - TP1 ALCANZADO]
{"timestamp":"2025-11-28T16:30:00.000000-03:00", "cycle":27, "type":"TRADE_CLOSED", "side":"SHORT", "entry_price":95432.50, "exit_price":97341.00, "exit_type":"TP1", "pnl_pct":1.98, "duration_hours":3.40}
```

**Análisis:**
- Ciclo 13: Señal generada, validada, aprobada y entrada ejecutada
- Ciclos 14-26: Posición abierta sin cambios (sin logs)
- Ciclo 27: Trade alcanza TP1 y se cierra con ganancia de 1.98%

## Validación de Logs

### Ejecutar Validador

```bash
python3 scripts/log_validator.py logs/trades_testnet.log
```

**Output:**
- ✅ Total líneas
- ✅ Líneas válidas
- ❌ Líneas inválidas
- 🔐 Checksum SHA256
- 📋 Tipos de eventos
- ⚠️ Advertencias
- ❌ Errores

### Criterios de Validación

✅ **Válido:**
- JSON bien formado
- Timestamp con timezone
- Campos requeridos presentes
- Valores en rango válido

❌ **Inválido:**
- JSON malformado
- Campos requeridos faltantes
- Timestamp inválido
- Ciclos fuera de secuencia

## Rotación de Logs

**Política de rotación (implementada automáticamente):**

- **Archivo activo:** `logs/trades_testnet.log`
- **Archivo anterior:** `logs/trades_testnet.log.1` (si excede 5 MB)
- **Compresión:** Archivos > 1 semana se comprimen a `.gz`
- **Archivo:** Archivos > 1 mes se mueven a `logs/archive/`
- **Eliminación:** Archivos > 3 meses se eliminan

**Monitoreo manual:**
```bash
# Ver tamaño actual
ls -lh logs/trades_testnet.log

# Validar integridad
python3 scripts/log_validator.py logs/trades_testnet.log

# Ver últimas líneas
tail -10 logs/trades_testnet.log | jq .
```

## Integrity Check (Checksum)

Cada hora, el bot calcula SHA256 del log y lo compara.

Si hay cambios inesperados:
```json
{
  "timestamp": "...",
  "type": "LOG_INTEGRITY_CHECK",
  "checksum_previous": "25b54d45cd6bbf43...",
  "checksum_current": "25b54d45cd6bbf43...",
  "status": "OK"
}
```

## Mejores Prácticas

### ✅ HACER

1. **Validar regularmente:**
   ```bash
   python3 scripts/log_validator.py logs/trades_testnet.log
   ```

2. **Monitorear tamaño:**
   ```bash
   du -sh logs/
   ls -lh logs/*.log
   ```

3. **Buscar eventos específicos:**
   ```bash
   jq 'select(.type == "ENTRY_EXECUTED")' logs/trades_testnet.log
   ```

4. **Ver estadísticas:**
   ```bash
   jq '.type' logs/trades_testnet.log | sort | uniq -c
   ```

### ❌ NO HACER

1. ❌ Editar logs manualmente
2. ❌ Eliminar logs sin archivar
3. ❌ Cambiar formato de timestamp
4. ❌ Truncar archivo de log activo

## Recuperación ante Fallos

Si el log se corrompe:

1. **Validar integridad:**
   ```bash
   python3 scripts/log_validator.py logs/trades_testnet.log
   ```

2. **Si hay corrupción:**
   ```bash
   # Restaurar desde backup (OSIRIS guarda cada 3 min)
   cp logs/archive/trades_testnet.log.backup logs/trades_testnet.log
   ```

3. **Reconstruir desde eventos válidos:**
   ```bash
   # El validador genera un archivo "trades_testnet.log.cleaned"
   python3 scripts/log_validator.py logs/trades_testnet.log --repair
   ```

## Monitoreo en Tiempo Real

### Ver nuevos eventos:
```bash
tail -f logs/trades_testnet.log
```

### Ver formato legible:
```bash
tail -20 logs/trades_testnet.log | jq '.'
```

### Buscar primeros trades:
```bash
jq 'select(.type == "ENTRY_EXECUTED")' logs/trades_testnet.log | head -1
```

### Contar eventos por tipo:
```bash
jq -s 'group_by(.type) | map({type: .[0].type, count: length})' logs/trades_testnet.log
```

## Timestamps

**Formato:** ISO 8601 con timezone de Buenos Aires

```
2025-11-28T13:05:36.623427-03:00
           |        |         |
           |        |         +-- Timezone (-03:00 = Buenos Aires)
           |        +----------- Fracciones de segundo (microsegundos)
           +------------------- Fecha + Hora (UTC-3)
```

**Conversión:**
- `-03:00` = UTC-3 (Buenos Aires en horario estándar)
- `-02:00` = UTC-2 (Buenos Aires en horario de verano, Oct-Mar)
- El sistema usa siempre `-03:00` (configurado en `bot.py`)

## Ejemplos de Queries Útiles

### Obtener primer trade:
```bash
jq 'select(.type == "ENTRY_EXECUTED") | .[0]' logs/trades_testnet.log
```

### Ver todos los rechazos:
```bash
jq 'select(.type | contains("REJECT"))' logs/trades_testnet.log
```

### Filtrar ciclo específico:
```bash
jq 'select(.cycle == 13)' logs/trades_testnet.log
```

### Ver confianza promedio:
```bash
jq '.confidence' logs/trades_testnet.log | jq -s 'add/length'
```

## Conclusión

El sistema de logs es **robusto y auditable**:
- ✅ 100% integridad verificable
- ✅ Timestamps precisos (Buenos Aires)
- ✅ Validación automática
- ✅ Recuperación ante fallos
- ✅ Archivo completo para referencia

**Este sistema permite:**
- 🔍 Debuguear cualquier problema
- 📊 Analizar performance
- 📋 Auditar operaciones
- 🔐 Verificar integridad

---

**Última actualización:** 2025-11-28
**Estado:** ✅ Producción
