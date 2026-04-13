"""
Phase Paths - Centralized path definitions for all Phase artifacts
===============================================================

All Framework tools should import from here instead of hardcoding paths.
This ensures Plan Doc paths and Tool paths are always consistent.

Phase 5 Plan WHERE: 05-verify/
Phase 5 actual outputs:
- BASELINE.md -> 05-verify/BASELINE.md
- TEST_RESULTS.md -> 04-testing/TEST_RESULTS.md  
- VERIFICATION_REPORT.md -> 05-verify/VERIFICATION_REPORT.md
"""

from pathlib import Path
from typing import Dict, List, Tuple

# Phase N outputs - all supported paths (Plan + alternatives)
# Any of these paths existing satisfies the requirement
PHASE_ARTIFACT_PATHS = {
    5: {  # Phase 5 (SYSTEM_TEST)
        "BASELINE.md": [
            "05-verify/BASELINE.md",      # Phase5_Plan WHERE
            "05-baseline/BASELINE.md",     # Alternative
            "docs/05-baseline/BASELINE.md",
        ],
        "TEST_RESULTS.md": [
            "04-testing/TEST_RESULTS.md",  # Phase5_Plan WHERE
            "05-verify/TEST_RESULTS.md",   # Alternative
            "docs/04-testing/TEST_RESULTS.md",
        ],
        "VERIFICATION_REPORT.md": [
            "05-verify/VERIFICATION_REPORT.md",  # Phase5_Plan WHERE
            "docs/05-verify/VERIFICATION_REPORT.md",
        ],
        "TEST_PLAN.md": [
            "04-testing/TEST_PLAN.md",
            "docs/04-testing/TEST_PLAN.md",
        ],
    },
    6: {  # Phase 6 (QUALITY)
        "QUALITY_REPORT.md": [
            "06-quality/QUALITY_REPORT.md",  # Phase6_Plan WHERE
            "docs/06-quality/QUALITY_REPORT.md",
        ],
        "MONITORING_PLAN.md": [
            "06-quality/MONITORING_PLAN.md",
            "docs/06-quality/MONITORING_PLAN.md",
        ],
    },
    7: {  # Phase 7 (RISK)
        "RISK_ASSESSMENT.md": [
            "07-risk/RISK_ASSESSMENT.md",   # Phase7_Plan WHERE
            "docs/07-risk/RISK_ASSESSMENT.md",
        ],
        "RISK_REGISTER.md": [
            "07-risk/RISK_REGISTER.md",
            "docs/07-risk/RISK_REGISTER.md",
        ],
    },
    8: {  # Phase 8 (DEPLOYMENT)
        "CONFIG_RECORDS.md": [
            "08-config/CONFIG_RECORDS.md",   # Phase8_Plan WHERE
            "docs/08-config/CONFIG_RECORDS.md",
        ],
        "requirements.lock": [
            "08-config/requirements.lock",
            "docs/08-config/requirements.lock",
        ],
    },
}


def check_artifact_exists(project_path: Path, phase: int, artifact: str) -> Tuple[bool, str]:
    """
    Check if a Phase artifact exists at any of the supported paths.
    
    Returns: (exists: bool, found_path: str or None)
    """
    if phase not in PHASE_ARTIFACT_PATHS:
        return False, None
    
    if artifact not in PHASE_ARTIFACT_PATHS[phase]:
        return False, None
    
    for path_str in PHASE_ARTIFACT_PATHS[phase][artifact]:
        path = project_path / path_str
        if path.exists():
            return True, path_str
    
    return False, None


def get_all_phase_artifacts(phase: int) -> List[str]:
    """Get all artifact names for a given phase."""
    return list(PHASE_ARTIFACT_PATHS.get(phase, {}).keys())


def check_phase_artifacts(project_path: Path, phase: int) -> Dict[str, Tuple[bool, str]]:
    """
    Check all artifacts for a phase.
    
    Returns: {artifact: (exists, found_path_or_None)}
    """
    results = {}
    for artifact in get_all_phase_artifacts(phase):
        results[artifact] = check_artifact_exists(project_path, phase, artifact)
    return results
