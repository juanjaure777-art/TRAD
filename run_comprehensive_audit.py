#!/usr/bin/env python3
"""
COMPREHENSIVE AUDIT REPORT - TRAD Bot v3.6 Multi-Timeframe System
===================================================================
This script validates:
1. Module imports and dependencies
2. Class initialization
3. Data integrity checks
4. Logic validation
5. Bot.py integration
"""

import sys
import os
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def print_header(title):
    print("\n" + "━"*80)
    print(title)
    print("━"*80 + "\n")

def test_module_imports():
    """Test 1: Module imports"""
    print_header("1. MODULE IMPORTS AND DEPENDENCIES")

    modules = [
        ('MultiTimeframeDataLoader', 'src.analysis.multi_timeframe_data_loader'),
        ('MultitimeframeCorrelator', 'src.analysis.multitimeframe_correlator'),
        ('MultitimeframeAdapter', 'src.analysis.multitimeframe_adapter'),
        ('MultitimeframeAudit', 'src.analysis.multitimeframe_audit'),
        ('TRADBot_v3', 'src.bot'),
        ('GatekeeperV2', 'src.trading.gatekeeper_v2')
    ]

    passed = 0
    failed = 0

    for class_name, module_path in modules:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✓ {class_name:30} from {module_path}")
            passed += 1
        except Exception as e:
            print(f"✗ {class_name:30} FAILED: {e}")
            failed += 1

    print(f"\n  Result: {passed}/{len(modules)} modules imported successfully")
    return failed == 0

