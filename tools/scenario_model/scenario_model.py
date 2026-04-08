"""
Scenario Model - Context Simulator for TCO/Cost Analysis.

Replaces the TCO Calculator by providing source-tagged cost estimates
without generating fictional ROI numbers. Each value is tagged with:
- historical_data: from FeedbackStore or Git history
- user_input: explicitly provided by user
- assumption: unverified estimate

Cost ranges are provided per scenario (conservative/moderate/aggressive)
instead of single-point estimates.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# Optional FeedbackStore import
try:
    from core.feedback.feedback import FeedbackStore

    HAS_FEEDBACK = True
except ImportError:
    HAS_FEEDBACK = False
    FeedbackStore = None

from tools.scenario_model.data_sources import (
    SourceTag,
    get_historical_defects,
    get_phase_completion_times,
    get_team_velocity,
)


class ScenarioModel:
    """
    Context-aware scenario model for cost estimation.

    Provides source-tagged cost ranges for different scenarios
    without generating fictional ROI numbers.

    Usage:
        model = ScenarioModel("/path/to/project", feedback_store)
        results = model.calculate(
            user_inputs={"team_size": 5, "hourly_rate": 100},
            scenarios={"conservative": {}, "moderate": {}, "aggressive": {}}
        )
        report = model.generate_report(results)
    """

    # Source tag constants
    HISTORICAL = "historical_data"
    USER_INPUT = "user_input"
    ASSUMPTION = "assumption"

    def __init__(
        self,
        project_path: str | Path,
        feedback_store: FeedbackStore | None = None,
    ) -> None:
        self.project_path = Path(project_path)
        self.feedback_store = feedback_store

        # Template for report
        self._template_path = Path(__file__).parent / "templates" / "scenario_report.md"
        self._report_template = self._load_template()

    def _load_template(self) -> str:
        """Load report template from file."""
        if self._template_path.exists():
            return self._template_path.read_text(encoding="utf-8")
        return self._get_default_template()

    def _get_default_template(self) -> str:
        """Fallback template if file not found."""
        return """# Scenario Analysis Report

**Generated:** {timestamp}
**Project:** {project_name}

---

## Source Tags Legend

- `[source: historical_data]` — Derived from actual project data
- `[source: user_input]` — Explicitly provided by user
- `[source: assumption]` — Unverified estimate

---

## Confidence Level: {confidence}

{confidence_warning}

---

## User Inputs

{user_inputs_table}

---

## Scenario Analysis

{scenario_tables}

---

## Disclaimer

