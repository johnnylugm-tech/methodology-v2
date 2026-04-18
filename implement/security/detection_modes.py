"""Detection modes and threshold rules."""
import re
from .shield_enums import Verdict, ScanResult, PatternMatch

class DetectionModes:
    MODES = {
        "direct_override": {"action": Verdict.BLOCK, "threshold_block": 0.70, "threshold_flag": 0.85},
        "role_hijack": {"action": Verdict.BLOCK, "threshold_block": 0.70, "threshold_flag": 0.85},
        "data_exfil": {"action": Verdict.BLOCK, "threshold_block": 0.70, "threshold_flag": 0.85},
        "tool_abuse": {"action": Verdict.BLOCK, "threshold_block": 0.70, "threshold_flag": 0.85},
        "subtle_steering": {"action": Verdict.FLAG, "threshold_flag": 0.85},
    }

    INJECTION_PATTERNS = {
        "direct_override": [
            re.compile(r"ignore?\s*previous?\s*instructions?", re.IGNORECASE),
            re.compile(r"disregard?\s*system\s*prompt", re.IGNORECASE),
        ],
        "role_hijack": [
            re.compile(r"you\s+are\s+now\s+DAN", re.IGNORECASE),
            re.compile(r"pretend?\s+you\s+have\s+no\s+restrictions?", re.IGNORECASE),
        ],
        "data_exfil": [
            re.compile(r"output\s+your\s+system\s+prompt", re.IGNORECASE),
            re.compile(r"reveal?\s+your\s+configuration", re.IGNORECASE),
        ],
        "tool_abuse": [
            re.compile(r"call\s+unauthorized?\s+tool", re.IGNORECASE),
            re.compile(r"execute\s+root\s+command", re.IGNORECASE),
        ],
    }

    def detect(self, content: str) -> list[PatternMatch]:
        matches = []
        for mode, patterns in self.INJECTION_PATTERNS.items():
            for pattern in patterns:
                for m in pattern.finditer(content):
                    matches.append(PatternMatch(
                        pattern_name=pattern.pattern,
                        mode=mode,
                        matched_text=m.group(),
                        position=(m.start(), m.end()),
                        confidence=0.85,
                    ))
        return matches

    def apply_thresholds(self, results: list[ScanResult]) -> ScanResult:
        if not results:
            return ScanResult(verdict=Verdict.PASS, confidence=1.0)
        block = [r for r in results if r.verdict == Verdict.BLOCK]
        if block:
            return max(block, key=lambda r: r.confidence)
        flag = [r for r in results if r.verdict == Verdict.FLAG]
        if flag:
            return max(flag, key=lambda r: r.confidence)
        return max(results, key=lambda r: r.confidence)
