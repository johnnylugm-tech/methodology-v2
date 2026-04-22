"""Pytest configuration for Feature #10 LangGraph tests."""

import sys
import os
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# CRITICAL: Pre-import langgraph submodules BEFORE modifying sys.path
#
# The root conftest.py creates 'implement.ml_langgraph' in sys.modules,
# and somehow this causes 'langgraph' to resolve to the test 'langgraph/'
# directory (which has langgraph.conftest) instead of the pip-installed
# langgraph package in site-packages.
#
# To fix this, we MUST remove any 'langgraph' stubs from sys.modules
# before trying to import langgraph.graph.state.
# ─────────────────────────────────────────────────────────────────────────────

# Remove any langgraph stubs from sys.modules created by root conftest
for key in list(sys.modules.keys()):
    if key == 'langgraph' or key.startswith('langgraph.'):
        del sys.modules[key]

# Now import - Python will resolve langgraph from site-packages
try:
    import langgraph.graph.state
except ImportError as e:
    # langgraph not installed - tests that need it will fail with their own error
    pass

# ─────────────────────────────────────────────────────────────────────────
# Add 03-implement to path so 'import ml_langgraph' works
# ─────────────────────────────────────────────────────────────────────────────
_impl_root = Path(__file__).parent.parent.parent / "03-implement"
if str(_impl_root) not in sys.path:
    sys.path.insert(0, str(_impl_root))

import pytest