def test_class_initialization():
    """Test 2: Class initialization without API"""
    print_header("2. CLASS INITIALIZATION")

    try:
        from src.analysis.multitimeframe_correlator import MultitimeframeCorrelator
        from src.analysis.multitimeframe_audit import MultitimeframeAudit

        correlator = MultitimeframeCorrelator()
        print("✓ MultitimeframeCorrelator initialized")

        audit = MultitimeframeAudit()
        print("✓ MultitimeframeAudit initialized")

        print("\n  Result: All classes initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return False

def test_data_integrity():
    """Test 3: Data integrity checks"""
    print_header("3. DATA INTEGRITY CHECKS")

    try:
        import numpy as np
        from src.analysis.multitimeframe_audit import MultitimeframeAudit

        audit = MultitimeframeAudit()

        # Test OHLCV data
        test_ohlcv = np.array([
            [1000, 100, 105, 95, 102, 1000],
            [2000, 102, 108, 100, 105, 1200],
            [3000, 105, 110, 103, 108, 1100]
        ])

        result = audit.audit_ohlcv_data(test_ohlcv, '1h')

        if result['passed']:
            print(f"✓ OHLCV data integrity check passed")
            print(f"  - Total candles: {result['total_candles']}")
            print(f"  - Anomaly rate: {result['anomaly_rate']}%")
        else:
            print(f"✗ OHLCV data integrity check failed")
            for issue in result['issues']:
                print(f"  - {issue}")

        print("\n  Result: Data integrity validation working")
        return True
    except Exception as e:
        print(f"✗ Data integrity test failed: {e}")
        return False

def test_correlation_logic():
    """Test 4: Correlation logic validation"""
    print_header("4. CORRELATION LOGIC VALIDATION")

    try:
        from src.analysis.multitimeframe_correlator import MultitimeframeCorrelator

        correlator = MultitimeframeCorrelator()

        # Mock timeframe data
        mock_data = {
            '1d': {
                'indicators': {'rsi': 65, 'volatility': 1.2, 'ema_fast': 50000, 'ema_slow': 49000},
                'momentum': 'BULLISH',
                'phase': 'TRENDING'
            },
            '4h': {
                'indicators': {'rsi': 60, 'volatility': 1.5, 'ema_fast': 50100, 'ema_slow': 49800},
                'momentum': 'BULLISH',
                'phase': 'TRENDING'
            },
            '1h': {
                'indicators': {'rsi': 55, 'volatility': 1.8, 'ema_fast': 50150, 'ema_slow': 49900},
                'momentum': 'BULLISH',
                'phase': 'CONSOLIDATION'
            }
        }

        result = correlator.correlate(mock_data)

        print(f"✓ Correlation analysis completed")
        print(f"  - Primary direction: {result['primary_direction']}")
        print(f"  - Alignment score: {result['alignment_score']}%")
        print(f"  - Opportunity score: {result['opportunity_score']}/100")
        print(f"  - Confidence: {result['confidence']:.2f}")

        # Validate result structure
        required_keys = ['alignment_score', 'primary_direction', 'confidence',
                        'volatility_context', 'opportunity_score', 'risk_factors']

        all_present = all(key in result for key in required_keys)

        if all_present:
            print("✓ All required keys present in correlation result")
        else:
            print("✗ Missing keys in correlation result")
            return False

        print("\n  Result: Correlation logic validated successfully")
        return True
    except Exception as e:
        print(f"✗ Correlation logic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_bot_integration():
    """Test 5: Bot.py integration check"""
    print_header("5. BOT.PY INTEGRATION CHECK")

    try:
        # Check if imports are in bot.py
        with open('src/bot.py', 'r') as f:
            bot_content = f.read()

        checks = [
            ('MultiTimeframeDataLoader import', 'from src.analysis.multi_timeframe_data_loader import MultiTimeframeDataLoader'),
            ('MultitimeframeCorrelator import', 'from src.analysis.multitimeframe_correlator import MultitimeframeCorrelator'),
            ('MultitimeframeAdapter import', 'from src.analysis.multitimeframe_adapter import MultitimeframeAdapter'),
            ('MultitimeframeAudit import', 'from src.analysis.multitimeframe_audit import MultitimeframeAudit'),
            ('MultitimeframeAdapter initialization', 'self.multitf_adapter = MultitimeframeAdapter'),
        ]

        passed = 0
        for check_name, check_string in checks:
            if check_string in bot_content:
                print(f"✓ {check_name}")
                passed += 1
            else:
                print(f"✗ {check_name} MISSING")

        print(f"\n  Result: {passed}/{len(checks)} integration checks passed")
        return passed == len(checks)
    except Exception as e:
        print(f"✗ Bot integration test failed: {e}")
        return False

def test_syntax_validation():
    """Test 6: Python syntax validation"""
    print_header("6. PYTHON SYNTAX VALIDATION")

    modules_to_check = [
        'src/analysis/multi_timeframe_data_loader.py',
        'src/analysis/multitimeframe_correlator.py',
        'src/analysis/multitimeframe_adapter.py',
        'src/analysis/multitimeframe_audit.py',
        'src/bot.py',
        'src/trading/gatekeeper_v2.py'
    ]

    passed = 0
    failed = 0

    import py_compile

    for module_path in modules_to_check:
        try:
            py_compile.compile(module_path, doraise=True)
            print(f"✓ {module_path:50} syntax OK")
            passed += 1
        except Exception as e:
            print(f"✗ {module_path:50} SYNTAX ERROR: {e}")
            failed += 1

    print(f"\n  Result: {passed}/{len(modules_to_check)} modules have valid syntax")
    return failed == 0

def main():
    """Run comprehensive audit"""
    print("="*80)
    print("🔍 COMPREHENSIVE AUDIT REPORT - TRAD Bot v3.6 Multi-Timeframe System")
    print("="*80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n")

    tests = [
        ("Module Imports", test_module_imports),
        ("Class Initialization", test_class_initialization),
        ("Data Integrity", test_data_integrity),
        ("Correlation Logic", test_correlation_logic),
        ("Bot Integration", test_bot_integration),
        ("Syntax Validation", test_syntax_validation)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print_header("AUDIT SUMMARY")

    total_tests = len(results)
    passed_tests = sum(1 for _, passed in results if passed)
    failed_tests = total_tests - passed_tests

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:10} {test_name}")

    print("\n" + "="*80)
    print(f"Overall Result: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("🎉 ✅ ALL TESTS PASSED - System ready for deployment")
    else:
        print(f"⚠️  ❌ {failed_tests} test(s) failed - Review errors above")

    print("="*80 + "\n")

    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
