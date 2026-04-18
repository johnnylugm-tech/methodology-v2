"""Direct injection shield for user prompts."""
import hashlib
import time
from .shield_enums import Verdict, ScanResult
from .detection_modes import DetectionModes

class PromptShield:
    def __init__(self, detection_modes: DetectionModes | None = None):
        self.detection_modes = detection_modes or DetectionModes()

    def check(self, prompt: str, identity_context: dict | None = None) -> ScanResult:
        start = time.time()
        input_hash = hashlib.sha256(prompt.encode()).hexdigest()
        
        # Detect patterns
        matches = self.detection_modes.detect(prompt)
        
        if not matches:
            return ScanResult(
                verdict=Verdict.PASS,
                confidence=1.0,
                input_hash=input_hash,
                latency_ms=(time.time() - start) * 1000,
                scanner="detection_modes",
            )
        
        # Highest confidence from matches
        max_conf = max(m.confidence for m in matches)
        mode = matches[0].mode
        
        # Apply threshold
        mode_config = self.detection_modes.MODES.get(mode, {})
        threshold_block = mode_config.get("threshold_block", 0.70)
        
        if max_conf < threshold_block:
            verdict = Verdict.FLAG
        else:
            verdict = Verdict.BLOCK
        
        return ScanResult(
            verdict=verdict,
            confidence=max_conf,
            matched_patterns=matches,
            input_hash=input_hash,
            latency_ms=(time.time() - start) * 1000,
            scanner="detection_modes",
        )
