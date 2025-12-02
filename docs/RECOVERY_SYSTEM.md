# TRAD Bot v3.3 - Failure Recovery System

## Overview

The TRAD Bot v3.3 includes a comprehensive **Failure Recovery System** that automatically handles bot crashes when trading positions are open. This system prevents loss of position data and provides graceful recovery mechanisms.

## Problem Statement

**Scenario:** The bot crashes or hangs while a position is open. What happens to the trade?

### Without Recovery System
- Position data is lost
- Trade remains open on the exchange
- Manual intervention required
- Risk of unexpected liquidation

### With Recovery System
- Position state is persisted to disk before every update
- Crash is automatically detected on restart
- Open positions are recovered and monitored
- Emergency closure triggers after 3 failures
- Full audit trail maintained

## Architecture

### 1. **StateRecovery Module** (`src/trading/recovery.py`)

#### Key Classes

##### `PositionState`
Represents a single open position with metadata:
```python
PositionState(
    order_id="12345",
    symbol="BTC/USDT",
    side="LONG",
    entry_price=45000.00,
    quantity=1.0,
    stop_loss=44100.00,
    take_profit_1=45450.00,
    take_profit_2=46000.00,
    tp1_closed=False,
    tp2_closed=False,
    trailing_stop_active=False
)
```

##### `StateRecovery`
Manages position persistence and recovery:

```python
recovery = StateRecovery(mode='testnet')

# Save position state
recovery.save_position(position)

# Load positions after crash
positions = recovery.get_open_positions()

# Detect if bot crashed with open positions
if recovery.detect_crash_with_open_positions():
    print("Bot crashed with open trades!")

# Reconcile with exchange API
reconciliation = recovery.reconcile_with_api(exchange)
# Returns: {'recovered': [...], 'lost': [...], 'extra': [...]}

# Clear state after recovery
recovery.clear_state()
```

##### `EmergencyClosureManager`
Handles repeated failures with emergency position closure:

```python
emergency = EmergencyClosureManager(
    exchange=exchange,
    symbol="BTC/USDT",
    recovery=recovery,
    max_failures=3
)

# Record each failure
emergency.record_failure()

# Check if positions should be closed
if emergency.should_close_positions():
    emergency.close_all_positions()
```

## Files Generated

### State Persistence Files

#### `.bot_state_testnet.json`
Contains persisted position data:
```json
{
  "positions": [
    {
      "order_id": "12345",
      "symbol": "BTC/USDT",
      "side": "LONG",
      "entry_price": 45000.00,
      "quantity": 1.0,
      "stop_loss": 44100.00,
      "take_profit_1": 45450.00,
      "take_profit_2": 46000.00,
      "entry_time": "2025-11-20T15:30:00",
      "tp1_closed": false,
      "tp2_closed": false,
      "trailing_stop_active": false
    }
  ],
  "last_update": "2025-11-20T15:30:15",
  "mode": "testnet"
}
```

#### `logs/recovery_testnet.log`
Recovery system audit trail:
```
[2025-11-20 15:30:15] Position saved: 12345 (LONG 1.0 @ $45000.00)
[2025-11-20 15:31:20] CRASH DETECTED! Open positions found after 65.0s inactivity
[2025-11-20 15:31:25] API Reconciliation: 1 recovered, 0 lost, 0 extra
[2025-11-20 15:31:30] Recovery completed and state cleared
```

## Recovery Flow

### Normal Operation
```
1. Bot starts
2. _handle_crash_recovery() checks for crashed positions
3. ✅ No crashed positions → Bot proceeds normally
```

### Bot Crash with Open Position

