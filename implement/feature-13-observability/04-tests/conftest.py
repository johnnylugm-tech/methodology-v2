"""conftest — shared pytest fixtures for Feature #13 tests."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the observability module is importable from the implement tree
# The test structure is:
#   implement/feature-13-observability/04-tests/conftest.py
#   implement/feature-13-observability/03-implement/observability/__init__.py
# So from conftest.py (at 04-tests/), parents[0]=04-tests, parents[1]=feature-13-observability
# We need: feature-13-observability/03-implement
_import_root = Path(__file__).resolve().parents[1] / "03-implement"
sys.path.insert(0, str(_import_root))