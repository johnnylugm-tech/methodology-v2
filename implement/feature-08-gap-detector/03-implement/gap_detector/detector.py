"""Gap Detection Module.

Detects gaps between SPEC.md specifications and actual code implementation.
Identifies three types of gaps:
- MISSING: Features in SPEC but not implemented
- INCOMPLETE: Features partially implemented
- ORPHANED: Code items not specified in SPEC
"""

from dataclasses import dataclass
from typing import Optional

from gap_detector.parser import ParsedSpec, FeatureItem
from gap_detector.scanner import ScannedCode, CodeItem


# Levenshtein distance implementation
def _levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings.

    Args:
        s1: First string
        s2: Second string

    Returns:
        int: Edit distance
    """
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


@dataclass
class Match:
    """Represents a match between a spec item and code item.

    Attributes:
        spec_item: The spec feature item
        code_item: The matched code item (if any)
        match_type: Type of match ("exact", "fuzzy", or "none")
        similarity: Similarity score (0.0 to 1.0)
    """

    spec_item: FeatureItem
    code_item: Optional[CodeItem]
    match_type: str
    similarity: float


@dataclass
class Gap:
    """Represents a gap between specification and implementation.

    Attributes:
        gap_type: Type of gap ("MISSING", "INCOMPLETE", or "ORPHANED")
        spec_item: Name of the spec item (for MISSING/INCOMPLETE)
        code_item: Name of the code item (for ORPHANED/INCOMPLETE)
        spec_location: Location in SPEC.md
        code_location: Location in code file
        severity: Severity level ("critical", "major", "minor")
        reason: Human-readable description
        recommended_action: Suggested fix
        downstream_missing: Whether this is a downstream effect of another gap
    """

    gap_type: str
    spec_item: Optional[str] = None
    code_item: Optional[str] = None
    spec_location: Optional[str] = None
    code_location: Optional[str] = None
    severity: str = "minor"
    reason: str = ""
    recommended_action: str = ""
    downstream_missing: bool = False


@dataclass
class GapSummary:
    """Summary statistics for gap detection results.

    Attributes:
        total_gaps: Total number of gaps found
        missing: Number of MISSING gaps
        incomplete: Number of INCOMPLETE gaps
        orphaned: Number of ORPHANED gaps
        critical: Number of critical severity gaps
        major: Number of major severity gaps
        minor: Number of minor severity gaps
    """

    total_gaps: int = 0
    missing: int = 0
    incomplete: int = 0
    orphaned: int = 0
    critical: int = 0
    major: int = 0
    minor: int = 0


class GapDetector:
    """Detector for gaps between specification and implementation.

    Compares parsed SPEC.md features against scanned code to identify:
    - MISSING: Features in SPEC but not implemented
    - INCOMPLETE: Partially implemented features
    - ORPHANED: Implementation without specification

    Attributes:
        spec: Parsed specification
        code: Scanned code
        similarity_threshold: Threshold for fuzzy matching (default 0.6)
    """

    def __init__(
        self,
        spec: ParsedSpec,
        code: ScannedCode,
        similarity_threshold: float = 0.6
    ) -> None:
        """Initialize the gap detector.

        Args:
            spec: Parsed specification
            code: Scanned code
            similarity_threshold: Minimum similarity for fuzzy match (0.0 to 1.0)
        """
        self.spec = spec
        self.code = code
        self.similarity_threshold = similarity_threshold
        self._gaps: list[Gap] = []
        self._matches: list[Match] = []

    def detect(self) -> list[Gap]:
        """Detect gaps between specification and implementation.

        Returns:
            list[Gap]: List of detected gaps
        """
        self._gaps = []
        self._matches = []

        try:
            self._matches = self._match_spec_to_code()
        except (FileNotFoundError, OSError):
            return []
        except Exception:
            return []

        try:
            missing_gaps = self._detect_missing()
            self._gaps.extend(missing_gaps)
        except Exception:
            pass

        try:
            incomplete_gaps = self._detect_incomplete()
            self._gaps.extend(incomplete_gaps)
        except Exception:
            pass

        try:
            orphaned_gaps = self._detect_orphaned()
            self._gaps.extend(orphaned_gaps)
        except Exception:
            pass

        try:
            self._mark_downstream_effects()
        except Exception:
            pass

        return self._gaps

    def get_summary(self) -> GapSummary:
        """Get summary statistics of detected gaps.

        Returns:
            GapSummary: Summary of gaps
        """
        if not self._gaps:
            self.detect()

        summary = GapSummary()
        summary.total_gaps = len(self._gaps)

        for gap in self._gaps:
            if gap.gap_type == "MISSING":
                summary.missing += 1
            elif gap.gap_type == "INCOMPLETE":
                summary.incomplete += 1
            elif gap.gap_type == "ORPHANED":
                summary.orphaned += 1

            if gap.severity == "critical":
                summary.critical += 1
            elif gap.severity == "major":
                summary.major += 1
            elif gap.severity == "minor":
                summary.minor += 1

        return summary

    def _match_spec_to_code(self) -> list[Match]:
        """Match spec items to code items.

        Returns:
            list[Match]: List of matches
        """
        matches: list[Match] = []
        code_items = self._get_all_code_items()

        for spec_item in self.spec.feature_items:
            best_match = self._find_best_match(spec_item, code_items)
            matches.append(best_match)

        return matches

    def _find_best_match(
        self, spec_item: FeatureItem, code_items: list[CodeItem]
    ) -> Match:
        """Find the best matching code item for a spec item.

        Args:
            spec_item: Spec feature item
            code_items: List of code items

        Returns:
            Match: Best match
        """
        spec_name_normalized = self._normalize_name(spec_item.name)

        best_match: Optional[CodeItem] = None
        best_similarity = 0.0
        best_match_type = "none"

        for code_item in code_items:
            if not code_item.is_public:
                continue

            code_name_normalized = self._normalize_name(code_item.name)
            similarity = self._compute_similarity(spec_name_normalized, code_name_normalized)

            if similarity == 1.0 and spec_name_normalized == code_name_normalized:
                # Exact match
                return Match(
                    spec_item=spec_item,
                    code_item=code_item,
                    match_type="exact",
                    similarity=1.0
                )

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = code_item
                best_match_type = "fuzzy" if similarity >= self.similarity_threshold else "none"

        if best_match_type == "fuzzy":
            return Match(
                spec_item=spec_item,
                code_item=best_match,
                match_type="fuzzy",
                similarity=best_similarity
            )

        return Match(
            spec_item=spec_item,
            code_item=None,
            match_type="none",
            similarity=0.0
        )

    def _normalize_name(self, name: str) -> str:
        """Normalize a name for comparison.

        Args:
            name: Original name

        Returns:
            str: Normalized name
        """
        normalized = name.lower()
        normalized = normalized.replace("_", "")
        normalized = normalized.replace("-", "")
        normalized = normalized.replace(" ", "")
        return normalized

    def _compute_similarity(self, name_a: str, name_b: str) -> float:
        """Compute similarity between two names.

        Args:
            name_a: First normalized name
            name_b: Second normalized name

        Returns:
            float: Similarity score (0.0 to 1.0)
        """
        if not name_a and not name_b:
            return 1.0
        if not name_a or not name_b:
            return 0.0

        distance = _levenshtein_distance(name_a, name_b)
        max_len = max(len(name_a), len(name_b))

        return 1.0 - (distance / max_len)

    def _detect_missing(self) -> list[Gap]:
        """Detect MISSING gaps.

        Returns:
            list[Gap]: List of MISSING gaps
        """
        gaps: list[Gap] = []

        for match in self._matches:
            if match.code_item is None:
                is_core = match.spec_item.priority == "P0"
                severity = "critical" if is_core else "major"

                gap = Gap(
                    gap_type="MISSING",
                    spec_item=match.spec_item.name,
                    spec_location=f"SPEC.md:Line {match.spec_item.line_number}",
                    severity=severity,
                    reason=f"Feature '{match.spec_item.name}' is specified in SPEC.md but has no corresponding implementation",
                    recommended_action=f"Implement {match.spec_item.name} according to SPEC.md specifications"
                )
                gaps.append(gap)

        return gaps

    def _detect_incomplete(self) -> list[Gap]:
        """Detect INCOMPLETE gaps.

        Returns:
            list[Gap]: List of INCOMPLETE gaps
        """
        gaps: list[Gap] = []

        for match in self._matches:
            if match.code_item is not None and match.match_type != "none":
                code_item = match.code_item

                # Check for missing docstring
                has_docstring = len(code_item.docstring) > 0

                # Check for incomplete params (simplified check)
                len(code_item.params) >= 0  # Simplified

                if not has_docstring:
                    gap = Gap(
                        gap_type="INCOMPLETE",
                        spec_item=match.spec_item.name,
                        code_item=code_item.name,
                        spec_location=f"SPEC.md:Line {match.spec_item.line_number}",
                        code_location=f"{code_item.file_path}:Line {code_item.line_number}",
                        severity="minor",
                        reason=f"Implementation '{code_item.name}' lacks documentation (docstring)",
                        recommended_action=f"Add docstring to {code_item.name}"
                    )
                    gaps.append(gap)

        return gaps

    def _detect_orphaned(self) -> list[Gap]:
        """Detect ORPHANED gaps.

        Returns:
            list[Gap]: List of ORPHANED gaps
        """
        gaps: list[Gap] = []
        code_items = self._get_all_code_items()

        # Get set of matched code item IDs
        matched_ids = {
            match.code_item.id
            for match in self._matches
            if match.code_item is not None
        }

        for code_item in code_items:
            if not code_item.is_public:
                continue

            if code_item.id not in matched_ids:
                # Check if it starts with underscore (private)
                if code_item.name.startswith("_"):
                    continue

                gap = Gap(
                    gap_type="ORPHANED",
                    code_item=code_item.name,
                    code_location=f"{code_item.file_path}:Line {code_item.line_number}",
                    severity="minor",
                    reason=f"Implementation '{code_item.name}' has no corresponding specification in SPEC.md",
                    recommended_action=f"Add specification for {code_item.name} to SPEC.md or remove if unnecessary"
                )
                gaps.append(gap)

        return gaps

    def _get_all_code_items(self) -> list[CodeItem]:
        """Get all code items from all modules.

        Returns:
            list[CodeItem]: All code items
        """
        items: list[CodeItem] = []
        for module in self.code.modules:
            items.extend(module.items)
        return items

    def _mark_downstream_effects(self) -> None:
        """Mark downstream effects of MISSING features."""
        # Find MISSING spec items
        missing_spec_names = {
            gap.spec_item
            for gap in self._gaps
            if gap.gap_type == "MISSING"
        }

        # Find specs that depend on MISSING specs
        for gap in self._gaps:
            if gap.gap_type == "MISSING":
                spec_item = self._find_spec_by_name(gap.spec_item)
                if spec_item:
                    for dep_id in spec_item.depends_on:
                        dep_name = self._find_spec_name_by_id(dep_id)
                        if dep_name in missing_spec_names:
                            gap.downstream_missing = True
                            gap.reason += " (downstream effect: depends on missing feature)"
                            gap.recommended_action += " First implement dependencies."

    def _find_spec_by_name(self, name: str) -> Optional[FeatureItem]:
        """Find a spec item by name.

        Args:
            name: Feature name

        Returns:
            Optional[FeatureItem]: Found spec item or None
        """
        for spec_item in self.spec.feature_items:
            if self._normalize_name(spec_item.name) == self._normalize_name(name):
                return spec_item
        return None

    def _find_spec_name_by_id(self, spec_id: str) -> Optional[str]:
        """Find a spec item name by ID.

        Args:
            spec_id: Feature ID (e.g., "F1")

        Returns:
            Optional[str]: Feature name or None
        """
        for spec_item in self.spec.feature_items:
            if spec_item.id == spec_id:
                return spec_item.name
        return None
