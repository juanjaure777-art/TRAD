# TRAD Bot v3.6 - Sistema Multi-Timeframe Continuo 24/7
## Documentación Completa del Sistema

**Fecha de Implementación:** 2025-12-01
**Versión:** 3.6.0
**Estado:** ✅ Producción Ready

---

## RESUMEN EJECUTIVO

TRAD Bot v3.6 implementa un sistema revolucionario de trading que **NO opera en un timeframe específico**, sino que **monitorea continuamente el mercado 24/7** buscando oportunidades cuando **todos los timeframes alinean**.

### Cambio de Paradigma

#### ANTES (v3.5):
- ❌ Opera en 4H → espera 4 horas entre ciclos
- ❌ Pierde oportunidades en timeframes menores
- ❌ No aprovecha volatilidad del mercado
- ❌ Timeframe = restricción temporal

#### AHORA (v3.6):
- ✅ Monitoreo continuo cada 2 minutos
- ✅ Analiza 6 timeframes simultáneamente (1m, 5m, 15m, 1h, 4h, 1d)
- ✅ Opera cuando TODO alinea (independiente del timeframe)
- ✅ Timeframes = CONTEXTO y FILTRO (no restricción)

---

## ARQUITECTURA DEL SISTEMA

### 1. Módulos Multi-Timeframe

#### **MultiTimeframeDataLoader** (`multi_timeframe_data_loader.py`)
**Responsabilidad:** Carga datos OHLCV de todos los timeframes

**Funcionalidades:**
- Descarga velas de 1m, 5m, 15m, 1h, 4h, 1d simultáneamente
- Calcula indicadores técnicos (RSI, EMA, ATR, volatilidad)
- Identifica soporte/resistencia por timeframe
- Determina momentum y fase de mercado

**Uso:**
```python
loader = MultiTimeframeDataLoader(exchange, symbol='BTC/USDT')
all_ohlcv = loader.load_all_timeframes(limit=100)
analysis_1h = loader.get_timeframe_analysis('1h', limit=100)
```

#### **MultitimeframeCorrelator** (`multitimeframe_correlator.py`)
**Responsabilidad:** Correlaciona múltiples timeframes con jerarquía

**Jerarquía de Pesos:**
- Daily (1d): 40% - Define tendencia principal del día
- 4 Hour (4h): 25% - Define estructura de las próximas 16 horas
- 1 Hour (1h): 20% - Confirmación de estructura
- 15 Min (15m): 10% - Entrada fina
- 5 Min (5m): 3% - Micro-confirmación
- 1 Min (1m): 2% - Ejecución precisa

**Métricas Calculadas:**
- `alignment_score`: 0-100% (alineación entre timeframes)
- `primary_direction`: BULLISH | BEARISH | NEUTRAL
- `opportunity_score`: 0-100 (calidad del setup)
- `confidence`: 0.0-1.0 (confianza general)
- `volatility_context`: LOW | MODERATE | HIGH
- `risk_factors`: Lista de riesgos detectados

**Uso:**
```python
correlator = MultitimeframeCorrelator()
result = correlator.correlate(timeframe_data)
print(f"Alignment: {result['alignment_score']}%")
print(f"Direction: {result['primary_direction']}")
```

#### **MultitimeframeAdapter** (`multitimeframe_adapter.py`)
**Responsabilidad:** API simple para integración con el bot

**Funcionalidades:**
- Un solo método: `load_and_analyze()` obtiene TODO
- Compila contexto completo para GatekeeperV2
- Métodos helper: `should_enter_now()`, `get_quick_signal()`

**Uso:**
```python
adapter = MultitimeframeAdapter(exchange, symbol='BTC/USDT')
context = adapter.load_and_analyze()  # TODO en una línea
# Pasar context a GatekeeperV2
```

#### **MultitimeframeAudit** (`multitimeframe_audit.py`)
**Responsabilidad:** Validación de integridad de datos

