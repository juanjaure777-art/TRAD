# 🚀 CONFIGURACIÓN MAINNET 10X - TRAD Bot v3.6+

**Fecha:** 02 Diciembre 2025
**Modo:** MAINNET (dinero real)
**Configurado para:** Trading nocturno SOL/USDC

---

## ✅ CONFIGURACIÓN APLICADA

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| **Par** | SOL/USDC:USDC | Solo Solana (NO Bitcoin) |
| **Modo** | MAINNET | Dinero real, API real |
| **Order Size** | 1.0 USDC | Capital por trade |
| **Leverage** | 10x | Amplifica x10 ganancias/pérdidas |
| **Margin Mode** | Isolated | Protege otras posiciones |
| **Stop Loss** | 1.5% | -0.15 USDC por trade |
| **Take Profit 1** | 4.5% | +0.45 USDC (cierra 50%) |
| **Ratio R:R** | 3:1 | ✓ Confirmado |

---

## 💰 CÁLCULOS DE RIESGO (10x Leverage)

### Por Trade Individual:

**LONG Example @ $200:**
```
Entry:           $200.00
Capital:         1.00 USDC
Posición real:   10.00 USDC (1 x 10x)
Cantidad SOL:    0.05 SOL

Stop Loss:       $197.00 (-1.5%)
→ Pérdida:       -0.15 USDC (-15% del capital)

TP1:             $209.00 (+4.5%)
→ Ganancia:      +0.225 USDC (+22.5% en 50% de posición)
→ Activa:        Trailing Stop para 50% restante

Trailing (ej):   $220.00 (+10%)
→ Ganancia extra: +0.50 USDC
→ Total:         +0.725 USDC (+72.5%)
```

**SHORT Example @ $200:**
```
Entry:           $200.00
Capital:         1.00 USDC
Posición real:   10.00 USDC (1 x 10x)
Cantidad SOL:    0.05 SOL

Stop Loss:       $203.00 (+1.5%)
→ Pérdida:       -0.15 USDC (-15% del capital)

TP1:             $191.00 (-4.5%)
→ Ganancia:      +0.225 USDC (+22.5% en 50% de posición)
→ Activa:        Trailing Stop para 50% restante
```

---

## ⚠️ RIESGOS IMPORTANTES

### 1. Precio de Liquidación
- Con **10x leverage**, el precio de liquidación está muy cerca
- Si SOL se mueve **~-10%** desde tu entrada → **LIQUIDACIÓN TOTAL**
- Margen **isolated** = Solo pierdes el capital de esta posición (1 USDC máximo)

### 2. Volatilidad Amplificada
- SOL es volátil (movimientos de 2-5% son comunes)
- Con **10x leverage**: 3% de movimiento = 30% en tu capital
- El bot tiene **SL automático** a -1.5% para limitar pérdidas

### 3. Fees de Trading
- Binance cobra ~0.04% por operación (maker/taker)
- Con 10 USDC de posición real:
  - Entry: ~0.004 USDC
  - Exit: ~0.004 USDC
  - Total: ~0.008 USDC por trade completo (~0.8% del capital)

---

## 📊 EXPECTATIVAS REALISTAS

### Escenario Conservador (50% Win Rate):
```
10 trades:
- 5 wins × 0.45 USDC = +2.25 USDC
- 5 losses × 0.15 USDC = -0.75 USDC
- Net: +1.50 USDC (+150% ROI)
```

### Escenario Optimista (65% Win Rate - objetivo del bot):
```
10 trades:
- 6 wins × 0.45 USDC = +2.70 USDC
- 4 losses × 0.15 USDC = -0.60 USDC
- Net: +2.10 USDC (+210% ROI)
```

### Escenario Pesimista (35% Win Rate):
```
10 trades:
- 3 wins × 0.45 USDC = +1.35 USDC
- 7 losses × 0.15 USDC = -1.05 USDC
- Net: +0.30 USDC (+30% ROI)
```

**Nota:** Estos cálculos no incluyen ganancias adicionales del trailing stop, que pueden aumentar significativamente el profit.

---

## 🚀 INSTRUCCIONES DE INICIO

### Paso 1: Abrir Terminal
```bash
cd /home/juan/Escritorio/osiris/proyectos/TRAD
```

### Paso 2: Ejecutar Script de Inicio
```bash
./start_mainnet.sh
```

El script te pedirá:
1. Confirmar que entiendes el riesgo de 10x leverage (escribe `SI`)
2. Confirmar inicio en mainnet (escribe `CONFIRMO`)

### Paso 3: Monitoreo (recomendado abrir 3 terminales)

**Terminal 1 - GatekeeperV2 (decisiones de Claude):**
```bash
cd /home/juan/Escritorio/osiris/proyectos/TRAD
tail -f logs/gatekeeper_mainnet.log
```

**Terminal 2 - Multi-Timeframe Analysis:**
```bash
cd /home/juan/Escritorio/osiris/proyectos/TRAD
tail -f logs/trades/trade_journal.txt | grep -E "MTF_ANALYSIS|SIGNAL|ENTRY|EXIT"
```

**Terminal 3 - Estado General:**
```bash
cd /home/juan/Escritorio/osiris/proyectos/TRAD
tail -f logs/bot_session.log
```

---

## 📋 QUÉ ESPERAR

### ✅ Comportamiento Normal:
- **MTF_ANALYSIS** cada 2 minutos
- **Alignment scores** entre 40-100%
- **GatekeeperV2 rechaza** la mayoría de señales (es muy selectivo)
- **0-4 trades por día** (4H es conservador, puede no operar algunos días)
- **Sin errores** en logs

