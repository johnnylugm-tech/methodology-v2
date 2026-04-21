"""Pytest configuration for Feature #8 Risk tests."""
import sys
from pathlib import Path

# Add 03-implement to path so tests can import directly
sys.path.insert(0, str(Path(__file__).parent.parent / "03-implement"))