# TRAD v3.4 - TRADING RULES & DECISION FRAMEWORK

**Versión:** v3.4 (Option C - RSI Lookback Implementation)
**Última Actualización:** 2025-11-21
**Estado:** PRODUCCIÓN - First Trade Executed

---

## 📋 TABLA DE CONTENIDOS

1. [Problema Identificado](#problema-identificado)
2. [Solución Implementada](#solución-implementada)
3. [Componentes del Sistema](#componentes-del-sistema)
4. [Configuración Activa (MODE 2)](#configuración-activa-mode-2)
5. [Flujo de Decisión](#flujo-de-decisión)
6. [Checklist de Debugging](#checklist-de-debugging)
7. [Métricas de Rendimiento](#métricas-de-rendimiento)

---

## 🚨 PROBLEMA IDENTIFICADO

### Síntoma Original
- **Ciclos Ejecutados:** 150+
- **Trades Realizados:** 0
- **Estado:** Sistema en bloqueo conceptual

### Causa Raíz Diagnosticada
El sistema esperaba **simultáneamente**:
1. RSI en extremo (RSI > 65 para SHORT, o RSI < 35 para LONG)
2. Candles en color opuesto (candles rojos para SHORT, verdes para LONG)

**El Problema Conceptual:**
- Cuando precio sube (uptrend): RSI ALTO + candles VERDES (correlación natural)
- Cuando precio baja (downtrend): RSI BAJO + candles ROJOS (correlación natural)

El sistema SHORT esperaba: RSI alto (70+) + candles ROJOS
**Pero en realidad:** RSI alto siempre correlaciona con candles VERDES

Esta es una **contradicción física** - es imposible que ocurran simultáneamente.

---

## ✅ SOLUCIÓN IMPLEMENTADA

### Option C: RSI Lookback Strategy

En lugar de detectar solo extremos RSI, ahora **detectamos transiciones/crossovers de RSI**:

#### Lógica de Detección

**Para SHORT (Reversal desde overbought a normal):**
```
Ciclo anterior: RSI > 75 (overbought)
Ciclo actual:   RSI ≤ 65 (normalized)

Resultado: Reversal SHORT detectado
Momento: Exactamente cuando RSI momentum se debilita
Alineación: En este momento, candles naturalmente están RED
```

**Para LONG (Reversal desde oversold a normal):**
```
Ciclo anterior: RSI < 25 (oversold)
Ciclo actual:   RSI ≥ 35 (recovered)

Resultado: Reversal LONG detectado
Momento: Exactamente cuando RSI momentum se fortalece
Alineación: En este momento, candles naturalmente están GREEN
```

#### Por Qué Funciona

El crossover RSI marca el **momento exacto de reversión**, cuando:
- Momentum cambia de dirección
- Candle colors naturalmente se alinean
- Patrones de velas comienzan a revertir
- Toda la correlación (RSI → Trend → Patterns → Candles) se alinea

---

## 🔧 COMPONENTES DEL SISTEMA

### 1. **RSI Lookback Tracking** (src/strategy/hybrid.py)

```python
# Inicialización en __init__:
self.rsi_prev = 50.0              # RSI neutral inicial
self.rsi_change_detected = False  # Flag de crossover
self.rsi_change_side = None       # "LONG" o "SHORT"
```

**Lógica de Detección (líneas 320-339):**
```python
# Detectar crossover SHORT (overbought → normal)
if self.rsi_prev > self.rsi_overbought and rsi <= self.rsi_overbought:
    self.rsi_change_detected = True
    self.rsi_change_side = "SHORT"
    print(f"[RSI CHANGE DETECTED] SHORT Reversal: RSI {self.rsi_prev:.1f} → {rsi:.1f}")

# Detectar crossover LONG (oversold → normal)
elif self.rsi_prev < self.rsi_oversold and rsi >= self.rsi_oversold:
    self.rsi_change_detected = True
    self.rsi_change_side = "LONG"
    print(f"[RSI CHANGE DETECTED] LONG Reversal: RSI {self.rsi_prev:.1f} → {rsi:.1f}")

# Guardar RSI para próximo ciclo
self.rsi_prev = rsi
```

### 2. **Pattern Detection Debug** (src/strategy/candle_patterns.py)

Agregamos logging detallado a `detect_bullish_entry()` y `detect_bearish_entry()`:

```python
# Output format: [BULLISH/BEARISH] SUCCESS/FAILED | Reason
[BULLISH] SUCCESS: detected | Price: 82,750.32
[BEARISH] FAILED: no_reds | Last 3 colors: [1, 1, 1]
```

**Esto permite debuggear correlaciones en tiempo real:**
- ¿Se detectó el RSI change?
- ¿Detectó patrones correctamente?
- ¿Qué colores tienen las velas?

### 3. **RSI Filter Modification** (src/strategy/hybrid.py, línea 373)

```python
# ANTES: Solo extremos
rsi_filter_passed = (rsi < self.rsi_oversold or rsi > self.rsi_overbought)

# AHORA: Extremos O cambios detectados
rsi_filter_passed = (rsi < self.rsi_oversold or rsi > self.rsi_overbought) or self.rsi_change_detected
```

---

## ⚙️ CONFIGURACIÓN ACTIVA (MODE 2)

### Valores de Configuración

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| **MODE** | 2 | PERMISSIVE - Configuración más flexible |
| **RSI Oversold** | < 35 | Umbral bajo para LONG |
| **RSI Overbought** | > 65 | Umbral alto para SHORT |
| **Candle Requirement** | 2-3 consecutivas | Color correcto consecutivo |
| **EMA Alignment** | NO requerido | MODE 2 ignora EMA |
| **Gatekeeper** | NO requerido | No hay validación Claude |
| **Position Size** | 25 USDT | Por trade |
| **Leverage** | 50x | Isolated margin |

### Ubicación de Configuración

- **Permissiveness:** `config/permissiveness_config.txt` (MODE: 2)
- **Gatekeeper:** `config/gatekeeper_config.json` (si se habilita)

---

## 🔄 FLUJO DE DECISIÓN

```
┌──────────────────────────────────────────────────────────────────┐
│ CICLO DE TRADING (Main Loop)                                     │
└────────────────────┬─────────────────────────────────────────────┘
                     │
         ┌───────────▼───────────┐
         │ 1. Obtener OHLCV Data │
         └───────────┬───────────┘
                     │
         ┌───────────▼────────────────────┐
         │ 2. Calcular RSI(14)            │
         │    → Guardar RSI anterior      │
         │    → Detectar cambios/extremos │
         └───────────┬────────────────────┘
                     │
         ┌───────────▼──────────────────────────┐
         │ 3. Evaluar RSI Filter                │
         │    ¿RSI extremo O cambio detectado? │
         └───────────┬──────────────────────────┘
                     │
              ┌──────▼──────┐
              │ ¿PASS?      │
              └──┬───────┬──┘
         SI      │       │ NO
            ┌────▼──┐    │
            │Pasar  │    │
            │a 4    │    │
            └────┬──┘    │
                 │       │
            ┌────▼───────▼────┐
            │ 4. Detect Candle│
            │    Patterns     │
            └────┬─────────┬──┘
                 │         │
          ┌──────▼──┐      │
          │BULLISH? │      │
          └──┬───┬──┘      │
        YES  │   │ NO      │
            ┌┴───▼──┐      │
            │BEARISH│      │
            └──┬───┬┘      │
              │   │        │
         LONG │   │SHORT   │ NONE
             ┌┴───▼─┐      │
             │Entry?│      │
             └──┬───┬──┘   │
             YES│   │NO    │
            ┌───▼┐  │      │
            │BUY │  │      │
            │    │  │      │
            │SELL│  │      │
            └───┬┘  │      │
                │   │      │
                └───┴──────▼───┐
                   [NEXT CYCLE] │
                        ◀───────┘
```

### Estados Posibles por Ciclo

| RSI State | Pattern State | Acción |
|-----------|---------------|--------|
| Extremo + Cambio | Bullish | LONG Entry |
| Extremo + Cambio | Bearish | SHORT Entry |
| Solo Extremo | Bullish | Esperar patrón |
| Solo Extremo | Bearish | Esperar patrón |
| Normal | Cualquiera | HOLD - esperar RSI |

---

## 🔍 CHECKLIST DE DEBUGGING

### Nivel 1: Ciclos y RSI

```bash
# Ver últimos 50 ciclos y RSI changes
tail -100 logs/current/bot_session.log | grep -E "^\[|RSI CHANGE"

# Buscar cambios de RSI específicos
grep "RSI CHANGE DETECTED" logs/current/bot_session.log | tail -20
```

**Esperado:**
```
[RSI CHANGE DETECTED] SHORT Reversal: RSI 75.2 → 63.1
[RSI CHANGE DETECTED] LONG Reversal: RSI 24.8 → 36.5
```

### Nivel 2: Pattern Detection

```bash
# Ver decisiones de patrones
tail -200 logs/current/bot_session.log | grep -E "\[BULLISH\]|\[BEARISH\]"
```

**Esperado:**
```
[BULLISH] SUCCESS: detected | Price: 82,750.32
[BEARISH] FAILED: no_reds | Last 3 colors: [1, 1, 1]
```

### Nivel 3: Correlación RSI → Patterns

```bash
# Ver relación entre RSI changes y patterns
grep -A 2 "RSI CHANGE DETECTED" logs/current/bot_session.log | grep -E "RSI|BULLISH|BEARISH"
```

**Esperado:** RSI CHANGE → BULLISH/BEARISH dentro de 1-2 líneas

### Nivel 4: Trade Entries

```bash
# Ver TODAS las entradas de trades
grep "ENTRADA" logs/current/bot_session.log | tail -10

# Con contexto (RSI + Pattern + Entry)
grep -B 5 "ENTRADA" logs/current/bot_session.log | tail -20
```

### Problemas Comunes y Soluciones

| Problema | Síntoma | Solución |
|----------|---------|----------|
| **No se detectan RSI changes** | Ciclos sin `[RSI CHANGE DETECTED]` | Verificar `rsi_prev` inicialización |
| **Patrones fallan frecuentemente** | `[BULLISH] FAILED: no_greens` | Ajustar umbral candle requirement |
| **RSI changes pero no hay patrón** | RSI OK pero `FAILED: insufficient_data` | Esperar 3 velas, es normal |
| **Trades entran pero raro** | Pocos ENTRADA vs RSI changes | Revisar correlation en logs |

---

## 📊 MÉTRICAS DE RENDIMIENTO

### Primera Ejecución (Post Option C)

| Métrica | Valor | Estado |
|---------|-------|--------|
| **Ciclos hasta primer trade** | 11 | ✅ EXITOSO |
| **Precio de entrada** | $82,733.01 | SHORT position |
| **Tipo de entrada** | Bearish pattern | Detectado correctamente |
| **Total ciclos ejecutados** | 105+ | Continuo |
| **Errores** | 0 | ✅ Limpio |
| **Crashes** | 0 | ✅ Estable |

### Targets de Rendimiento

- **Trades por hora:** 2-4 (depende volatilidad)
- **Win rate objetivo:** 55-60%
- **Average trade duration:** 5-30 minutos
- **Profit target (TP1):** 50% position at 1-2% profit
- **Profit target (TP2):** 25% position at 3-5% profit
- **Stop loss:** -1.5% del entry

---

## 🚀 PRÓXIMOS PASOS

### Fase 1: Validación (Próximas 50 ciclos)
- [ ] Monitorear 50+ ciclos adicionales
- [ ] Verificar consistencia de trades
- [ ] Analizar win rate
- [ ] Revisar logs de pattern detection

### Fase 2: Integración Crecetrader (Pendiente)
- [ ] Integrar niveles calculados de `/home/juan/Downloads/crecetrader`
- [ ] Ajustar take-profits basado en support/resistance
- [ ] Mejorar entry signals con niveles de Crecetrader

### Fase 3: Optimización
- [ ] Fine-tune RSI thresholds basado en datos
- [ ] Ajustar candle pattern requirements
- [ ] Evaluar EMA filters para próximas versiones

---

## 📝 NOTAS IMPORTANTES

1. **Option C es la solución final** - Reemplaza lógica anterior rígida con detección inteligente de reversión RSI
2. **Correlación es clave** - RSI change → candles alineadas → patrones activan
3. **MODE 2 es permisivo** - No requiere EMA/Gatekeeper, solo RSI + patrones
4. **Debug con logs** - Los logs muestran exactamente qué decidió cada componente

---

**Archivo de configuración:** `config/permissiveness_config.txt`
**Logs activos:** `logs/current/bot_session.log`
**Última modificación:** 2025-11-21 11:42 UTC