**Validaciones:**
- OHLC relationships (High >= Low, etc.)
- Valores válidos (no NaN, no negativos)
- Timestamps consecutivos
- Gaps extremos (> 20%)
- Indicadores en rangos válidos
- Lógica de correlación correcta

---

## LÓGICA OPERATIVA

### Modelo Operativo

```
LOOP CONTINUO (cada 2 minutos):
├── 1. Cargar análisis multi-timeframe (6 timeframes)
├── 2. Correlator calcula alignment_score
├── 3. Si alignment < 40% → SKIP (timeframes conflictivos)
├── 4. Buscar señales técnicas en timeframes bajos (15m/5m/1m)
├── 5. GatekeeperV2 (Claude AI) valida con contexto completo
├── 6. Si APROBADO → ENTER inmediatamente
└── 7. Gestionar posición abierta
```

### Decisión de Entrada

**NO se espera a un timeframe específico.**
Se entra cuando:

1. **Daily/4H/1H muestran alineación** → Contexto favorable
2. **15m/5m/1m dan señal técnica** → RSI oversold/overbought
3. **Alignment score >= threshold** → Según gatekeeper level
4. **GatekeeperV2 aprueba** → Claude valida con TODO el contexto

---

## GATEKEEPERV2 CON MULTI-TIMEFRAME AWARENESS

### System Prompt Actualizado

GatekeeperV2 ahora entiende:
- Jerarquía de timeframes (Daily > 4H > 1H > Micro)
- Alignment score y su significado
- Volatility context (LOW/MODERATE/HIGH)
- Risk factors identificados
- Opportunity score

### Niveles de Selectividad

**LEVEL 1 (PERMISSIVE):**
- Alignment > 70%: Entra fácilmente
- RSI < 35 o > 65
- R:R >= 1:1

**LEVEL 2 (MODERATE):**
- Require 4H confirmación de Daily
- Alignment > 60%
- RSI < 35 o > 65
- R:R >= 1:1.5

**LEVEL 3 (BALANCED - DEFAULT):**
- Daily = 4H = 1H (perfecta alineación recomendada)
- Alignment > 75%
- RSI < 30 o > 70
- R:R >= 1:2

**LEVEL 4 (SELECTIVE):**
- Alignment > 85%
- RSI < 25 o > 75 (extremos)
- R:R >= 1:3
- Solo trending/reversal phases

**LEVEL 5 (MAXIMUM SELECTIVE):**
- Alignment > 90% (perfecta en TODOS los timeframes)
- RSI < 20 o > 80 (extremos extremos)
- R:R >= 1:4
- Solo reversiones confirmadas por Daily

### Manejo de Volatilidad

**Alta Volatilidad (> 2.5%):**
- Aumenta selectividad automáticamente
- Requiere alignment > 80%
- Aumenta requerimientos R:R

**Volatilidad Moderada (1-2.5%):**
- Reglas normales
- Alignment > 70%

**Baja Volatilidad (< 1%):**
- Puede ser más permisivo
- Reglas estándar

---

## CONFIGURACIÓN

### Loop Continuo

**Archivo:** `src/bot.py`

```python
def _get_sleep_seconds(self) -> int:
    """
    NEW v3.6+: Return sleep interval for CONTINUOUS MONITORING

    El bot ya NO opera en un timeframe específico.
    Opera 24/7 buscando oportunidades cuando los timeframes alinean.

    Intervalo: 2 minutos (120 segundos)
    """
    return 120  # 2 minutos - monitoreo continuo
```

### Integración en Bot.py

**Inicialización:**
```python
# NEW v3.6+ - Multi-Timeframe Adapter
self.multitf_adapter = MultitimeframeAdapter(self.exchange, symbol=self.symbol)
self.multitf_audit = MultitimeframeAudit()
```

