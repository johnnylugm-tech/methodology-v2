# core/ — Core modules for methodology-v2
#
# This file makes `core/` a Python package, enabling imports like:
#   from core.quality_gate import AutoQualityGate
#   from core.feedback import FeedbackStore
#   from core.self_correction import SelfCorrectionEngine
#
# Without this __init__.py, `core` would not be recognized as a package
# and dotted imports (from core.X) would fail.
