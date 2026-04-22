"""Test configuration for observability module."""
import sys
from pathlib import Path

# Test structure:
#   .../04-tests/test_obs/conftest.py
#   .../03-implement/observability/__init__.py
# parents[0]=test_obs, parents[1]=04-tests, parents[2]=feature-13-observability
_import_root = Path(__file__).resolve().parents[1] / "03-implement"
sys.path.insert(0, str(_import_root))
