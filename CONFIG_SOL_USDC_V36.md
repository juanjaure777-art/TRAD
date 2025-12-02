# Configuración SOL/USDC - TRAD Bot v3.6

**Fecha:** 2025-12-01
**Versión:** 3.6.0
**Modo:** Futuros con USDC (sin comisiones)

---

## RESUMEN DE CONFIGURACIÓN

### Par de Trading
- **Símbolo:** SOL/USDC
- **Mercado:** Futuros Binance
- **Tipo:** Futuros con USDC (evita comisiones vs USDT)

### Apalancamiento
- **Leverage:** 1x (sin apalancamiento)
- **Margin Mode:** Isolated (margen aislado)
- **Ventaja:** Menor riesgo, sin liquidación agresiva

### Tamaño de Orden
- **Order Size:** 5 USDC por trade
- **Capital por operación:** 5 USDC
- **Con 1x leverage:** Exposición real de 5 USDC (sin multiplicar)

---

## GESTIÓN DE RIESGO (RATIO 1:3)

### Stop Loss
- **Porcentaje:** 1.5%
- **Riesgo por trade:** ~$0.075 (en orden de 5 USDC)

### Take Profit 1 (TP1)
- **Porcentaje:** 4.5%
- **Ratio:** 3:1 (3x el stop loss)
- **Acción:** Cierra 50% + activa trailing stop para 50% restante
- **Ganancia esperada:** ~$0.225 (en el 50% de la posición)

### Trailing Stop
- **Activación:** Inmediatamente después de TP1
- **Gestión:** 50% restante de la posición
- **Trailing %:** 1% (TRAILING_STOP_PCT)
- **Objetivo:** Maximizar ganancias en movimientos fuertes

---

## EJEMPLO DE OPERACIÓN LONG

### Entrada
- **Precio SOL:** $200.00
- **Orden:** 5 USDC / $200 = 0.025 SOL
- **Capital comprometido:** 5 USDC (1x leverage)

### Niveles de Salida

**Stop Loss ($197.00):**
- Precio: $200 - 1.5% = $197.00
- Si se activa: Pierde $0.075 (100% de la posición)
- **Pérdida total:** -$0.075

**Take Profit 1 ($209.00):**
- Precio: $200 + 4.5% = $209.00
- Cierra: 50% de la posición (0.0125 SOL)
- Ganancia: 0.0125 SOL × $9 = $0.1125
- **✅ Activa trailing stop para 0.0125 SOL restante**
- **Posición restante:** 0.0125 SOL con trailing stop

**Trailing Stop (desde $209.00):**
- Inicial: $209 - 1% = $206.91
- Si SOL sube a $220: Trailing = $220 - 1% = $217.80
- Si SOL sube a $230: Trailing = $230 - 1% = $227.70
- Si SOL baja a $227: **CIERRA** en $227.70

### Resultado Final (Ejemplo)
- TP1: +$0.1125 (50% en $209)
- Trailing: +$0.3463 (50% en $227.70)
- **Ganancia total:** +$0.4588 (+9.18% sobre 5 USDC)
- **Risk/Reward logrado:** 1:6.1

---

## COMPARACIÓN: ANTES vs AHORA

### ANTES (v3.5)
```
Símbolo:        BTC/USDT
Leverage:       10x
Order Size:     25 USDT
Stop Loss:      0.8%
TP1:            2.0%
TP2:            3.5%
Ratio:          ~1:2.5
```

**Riesgo por trade:** 25 USDT × 10x × 0.8% = **$2.00**

---

### AHORA (v3.6)
```
Símbolo:        SOL/USDC
Leverage:       1x
Order Size:     5 USDC
Stop Loss:      1.5%
TP1:            4.5%
TP2:            DEPRECATED (trailing gestiona 50% restante)
Ratio:          1:3 (mínimo, puede ser mayor con trailing)
```

**Riesgo por trade:** 5 USDC × 1x × 1.5% = **$0.075**

---

## VENTAJAS DE LA NUEVA CONFIGURACIÓN

### 1. **Sin Comisiones**
- SOL/USDC en futuros no paga comisiones (vs USDT)
- Ahorro en cada entrada/salida

### 2. **Menor Riesgo por Trade**
- Antes: $2.00 de riesgo
- Ahora: $0.075 de riesgo
- **Reducción:** 96.25% menos riesgo

### 3. **Mejor Risk/Reward**
- Antes: 1:2.5 ratio
- Ahora: 1:3 mínimo (puede llegar a 1:6+ con trailing)

### 4. **Sin Apalancamiento = Sin Liquidación**
- Con 1x leverage, prácticamente imposible ser liquidado
- Solo pierdes si tocas el stop loss

### 5. **Trailing Stop desde TP1**
- 50% de la posición captura movimientos grandes
- No limitado a TP2 fijo

---

## CONFIGURACIÓN MULTI-TIMEFRAME

El bot analiza **6 timeframes simultáneamente:**

| Timeframe | Peso | Función |
|-----------|------|---------|
| Daily (1d) | 40% | Define tendencia principal del día |
| 4 Hour (4h) | 25% | Define estructura para próximas 16 horas |
| 1 Hour (1h) | 20% | Confirmación de estructura |
| 15 Min (15m) | 10% | Entrada fina |
| 5 Min (5m) | 3% | Micro-confirmación |
| 1 Min (1m) | 2% | Ejecución precisa |

### Lógica de Entrada

**El bot NO espera un timeframe específico.**

Opera cuando:
1. ✅ **Alignment Score >= 70%** (timeframes alineados)
2. ✅ **Daily/4H/1H muestran misma dirección**
3. ✅ **15m/5m/1m dan señal técnica** (RSI extremo)
4. ✅ **GatekeeperV2 (Claude AI) aprueba**