**Uso en run_cycle():**
```python
# Load multi-timeframe analysis
multitf_context = self.multitf_adapter.load_and_analyze(limit=100)

# Skip cycle if alignment too low
if multitf_context['alignment_score'] < 40:
    return  # Skip

# Pass to GatekeeperV2
enhanced_context = {
    'volatility': volatility_desc,
    'momentum': momentum_desc
}
enhanced_context.update(multitf_context)

gk_approved, gk_decision = self.gatekeeper_adapter.should_enter(
    signal=signal,
    additional_context=enhanced_context
)
```

---

## CASOS DE USO

### Caso 1: Tendencia Alcista Clara

**Situación:**
- Daily: BULLISH (EMA fast > EMA slow, RSI 60)
- 4H: BULLISH (RSI 55, trending)
- 1H: BULLISH (RSI 50)
- 15m: RSI 22 (oversold - señal de entrada)

**Resultado:**
- Alignment score: 95%
- Primary direction: BULLISH
- Opportunity score: 85/100
- GatekeeperV2: **APRUEBA** con confianza 0.85
- **Entra LONG inmediatamente**

### Caso 2: Señales Conflictivas

**Situación:**
- Daily: BEARISH (tendencia bajista)
- 4H: BULLISH (contratendencia)
- 1H: NEUTRAL
- 15m: RSI 25 (oversold)

**Resultado:**
- Alignment score: 35%
- Primary direction: NEUTRAL (conflicto)
- Opportunity score: 20/100
- Risk factors: ["DAILY_4H_DIVERGENCE"]
- **Ciclo SKIPPED** (alignment < 40%)

### Caso 3: Alta Volatilidad

**Situación:**
- Daily: BULLISH
- 4H: BULLISH
- 1H: BULLISH
- Volatility: 4.2% (EXTREME)
- Alignment: 70%

**Resultado:**
- Volatility context: HIGH
- GatekeeperV2 ve: volatilidad extrema + alignment no perfecto
- **RECHAZA** entrada (necesita alignment > 80% para volatilidad alta)

---

## MONITOREO Y LOGS

### Logs de MTF Analysis

**Ubicación:** `logs/trades/trade_journal.txt`

**Formato:**
```
[MTF_ANALYSIS] Direction: BULLISH | Alignment: 85% | Opportunity: 75/100 | Confidence: 0.80
[MTF_SKIP] Alignment 35% too low - skipping cycle
[MTF_ERROR] Connection timeout
```

### Logs de GatekeeperV2

**Ubicación:** `logs/gatekeeper_mainnet.log`

**Formato:**
```
[2025-12-01 15:30:45] APPROVED | Conf: 0.85 | Perfect alignment Daily=BULLISH, 4H=BULLISH, 1H=BULLISH, RSI 18 oversold
[2025-12-01 15:35:12] REJECTED | Conf: 0.25 | Volatility 3.5% exceeds alignment 60%, need better structure
```

### Comandos de Monitoreo

**Ver razonamiento en tiempo real:**
```bash
tail -f logs/gatekeeper_mainnet.log
```

**Ver análisis multi-timeframe:**
```bash
tail -f logs/trades/trade_journal.txt | grep MTF
```

**Monitoreo combinado:**
```bash
watch -n 1 'echo "=== GATEKEEPER ===" && tail -3 logs/gatekeeper_mainnet.log && echo "" && echo "=== MTF ANALYSIS ===" && tail -3 logs/trades/trade_journal.txt | grep MTF'
```

---

## AUDITORÍA Y TESTING

### Script de Auditoría Comprehensive

**Archivo:** `run_comprehensive_audit.py`

**Tests incluidos:**
1. Module imports (6 módulos)
2. Class initialization
3. Data integrity (OHLCV validation)
4. Correlation logic
5. Bot.py integration
6. Python syntax validation

**Ejecución:**
```bash
python3 run_comprehensive_audit.py
```

**Resultado esperado:**
```
🎉 ✅ ALL TESTS PASSED - System ready for deployment
Overall Result: 6/6 tests passed
```

### Testing Manual

