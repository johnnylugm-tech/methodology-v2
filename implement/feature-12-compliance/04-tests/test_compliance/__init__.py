"""Feature #12 Compliance Layer Test Suite.

Tests for EU AI Act Article 14, NIST AI RMF, and RSP v3.0 compliance mechanisms.

FR Coverage:
- FR-12-01: EU AI Act Article 14 Compliance Checker
- FR-12-02: NIST AI RMF Function Mapper
- FR-12-03: Anthropic RSP ASL Level Detector
- FR-12-04: Unified Compliance Matrix Generator
- FR-12-05: Automated Compliance Reporter
- FR-12-06: Kill-Switch Compliance Monitor
- FR-12-07: Human Override Audit Trail
"""

import sys
from pathlib import Path

# Add implement directory to path for imports
_implement_path = Path(__file__).parent.parent.parent / "03-implement"
sys.path.insert(0, str(_implement_path))