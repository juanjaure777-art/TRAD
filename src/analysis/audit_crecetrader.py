#!/usr/bin/env python3
"""
Crecetrader Implementation Audit
Verifica que toda la lógica esté correctamente implementada
"""

import numpy as np
from typing import Dict, List, Tuple
from src.analysis.structure_change_detector import StructureChangeDetector
from src.strategy.tzv_validator import TZVValidator
from src.analysis.scenario_manager import ScenarioManager
from src.analysis.bitcoin_context import BitcoinContext


class CrecetraderAudit:
    """Audita la implementación de Crecetrader"""

    def __init__(self):
        self.audit_results = []
        self.errors = []
        self.warnings = []

    def audit_all(self) -> Dict:
        """Ejecuta auditoría completa"""
        results = {
            'structure_detector': self.audit_structure_detector(),
            'tzv_validator': self.audit_tzv_validator(),
            'scenario_manager': self.audit_scenario_manager(),
            'bitcoin_context': self.audit_bitcoin_context(),
            'integration': self.audit_integration(),
            'summary': {
                'errors': len(self.errors),
                'warnings': len(self.warnings),
                'status': 'PASS' if len(self.errors) == 0 else 'FAIL'
            }
        }
        return results

    def audit_structure_detector(self) -> Dict:
        """Audita StructureChangeDetector"""
        print("🔍 Auditando StructureChangeDetector...")

        try:
            detector = StructureChangeDetector()

            # Test 1: Bullish structure (crecientes + crecientes)
            bullish_highs = np.array([90.0, 90.5, 91.0, 91.5, 92.0])
            bullish_lows = np.array([89.0, 89.5, 90.0, 90.5, 91.0])

            result = detector.analyze_maximos_minimos(bullish_highs, bullish_lows)
            assert result['maximos_trend'] == 'crecientes', "Maximos debe ser crecientes"
            assert result['minimos_trend'] == 'crecientes', "Minimos debe ser crecientes"

            # Test 2: Bearish structure (decrecientes + decrecientes)
            bearish_highs = np.array([92.0, 91.5, 91.0, 90.5, 90.0])
            bearish_lows = np.array([91.0, 90.5, 90.0, 89.5, 89.0])

            result = detector.analyze_maximos_minimos(bearish_highs, bearish_lows)
            assert result['maximos_trend'] == 'decrecientes', "Maximos debe ser decrecientes"
            assert result['minimos_trend'] == 'decrecientes', "Minimos debe ser decrecientes"

            # Test 3: Detect phase
            phase_info = detector.detect_structure_phase(bullish_highs, bullish_lows)
            assert 'bullish' in phase_info['phase'].value, "Fase debe ser bullish"

            print("   ✅ StructureChangeDetector: PASS")
            return {
                'status': 'PASS',
                'tests_passed': 3,
                'details': 'Detecta correctamente máximos, mínimos, y fases'
            }

        except AssertionError as e:
            self.errors.append(f"StructureDetector: {e}")
            print(f"   ❌ {e}")
            return {'status': 'FAIL', 'error': str(e)}

    def audit_tzv_validator(self) -> Dict:
        """Audita TZVValidator"""
        print("🔍 Auditando TZVValidator...")

        try:
            validator = TZVValidator()

            # Crear datos de test
            bullish_highs = np.array([90.0, 90.5, 91.0, 91.5, 92.0])
            bullish_lows = np.array([89.0, 89.5, 90.0, 90.5, 91.0])
            closes = np.array([90.2, 90.7, 91.1, 91.6, 92.0])

            # Test T validation
            t_result = validator.validate_t_tendencia(bullish_highs, bullish_lows, closes)
            # Print for debugging
            print(f"   T result: is_uptrend={t_result['is_uptrend']}, structure={t_result.get('structure_phase')}, confidence={t_result.get('structure_confidence')}")
            assert t_result['is_uptrend'], "Debe detectar uptrend"
            assert t_result['validation_passed'], f"T validation debe pasar - details: {t_result}"
            assert 'bullish' in t_result['structure_phase'], f"Fase debe ser bullish, got {t_result['structure_phase']}"

            # Test con datos bearish
            bearish_highs = np.array([92.0, 91.5, 91.0, 90.5, 90.0])
            bearish_lows = np.array([91.0, 90.5, 90.0, 89.5, 89.0])
            bearish_closes = np.array([91.8, 91.3, 90.8, 90.3, 89.8])

            t_result = validator.validate_t_tendencia(bearish_highs, bearish_lows, bearish_closes)
            assert t_result['is_downtrend'], "Debe detectar downtrend"

            # Test Z validation
            supports = {
                'supports': [
                    {'price': 89.0, 'type': 'historical_low'},
                    {'price': 88.5, 'type': 'fibonacci_correction'}
                ]
            }
            resistances = {
                'resistances': [
                    {'price': 92.5, 'type': 'historical_high'},
                    {'price': 93.0, 'type': 'fibonacci_extension'}
                ]
            }

            z_result = validator.validate_z_zonas(supports, resistances, 91.0)
            assert z_result['first_support'] is not None, "Debe encontrar soporte"
            assert z_result['first_resistance'] is not None, "Debe encontrar resistencia"

            # Test V validation
            # entry=91.0, resistance=94.0, support=89.0 → ratio = 3.0/2.0 = 1.5:1 (actual 1.5, but we need >= 2)
            # entry=91.0, resistance=95.0, support=89.0 → ratio = 4.0/2.0 = 2.0:1 ✓
            v_result = validator.validate_v_vacio(91.0, 95.0, 89.0, min_ratio=2.0)
            assert v_result['ratio'] >= 2.0, f"Ratio debe ser >= 2.0, got {v_result['ratio']}"
            assert v_result['validation_passed'], f"V debe pasar con ratio >= 2:1 - details: {v_result}"

            print("   ✅ TZVValidator: PASS")
            return {
                'status': 'PASS',
                'tests_passed': 5,
                'details': 'T, Z, V validation funcionan correctamente'
            }

        except AssertionError as e:
            self.errors.append(f"TZVValidator: {e}")
            print(f"   ❌ {e}")
            return {'status': 'FAIL', 'error': str(e)}

    def audit_scenario_manager(self) -> Dict:
        """Audita ScenarioManager"""
        print("🔍 Auditando ScenarioManager...")

        try:
            mgr = ScenarioManager()

            # Test Scenario A
            result_a = mgr.analyze_scenario(
                current_price=91.0,
                maximos_trend='crecientes',
                minimos_trend='crecientes',
                distribution_level='minuscula',
                volatility_level='normal'
            )
            assert result_a['scenario'].value == 'A_liquidity_entering', "Debe detectar Escenario A"
            assert result_a['confidence'] > 0.8, "Confianza debe ser alta"

            # Test Scenario B
            result_b = mgr.analyze_scenario(
                current_price=89.0,
                maximos_trend='decrecientes',
                minimos_trend='decrecientes',
                distribution_level='mayuscula',
                volatility_level='normal'
            )
            assert result_b['scenario'].value == 'B_liquidity_retreating', "Debe detectar Escenario B"

            # Test Scenario C
            result_c = mgr.analyze_scenario(
                current_price=90.9,
                maximos_trend='flat',
                minimos_trend='flat',
                distribution_level='neutral',
                volatility_level='normal'
            )
            assert result_c['scenario'].value == 'C_neutral_zone', "Debe detectar Escenario C"

            # Test position management
            pos_mgmt = mgr.get_position_management(result_a['scenario'], 91.0)
            assert 'strategy' in pos_mgmt, "Debe tener strategy"
            assert 'take_profit_1' in pos_mgmt or 'buy_zone' in pos_mgmt, "Debe tener TP o buy_zone"

            print("   ✅ ScenarioManager: PASS")
            return {
                'status': 'PASS',
                'tests_passed': 4,
                'details': 'Detecta correctamente los 3 escenarios'
            }

        except AssertionError as e:
            self.errors.append(f"ScenarioManager: {e}")
            print(f"   ❌ {e}")
            return {'status': 'FAIL', 'error': str(e)}

    def audit_bitcoin_context(self) -> Dict:
        """Audita BitcoinContext"""
        print("🔍 Auditando BitcoinContext...")

        try:
            ctx = BitcoinContext()

            # Test Bitcoin levels
            levels = ctx._get_bitcoin_levels()
            assert levels['pivot'] == 90.823, "Pivot debe ser 90.823"
            assert levels['take_profit']['tp_2'] == 93.347, "TP2 debe ser 93.347"

            # Test Fear-Greed (puede fallar por red, pero lógica debe existir)
            fg = ctx.fetch_fear_greed_index()
            assert 'value' in fg, "Debe tener valor"
            assert 'level' in fg, "Debe tener nivel"

            # Test position multiplier
            multiplier = ctx.get_position_size_multiplier(fear_greed_value=15)  # Extreme fear
            assert multiplier == 0.6, "Extreme fear debe reducir posición"

            multiplier = ctx.get_position_size_multiplier(fear_greed_value=50)  # Neutral
            assert multiplier == 1.0, "Neutral debe tener multiplier 1.0"

            # Test session quality
            session_ny = ctx.is_good_entry_timing(14)  # 14:00 UTC = NY+EU overlap
            assert session_ny['liquidity'] == 'HIGH', "NY+EU overlap debe tener HIGH liquidity"

            session_asia = ctx.is_good_entry_timing(3)
            assert session_asia['liquidity'] == 'MEDIUM', "Asia solo debe tener MEDIUM liquidity"

            print("   ✅ BitcoinContext: PASS")
            return {
                'status': 'PASS',
                'tests_passed': 6,
                'details': 'Bitcoin levels, Fear-Greed, y session quality correctos'
            }

        except AssertionError as e:
            self.errors.append(f"BitcoinContext: {e}")
            print(f"   ❌ {e}")
            return {'status': 'FAIL', 'error': str(e)}

    def audit_integration(self) -> Dict:
        """Audita integración entre módulos"""
        print("🔍 Auditando integración...")

        try:
            # Flow completo: StructureDetector → TZVValidator → ScenarioManager → BitcoinContext

            # Paso 1: Detectar estructura
            detector = StructureChangeDetector()
            bullish_highs = np.array([90.0, 90.5, 91.0, 91.5, 92.0])
            bullish_lows = np.array([89.0, 89.5, 90.0, 90.5, 91.0])
            closes = np.array([90.2, 90.7, 91.1, 91.6, 92.0])

            phase = detector.detect_structure_phase(bullish_highs, bullish_lows)
            assert 'bullish' in phase['phase'].value, "Fase debe ser bullish"

            # Paso 2: Validar T+Z+V
            validator = TZVValidator()
            t_result = validator.validate_t_tendencia(bullish_highs, bullish_lows, closes)
            assert t_result['validation_passed'], "T debe pasar"

            # Paso 3: Aplicar escenario
            mgr = ScenarioManager()
            scenario_result = mgr.analyze_scenario(
                current_price=91.0,
                maximos_trend=phase['maximos_minimos']['maximos_trend'],
                minimos_trend=phase['maximos_minimos']['minimos_trend'],
                distribution_level='minuscula',
                volatility_level='normal'
            )
            assert scenario_result['scenario'].value == 'A_liquidity_entering', "Debe ser Escenario A"

            # Paso 4: Bitcoin context
            btc_ctx = BitcoinContext()
            setup = btc_ctx.evaluate_bitcoin_setup(
                current_price=91.0,
                scenario='A',
                structure_confidence=phase['confidence'],
                session_hour=14
            )
            assert 'recommendation' in setup, "Debe tener recomendación"
            assert 'composite_confidence' in setup, "Debe tener confianza compuesta"

            print("   ✅ Integración: PASS")
            return {
                'status': 'PASS',
                'tests_passed': 4,
                'details': 'Flow completo funciona: StructureDetector → TZVValidator → Scenario → Bitcoin'
            }

        except Exception as e:
            self.errors.append(f"Integration: {e}")
            print(f"   ❌ {e}")
            return {'status': 'FAIL', 'error': str(e)}

    def generate_report(self) -> str:
        """Genera reporte de auditoría"""
        report = "\n" + "="*60 + "\n"
        report += "🔍 CRECETRADER IMPLEMENTATION AUDIT REPORT\n"
        report += "="*60 + "\n\n"

        results = self.audit_all()

        # Results por módulo
        report += "📊 RESULTADOS POR MÓDULO:\n"
        report += "-" * 60 + "\n"
        for module, result in results.items():
            if module == 'summary':
                continue
            status_emoji = "✅" if result.get('status') == 'PASS' else "❌"
            report += f"{status_emoji} {module.upper()}: {result.get('status')}\n"
            if result.get('tests_passed'):
                report += f"   Tests pasados: {result['tests_passed']}\n"
            if result.get('details'):
                report += f"   {result['details']}\n"
            if result.get('error'):
                report += f"   ERROR: {result['error']}\n"
            report += "\n"

        # Summary
        report += "📋 RESUMEN:\n"
        report += "-" * 60 + "\n"
        summary = results['summary']
        report += f"Errores: {summary['errors']}\n"
        report += f"Advertencias: {summary['warnings']}\n"
        report += f"Estado General: {summary['status']}\n\n"

        if summary['errors'] == 0:
            report += "✅ TODO PASA - Lógica Crecetrader correctamente implementada\n"
        else:
            report += "❌ FALLOS ENCONTRADOS - Ver detalles arriba\n"

        report += "="*60 + "\n"
        return report


if __name__ == '__main__':
    audit = CrecetraderAudit()
    print(audit.generate_report())
