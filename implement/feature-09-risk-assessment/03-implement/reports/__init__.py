"""reports/__init__.py
[FR-04] Risk Assessment Report Generators

Generates human-readable assessment reports for Phase 6/7:
- RiskAssessmentReportGenerator: Creates RISK_ASSESSMENT.md and RISK_REGISTER.md
- DecisionGateReportGenerator: Creates Phase 7 Decision Gate reports

Usage:
    >>> from reports.assessor_report import RiskAssessmentReportGenerator
    >>> gen = RiskAssessmentReportGenerator("/path/to/project")
    >>> gen.generate(result)
"""
