#!/usr/bin/env python3
"""
TRAD Bot v3.3 - GatekeeperV2: Intelligent Entry Decision Engine
Replaces hardcoded MODE rules with Claude-based decision making.

Optimization focus:
- Prompt caching for repeated analysis
- Token-efficient JSON responses
- Batch processing support
- Centralized decision logic
"""

import json
import os
from datetime import datetime
from typing import Optional, Dict, List, Any
import anthropic
from functools import lru_cache

# System prompt is cached to reduce token usage
# NEW v3.6+ - Multi-Timeframe Aware System Prompt
SYSTEM_PROMPT = """You are TRAD Bot's intelligent trading gatekeeper with MULTI-TIMEFRAME AWARENESS.
Your job is to decide whether to enter a trade using HIERARCHICAL TIMEFRAME ANALYSIS.

═══════════════════════════════════════════════════════════════════════════════

HIERARCHICAL TIMEFRAME STRUCTURE (DAILY → 4H → 1H → MICRO):

DAILY (1d):
- Defines the PRIMARY TREND direction for the entire day
- BULLISH: EMA fast > EMA slow, suggests long bias
- BEARISH: EMA fast < EMA slow, suggests short bias
- REVERSAL: RSI extreme (>70 or <30), potential mean reversion

4-HOUR (4h):
- Defines CANDLE STRUCTURE for next 16 hours
- Alignment with Daily = STRONG (high confidence)
- Divergence with Daily = CAUTION (needs confirmation)

1-HOUR (1h):
- Fine-tuning of 4H structure
- Entry confirmation level
- Last filter before execution

15M/5M/1M (Micro):
- Entry EXECUTION precision
- Avoid micro-timeframe noise alone
- Use only when aligned with higher timeframes

═══════════════════════════════════════════════════════════════════════════════

MULTI-TIMEFRAME DECISION LOGIC:

✓ OPTIMAL CONDITIONS (Enter with confidence):
1. Daily trend = 4H trend = 1H trend (Perfect alignment)
2. RSI extreme on lower timeframes (oversold <25 or overbought >75 if trending)
3. Price touching support/resistance with alignment
4. Good R:R (depends on GATEKEEPER_LEVEL)

⚠️ CAUTION CONDITIONS (Enter carefully or skip):
1. Daily and 4H disagree on direction
2. 1H diverging from 4H (wait for re-alignment)
3. Volatility > 3% AND alignment score < 70%
4. Multiple timeframes in extreme RSI (reversal risk)

❌ REJECT CONDITIONS (Do NOT enter):
1. Alignment score < 40% (timeframes misaligned)
2. Volatility extreme (>4%) without perfect alignment
3. Daily in one direction, 4H in opposite (conflicting signals)
4. Recent consecutive losses + weak setup

═══════════════════════════════════════════════════════════════════════════════

INPUTS you receive:

Primary inputs:
- Current RSI(7), Price, EMA values
- Market phase per timeframe
- GATEKEEPER_LEVEL (1=permissive, 5=restrictive)

ADDITIONAL CONTEXT (when available):
- multitimeframe: {daily, 4h, 1h, 15m, 5m, 1m} with RSI, phase, momentum
- alignment_score: 0-100 (% of timeframes aligned)
- volatility_context: description of current volatility environment
- structure_context: daily/4h/1h phase alignment
- risk_factors: list of identified risks
- opportunity_score: 0-100 (quality of setup)
- primary_direction: BULLISH|BEARISH|NEUTRAL

═══════════════════════════════════════════════════════════════════════════════

DECISION RULES by GATEKEEPER_LEVEL (Using Multi-Timeframe Context):

LEVEL 1 (PERMISSIVE - Enter easily, trust strong alignment):
- If alignment > 70%: Enter on RSI < 35 or > 65 in any phase
- If alignment > 50%: Enter on RSI < 30 or > 70 in trending phases
- Accept R:R >= 1:1 in strong aligned setups
- Entry confidence: Based on alignment score

LEVEL 2 (MODERATE):
- ✅ If alignment > 70%: Trust MTF direction, enter on RSI 30-35 (oversold) or 65-70 (overbought)
- ✅ If alignment 60-70%: Require 4H confirmation of Daily trend
- ✅ Ignore single-timeframe "Phase" if MTF alignment > 70% (MTF takes priority)
- R:R >= 1:1.5, favor aligned timeframes
- Avoid if volatility > 2.5% and alignment < 70%

LEVEL 3 (BALANCED - DEFAULT):
- Perfect alignment recommended: Daily = 4H = 1H
- RSI < 30 or > 70 with alignment > 75%
- R:R >= 1:2, strong confirmation required
- Volatility check: If > 2%, need alignment > 80%

LEVEL 4 (SELECTIVE):
- Require strict alignment: Daily = 4H = 1H = 15m signals
- RSI < 25 or > 75 (extreme oversold/bought)
- R:R >= 1:3 minimum
- Reject if volatility > 2% or alignment < 85%
- Only trending/reversal phases, no consolidation

LEVEL 5 (MAXIMUM SELECTIVE):
- Perfect alignment on ALL visible timeframes
- RSI < 20 or > 80 (extreme extremes)
- R:R >= 1:4 required
- Only proven reversal setups with Daily reversal confirmation
- Reject any volatility > 1.5% or if alignment < 90%

═══════════════════════════════════════════════════════════════════════════════

VOLATILITY CONTEXT HANDLING:

In HIGH VOLATILITY (>2.5%):
- Raise gatekeeper level effectively (be MORE selective)
- Require tighter alignment (>80%)
- Increase R:R requirements
- Consider tighter stops (risk reduction)

In MODERATE VOLATILITY (1-2.5%):
- Use normal rules
- Standard alignment required (>70%)
- Normal R:R

In LOW VOLATILITY (<1%):
- Can be more permissive on alignment
- Standard rules apply
- Can consider more entries

═══════════════════════════════════════════════════════════════════════════════

🔴 CRITICAL PRIORITIZATION RULE (v3.6+):

When MULTI-TIMEFRAME ANALYSIS is present (alignment_score exists):
1. **TRUST MTF Direction over single-timeframe Phase**
   - If alignment > 70% and MTF says BEARISH → trust BEARISH (ignore Phase: NEUTRAL)
   - If alignment > 70% and MTF says BULLISH → trust BULLISH (ignore Phase: NEUTRAL)

2. **RSI should be treated as a RANGE, not exact threshold:**
   - Oversold RANGE: 30-35 (anywhere in this range is valid for oversold entry)
   - Overbought RANGE: 65-70 (anywhere in this range is valid for overbought entry)
   - Don't reject RSI 34 because it's "not < 35" - it's IN THE RANGE!

3. **Alignment score is the PRIMARY confidence metric**
   - alignment > 80% = HIGH confidence (enter easily)
   - alignment 70-80% = GOOD confidence (enter with RSI in range)
   - alignment 60-70% = MODERATE confidence (need confirmation)
   - alignment < 60% = LOW confidence (skip)

═══════════════════════════════════════════════════════════════════════════════

ALWAYS CONSIDER:
1. Timeframe hierarchy: Higher timeframes = more weight
2. Alignment score: How much are timeframes in agreement?
3. Volatility context: Adjust risk based on market noise
4. Risk factors: Any specific warnings?
5. Opportunity score: Is this a good setup overall?
6. Open positions: Avoid over-trading

═══════════════════════════════════════════════════════════════════════════════

DECISION OUTPUT (always JSON, no markdown):
{
  "should_enter": true/false,
  "confidence": 0.0-1.0,
  "reason": "EXPLAIN using timeframe alignment. Reference Daily/4H/1H if available"
}

Examples:
- "Confidence 0.90: Alignment 85%, MTF Direction BEARISH, RSI 34 in oversold range (30-35), excellent setup"
- "Confidence 0.75: Alignment 78%, MTF Direction BULLISH, RSI 32 oversold, Phase NEUTRAL ignored due to strong MTF"
- "Confidence 0.25: Alignment 55% too low, conflicting timeframes, skip"
- "Confidence 0.0: Volatility 3.5% extreme with alignment only 60%, too risky"

Respond ONLY with valid JSON. No explanations, no markdown."""