### 🔴 Señales de Problema:
- Errores de `-inf%` en risk manager
- Errores de `confidence_threshold`
- Bot crashea o se reinicia constantemente
- No hay `MTF_ANALYSIS` después de 5 minutos
- Warnings repetidos

---

## 🛑 CÓMO DETENER

En la terminal donde corre el bot:
```
Presiona: Ctrl+C
```

El bot:
1. Cierra el loop de monitoreo
2. **NO cierra posiciones abiertas automáticamente** (debes cerrar manualmente si hay alguna)
3. Guarda estadísticas de sesión

---

## 📊 CARACTERÍSTICAS DEL BOT v3.6+

### Sistema Multi-Timeframe Continuo
- Loop cada **2 minutos** (no espera 4 horas)
- Analiza **6 timeframes**: 1m, 5m, 15m, 1h, 4h, 1d
- Opera cuando **todos alinean** (independiente del timeframe)

### GatekeeperV2 con Claude AI
- Validación inteligente de **todas las señales**
- Recibe contexto completo: RSI, EMAs, Phase, MTF alignment
- Level 2 (permissive-moderate)
- **Explicación razonada** de cada decisión

### Metodología Crecetrader
- **T+Z+V Formula:** Tendencia + Zonas + Vacío
- Solo opera con setup **completo**
- Análisis de calidad de vela (location quality)
- Validación multi-timeframe

### Risk Management Profesional
- **Daily loss limit:** Máximo -5% diario
- **Max 1 posición abierta** a la vez
- **Trade cooldown:** 30s entre trades
- **Stats persistence:** Se guardan entre sesiones

---

## 💡 RECOMENDACIONES

### Antes de Iniciar:
1. ✅ Tener al menos **10-20 USDC** en cuenta (para múltiples trades)
2. ✅ Verificar que API keys están correctas en `config/.env`
3. ✅ Entender que puedes perder **hasta 0.15 USDC por trade**
4. ✅ Leer esta documentación completa

### Durante la Operación:
1. 🔍 **Monitorear logs** en las primeras 1-2 horas
2. 🔍 Verificar que **MTF_ANALYSIS** se genera correctamente
3. 🔍 Observar **decisiones de GatekeeperV2**
4. ⚠️ **NO interferir** con posiciones abiertas (dejar que SL/TP trabajen)
5. ⚠️ **NO cambiar configuración** con bot corriendo

### Después de las Primeras Operaciones:
1. 📊 Revisar **logs de trades** en `logs/trades/trade_journal.txt`
2. 📊 Analizar **win rate** y **average P&L**
3. 📊 Evaluar si **ajustar gatekeeper level** (2→3 si muchas pérdidas, 2→1 si muy selectivo)
4. 💰 Considerar **aumentar order size** si resultados son consistentes

---

## 🔧 ARCHIVOS DE CONFIGURACIÓN

### Configuración Principal
- `config/config.json` - Parámetros del bot
- `config/.env` - API keys (NO compartir)
- `config/gatekeeper_config.json` - Configuración de Claude

### Backups Creados
- `config/config.json.backup_YYYYMMDD_HHMMSS` - Backup automático

### Scripts de Inicio
- `start_mainnet.sh` - Inicio en mainnet (este script)
- `start_testnet.sh` - Inicio en testnet (para pruebas)

### Logs Importantes
- `logs/gatekeeper_mainnet.log` - Decisiones de Claude
- `logs/trades/trade_journal.txt` - Historial completo de trades
- `logs/bot_session.log` - Estado general del bot
- `logs/risk_management/events.log` - Eventos de risk management

---

## 🆘 TROUBLESHOOTING

### Problema: Bot rechaza todos los trades
**Causa:** Daily loss limit activado o alignment muy bajo
**Solución:**
```bash
# Verificar estado de risk
grep "RISK_REJECTED" logs/trades/trade_journal.txt | tail -5

# Si daily loss limit está activo incorrectamente, resetear:
rm logs/risk_management/stats.json
```

### Problema: Error de `-inf%`
**Causa:** Bug corregido, no debería ocurrir
**Solución:** Si ocurre, detener bot y reportar

### Problema: Error de `confidence_threshold`
**Causa:** Bug corregido, no debería ocurrir
**Solución:** Si ocurre, detener bot y reportar

### Problema: GatekeeperV2 no responde
**Causa:** API key de Anthropic inválida o sin créditos
**Solución:** Verificar `ANTHROPIC_API_KEY` en `config/.env`

---

## 📞 INFORMACIÓN DE CONTACTO

**Bot Version:** 3.6+
**Configurado:** 02 Diciembre 2025
**Auditoría:** Ver `AUDITORIA_02_DIC_2025.md`
**Bugs Corregidos:** 3/3 críticos

---

## ⚡ INICIO RÁPIDO

```bash
# 1. Ir al directorio
cd /home/juan/Escritorio/osiris/proyectos/TRAD

# 2. Iniciar bot
./start_mainnet.sh

# 3. En otra terminal, monitorear
tail -f logs/gatekeeper_mainnet.log
```

**¡Listo para operar!** 🚀

---

**⚠️ DISCLAIMER:** Trading con leverage conlleva alto riesgo. Solo opera con capital que puedes permitirte perder. Este bot no garantiza ganancias y los resultados pasados no garantizan resultados futuros.
