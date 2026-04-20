"""constitution/__init__.py
[FR-01, FR-02, FR-03, FR-04] Constitution compliance checker

Verifies risk assessment meets Constitution standards by checking:
- Required files (RISK_ASSESSMENT.md, RISK_REGISTER.md)
- Required sections in assessment documents
- Mitigation plan completeness
- Risk register format compliance
- Status tracking consistency

Usage:
    >>> from constitution.risk_assessment_checker import RiskAssessmentConstitutionChecker
    >>> checker = RiskAssessmentConstitutionChecker("/path/to/project")
    >>> result = checker.check()
    >>> print(f"Score: {result.score:.1f}%")
"""

__all__ = []
