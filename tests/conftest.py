# conftest.py - pytest configuration for tests package
import sys
from pathlib import Path

# Add the project root to sys.path so quality_gate and enforcement packages are importable
_ROOT = Path(__file__).parent.parent.resolve()
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
