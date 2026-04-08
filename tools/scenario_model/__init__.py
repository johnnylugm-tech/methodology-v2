"""
Scenario Model - Context Simulator for TCO/ROI Analysis.

Provides source-tagged cost estimation without fictional numbers.
Each numeric value is tagged with its source: historical_data, user_input, or assumption.
"""

from tools.scenario_model.scenario_model import ScenarioModel

__all__ = ["ScenarioModel"]
