"""Pytest configuration for Feature #6 Hunter tests."""
import sys
from pathlib import Path

# Add 03-implement to path so tests can import `from hunter.xxx`
sys.path.insert(0, str(Path(__file__).parent.parent / "03-implement"))