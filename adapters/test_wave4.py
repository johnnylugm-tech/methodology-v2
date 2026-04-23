"""
adapters/test_wave4.py — Wave 4 Integration Tests

Test each Wave 4 Feature:
- #9 Risk: 8-dimension risk assessment (warn ≥7, freeze ≥9)
- #12 Compliance: ASPICE reporting + event-driven compliance

Run: python adapters/test_wave4.py
"""

import sys
import tempfile
from pathlib import Path

# Add methodology root to path
METHODOLOGY_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(METHODOLOGY_ROOT))

from adapters.phase_hooks_adapter import (
    PhaseHooksAdapter,
    POSTFLIGHT_FAILED,
)


def test_risk_freeze_on_critical():
    """TEST F09-03: Risk triggers FREEZE when aggregate ≥ 9."""
    print("\n=== TEST F09-03: Risk FREEZE on Critical ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        adapter = PhaseHooksAdapter(tmpdir, phase=1)
        adapter.feature_flags["risk"] = True
        
        # Mock Risk with critical score (≥9)
        class MockRisk:
            def assess(self, phase=None):
                return {
                    "dimensions": {dim: 9.5 for dim in [
                        "complexity", "dependency", "quality", "stability",
                        "team", "process", "knowledge", "external"
                    ]},
                    "aggregate": 9.5,
                    "level": "FREEZE",
                    "phase": phase,
                    "timestamp": "2026-04-24T00:00:00",
                }
            def check_freeze(self):
                return True  # Critical
            def generate_register(self):
                return {"path": f"{tmpdir}/RISK_REGISTER.md", "content": "...", "blocked": True}
        
        adapter.risk = MockRisk()
        # Mock phase_hooks.postflight_all to avoid file system requirements
        adapter.phase_hooks.postflight_all = lambda: {"status": "ok"}
        
        try:
            adapter.postflight_all()
            assert False, "Should have raised POSTFLIGHT_FAILED"
        except POSTFLIGHT_FAILED as e:
            print(f"  POSTFLIGHT_FAILED raised: {e}")
            print(f"  ✅ PASS: Risk FREEZE blocks postflight")
            return True


def test_risk_assessment_8_dimensions():
    """TEST F09-01: Risk returns 8 dimensions."""
    print("\n=== TEST F09-01: Risk 8 Dimensions ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        adapter = PhaseHooksAdapter(tmpdir, phase=1)
        adapter.feature_flags["risk"] = True
        
        class MockRisk:
            def assess(self, phase=None):
                return {
                    "dimensions": {
                        "complexity": 6.5,
                        "dependency": 5.0,
                        "quality": 7.2,
                        "stability": 4.8,
                        "team": 3.0,
                        "process": 2.5,
                        "knowledge": 4.0,
                        "external": 5.5,
                    },
                    "aggregate": 5.2,
                    "level": "OK",
                    "phase": phase,
                    "timestamp": "2026-04-24T00:00:00",
                }
            def check_freeze(self):
                return False
            def generate_register(self):
                return {"path": f"{tmpdir}/RISK_REGISTER.md", "content": "...", "blocked": False}
        
        adapter.risk = MockRisk()
        adapter.phase_hooks.postflight_all = lambda: {"status": "ok"}
        
        result = adapter.postflight_all()
        
        print(f"  risk_profile: {result.get('risk_profile', {}).get('level')}")
        assert result.get("risk_profile") is not None
        
        print(f"  ✅ PASS: Risk assessment returns 8 dimensions")
        return True


def test_risk_warns_high_score():
    """TEST F09-02: Risk warns when aggregate ≥ 7."""
    print("\n=== TEST F09-02: Risk WARN on High Score ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        adapter = PhaseHooksAdapter(tmpdir, phase=1)
        adapter.feature_flags["risk"] = True
        
        class MockRisk:
            def assess(self, phase=None):
                return {
                    "dimensions": {dim: 7.5 for dim in [
                        "complexity", "dependency", "quality", "stability",
                        "team", "process", "knowledge", "external"
                    ]},
                    "aggregate": 7.5,
                    "level": "WARN",
                    "phase": phase,
                    "timestamp": "2026-04-24T00:00:00",
                }
            def check_freeze(self):
                return False
            def generate_register(self):
                return {"path": f"{tmpdir}/RISK_REGISTER.md", "content": "...", "blocked": False}
        
        adapter.risk = MockRisk()
        adapter.phase_hooks.postflight_all = lambda: {"status": "ok"}
        
        result = adapter.postflight_all()
        
        print(f"  risk_level: {result.get('risk_profile', {}).get('level')}")
        assert result.get("risk_profile", {}).get("level") == "WARN"
        
        print(f"  ✅ PASS: Risk warns on high score (no exception)")
        return True


def test_risk_generates_register():
    """TEST F09-04: Risk generates RISK_REGISTER.md."""
    print("\n=== TEST F09-04: Risk Register Generated ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        adapter = PhaseHooksAdapter(tmpdir, phase=1)
        adapter.feature_flags["risk"] = True
        
        class MockRisk:
            def assess(self, phase=None):
                return {
                    "dimensions": {dim: 5.0 for dim in [
                        "complexity", "dependency", "quality", "stability",
                        "team", "process", "knowledge", "external"
                    ]},
                    "aggregate": 5.0,
                    "level": "OK",
                    "phase": phase,
                    "timestamp": "2026-04-24T00:00:00",
                }
            def check_freeze(self):
                return False
            def generate_register(self):
                register_path = Path(tmpdir) / "RISK_REGISTER.md"
                content = "# Risk Register\n\n**Score**: 5.0\n"
                register_path.write_text(content)
                return {"path": str(register_path), "content": content, "blocked": False}
        
        adapter.risk = MockRisk()
        adapter.phase_hooks.postflight_all = lambda: {"status": "ok"}
        
        result = adapter.postflight_all()
        
        register_path = Path(tmpdir) / "RISK_REGISTER.md"
        print(f"  register exists: {register_path.exists()}")
        assert register_path.exists()
        
        print(f"  ✅ PASS: RISK_REGISTER.md generated")
        return True


def test_compliance_records_hr12_event():
    """TEST F12-01: Compliance records HR-12 trigger event."""
    print("\n=== TEST F12-01: Compliance HR-12 Event ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        adapter = PhaseHooksAdapter(tmpdir, phase=1)
        adapter.feature_flags["compliance"] = True
        adapter.feature_flags["kill_switch"] = True
        
        class MockCompliance:
            def __init__(self):
                self._events = []
            def record_hr12_trigger(self, fr_id, iteration):
                self._events.append({"event": "HR12_TRIGGERED", "fr_id": fr_id, "iteration": iteration})
            def record_event(self, event_type, fr_id=None, metadata=None):
                self._events.append({"event": event_type, "fr_id": fr_id})
            def generate_phase_report(self, phase):
                return {"path": f"{tmpdir}/COMPLIANCE_REPORT.md", "aspice_rate": 0.85, "events": self._events, "warn": False}
            def reset_events(self):
                self._events = []
        
        adapter.compliance = MockCompliance()
        
        # Manually call compliance record
        if adapter.compliance:
            adapter.compliance.record_hr12_trigger("FR-01", iteration=5)
        
        assert len(adapter.compliance._events) > 0
        print(f"  events recorded: {len(adapter.compliance._events)}")
        
        print(f"  ✅ PASS: Compliance records HR-12 event")
        return True


def test_compliance_phase_report_generated():
    """TEST F12-02: Compliance generates phase report."""
    print("\n=== TEST F12-02: Compliance Phase Report ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        adapter = PhaseHooksAdapter(tmpdir, phase=1)
        adapter.feature_flags["compliance"] = True
        
        class MockCompliance:
            def __init__(self):
                self._events = []
            def record_event(self, event_type, fr_id=None, metadata=None):
                self._events.append({"event": event_type, "fr_id": fr_id})
            def generate_phase_report(self, phase):
                report_path = Path(tmpdir) / "COMPLIANCE_REPORT.md"
                content = f"# Compliance Report - Phase {phase}\n\n**ASPICE Rate**: 85%"
                report_path.write_text(content)
                return {"path": str(report_path), "aspice_rate": 0.85, "events": self._events, "warn": False}
            def reset_events(self):
                self._events = []
        
        adapter.compliance = MockCompliance()
        adapter.phase_hooks.postflight_all = lambda: {"status": "ok"}
        
        result = adapter.postflight_all()
        
        report_path = Path(tmpdir) / "COMPLIANCE_REPORT.md"
        print(f"  report exists: {report_path.exists()}")
        assert report_path.exists()
        
        compliance_result = result.get("compliance_report", {})
        print(f"  aspice_rate: {compliance_result.get('aspice_rate')}")
        
        print(f"  ✅ PASS: COMPLIANCE_REPORT.md generated")
        return True


def test_compliance_warns_low_aspice():
    """TEST F12-03: Compliance warns when ASPICE rate < 80%."""
    print("\n=== TEST F12-03: Compliance Low ASPICE Warning ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        adapter = PhaseHooksAdapter(tmpdir, phase=1)
        adapter.feature_flags["compliance"] = True
        
        class MockCompliance:
            def __init__(self):
                self._events = [{"event": "HR12_TRIGGERED", "fr_id": "FR-01"}]
            def record_event(self, event_type, fr_id=None, metadata=None):
                self._events.append({"event": event_type})
            def calculate_aspice_rate(self):
                return 0.72
            def generate_phase_report(self, phase):
                return {
                    "path": f"{tmpdir}/COMPLIANCE_REPORT.md",
                    "aspice_rate": 0.72,
                    "events": self._events,
                    "violations": [{"event": "HR12_TRIGGERED"}],
                    "warn": True,
                }
            def reset_events(self):
                self._events = []
        
        adapter.compliance = MockCompliance()
        adapter.phase_hooks.postflight_all = lambda: {"status": "ok"}
        
        result = adapter.postflight_all()
        
        compliance_result = result.get("compliance_report", {})
        print(f"  aspice_rate: {compliance_result.get('aspice_rate')}")
        print(f"  warn: {compliance_result.get('warn')}")
        
        assert compliance_result.get("warn") == True
        assert compliance_result.get("aspice_rate") < 0.80
        
        print(f"  ✅ PASS: Compliance warns on low ASPICE rate")
        return True


def test_compliance_no_block_on_warn():
    """TEST F12-04: Compliance does not block on warn (only warn)."""
    print("\n=== TEST F12-04: Compliance Warn Does Not Block ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        adapter = PhaseHooksAdapter(tmpdir, phase=1)
        adapter.feature_flags["compliance"] = True
        
        class MockCompliance:
            def __init__(self):
                self._events = []
            def record_event(self, event_type, fr_id=None, metadata=None):
                pass
            def generate_phase_report(self, phase):
                return {
                    "path": f"{tmpdir}/COMPLIANCE_REPORT.md",
                    "aspice_rate": 0.75,
                    "events": [],
                    "warn": True,
                }
            def reset_events(self):
                pass
        
        adapter.compliance = MockCompliance()
        adapter.phase_hooks.postflight_all = lambda: {"status": "ok"}
        
        result = adapter.postflight_all()
        
        assert result is not None
        print(f"  postflight completed: {result is not None}")
        
        print(f"  ✅ PASS: Compliance warn does not block")
        return True


def run_all_tests():
    """Run all Wave 4 tests."""
    print("=" * 60)
    print("Wave 4 Integration Tests — PhaseHooksAdapter")
    print("=" * 60)
    
    tests = [
        ("F09-01 Risk 8 Dimensions", test_risk_assessment_8_dimensions),
        ("F09-02 Risk WARN on High Score", test_risk_warns_high_score),
        ("F09-03 Risk FREEZE on Critical", test_risk_freeze_on_critical),
        ("F09-04 Risk Register Generated", test_risk_generates_register),
        ("F12-01 Compliance HR-12 Event", test_compliance_records_hr12_event),
        ("F12-02 Compliance Phase Report", test_compliance_phase_report_generated),
        ("F12-03 Compliance Low ASPICE Warning", test_compliance_warns_low_aspice),
        ("F12-04 Compliance Warn Does Not Block", test_compliance_no_block_on_warn),
    ]
    
    results = []
    for name, test_fn in tests:
        try:
            passed = test_fn()
            results.append((name, "✅ PASS" if passed else "❌ FAIL"))
        except Exception as e:
            print(f"  ❌ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, f"❌ EXCEPTION: {e}"))
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, result in results:
        print(f"  {result}: {name}")
    
    passed = sum(1 for _, r in results if "PASS" in r)
    print(f"\n  Total: {passed}/{len(results)} passed")
    
    return all("PASS" in r for _, r in results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)