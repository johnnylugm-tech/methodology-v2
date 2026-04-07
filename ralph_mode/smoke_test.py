#!/usr/bin/env python3
"""
Ralph Mode Smoke Test
====================
Quick health check for Ralph Mode components.

Usage:
    python -m ralph_mode.smoke_test
    python -m ralph_mode.smoke_test --verbose

Author: methodology-v2 v5.95
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class SmokeTestResult:
    """Smoke test result."""
    
    def __init__(self):
        self.passed: List[str] = []
        self.failed: List[Tuple[str, str]] = []  # (test_name, error_message)
        self.warnings: List[str] = []
    
    @property
    def all_passed(self) -> bool:
        return len(self.failed) == 0
    
    @property
    def pass_rate(self) -> float:
        total = len(self.passed) + len(self.failed)
        if total == 0:
            return 0.0
        return (len(self.passed) / total) * 100
    
    def add_pass(self, test_name: str):
        self.passed.append(test_name)
    
    def add_fail(self, test_name: str, error: str):
        self.failed.append((test_name, error))
    
    def add_warning(self, message: str):
        self.warnings.append(message)
    
    def print_summary(self):
        print("=" * 60)
        print("📋 Ralph Mode Smoke Test Results")
        print("=" * 60)
        print(f"\n✅ Passed: {len(self.passed)}")
        print(f"❌ Failed: {len(self.failed)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"\n📊 Pass Rate: {self.pass_rate:.1f}%")
        
        if self.all_passed:
            print("\n🎉 All smoke tests passed!")
        else:
            print("\n🚨 Some smoke tests failed:")
            for test_name, error in self.failed:
                print(f"   - {test_name}: {error}")
        
        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"   - {warning}")
        
        print()


def smoke_test_task_state() -> Tuple[bool, str]:
    """Test TaskState class."""
    try:
        from ralph_mode.task_persistence import TaskState
        state = TaskState(
            task_id="smoke-test-001",
            status="pending",
            current_phase="init"
        )
        # Check attributes
        assert state.task_id == "smoke-test-001"
        assert state.status == "pending"
        assert state.current_phase == "init"
        assert state.progress == 0.0
        # Check methods
        assert hasattr(state, 'to_dict')
        assert hasattr(state, 'from_dict')
        data = state.to_dict()
        assert isinstance(data, dict)
        return True, ""
    except Exception as e:
        return False, str(e)


def smoke_test_task_persistence() -> Tuple[bool, str]:
    """Test TaskPersistence class."""
    try:
        from ralph_mode.task_persistence import TaskPersistence, TaskState
        import tempfile
        import shutil
        
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        try:
            persistence = TaskPersistence(storage_dir=temp_dir)
            state = TaskState(
                task_id="smoke-test-persist",
                status="running",
                current_phase="run_batch"
            )
            
            # Save and load
            persistence.save_state(state)
            loaded = persistence.load_state("smoke-test-persist")
            
            assert loaded is not None
            assert loaded.task_id == "smoke-test-persist"
            assert loaded.status == "running"
            
            return True, ""
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception as e:
        return False, str(e)


def smoke_test_phase_state_machine() -> Tuple[bool, str]:
    """Test PhaseStateMachine class."""
    try:
        from ralph_mode.state_machine import PhaseStateMachine, PhaseStatus
        
        sm = PhaseStateMachine()
        assert sm is not None
        
        # Check phases
        phases = sm.get_phases()
        assert isinstance(phases, list)
        assert len(phases) > 0
        
        # Check status transitions
        assert hasattr(sm, 'start')
        assert hasattr(sm, 'advance')
        assert hasattr(sm, 'get_current_phase')
        
        return True, ""
    except Exception as e:
        return False, str(e)


def smoke_test_ralph_scheduler() -> Tuple[bool, str]:
    """Test RalphScheduler class."""
    try:
        from ralph_mode.scheduler import RalphScheduler, SchedulerConfig
        
        config = SchedulerConfig(
            task_id="smoke-test-scheduler",
            interval_seconds=60
        )
        assert config.task_id == "smoke-test-scheduler"
        assert config.interval_seconds == 60
        
        scheduler = RalphScheduler(
            task_id="smoke-test-scheduler",
            interval_seconds=60
        )
        assert scheduler is not None
        assert hasattr(scheduler, 'start')
        assert hasattr(scheduler, 'stop')
        assert hasattr(scheduler, 'get_status')
        
        return True, ""
    except Exception as e:
        return False, str(e)


def smoke_test_progress_tracker() -> Tuple[bool, str]:
    """Test RalphProgressTracker class."""
    try:
        from ralph_mode.progress_tracker import RalphProgressTracker
        
        tracker = RalphProgressTracker("smoke-test-tracker")
        assert tracker is not None
        
        # Check methods
        assert hasattr(tracker, 'update_progress')
        assert hasattr(tracker, 'get_progress')
        assert hasattr(tracker, 'get_report')
        
        # Test update
        tracker.update_progress("run_batch", 50.0)
        progress = tracker.get_progress()
        assert progress >= 0
        
        return True, ""
    except Exception as e:
        return False, str(e)


def smoke_test_5w1h_structure() -> Tuple[bool, str]:
    """Test 5W1H structure validation."""
    try:
        from ralph_mode.task_persistence import TaskState
        
        # Validate 5W1H fields exist in TaskState
        state = TaskState(task_id="5w1h-test")
        
        # WHO - task_id is the identifier
        assert hasattr(state, 'task_id')
        
        # WHAT - current_phase describes what task is doing
        assert hasattr(state, 'current_phase')
        
        # WHEN - timestamps
        assert hasattr(state, 'created_at')
        assert hasattr(state, 'updated_at')
        assert hasattr(state, 'last_check')
        
        # WHERE - progress tracking
        assert hasattr(state, 'progress')
        
        # WHY - metadata for context
        assert hasattr(state, 'metadata')
        
        # HOW - status for execution state
        assert hasattr(state, 'status')
        
        return True, ""
    except Exception as e:
        return False, str(e)


def smoke_test_health_check() -> Tuple[bool, str]:
    """Test basic health check."""
    try:
        from ralph_mode import (
            TaskState,
            TaskPersistence,
            RalphScheduler,
            PhaseStateMachine,
            RalphProgressTracker
        )
        
        # Check all exports
        components = [
            "TaskState",
            "TaskPersistence",
            "RalphScheduler",
            "PhaseStateMachine",
            "RalphProgressTracker"
        ]
        
        for component in components:
            assert component in dir()
        
        return True, ""
    except Exception as e:
        return False, str(e)


def run_smoke_tests(verbose: bool = False) -> SmokeTestResult:
    """Run all smoke tests."""
    result = SmokeTestResult()
    
    tests = [
        ("TaskState", smoke_test_task_state),
        ("TaskPersistence", smoke_test_task_persistence),
        ("PhaseStateMachine", smoke_test_phase_state_machine),
        ("RalphScheduler", smoke_test_ralph_scheduler),
        ("ProgressTracker", smoke_test_progress_tracker),
        ("5W1H Structure", smoke_test_5w1h_structure),
        ("Health Check", smoke_test_health_check),
    ]
    
    print("Running Ralph Mode smoke tests...\n")
    
    for test_name, test_func in tests:
        if verbose:
            print(f"  Testing {test_name}...", end=" ")
        
        try:
            passed, error = test_func()
            if passed:
                result.add_pass(test_name)
                if verbose:
                    print("✅")
            else:
                result.add_fail(test_name, error)
                if verbose:
                    print(f"❌ ({error})")
        except Exception as e:
            result.add_fail(test_name, str(e))
            if verbose:
                print(f"❌ ({str(e)})")
    
    return result


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ralph Mode Smoke Test")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    result = run_smoke_tests(verbose=args.verbose)
    result.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if result.all_passed else 1)


if __name__ == "__main__":
    main()