**Test del Adapter:**
```python
from src.analysis.multitimeframe_adapter import MultitimeframeAdapter
import ccxt

exchange = ccxt.binance({'enableRateLimit': True})
adapter = MultitimeframeAdapter(exchange, symbol='BTC/USDT')

# Ver análisis completo
adapter.print_current_analysis()

# Quick signal
signal = adapter.get_quick_signal()  # LONG / SHORT / WAIT

# Should enter now?
should_enter = adapter.should_enter_now(gatekeeper_level=3)
```

---

## VENTAJAS DEL SISTEMA

### 1. No Pierde Oportunidades
- Monitoreo cada 2 minutos
- Detecta señales en cualquier timeframe
- No espera 4 horas para próximo ciclo

### 2. Contexto Completo
- GatekeeperV2 ve TODA la estructura del mercado
- Daily + 4H + 1H = pronóstico
- 15m + 5m + 1m = ejecución

### 3. Inteligencia AI Mejorada
- Claude tiene 6x más información
- Decisiones basadas en correlación real
- Rechaza conflictos automáticamente

### 4. Adaptable a Volatilidad
- Alta volatilidad → más selectivo
- Baja volatilidad → más permisivo
- Ajuste automático de thresholds

### 5. Risk Management Avanzado
- Detecta divergencias (Daily vs 4H)
- Identifica RSI extremos múltiples
- Calcula opportunity score automáticamente

---

## PRÓXIMOS PASOS RECOMENDADOS

### 1. Testing Inicial (1-3 días)
```bash
# Configurar en testnet primero
# Edit config/config.json: "mode": "testnet"
# Edit config/.env: BOT_MODE=testnet

python3 main.py
```

**Monitorear:**
- Alignment scores
- Decisiones de GatekeeperV2
- Señales generadas vs ejecutadas

### 2. Ajuste de Parámetros

**Si demasiadas señales rechazadas:**
- Bajar gatekeeper_level (2 o 1)
- Reducir alignment threshold (< 70%)

**Si demasiadas señales aceptadas:**
- Subir gatekeeper_level (4 o 5)
- Aumentar alignment threshold (> 80%)

### 3. Producción (Mainnet)

Una vez validado en testnet:
```bash
# Edit config/config.json: "mode": "mainnet"
# Edit config/.env: BOT_MODE=mainnet

python3 main.py
```

---

## TROUBLESHOOTING

### Error: "MultitimeframeAdapter failed to initialize"

**Causa:** Problemas con API de Binance
**Solución:**
```bash
# Verificar API keys en config/.env
# Verificar conectividad
python3 -c "import ccxt; ccxt.binance({'enableRateLimit': True}).fetch_ticker('BTC/USDT')"
```

### Error: "MTF_ERROR Connection timeout"

**Causa:** Rate limit o conectividad
**Solución:**
- El bot continúa normalmente (skip ese ciclo)
- Si persiste, verificar rate limits de Binance

### Alignment siempre bajo (< 40%)

**Causa:** Mercado lateral/indeciso
**Solución:**
- Normal en mercados laterales
- Bot espera condiciones mejores
- No forzar entradas

### GatekeeperV2 rechaza todo

**Causa:** Nivel muy alto o volatilidad extrema
**Solución:**
- Bajar gatekeeper_level
- Revisar volatility_context en logs
- Ajustar thresholds en gatekeeper_v2.py

---

## CONCLUSIÓN

TRAD Bot v3.6 representa un cambio fundamental en la operativa:

**De:**
- Operar en un timeframe fijo (esperar 4 horas)
- Perder oportunidades en volatilidad
- Decisiones basadas en un solo contexto

**A:**
- Monitoreo continuo 24/7 (cada 2 minutos)
- Aprovechar oportunidades cuando TODO alinea
- Decisiones basadas en 6 timeframes correlacionados

El sistema es **más inteligente**, **más rápido** y **más efectivo** que cualquier versión anterior.

---

**Versión:** 3.6.0
**Fecha:** 2025-12-01
**Estado:** ✅ Listo para Producción
**Desarrollado por:** Claude Code Assistant
