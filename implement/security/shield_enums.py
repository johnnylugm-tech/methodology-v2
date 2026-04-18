"""Shield enums and data classes for Prompt Shields."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class Verdict(Enum):
    PASS = "pass"
    FLAG = "flag"
    BLOCK = "block"

@dataclass
class PatternMatch:
    pattern_name: str
    mode: str
    matched_text: str
    position: tuple[int, int]
    confidence: float

@dataclass
class ScanResult:
    verdict: Verdict
    confidence: float
    matched_patterns: list[PatternMatch] = field(default_factory=list)
    latency_ms: float = 0.0
    scanner: str = "unknown"
    input_hash: str = ""
    error: Optional[str] = None

class ScannerUnavailableError(Exception):
    pass

class AllScannersUnavailableError(Exception):
    pass
