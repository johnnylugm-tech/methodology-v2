# conftest.py - pytest configuration for Feature #9 Risk Assessment tests
import sys
from pathlib import Path

# Add the feature package directory to sys.path
# so that "from engine.xxx" and "from models.xxx" imports work
feature_dir = Path(__file__).parent.parent
if str(feature_dir) not in sys.path:
    sys.path.insert(0, str(feature_dir))
