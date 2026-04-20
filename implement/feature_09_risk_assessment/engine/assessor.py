#!/usr/bin/env python3
"""
assessor.py - Risk Assessment Core
[FR-01] Risk identification
[FR-02] Risk evaluation and scoring

Scans project artifacts to identify and evaluate risks across three
dimensions: Technical, Operational, and External.

Usage:
    >>> assessor = RiskAssessor("/path/to/project")
    >>> result = assessor.assess()
"""


import re
from pathlib import Path
from typing import List, Dict
from datetime import datetime

from ..models.risk import Risk, RiskAssessmentResult
from ..models.enums import RiskDimension, RiskLevel


class RiskScorer:
    """
    [FR-02] Risk scoring calculator

    Score = Probability × Impact × Detectability_Factor / 5
    Normalized to 0-1 range
    """

    # Risk pattern signatures by dimension
    TECHNICAL_PATTERNS = {
        "complexity": [r"cyclomatic.*complex", r" cognitive.*load", r"too many.*responsibilities"],
        "dependency": [r"circular.*depend", r"tightly.*coupled", r"spaghetti"],
        "quality": [r"technical.*debt", r"code.*smell", r"dead.*code", r"duplicate.*code"],
        "stability": [r"flaky.*test", r"race.*condition", r"concurren"],
    }

    OPERATIONAL_PATTERNS = {
        "resource": [r"understaffed", r"skill.*gap", r"knowledge.*transfer"],
        "process": [r"manual.*deploy", r"no.*monitoring", r"missing.*documentation"],
        "knowledge": [r"single.*point.*failure", r"bus.*factor", r"onboarding.*slow"],
    }

    EXTERNAL_PATTERNS = {
        "market": [r"competitor.*release", r"technology.*obsolete", r"market.*shift"],
        "regulatory": [r"compliance.*risk", r"legal.*issue", r"gdpr.*violation"],
        "third_party": [r"vendor.*lock.*in", r"api.*deprecation", r"service.*outage"],
    }

    def calculate(self, probability: float, impact: int, detectability: float = 1.0) -> float:
        """[FR-02] 計算風險分數"""
        try:
            prob = max(0.0, min(1.0, float(probability)))
            imp = max(1, min(5, int(impact)))
            det = max(0.5, min(1.0, float(detectability)))
            return round(prob * imp * det / 5, 3)
        except (TypeError, ValueError):
            return 0.3  # Default to MEDIUM

    def assess_probability(self, risk_data: Dict) -> float:
        """[FR-02] 評估發生概率"""
        # Base probability from historical data
        base_prob = risk_data.get("probability", 0.5)

        # Adjust based on risk patterns detected
        patterns_found = risk_data.get("pattern_matches", 0)
        if patterns_found >= 3:
            base_prob = min(1.0, base_prob + 0.2)
        elif patterns_found >= 1:
            base_prob = min(1.0, base_prob + 0.1)

        return base_prob

    def assess_impact(self, dimension: RiskDimension, risk_data: Dict) -> int:
        """[FR-02] 評估影響程度 (1-5)"""
        base_impact = risk_data.get("impact", 3)

        # Dimension-specific impact factors
        if dimension == RiskDimension.TECHNICAL:
            # Technical risks affect system reliability
            if "system_failure" in risk_data.get("type", ""):
                base_impact = max(base_impact, 4)
        elif dimension == RiskDimension.OPERATIONAL:
            # Operational risks affect team productivity
            if "delay" in risk_data.get("type", ""):
                base_impact = max(base_impact, 3)
        elif dimension == RiskDimension.EXTERNAL:
            # External risks may have high uncertainty
            if "regulatory" in risk_data.get("type", ""):
                base_impact = max(base_impact, 4)

        return min(5, base_impact)

    def detect_patterns(self, content: str, dimension: RiskDimension) -> List[str]:
        """[FR-01] 檢測風險模式"""
        patterns = []

        if dimension == RiskDimension.TECHNICAL:
            pattern_dict = self.TECHNICAL_PATTERNS
        elif dimension == RiskDimension.OPERATIONAL:
            pattern_dict = self.OPERATIONAL_PATTERNS
        else:
            pattern_dict = self.EXTERNAL_PATTERNS

        for category, regex_list in pattern_dict.items():
            for pattern in regex_list:
                if re.search(pattern, content, re.IGNORECASE):
                    patterns.append(f"{category}:{pattern}")

        return patterns


