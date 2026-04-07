# conftest.py - pytest configuration for tests package
import sys
from pathlib import Path

# Add paths so BOTH quality_gate.X AND core.feedback.X are importable.
# project_root must come BEFORE core/ in sys.path so that:
# - "quality_gate.constitution" is found at project_root/quality_gate/constitution/
# - "core.feedback" is found at project_root/core/feedback/
# orchestration.py also does this, but we set it up here first so
# all imports are resolved correctly before any module caching happens.
_ROOT = Path(__file__).parent.parent.resolve()
_CORE = _ROOT / "core"

# Add project root first (for quality_gate.X, steering.X, etc.)
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
# Add core/ second (for core.feedback.X, core.self_correction.X)
elif str(_CORE) not in sys.path:
    sys.path.insert(1, str(_CORE))