class GatekeeperV2:
    """Claude-based trading decision engine with token optimization"""

    def __init__(self, level: int = 3, mode: str = "testnet"):
        """
        Initialize GatekeeperV2

        Args:
            level: 1-5 (1=permissive, 5=restrictive)
            mode: 'testnet' or 'live'
        """
        self.level = max(1, min(5, level))  # Clamp 1-5
        self.mode = mode

        self.client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )

        self.log_file = f"logs/gatekeeper_{mode}.log"
        self.stats_file = f".gatekeeper_stats_{mode}.json"
        self.decision_cache = {}  # Simple cache for repeated scenarios

        self._ensure_logs_dir()
        self._load_stats()

    def _ensure_logs_dir(self):
        """Ensure logs directory exists"""
        os.makedirs("logs", exist_ok=True)

    def _load_stats(self):
        """Load decision statistics"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    self.stats = json.load(f)
            else:
                self.stats = {
                    'total_decisions': 0,
                    'approved_entries': 0,
                    'rejected_entries': 0,
                    'average_confidence': 0.0,
                    'level_history': []
                }
        except (json.JSONDecodeError, FileNotFoundError):
            # Stats file invalid or missing, use defaults
            self.stats = {'total_decisions': 0}

    def _save_stats(self):
        """Save decision statistics"""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except (IOError, OSError):
            # Failed to write stats file, skip silently
            pass

    def should_enter(self,
                    rsi: float,
                    price: float,
                    ema_fast: float,
                    ema_slow: float,
                    market_phase: str,
                    open_positions: int = 0,
                    reward_risk_ratio: float = 1.0,
                    additional_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get Claude's decision on whether to enter a trade.

        Args:
            rsi: RSI(7) value
            price: Current price
            ema_fast: Fast EMA value
            ema_slow: Slow EMA value
            market_phase: IMPULSE, CORRECTIVE, REVERSAL, NEUTRAL
            open_positions: Current open position count
            reward_risk_ratio: Risk:Reward ratio (e.g., 1.0, 2.5)
            additional_context: Dict with any additional analysis

        Returns:
            {
                'should_enter': bool,
                'confidence': float (0-1),
                'reason': str,
                'level': int,
                'timestamp': str
            }
        """

        # Build compact analysis message
        analysis = self._build_analysis_message(
            rsi, price, ema_fast, ema_slow, market_phase,
            open_positions, reward_risk_ratio, additional_context
        )

        # Check simple cache first (for same exact conditions)
        cache_key = hash(analysis)
        if cache_key in self.decision_cache:
            cached = self.decision_cache[cache_key]
            if (datetime.now() - cached['timestamp']).total_seconds() < 30:
                return cached['decision']

        try:
            # Call Claude with system prompt caching
            response = self.client.messages.create(
                model="claude-opus-4-1-20250805",
                max_tokens=150,  # Only need JSON response
                system=[
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"}  # Cache system prompt
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": analysis
                    }
                ]
            )

            # Parse Claude's JSON response
            response_text = response.content[0].text.strip()

            # Handle markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            decision_data = json.loads(response_text)

            # Enhance decision with metadata
            decision = {
                'should_enter': decision_data.get('should_enter', False),
                'confidence': decision_data.get('confidence', 0.0),
                'reason': decision_data.get('reason', 'Unknown'),
                'level': self.level,
                'timestamp': datetime.now().isoformat(),
                'tokens_used': {
                    'input': response.usage.input_tokens,
                    'output': response.usage.output_tokens,
                    'cache_creation': response.usage.cache_creation_input_tokens,
                    'cache_read': response.usage.cache_read_input_tokens
                }
            }

            # Update stats
            self.stats['total_decisions'] += 1
            if decision['should_enter']:
                self.stats['approved_entries'] += 1
            else:
                self.stats['rejected_entries'] += 1

            # Track confidence
            if 'average_confidence' not in self.stats:
                self.stats['average_confidence'] = 0.0

            n = self.stats['total_decisions']
            old_avg = self.stats.get('average_confidence', 0.0)
            self.stats['average_confidence'] = (
                (old_avg * (n - 1) + decision['confidence']) / n
            )

            # Log decision
            self._log_decision(decision, analysis)

            # Cache for 30 seconds
            self.decision_cache[cache_key] = {
                'decision': decision,
                'timestamp': datetime.now()
            }

            return decision

        except json.JSONDecodeError as e:
            self._log_error(f"Failed to parse Claude response: {response_text}")
            return {
                'should_enter': False,
                'confidence': 0.0,
                'reason': 'Decision error',
                'level': self.level,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            import traceback
            self._log_error(f"Gatekeeper error: {e}")
            self._log_error(f"Traceback: {traceback.format_exc()}")
            return {
                'should_enter': False,
                'confidence': 0.0,
                'reason': f'API error: {str(e)}',
                'level': self.level,
                'timestamp': datetime.now().isoformat()
            }
        finally:
            self._save_stats()

    def _build_analysis_message(self, rsi: float, price: float, ema_fast: float,
                               ema_slow: float, market_phase: str, open_positions: int,
                               reward_risk_ratio: float, additional_context: Dict) -> str:
        """Build compact analysis message (token-optimized)"""

        msg = f"""ANALYSIS:
Level: {self.level}
RSI: {rsi:.1f}
Price: ${price:.2f}
EMA: {ema_fast:.0f} vs {ema_slow:.0f}
Phase: {market_phase}
Open: {open_positions}
R:R: 1:{reward_risk_ratio:.1f}"""

        if additional_context:
            # NEW v3.6+: Prioritize multi-timeframe context
            if 'alignment_score' in additional_context:
                msg += f"\n\n🎯 MULTI-TIMEFRAME ANALYSIS:"
                msg += f"\nAlignment: {additional_context['alignment_score']}%"
                msg += f"\nDirection: {additional_context.get('primary_direction', 'N/A')}"
                msg += f"\nOpportunity: {additional_context.get('opportunity_score', 0)}/100"
                msg += f"\nConfidence: {additional_context.get('confidence', 0):.2f}"

                if 'risk_factors' in additional_context and additional_context['risk_factors']:
                    msg += f"\nRisk Factors: {', '.join(additional_context['risk_factors'])}"

                if 'volatility_context' in additional_context:
                    msg += f"\nVolatility Context: {additional_context['volatility_context']}"

            # Legacy context (lower priority)
            if 'volatility' in additional_context:
                msg += f"\nVolatility: {additional_context['volatility']}"
            if 'momentum' in additional_context:
                msg += f"\nMomentum: {additional_context['momentum']}"
            if 'support_resistance' in additional_context:
                msg += f"\nS/R: {additional_context['support_resistance']}"

        return msg

    def _log_decision(self, decision: Dict, analysis: str):
        """Log decision to file"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            entry = "APPROVED" if decision['should_enter'] else "REJECTED"
            confidence = decision['confidence']
            reason = decision['reason']

            log_line = f"[{timestamp}] {entry} | Conf: {confidence:.2f} | {reason}\n"

            with open(self.log_file, 'a') as f:
                f.write(log_line)
        except (IOError, OSError):
            # Failed to write log, skip silently
            pass

    def _log_error(self, error: str):
        """Log error to file"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(self.log_file, 'a') as f:
                f.write(f"[{timestamp}] ERROR: {error}\n")
        except (IOError, OSError):
            # Failed to write error log, skip silently
            pass

    def set_level(self, level: int):
        """Dynamically change gatekeeper level (1-5)"""
        self.level = max(1, min(5, level))
        self._log_decision(
            {'should_enter': False, 'confidence': 0.0, 'reason': f'Level changed to {self.level}'},
            'LEVEL_CHANGE'
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get decision statistics"""
        self._load_stats()
        return {
            'level': self.level,
            'total_decisions': self.stats.get('total_decisions', 0),
            'approved': self.stats.get('approved_entries', 0),
            'rejected': self.stats.get('rejected_entries', 0),
            'approval_rate': (
                self.stats.get('approved_entries', 0) /
                max(1, self.stats.get('total_decisions', 1))
            ),
            'average_confidence': self.stats.get('average_confidence', 0.0),
            'cache_file': self.stats_file
        }

    def clear_stats(self):
        """Reset statistics"""
        self.stats = {
            'total_decisions': 0,
            'approved_entries': 0,
            'rejected_entries': 0,
            'average_confidence': 0.0
        }
        self._save_stats()
