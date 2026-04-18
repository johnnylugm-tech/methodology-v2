"""
Data-as-Perimeter: L1/L2/L3 De-identification
"""
import hashlib
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class PerimeterLevel(Enum):
    """Data perimeter protection levels"""
    L1_RAW = "L1"      # Original data, planner only
    L2_SCHEMA = "L2"  # Intent + schema, no raw values
    L3_HASH = "L3"     # Evidence hash only


# PII field patterns
PII_PATTERNS = {
    "ssn": re.compile(r"\d{3}-\d{2}-\d{4}"),
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "phone": re.compile(r"\+?1?\d{9,15}"),
    "credit_card": re.compile(r"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}"),
    "ip_address": re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"),
}


@dataclass
class DeidentifiedPayload:
    """Result of deidentification"""
    intent: Optional[str] = None
    schema: Optional[dict] = None
    evidence_hash: Optional[str] = None
    raw_present: bool = False
    deidentified_fields: list[str] = None
    perimeter_level: Optional[str] = None
    
    def __post_init__(self):
        if self.deidentified_fields is None:
            self.deidentified_fields = []
        if self.perimeter_level is None:
            self.perimeter_level = "L1"


def _compute_evidence_hash(data: Any) -> str:
    """Compute SHA256 hash of data for evidence"""
    if isinstance(data, dict):
        data_str = str(sorted(data.items()))
    else:
        data_str = str(data)
    return hashlib.sha256(data_str.encode()).hexdigest()


def _detect_pii_fields(data: dict) -> list[str]:
    """Detect which fields contain PII"""
    pii_fields = []
    for key, value in data.items():
        if value is None:
            continue
        value_str = str(value)
        for pii_type, pattern in PII_PATTERNS.items():
            if pattern.search(value_str):
                pii_fields.append(key)
                break
    return pii_fields


def _generate_schema(data: dict) -> dict:
    """Generate schema from data (types only, no values)"""
    schema = {}
    for key, value in data.items():
        if isinstance(value, str):
            schema[key] = "string"
        elif isinstance(value, int):
            schema[key] = "integer"
        elif isinstance(value, float):
            schema[key] = "float"
        elif isinstance(value, bool):
            schema[key] = "boolean"
        elif isinstance(value, dict):
            schema[key] = {"type": "object", "nested": True}
        elif isinstance(value, list):
            schema[key] = {"type": "array", "item_type": "mixed"}
        else:
            schema[key] = "unknown"
    return schema


def deidentify(
    payload: dict,
    level: PerimeterLevel = PerimeterLevel.L2_SCHEMA,
    intent: Optional[str] = None,
) -> DeidentifiedPayload:
    """
    Deidentify a payload according to perimeter level.
    
    L1: Return original data (planner only)
    L2: Return intent + schema + evidence_hash (critic/DA)
    L3: Return evidence_hash only (judge verification)
    """
    if level == PerimeterLevel.L1_RAW:
        return DeidentifiedPayload(
            raw_present=True,
            deidentified_fields=[],
            perimeter_level="L1",
        )
    
    # Compute evidence hash (always)
    evidence = _compute_evidence_hash(payload)
    
    # Generate schema (L2+)
    schema = _generate_schema(payload)
    
    if level == PerimeterLevel.L2_SCHEMA:
        # Detect PII fields
        pii_fields = _detect_pii_fields(payload)
        return DeidentifiedPayload(
            intent=intent or "Process user data for validation",
            schema=schema,
            evidence_hash=evidence,
            raw_present=False,
            deidentified_fields=pii_fields,
            perimeter_level="L2",
        )
    
    # L3 — evidence hash only
    return DeidentifiedPayload(
        intent=None,
        schema=None,
        evidence_hash=evidence,
        raw_present=False,
        deidentified_fields=[],
        perimeter_level="L3",
    )


def verify_evidence(original: Any, evidence_hash: str) -> bool:
    """Verify that original data matches a given evidence hash"""
    computed = _compute_evidence_hash(original)
    return computed == evidence_hash


def auto_detect_and_deidentify(
    payload: dict,
    level: Optional[PerimeterLevel] = None,
    intent: Optional[str] = None,
) -> DeidentifiedPayload:
    """
    Automatically detect PII fields and apply appropriate deidentification.
    """
    pii_fields = _detect_pii_fields(payload)
    
    if not pii_fields:
        # No PII detected, apply requested level or default L2
        return deidentify(payload, level or PerimeterLevel.L2_SCHEMA, intent)
    
    # PII detected — apply L2 at minimum
    effective_level = level or PerimeterLevel.L2_SCHEMA
    if level == PerimeterLevel.L1_RAW:
        effective_level = PerimeterLevel.L2_SCHEMA  # Override L1 if PII detected
    
    return deidentify(payload, effective_level, intent)