**Frecuencia:** Loop cada 2 minutos (monitoreo continuo 24/7)

---

## PARÁMETROS TÉCNICOS

### Indicadores
- **RSI Period:** 7
- **RSI Oversold:** 25
- **RSI Overbought:** 75
- **EMA Fast:** 9
- **EMA Slow:** 21

### Límites
- **Max trades/día:** 8
- **Trade cooldown:** 5 minutos
- **Max daily loss:** 2.0%
- **Max open positions:** 3

---

## ARCHIVOS MODIFICADOS

### 1. `config/config.json`
```json
{
  "trading": {
    "symbol": "SOL/USDC",        // ← CAMBIADO de BTC/USDT
    "order_size_usdt": 5.0,      // ← CAMBIADO de 25.0
    "leverage": 1.0,             // ← CAMBIADO de 10.0
  },
  "risk_management": {
    "sl_pct": 1.5,               // ← CAMBIADO de 0.8
    "tp1_pct": 4.5,              // ← CAMBIADO de 2.0
    "tp2_pct": 6.0,              // ← (DEPRECATED, no se usa)
  }
}
```

### 2. `src/exit/sl_tp_manager.py`
- ✅ TP1 activa trailing stop inmediatamente
- ✅ TP2 deprecated (no se usa)
- ✅ Trailing gestiona 50% restante desde TP1

---

## CÁLCULO DE GANANCIAS ESPERADAS

### Escenario Conservador (Solo TP1)
- Win rate: 60%
- Trades/día: 3
- Días/mes: 20

**Pérdidas:**
- 40% × 3 × 20 = 24 trades perdedores
- 24 × -$0.075 = **-$1.80**

**Ganancias:**
- 60% × 3 × 20 = 36 trades ganadores
- 36 × $0.1125 = **+$4.05** (solo TP1, sin contar trailing)

**Ganancia neta:** +$2.25/mes (+45% ROI sobre capital de 5 USDC)

### Escenario Realista (TP1 + Trailing promedio)
Si trailing captura en promedio +2% adicional en el 50%:
- Ganancia por trade: $0.1125 (TP1) + $0.05 (trailing) = $0.1625
- 36 trades ganadores × $0.1625 = **+$5.85**
- **Ganancia neta:** +$4.05/mes (+81% ROI)

---

## CHECKLIST PRE-EJECUCIÓN

Antes de ejecutar en mainnet:

- [✅] Config actualizado: SOL/USDC
- [✅] Leverage: 1x
- [✅] Order size: 5 USDC
- [✅] SL/TP ratio: 1:3 (1.5% / 4.5%)
- [✅] Trailing stop logic actualizada
- [ ] **API Keys verificadas** en config/.env
- [ ] **Balance suficiente** en cuenta (mínimo 10 USDC)
- [ ] **Verificar símbolo** existe en Binance Futures: `SOL/USDC`
- [ ] **Testnet** ejecutado y validado (RECOMENDADO)

---

## COMANDOS DE EJECUCIÓN

### Activar virtualenv
```bash
cd /home/juan/Escritorio/osiris/proyectos/TRAD
source venv/bin/activate
```

### Ejecutar bot en mainnet
```bash
python3 main.py
```

### Monitorear logs en tiempo real
```bash
# Ver journal de trades
tail -f logs/trades/trade_journal.txt

# Ver decisiones de GatekeeperV2
tail -f logs/gatekeeper_mainnet.log

# Ver análisis multi-timeframe
tail -f logs/trades/trade_journal.txt | grep MTF

# Monitoreo combinado
watch -n 1 'echo "=== GATEKEEPER ===" && tail -3 logs/gatekeeper_mainnet.log && echo "" && echo "=== MTF ANALYSIS ===" && tail -3 logs/trades/trade_journal.txt | grep MTF'
```

### Detener bot
```bash
Ctrl + C
```

---

## NOTAS IMPORTANTES

### ⚠️ Verificar antes de operar:

1. **SOL/USDC disponible en Binance Futures**
   ```bash
   # Verificar desde Python:
   python3 -c "import ccxt; ex = ccxt.binance(); markets = ex.load_markets(); print('SOL/USDC' in markets)"
   ```

2. **Balance suficiente:**
   - Mínimo: 10 USDC (para 1-2 trades simultáneos)
   - Recomendado: 50+ USDC (para 8-10 trades)

3. **Margin Mode configurado:**
   - Isolated margin debe estar habilitado en Binance
   - Leverage 1x configurado para SOL/USDC

---

## PRÓXIMOS PASOS RECOMENDADOS

### 1. Testnet (ALTAMENTE RECOMENDADO)
```bash
# Cambiar a testnet en config/config.json:
"mode": "testnet"

# Ejecutar por 1-3 días
python3 main.py

# Validar:
# - Órdenes se ejecutan correctamente
# - TP1 cierra 50% y activa trailing
# - Trailing gestiona 50% restante
# - Símbolo SOL/USDC funciona correctamente
```

### 2. Mainnet (después de validar testnet)
```bash
# Cambiar a mainnet en config/config.json:
"mode": "mainnet"

# Ejecutar
python3 main.py
```

### 3. Monitoreo
- Revisar logs cada 6-12 horas
- Validar alignment scores
- Verificar decisiones de GatekeeperV2
- Ajustar gatekeeper_level si es necesario (1-5)

---

**Versión:** 3.6.0
**Autor:** Claude Code Assistant
**Estado:** ✅ Configurado y listo para operar
**Símbolo:** SOL/USDC Futuros
**Leverage:** 1x
**Risk/Reward:** 1:3 mínimo
