#!/usr/bin/env python3
"""
MULTITIMEFRAME AUDIT MODULE - Auditoría profunda de integridad
==============================================================
Verifica:
1. Integridad de datos OHLCV
2. Consistencia de valores
3. Lógica de correlación
4. Validación de cálculos
5. Detección de anomalías
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class MultitimeframeAudit:
    """
    Audita integridad y lógica del sistema multi-timeframe
    """

    def __init__(self):
        self.audit_history = []
        self.anomaly_threshold = 5.0  # % máximo de anomalías aceptadas

    def audit_ohlcv_data(self, ohlcv: np.ndarray, timeframe: str) -> Dict:
        """
        Audita integridad de datos OHLCV

        Verifica:
        - No hay valores negativos
        - No hay NaN/Inf
        - OHLC relationships son válidos (High >= Low, etc.)
        - No hay gaps extremos
        - Timestamps son consecutivos

        Returns:
            {
                'passed': bool,
                'issues': [str],
                'anomalies': int,
                'total_candles': int,
                'anomaly_rate': float
            }
        """
        issues = []
        anomalies = 0
        checks_passed = 0
        checks_total = 0

        if len(ohlcv) == 0:
            return {
                'passed': False,
                'issues': ['NO_DATA'],
                'anomalies': 0,
                'total_candles': 0,
                'anomaly_rate': 100.0
            }

        total_candles = len(ohlcv)

        # Check 1: Valores válidos (no NaN, no Inf, no negativos)
        checks_total += 1
        if not np.all(np.isfinite(ohlcv)):
            issues.append(f"{timeframe}: Contains NaN or Inf values")
            anomalies += np.sum(~np.isfinite(ohlcv))
        elif np.any(ohlcv < 0):
            issues.append(f"{timeframe}: Contains negative values")
            anomalies += np.sum(ohlcv < 0)
        else:
            checks_passed += 1

        # Check 2: Timestamps consecutivos
        checks_total += 1
        timestamps = ohlcv[:, 0]
        if len(timestamps) > 1:
            time_diffs = np.diff(timestamps)
            if not np.all(time_diffs > 0):
                issues.append(f"{timeframe}: Timestamps not monotonically increasing")
            else:
                checks_passed += 1
        else:
            checks_passed += 1

        # Check 3: OHLC relationships (High >= Open, High >= Close, High >= Low, etc.)
        checks_total += 1
        ohlc_violations = 0
        for i, candle in enumerate(ohlcv):
            try:
                o, h, l, c = float(candle[1]), float(candle[2]), float(candle[3]), float(candle[4])

                if not (h >= o and h >= c and h >= l):
                    ohlc_violations += 1
                if not (l <= o and l <= c and l <= h):
                    ohlc_violations += 1

            except (IndexError, ValueError):
                ohlc_violations += 1

        if ohlc_violations > 0:
            issues.append(f"{timeframe}: {ohlc_violations} OHLC relationship violations")
            anomalies += ohlc_violations
        else:
            checks_passed += 1

        # Check 4: Gaps extremos (cambios > 20% entre velas)
        checks_total += 1
        closes = ohlcv[:, 4]
        if len(closes) > 1:
            pct_changes = np.abs(np.diff(closes) / closes[:-1] * 100)
            extreme_gaps = np.sum(pct_changes > 20.0)
            if extreme_gaps > 0:
                issues.append(f"{timeframe}: {extreme_gaps} extreme price gaps (>20%)")
                anomalies += extreme_gaps
            else:
                checks_passed += 1
        else:
            checks_passed += 1

        # Calcular tasa de anomalías
        anomaly_rate = (anomalies / total_candles * 100) if total_candles > 0 else 0

        # Passed si anomaly_rate está debajo del threshold
        passed = anomaly_rate < self.anomaly_threshold

        result = {
            'passed': passed,
            'issues': issues,
            'anomalies': anomalies,
            'total_candles': total_candles,
            'anomaly_rate': round(anomaly_rate, 2),
            'checks_passed': checks_passed,
            'checks_total': checks_total,
            'timeframe': timeframe
        }

        self.audit_history.append(result)
        return result

    def audit_indicators(self, indicators: Dict, timeframe: str) -> Dict:
        """
        Audita indicadores calculados

        Verifica:
        - RSI está entre 0-100
        - Volatility es positiva
        - Support < Resistance
        - EMAs son positivas
        - Last close es coherente

        Returns:
            {
                'passed': bool,
                'issues': [str],
                'warnings': [str]
            }
        """
        issues = []
        warnings = []

        # RSI check
        rsi = indicators.get('rsi', 50)
        if not (0 <= rsi <= 100):
            issues.append(f"{timeframe}: RSI={rsi} out of bounds [0,100]")
        elif rsi < 5 or rsi > 95:
            warnings.append(f"{timeframe}: RSI={rsi} extreme value")

        # Volatility check
        vol = indicators.get('volatility', 0)
        if vol < 0:
            issues.append(f"{timeframe}: Negative volatility={vol}")
        elif vol > 10.0:
            warnings.append(f"{timeframe}: Very high volatility={vol}%")

        # Support/Resistance check
        support = indicators.get('support', 0)
        resistance = indicators.get('resistance', 0)
        if support >= resistance:
            issues.append(f"{timeframe}: Support={support} >= Resistance={resistance}")

        # EMAs check
        ema_fast = indicators.get('ema_fast', 0)
        ema_slow = indicators.get('ema_slow', 0)
        if ema_fast < 0 or ema_slow < 0:
            issues.append(f"{timeframe}: Negative EMA values")

        # Last close check
        last_close = indicators.get('last_close', 0)
        if last_close <= 0:
            issues.append(f"{timeframe}: Invalid last_close={last_close}")

        passed = len(issues) == 0

        return {
            'passed': passed,
            'issues': issues,
            'warnings': warnings,
            'timeframe': timeframe
        }

    def audit_correlation_logic(self, correlation: Dict) -> Dict:
        """
        Audita lógica de correlación

        Verifica:
        - Alignment score entre 0-100
        - Direction es válido
        - Confidence entre 0-1
        - Opportunity score entre 0-100
        - Risk factors es lista

        Returns:
            {
                'passed': bool,
                'issues': [str]
            }
        """
        issues = []

        # Alignment score
        alignment = correlation.get('alignment_score', 0)
        if not (0 <= alignment <= 100):
            issues.append(f"Alignment score={alignment} out of bounds [0,100]")

        # Direction
        direction = correlation.get('primary_direction', '')
        if direction not in ['BULLISH', 'BEARISH', 'NEUTRAL']:
            issues.append(f"Invalid direction={direction}")

        # Confidence
        confidence = correlation.get('confidence', 0)
        if not (0.0 <= confidence <= 1.0):
            issues.append(f"Confidence={confidence} out of bounds [0,1]")

        # Opportunity score
        opportunity = correlation.get('opportunity_score', 0)
        if not (0 <= opportunity <= 100):
            issues.append(f"Opportunity score={opportunity} out of bounds [0,100]")

        # Risk factors
        risks = correlation.get('risk_factors', [])
        if not isinstance(risks, list):
            issues.append(f"Risk factors is not a list: {type(risks)}")

        passed = len(issues) == 0

        return {
            'passed': passed,
            'issues': issues
        }

    def comprehensive_audit(self, multitf_context: Dict) -> Dict:
        """
        Auditoría comprehensive de todo el contexto multi-timeframe

        Returns:
            {
                'overall_passed': bool,
                'data_integrity': {...},
                'indicators_integrity': {...},
                'correlation_logic': {...},
                'summary': str
            }
        """
        results = {
            'overall_passed': True,
            'data_integrity': [],
            'indicators_integrity': [],
            'correlation_logic': {},
            'summary': ''
        }

        # Audit each timeframe's data and indicators
        multitf = multitf_context.get('multitimeframe', {})

        for tf, data in multitf.items():
            # Indicators audit
            ind_audit = self.audit_indicators(data, tf)
            results['indicators_integrity'].append(ind_audit)

            if not ind_audit['passed']:
                results['overall_passed'] = False

        # Audit correlation logic
        corr_audit = self.audit_correlation_logic(multitf_context)
        results['correlation_logic'] = corr_audit

        if not corr_audit['passed']:
            results['overall_passed'] = False

        # Generate summary
        total_issues = sum(len(x['issues']) for x in results['indicators_integrity'])
        total_issues += len(corr_audit['issues'])

        if results['overall_passed']:
            results['summary'] = f"✅ AUDIT PASSED - All checks OK"
        else:
            results['summary'] = f"❌ AUDIT FAILED - {total_issues} issues found"

        return results

    def print_audit_report(self, audit_result: Dict):
        """
        Imprime reporte de auditoría legible
        """
        print("\n" + "="*80)
        print("MULTI-TIMEFRAME AUDIT REPORT")
        print("="*80)

        print(f"\nStatus: {audit_result['summary']}")

        # Indicators integrity
        print("\n--- Indicators Integrity ---")
        for ind_audit in audit_result['indicators_integrity']:
            tf = ind_audit['timeframe']
            status = "✓" if ind_audit['passed'] else "✗"
            print(f"{status} {tf}: ", end="")

            if ind_audit['passed']:
                print("OK")
            else:
                print(f"{len(ind_audit['issues'])} issues")
                for issue in ind_audit['issues']:
                    print(f"    - {issue}")

            if len(ind_audit.get('warnings', [])) > 0:
                for warning in ind_audit['warnings']:
                    print(f"    ⚠ {warning}")

        # Correlation logic
        print("\n--- Correlation Logic ---")
        corr_audit = audit_result['correlation_logic']
        if corr_audit['passed']:
            print("✓ Correlation logic: OK")
        else:
            print(f"✗ Correlation logic: {len(corr_audit['issues'])} issues")
            for issue in corr_audit['issues']:
                print(f"    - {issue}")

        print("="*80 + "\n")

    def detect_anomalies(self, ohlcv: np.ndarray, timeframe: str) -> List[Tuple[int, str]]:
        """
        Detecta anomalías específicas en datos OHLCV

        Returns:
            List of (candle_index, anomaly_description)
        """
        anomalies = []

        if len(ohlcv) < 2:
            return anomalies

        for i in range(1, len(ohlcv)):
            prev_close = ohlcv[i-1, 4]
            curr_open = ohlcv[i, 1]
            curr_high = ohlcv[i, 2]
            curr_low = ohlcv[i, 3]
            curr_close = ohlcv[i, 4]

            # Anomaly 1: Gap extremo (>10%)
            gap = abs(curr_open - prev_close) / prev_close * 100
            if gap > 10.0:
                anomalies.append((i, f"Extreme gap: {gap:.2f}%"))

            # Anomaly 2: Vela anormal (rango >15% del precio)
            candle_range = (curr_high - curr_low) / curr_close * 100
            if candle_range > 15.0:
                anomalies.append((i, f"Extreme candle range: {candle_range:.2f}%"))

            # Anomaly 3: OHLC inconsistency
            if curr_high < curr_low:
                anomalies.append((i, "High < Low"))
            if curr_high < curr_open or curr_high < curr_close:
                anomalies.append((i, "High not highest"))
            if curr_low > curr_open or curr_low > curr_close:
                anomalies.append((i, "Low not lowest"))

        return anomalies