class RiskAssessor:
    """
    [FR-01, FR-02] Risk identification and assessment

    Scans project artifacts to identify and evaluate risks.
    """

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.scorer = RiskScorer()
        self._phase_indicators = self._load_phase_indicators()

    def _load_phase_indicators(self) -> Dict[str, List[str]]:
        """載入 Phase 風險指標"""
        return {
            "phase_1": ["unclear requirements", "ambiguous scope", "missing acceptance criteria"],
            "phase_2": ["architecture drift", "missing adr", "circular dependency"],
            "phase_3": ["complexity", "code smell", "missing tests", "dead code"],
            "phase_4": ["flaky test", "test coverage gap", "integration failure"],
            "phase_5": ["deployment failure", "rollback", "config error"],
            "phase_6": ["monitoring gap", "incident response", "knowledge transfer"],
        }

    def assess(self) -> RiskAssessmentResult:
        """
        [FR-01, FR-02] 執行完整風險評估

        Returns:
            RiskAssessmentResult with identified and scored risks
        """
        risks = []

        # 1. Scan code artifacts
        risks.extend(self._scan_code_artifacts())

        # 2. Scan documentation
        risks.extend(self._scan_documentation())

        # 3. Scan phase deliverables
        risks.extend(self._scan_phase_deliverables())

        # 4. Check for known risk patterns
        risks = self._enrich_with_patterns(risks)

        # 5. Calculate scores
        for risk in risks:
            risk._score = self.scorer.calculate(
                risk.probability,
                risk.impact,
                risk.detectability_factor
            )
            # Update level based on score
            risk.level = RiskLevel.from_score(risk.score)

        # Calculate average score
        avg_score = sum(r.score for r in risks) / len(risks) if risks else 0.0

        return RiskAssessmentResult(
            project_name=self.project_root.name,
            phase=self._detect_current_phase(),
            total_risks=len(risks),
            risks=risks,
            average_score=round(avg_score, 3),
            generated_at=datetime.now(),
        )

    def identify_from_code(self, file_path: Path) -> List[Risk]:
        """[FR-01] 從程式碼識別風險"""
        risks = []

        if not file_path.exists():
            return risks

        content = file_path.read_text(errors="ignore")

        # Detect technical debt patterns
        if self.scorer.detect_patterns(content, RiskDimension.TECHNICAL):
            risks.append(Risk(
                title=f"Technical debt in {file_path.name}",
                description=f"Code quality issues detected in {file_path}",
                dimension=RiskDimension.TECHNICAL,
                probability=0.4,
                impact=3,
                evidence=[f"Pattern match in {file_path}"],
            ))

        # Check for missing tests
        if file_path.suffix == ".py" and "test_" not in file_path.name:
            test_file = file_path.parent / f"test_{file_path.name}"
            if not test_file.exists():
                risks.append(Risk(
                    title=f"Missing test coverage for {file_path.name}",
                    description=f"No corresponding test file found",
                    dimension=RiskDimension.TECHNICAL,
                    probability=0.5,
                    impact=2,
                    evidence=[f"Missing: {test_file.name}"],
                ))

        return risks

    def identify_from_documentation(self, doc_path: Path) -> List[Risk]:
        """[FR-01] 從文件識別風險"""
        risks = []

        if not doc_path.exists():
            return risks

        content = doc_path.read_text(errors="ignore")

        # Check for incomplete documentation
        if "TODO" in content or "FIXME" in content:
            todos = re.findall(r"(TODO|FIXME):\s*(.+)", content)
            for _, desc in todos:
                risks.append(Risk(
                    title=f"Outstanding task: {desc[:50]}",
                    description=f"TODO/FIXME found in {doc_path.name}",
                    dimension=RiskDimension.OPERATIONAL,
                    probability=0.3,
                    impact=2,
                    evidence=[f"TODO in {doc_path.name}: {desc}"],
                ))

        return risks

    def _scan_code_artifacts(self) -> List[Risk]:
        """[FR-01] 掃描程式碼構件"""
        risks = []

        src_dir = self.project_root / "src"
        if src_dir.exists():
            for py_file in src_dir.rglob("*.py"):
                risks.extend(self.identify_from_code(py_file))

        return risks

    def _scan_documentation(self) -> List[Risk]:
        """[FR-01] 掃描文件"""
        risks = []

        docs_dir = self.project_root / "docs"
        if docs_dir.exists():
            for doc_file in docs_dir.rglob("*.md"):
                risks.extend(self.identify_from_documentation(doc_file))

        # Check for required docs
        required_docs = ["SRS.md", "SAD.md", "RISK_ASSESSMENT.md"]
        for doc in required_docs:
            if not (docs_dir / doc).exists() and not (self.project_root / doc).exists():
                risks.append(Risk(
                    title=f"Missing required document: {doc}",
                    description=f"{doc} is required by methodology-v2 constitution",
                    dimension=RiskDimension.OPERATIONAL,
                    probability=0.6,
                    impact=3,
                    evidence=[f"File not found: {doc}"],
                ))

        return risks

    def _scan_phase_deliverables(self) -> List[Risk]:
        """[FR-01] 掃描 Phase 交付物"""
        risks = []

        # Check each phase directory
        for phase_num in range(1, 8):
            phase_dir = self.project_root / f"0{phase_num}-"
            if not phase_dir.exists():
                continue

            phase_indicators = self._phase_indicators.get(f"phase_{phase_num}", [])

            # Scan phase files for indicators
            for file in phase_dir.rglob("*"):
                if not file.is_file():
                    continue

                content = file.read_text(errors="ignore")
                for indicator in phase_indicators:
                    if indicator.lower() in content.lower():
                        risks.append(Risk(
                            title=f"Phase {phase_num} risk: {indicator}",
                            description=f"Risk indicator '{indicator}' detected in {file.name}",
                            dimension=RiskDimension.OPERATIONAL,
                            probability=0.4,
                            impact=3,
                            evidence=[f"Phase {phase_num}: {file.name}"],
                        ))

        return risks

    def _enrich_with_patterns(self, risks: List[Risk]) -> List[Risk]:
        """[FR-02] 用風險模式強化風險評估"""
        for risk in risks:
            # Scan project for matching patterns
            content_parts = []

            # Collect content from relevant areas
            if risk.dimension == RiskDimension.TECHNICAL:
                scan_paths = [self.project_root / "src"]
            elif risk.dimension == RiskDimension.OPERATIONAL:
                scan_paths = [self.project_root / "docs", self.project_root / "scripts"]
            else:
                scan_paths = [self.project_root]

            for scan_path in scan_paths:
                if scan_path.exists():
                    for f in scan_path.rglob("*"):
                        if f.is_file():
                            try:
                                content_parts.append(f.read_text(errors="ignore")[:500])
                            except (OSError, UnicodeDecodeError):
                                pass

            combined = " ".join(content_parts)
            patterns = self.scorer.detect_patterns(combined, risk.dimension)
            risk.evidence.extend([f"pattern:{p}" for p in patterns])

            # Update probability based on pattern matches
            risk.probability = self.scorer.assess_probability({
                "probability": risk.probability,
                "pattern_matches": len(patterns),
            })

        return risks

    def _detect_current_phase(self) -> int:
        """檢測當前 Phase"""
        state_file = self.project_root / ".methodology" / "state.json"
        if state_file.exists():
            try:
                import json
                state = json.loads(state_file.read_text())
                return state.get("current_phase", 1)
            except (OSError, UnicodeDecodeError):
                pass

        # Fallback: check for highest phase directory
        for phase in range(7, 0, -1):
            if (self.project_root / f"0{phase}-").exists():
                return phase

        return 1