{disclaimer}
"""

    def calculate(
        self,
        user_inputs: dict[str, Any],
        scenarios: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Calculate cost ranges for each scenario.

        Args:
            user_inputs: Dict with keys like team_size, hourly_rate, problem_count
            scenarios: Dict with scenario names as keys and config dicts as values.
                      Supported configs: defect_reduction_range, time_savings_range

        Returns:
            Dict with calculation results, each value tagged with source
        """
        # Tag all user inputs
        tagged_inputs = self._tag_sources(user_inputs)

        # Fetch historical data
        historical_defects = get_historical_defects(self.feedback_store, self.project_path)
        historical_velocity = get_team_velocity(self.feedback_store, self.project_path)
        historical_phase_time = get_phase_completion_times(self.project_path)

        # Build tagged parameters
        params: dict[str, SourceTag] = {
            "team_size": tagged_inputs.get("team_size", SourceTag(value=None, source=self.ASSUMPTION, detail="Not provided")),
            "hourly_rate": tagged_inputs.get("hourly_rate", SourceTag(value=None, source=self.ASSUMPTION, detail="Not provided")),
            "problem_count": tagged_inputs.get("problem_count", SourceTag(value=None, source=self.ASSUMPTION, detail="Not provided")),
            "historical_defects": historical_defects,
            "historical_velocity": historical_velocity,
            "historical_phase_time": historical_phase_time,
        }

        # Calculate scenario ranges
        scenario_results: dict[str, dict[str, Any]] = {}

        for name, config in scenarios.items():
            scenario_results[name] = self._calculate_scenario(params, config)

        # Build confidence score
        all_tags = {k: v["source"] for k, v in params.items() if v.get("source")}
        confidence = self._calc_confidence(all_tags)

        return {
            "project_name": self.project_path.name,
            "project_path": str(self.project_path),
            "timestamp": self._get_timestamp(),
            "user_inputs": tagged_inputs,
            "params": params,
            "scenarios": scenario_results,
            "confidence": confidence,
        }

    def _tag_sources(self, params: dict[str, Any]) -> dict[str, SourceTag]:
        """Tag user inputs with source."""
        result: dict[str, SourceTag] = {}
        for key, value in params.items():
            if value is None:
                result[key] = SourceTag(value=None, source=self.ASSUMPTION, detail="Not provided")
            elif isinstance(value, (int, float)):
                result[key] = SourceTag(
                    value=float(value),
                    source=self.USER_INPUT,
                    detail=f"User provided: {value}",
                )
            else:
                result[key] = SourceTag(
                    value=None,
                    source=self.USER_INPUT,
                    detail=f"User provided non-numeric: {value}",
                )
        return result

    def _calculate_scenario(
        self,
        params: dict[str, SourceTag],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Calculate cost range for a single scenario.

        Returns ranges (min, max) rather than single values.
        All values are source-tagged.
        """
        team_size = params.get("team_size", SourceTag(value=None, source=self.ASSUMPTION, detail="default"))
        hourly_rate = params.get("hourly_rate", SourceTag(value=None, source=self.ASSUMPTION, detail="default"))
        problem_count = params.get("problem_count", SourceTag(value=None, source=self.ASSUMPTION, detail="default"))
        hist_defects = params.get("historical_defects", SourceTag(value=None, source=self.ASSUMPTION, detail="default"))
        hist_velocity = params.get("historical_velocity", SourceTag(value=None, source=self.ASSUMPTION, detail="default"))
        hist_phase_time = params.get("historical_phase_time", SourceTag(value=None, source=self.ASSUMPTION, detail="default"))

        # Calculate cost range based on available data
        # If we have historical defect data, use it as baseline
        # Otherwise, use user-provided problem_count

        if hist_defects["value"] is not None and problem_count["value"] is not None:
            base_issues = problem_count["value"]  # User count takes precedence if provided
            issues_source = problem_count["source"]
        elif hist_defects["value"] is not None:
            base_issues = hist_defects["value"]
            issues_source = hist_defects["source"]
        elif problem_count["value"] is not None:
            base_issues = problem_count["value"]
            issues_source = problem_count["source"]
        else:
            base_issues = None
            issues_source = self.ASSUMPTION

        # Defect reduction range from config (e.g., 0.1 to 0.3 for 10%-30% reduction)
        reduction_min = config.get("defect_reduction_min", 0.1)
        reduction_max = config.get("defect_reduction_max", 0.3)
        reduction_source = self.USER_INPUT if "defect_reduction_min" in config else self.ASSUMPTION

        # Time savings range (hours per issue)
        time_savings_min = config.get("time_savings_min", 0.5)  # 30 min
        time_savings_max = config.get("time_savings_max", 2.0)  # 2 hours
        time_savings_source = self.USER_INPUT if "time_savings_min" in config else self.ASSUMPTION

        # Calculate cost range if we have the required data
        if (
            base_issues is not None
            and team_size["value"] is not None
            and hourly_rate["value"] is not None
        ):
            # Conservative: low reduction, low time savings
            cost_min = (
                base_issues
                * reduction_min
                * time_savings_min
                * team_size["value"]
                * hourly_rate["value"]
            )
            # Aggressive within scenario: high reduction, high time savings
            cost_max = (
                base_issues
                * reduction_max
                * time_savings_max
                * team_size["value"]
                * hourly_rate["value"]
            )
            cost_source = issues_source
        else:
            cost_min = None
            cost_max = None
            cost_source = self.ASSUMPTION

        # Hours saved range (per-engineer per-issue, not team-total)
        if base_issues is not None:
            hours_min = base_issues * reduction_min * time_savings_min
            hours_max = base_issues * reduction_max * time_savings_max
            hours_source = issues_source
        else:
            hours_min = None
            hours_max = None
            hours_source = self.ASSUMPTION

        return {
            "cost_range": {
                "min": {"value": cost_min, "source": cost_source},
                "max": {"value": cost_max, "source": cost_source},
            },
            "hours_saved_range": {
                "min": {"value": hours_min, "source": hours_source},
                "max": {"value": hours_max, "source": hours_source},
            },
            "defect_reduction_range": {
                "min": {"value": reduction_min, "source": reduction_source},
                "max": {"value": reduction_max, "source": reduction_source},
            },
            "time_per_issue_range": {
                "min": {"value": time_savings_min, "source": time_savings_source},
                "max": {"value": time_savings_max, "source": time_savings_source},
            },
            "params_used": {
                "base_issues": {"value": base_issues, "source": issues_source},
                "team_size": team_size,
                "hourly_rate": hourly_rate,
                "historical_defects": hist_defects,
                "historical_velocity": hist_velocity,
                "historical_phase_time": hist_phase_time,
            },
        }

    def _calc_confidence(self, source_tags: dict[str, str]) -> dict[str, Any]:
        """
        Calculate confidence level based on source tag distribution.

        Returns confidence score (0-100) and level string.
        """
        if not source_tags:
            return {
                "score": 0,
                "level": "none",
                "warning": "No data available - all values are assumptions",
            }

        total = len(source_tags)
        assumption_count = sum(1 for v in source_tags.values() if v == self.ASSUMPTION)
        historical_count = sum(1 for v in source_tags.values() if v == self.HISTORICAL)

        assumption_ratio = assumption_count / total
        historical_ratio = historical_count / total

        # Score based on proportion of real data
        score = int(historical_ratio * 100 + (1 - assumption_ratio) * 50)
        score = min(100, max(0, score))

        if score >= 80:
            level = "high"
            warning = ""
        elif score >= 50:
            level = "medium"
            warning = "Medium confidence: Report contains assumptions that should be verified with project data."
        elif score >= 20:
            level = "low"
            warning = "Low confidence: Most values are based on assumptions. Supplement with actual project metrics."
        else:
            level = "very_low"
            warning = "Very low confidence: Report is primarily based on unverified assumptions. Do not use for major decisions without data validation."

        return {
            "score": score,
            "level": level,
            "warning": warning,
            "details": {
                "total_params": total,
                "from_historical": historical_count,
                "from_user_input": sum(1 for v in source_tags.values() if v == self.USER_INPUT),
                "from_assumption": assumption_count,
            },
        }

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")

    def generate_report(self, results: dict[str, Any]) -> str:
        """
        Generate formatted report from calculation results.

        Each numeric value is tagged with its source.
        """
        confidence_data = results.get("confidence", {})

        # Format user inputs table
        user_inputs_lines = []
        for key, tagged in results.get("user_inputs", {}).items():
            val = tagged.get("value")
            src = tagged.get("source", "unknown")
            detail = tagged.get("detail", "")
            val_str = f"{val}" if val is not None else "N/A"
            user_inputs_lines.append(f"| {key} | {val_str} | `{src}` | {detail} |")

        user_inputs_table = "\n".join(user_inputs_lines) if user_inputs_lines else "| (none) | N/A | - | - |"

        # Format scenario tables
        scenario_tables = []
        for name, scenario in results.get("scenarios", {}).items():
            scenario_tables.append(f"### {name.capitalize()} Scenario\n")

            # Cost range
            cost_range = scenario.get("cost_range", {})
            cost_min = cost_range.get("min", {})
            cost_max = cost_range.get("max", {})

            if cost_min.get("value") is not None and cost_max.get("value") is not None:
                scenario_tables.append(
                    f"- **Cost Range:** ${cost_min['value']:,.0f} – ${cost_max['value']:,.0f} "
                    f"[source: {cost_min.get('source', 'unknown')}]"
                )
            else:
                scenario_tables.append("- **Cost Range:** Unable to calculate (insufficient data)")

            # Hours saved
            hours_range = scenario.get("hours_saved_range", {})
            hours_min = hours_range.get("min", {})
            hours_max = hours_range.get("max", {})

            if hours_min.get("value") is not None and hours_max.get("value") is not None:
                scenario_tables.append(
                    f"- **Hours Saved:** {hours_min['value']:,.0f} – {hours_max['value']:,.0f} hours "
                    f"[source: {hours_min.get('source', 'unknown')}]"
                )
            else:
                scenario_tables.append("- **Hours Saved:** Unable to calculate (insufficient data)")

            # Reduction range
            red_range = scenario.get("defect_reduction_range", {})
            red_min = red_range.get("min", {})
            red_max = red_range.get("max", {})
            if red_min.get("value") is not None and red_max.get("value") is not None:
                scenario_tables.append(
                    f"- **Defect Reduction:** {red_min['value']*100:.0f}% – {red_max['value']*100:.0f}% "
                    f"[source: {red_min.get('source', 'unknown')}]"
                )

            scenario_tables.append("")

        scenario_tables_str = "\n".join(scenario_tables)

        # Confidence
        conf_score = confidence_data.get("score", 0)
        conf_level = confidence_data.get("level", "unknown")
        conf_warning = confidence_data.get("warning", "")

        confidence_str = f"{conf_score}% ({conf_level})"

        # Disclaimer
        disclaimer = (
            "**Disclaimer:** This report contains estimates based on available data. "
            "Values tagged as [assumption] are unverified and should not be used for budgeting "
            "or major decisions without validation. Actual costs and savings may vary significantly. "
            "This tool does not calculate ROI — it provides cost ranges for scenario comparison only."
        )

        # Build report
        report = self._report_template.format(
            timestamp=results.get("timestamp", "N/A"),
            project_name=results.get("project_name", "Unknown"),
            confidence=confidence_str,
            confidence_warning=conf_warning,
            user_inputs_table=user_inputs_table,
            scenario_tables=scenario_tables_str,
            disclaimer=disclaimer,
        )

        return report
