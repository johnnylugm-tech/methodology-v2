#!/bin/bash
# Ralph Mode E2E Test: Complete Flow

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RALPH_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TEST_DIR="/tmp/ralph_e2e_test_$$"

echo "============================================"
echo "E2E Test: Ralph Mode Complete Flow"
echo "============================================"
echo "Test dir: $TEST_DIR"
echo ""

# Setup
mkdir -p "$TEST_DIR/.methodology"
cd "$TEST_DIR"

# Initialize sessions_spawn.log with schema v1.0
python3 << PYEOF
import sys
sys.path.insert(0, '$RALPH_DIR')

from ralph_mode.schema_validator import SessionsSpawnLogValidator
from pathlib import Path
import json

validator = SessionsSpawnLogValidator()
log_path = Path('$TEST_DIR/.methodology/sessions_spawn.log')
log_content = validator.create_empty_log()
log_path.write_text(json.dumps(log_content, indent=2))

print("[1/6] Created sessions_spawn.log with schema v1.0")
print(f"       Schema version: {log_content['schema_version']}")
PYEOF

# Start Ralph (estimated 3 FRs)
python3 << PYEOF
import sys
sys.path.insert(0, '$RALPH_DIR')

from ralph_mode.lifecycle import RalphLifecycleManager
from pathlib import Path

repo = Path('$TEST_DIR')
manager = RalphLifecycleManager(repo)

try:
    task_id = manager.start(phase=3, estimated_minutes=5, fr_list=["FR-01", "FR-02", "FR-03"])
    print(f"[2/6] Ralph started: {task_id}")
    
    # Check Ralph is running
    running = manager.get_running_ralph(phase=3)
    assert running is not None, "Ralph should be running"
    assert running.task_id == task_id
    print(f"       Running state confirmed: {running.status}")
except Exception as e:
    print(f"[FAIL] Ralph start failed: {e}")
    sys.exit(1)
PYEOF

# Add 1 FR COMPLETED (out of 3)
python3 << PYEOF
import sys
sys.path.insert(0, '$RALPH_DIR')

from pathlib import Path
import json

log_path = Path('$TEST_DIR/.methodology/sessions_spawn.log')
content = json.loads(log_path.read_text())

# Add FR-01 COMPLETED (1 of 3)
content['entries'].append({
    "timestamp": "2026-04-15T20:00:00",
    "session_id": "sess-001",
    "fr": "FR-01",
    "status": "COMPLETED"
})

log_path.write_text(json.dumps(content, indent=2))
print("[3/6] Added FR-01 COMPLETED (1/3)")
PYEOF

# Check Ralph detects progress
python3 << PYEOF
import sys
sys.path.insert(0, '$RALPH_DIR')

from ralph_mode.lifecycle import RalphLifecycleManager
from pathlib import Path

repo = Path('$TEST_DIR')
manager = RalphLifecycleManager(repo)

running = manager.get_running_ralph(phase=3)
manager._current_task_id = running.task_id
manager._current_state = running

result = manager.check()

print(f"[4/6] Ralph check (1/3 completed):")
print(f"       Status: {result.status}")
print(f"       FR Completed: {result.fr_completed}/{result.fr_total}")
print(f"       Progress: {result.progress:.1f}%")

# Should be running (not all FRs done yet)
assert result.status == "running", f"Expected running, got {result.status}"
assert result.fr_completed == 1
print(f"       ✓ Ralph correctly detects running state")
PYEOF

# Complete all remaining FRs
python3 << PYEOF
import sys
sys.path.insert(0, '$RALPH_DIR')

from pathlib import Path
import json

log_path = Path('$TEST_DIR/.methodology/sessions_spawn.log')
content = json.loads(log_path.read_text())

# Add FR-02 and FR-03 COMPLETED
content['entries'].append({
    "timestamp": "2026-04-15T20:15:00",
    "session_id": "sess-002",
    "fr": "FR-02",
    "status": "COMPLETED"
})
content['entries'].append({
    "timestamp": "2026-04-15T20:20:00",
    "session_id": "sess-003",
    "fr": "FR-03",
    "status": "COMPLETED"
})

log_path.write_text(json.dumps(content, indent=2))
print("[5/6] Added FR-02 and FR-03 COMPLETED (all 3 done)")
PYEOF

# Final check - should detect completion
python3 << PYEOF
import sys
sys.path.insert(0, '$RALPH_DIR')

from ralph_mode.lifecycle import RalphLifecycleManager
from pathlib import Path

repo = Path('$TEST_DIR')
manager = RalphLifecycleManager(repo)

running = manager.get_running_ralph(phase=3)
manager._current_task_id = running.task_id
manager._current_state = running

result = manager.check()

print(f"[6/6] Final check (3/3 completed):")
print(f"       Status: {result.status}")
print(f"       FR Completed: {result.fr_completed}/{result.fr_total}")
print(f"       Progress: {result.progress:.1f}%")

# All done!
assert result.status == "completed", f"Expected completed, got {result.status}"
assert result.fr_completed == 3
print(f"       ✓ Ralph correctly detects completion")
PYEOF

echo ""
echo "============================================"
echo "E2E Test: PASSED"
echo "============================================"

# Cleanup
rm -rf "$TEST_DIR"
echo "Cleaned up: $TEST_DIR"