```
1. Bot running with LONG position
   ├─ Position saved to .bot_state_testnet.json
   └─ State updated every cycle

2. Bot crashes/hangs (PID dies)

3. Health check detects problem (cron every 5 min)
   ├─ Kills stale process
   ├─ Restarts bot via start_bot_safe.sh
   └─ Bot initializes

4. Bot startup → _handle_crash_recovery() executes
   ├─ Detects: 1 open position in .bot_state_testnet.json
   ├─ Calls: recovery.detect_crash_with_open_positions()
   └─ Result: CRASH DETECTED ⚠️

5. Recovery Phase
   ├─ Calls: recovery.reconcile_with_api(exchange)
   └─ Checks: Position exists in API?

6a. If RECOVERED ✅
   ├─ Position verified in API
   ├─ Logs: "RECOVERED POSITIONS: 1"
   ├─ Clears state file
   └─ Bot resumes normal trading

6b. If LOST ❌ (Position missing from API)
   ├─ Logs: "LOST POSITIONS: 1"
   ├─ Records failure
   ├─ Checks: emergency.should_close_positions()?
   │
   ├─ If < 3 failures:
   │  └─ Keeps position open for manual review
   │
   └─ If >= 3 failures (3 restart cycles):
      ├─ Triggers: emergency.close_all_positions()
      ├─ Sends: Market orders to close
      ├─ Logs: 🚨 "EMERGENCY CLOSURE TRIGGERED"
      └─ Requires: Manual intervention
```

## Configuration

### StateRecovery Options

```python
recovery = StateRecovery(mode='testnet')

# Configuration
recovery.max_recovery_attempts = 3      # Max retries
recovery.recovery_timeout_seconds = 300 # 5 min timeout
```

### EmergencyClosureManager Options

```python
emergency = EmergencyClosureManager(
    exchange=exchange,
    symbol="BTC/USDT",
    recovery=recovery,
    max_failures=3  # Trigger closure after 3 crashes
)

# Failures tracked within 1-hour window
emergency.failure_count  # Current failure count
emergency.failure_timestamps  # Timestamps of failures
```

## Integration with Bot

### In `src/bot.py`

#### 1. Initialization
```python
from src.trading.recovery import StateRecovery, EmergencyClosureManager

class TRADBot_v3:
    def __init__(self, config_path: str = "config/config.json"):
        # ...existing code...

        # Initialize recovery system
        self.recovery = StateRecovery(mode=self.mode)
        self.emergency_closure = EmergencyClosureManager(
            self.exchange, self.symbol, self.recovery
        )
```

#### 2. Crash Detection on Startup
```python
def run(self):
    # ... startup logging ...

    # NEW v3.3 - Crash Recovery
    print(f"\n🔄 CHECKING FOR CRASHED POSITIONS...")
    self._handle_crash_recovery()

    # ... main loop ...
```

#### 3. Recovery Handler
```python
def _handle_crash_recovery(self):
    """Handle recovery from bot crashes with open positions"""
    if self.recovery.detect_crash_with_open_positions():
        open_positions = self.recovery.get_open_positions()

        # Reconcile with API
        reconciliation = self.recovery.reconcile_with_api(self.exchange)

        if reconciliation['recovered']:
            # Positions found in API ✅
            self.recovery.clear_state()
        elif reconciliation['lost']:
            # Positions NOT found in API ❌
            self.emergency_closure.record_failure()
            if self.emergency_closure.should_close_positions():
                self.emergency_closure.close_all_positions()
```

## Health Check Integration

### In `scripts/bot/health_check.sh`

Enhanced 5-point health check:

```bash
1. ✅ Tmux session running?
2. ✅ Single Python process (python3 main.py)?
3. ✅ Log file recently updated (< 3 min)?
4. ✅ Bot executing cycles?
5. ✅ Recovery system not in emergency closure?
```

If emergency closure is detected:
```
🚨 EMERGENCY CLOSURE ACTIVE
   └─ Requires manual intervention
   └─ Check: logs/recovery_testnet.log
```

## Manual Recovery Procedures

### Scenario 1: Position Recovered
```
Bot Output:
✅ CRASH RECOVERY DETECTED: 1 open position(s) found
✅ RECOVERED POSITIONS: 1
   - LONG 1.0 @ $45000.00
✅ Recovery completed and state cleared

Action: None - Bot continues normal operation
```

### Scenario 2: Position Lost (< 3 failures)
```
Bot Output:
⚠️ CRASH RECOVERY DETECTED: 1 open position(s) found
❌ LOST POSITIONS: 1
   - 12345: LONG 1.0
⚠️ Keeping positions open for manual review
   Failure count: 1/3

Action:
1. Check exchange manually for position
2. If found: Document in recovery log
3. If missing: Verify trade was closed on exchange
```

