# conftest.py - pytest configuration for Feature #9 Risk Assessment tests
import sys
from pathlib import Path

# Add implement/ parent to sys.path so that
# "from implement.feature_09_risk_assessment.xxx" style imports work
implement_parent = Path(__file__).parent.parent.parent
if str(implement_parent) not in sys.path:
    sys.path.insert(0, str(implement_parent))