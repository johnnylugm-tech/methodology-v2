"""Feature #8 Gap Detector — SPEC.md Parser.

This module provides functionality to parse SPEC.md files and extract
structured feature information.
"""

from gap_detector.parser import (
    SpecParser,
    ParsedSpec,
    FeatureItem,
    SpecMetadata,
    ParseStats,
    ParseError,
    SpecParseError,
)

from gap_detector.scanner import (
    CodeScanner,
    ScannedCode,
    CodeItem,
    CodeFile,
    ScanStats,
    ScanError,
    ScanErrorRecord,
)

from gap_detector.detector import (
    GapDetector,
    Gap,
    GapSummary,
    Match,
)

from gap_detector.reporter import (
    GapReporter,
    ReportPaths,
    GapReportJSON,
)

__all__ = [
    # Parser
    "SpecParser",
    "ParsedSpec",
    "FeatureItem",
    "SpecMetadata",
    "ParseStats",
    "ParseError",
    "SpecParseError",
    # Scanner
    "CodeScanner",
    "ScannedCode",
    "CodeItem",
    "CodeFile",
    "ScanStats",
    "ScanError",
    "ScanErrorRecord",
    # Detector
    "GapDetector",
    "Gap",
    "GapSummary",
    "Match",
    # Reporter
    "GapReporter",
    "ReportPaths",
    "GapReportJSON",
]