### Scenario 3: Emergency Closure Triggered
```
Bot Output:
🚨 EMERGENCY CLOSURE TRIGGERED (3 failures)
   Closing all open positions at market
✅ All positions closed via emergency mechanism

Action:
1. Review logs/recovery_testnet.log
2. Check account for closed positions
3. Verify P&L impact
4. Investigate root cause
5. Restart bot if needed
```

## Logs and Debugging

### Key Log Files

1. **`logs/trades_testnet.log`** - Main trading activity
2. **`logs/recovery_testnet.log`** - Recovery system only
3. **`.bot_health.log`** - Health check results (every 5 min)
4. **`.bot_state_testnet.json`** - Current persisted state

### Monitoring Recovery

```bash
# Watch recovery in real-time
tail -f logs/recovery_testnet.log

# Check current state
cat .bot_state_testnet.json | jq '.'

# View health check history
tail -20 .bot_health.log

# Check emergency closure status
grep -i "emergency" logs/recovery_testnet.log
```

## Testing Recovery

### Test 1: Simulate Crash
```bash
# 1. Start bot and open a position
./scripts/bot/start_bot_safe.sh

# 2. Wait for position entry (monitor logs)

# 3. Kill bot process while position is open
pkill -9 -f "python3 main.py"

# 4. Restart bot
./scripts/bot/start_bot_safe.sh

# Expected output:
# ✅ CRASH RECOVERY DETECTED: 1 open position(s) found
# ✅ RECOVERED POSITIONS: 1
```

### Test 2: Force Emergency Closure
```bash
# 1. Simulate multiple crashes (3 times)
pkill -9 -f "python3 main.py"
sleep 2
./scripts/bot/start_bot_safe.sh
# Repeat 3 times total

# Expected output on 3rd restart:
# 🚨 EMERGENCY CLOSURE TRIGGERED (3 failures)
```

## Performance Impact

### Overhead
- **State Persistence**: ~2ms per cycle (JSON write)
- **Recovery Detection**: ~100ms on startup (1-time)
- **API Reconciliation**: ~500ms on crash (1-time)
- **Emergency Closure**: ~1-2s (if triggered)

### Storage
- State file: ~200 bytes per position
- Recovery log: ~100 bytes per event
- Daily recovery log growth: ~14 KB (typical)

## Limitations

1. **Exchange-Specific**: Recovery assumes CCXT exchange interface
2. **Partial Fills**: Assumes positions are fully filled before crash
3. **API Rate Limits**: Reconciliation respects CCXT rate limiting
4. **Manual Orders**: Doesn't detect exchange orders placed outside bot
5. **Network Outage**: Assumes exchange is accessible after restart

## Best Practices

1. **Monitor Recovery Logs**: Check `logs/recovery_testnet.log` daily
2. **Test Procedures**: Run recovery test monthly
3. **Backup State**: Archive `.bot_state_*.json` files weekly
4. **Review Emergencies**: Investigate every emergency closure
5. **Health Checks**: Ensure cron health checks run every 5 minutes

## Troubleshooting

### Issue: "Crash recovery triggered but no positions found"
**Cause**: State file existed but was stale
**Fix**: Check `.bot_state_testnet.json` timestamp and contents

### Issue: "LOST POSITIONS but they exist in API"
**Cause**: API reconciliation failed or position format mismatch
**Fix**: Check API response in recovery_testnet.log and verify position IDs

### Issue: "Emergency closure failed"
**Cause**: Exchange connection issue or insufficient balance
**Fix**: Check network connectivity and account balance, retry manually

## Summary

The Recovery System provides:
- ✅ **Automatic Detection** of crashed positions
- ✅ **State Persistence** to disk before every update
- ✅ **API Reconciliation** to verify positions exist
- ✅ **Graceful Recovery** when positions are recovered
- ✅ **Emergency Closure** after repeated failures
- ✅ **Full Audit Trail** of all recovery events

**Philosophy**: "Fail Safe with Full Transparency" - The bot always knows what positions it has, even after crashes, and handles recovery gracefully with full logging.
