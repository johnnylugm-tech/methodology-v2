"""Configure pytest to find the detection module."""
import sys
from pathlib import Path

# Add the implement directory to Python path so 'from detection.xxx import' works
implement_path = Path(__file__).parent.parent / "03-implement"
sys.path.insert(0, str(implement_path))
