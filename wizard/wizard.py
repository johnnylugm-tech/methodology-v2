"""
Setup Wizard for methodology-v2

Interactive wizard to help new users set up their first agent project.
"""

import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class UseCase(Enum):
    CUSTOMER_SERVICE = "customer_service"
    CODING = "coding"
    RESEARCH = "research"
    DATA_ANALYSIS = "data_analysis"
    CUSTOM = "custom"


class BudgetLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class AgentConfig:
    """Agent configuration"""
    name: str
    role: str
    model: str = "gpt-4o-mini"
    tools: List[str] = field(default_factory=list)


@dataclass
class ProjectConfig:
    """Project configuration"""
    name: str
    use_case: UseCase
    agents: List[AgentConfig] = field(default_factory=list)
    workflow: str = "sequential"
    guardrails: List[str] = field(default_factory=list)
    integrations: Dict[str, str] = field(default_factory=dict)
    budget: BudgetLevel = BudgetLevel.MEDIUM


TEMPLATES = {
    UseCase.CUSTOMER_SERVICE: {
        "name": "customer_service_bot",
        "agents": [
            AgentConfig("classifier", "intent_classification", "gpt-4o-mini"),
            AgentConfig("responder", "generate_response", "gpt-4o"),
            AgentConfig("escalator", "human_handoff", "gpt-4o"),
        ],
        "workflow": "sequential",
        "guardrails": ["sentiment", "pii_filter", "content_filter"],
    },
    UseCase.CODING: {
        "name": "code_review_agent",
        "agents": [
            AgentConfig("coder", "generate_code", "claude-3.5-sonnet"),
            AgentConfig("reviewer", "code_review", "claude-3.5-sonnet"),
            AgentConfig("tester", "generate_tests", "gpt-4o-mini"),
        ],
        "workflow": "sequential",
        "guardrails": ["security_scan", "syntax_check"],
    },
    UseCase.RESEARCH: {
        "name": "research_assistant",
        "agents": [
            AgentConfig("researcher", "gather_information", "gpt-4o"),
            AgentConfig("synthesizer", "synthesize_findings", "gpt-4o"),
        ],
        "workflow": "sequential",
        "guardrails": ["source_verification"],
    },
    UseCase.DATA_ANALYSIS: {
        "name": "data_analysis_pipeline",
        "agents": [
            AgentConfig("processor", "process_data", "gpt-4o-mini"),
            AgentConfig("analyzer", "analyze_results", "gpt-4o"),
            AgentConfig("reporter", "generate_report", "gpt-4o-mini"),
        ],
        "workflow": "sequential",
        "guardrails": ["data_validation"],
    },
}


class SetupWizard:
    """
    Interactive setup wizard for methodology-v2.
    
    Usage:
        wizard = SetupWizard()
        wizard.run()
    """
    
    def __init__(self, interactive: bool = True):
        self.interactive = interactive
        self.config: Optional[ProjectConfig] = None
    
    def run(self):
        """Run interactive wizard"""
        print("\n" + "="*50)
        print("Welcome to methodology-v2 Setup Wizard!")
        print("="*50 + "\n")
        
        # Step 1: Select use case
        use_case = self._ask_use_case()
        
        # Step 2: Get project name
        project_name = self._ask_project_name()
        
        # Step 3: Configure budget
        budget = self._ask_budget()
        
        # Step 4: Select integrations
        integrations = self._ask_integrations()
        
        # Generate config
        self.config = self._generate_config(
            project_name, use_case, budget, integrations
        )
        
        # Generate project
        self._generate_project()
        
        print("\n✅ Setup complete!")
        print(f"Project: {self.config.name}")
        print(f"Agents: {len(self.config.agents)}")
        print(f"Workflow: {self.config.workflow}")
    
    def _ask_use_case(self) -> UseCase:
        """Ask user to select use case"""
        print("What do you want to build?")
        print("  [1] Customer Service Agent")
        print("  [2] Code Review Agent")
        print("  [3] Research Assistant")
        print("  [4] Data Analysis Pipeline")
        print("  [5] Custom Configuration")
        
        if not self.interactive:
            return UseCase.CUSTOMER_SERVICE
        
        while True:
            try:
                choice = int(input("\nEnter number: "))
                if choice == 1:
                    return UseCase.CUSTOMER_SERVICE
                elif choice == 2:
                    return UseCase.CODING
                elif choice == 3:
                    return UseCase.RESEARCH
                elif choice == 4:
                    return UseCase.DATA_ANALYSIS
                elif choice == 5:
                    return UseCase.CUSTOM
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a number.")
    
    def _ask_project_name(self) -> str:
        """Ask for project name"""
        if not self.interactive:
            return "my_project"
        
        name = input("Project name [my_project]: ")
        return name or "my_project"
    
    def _ask_budget(self) -> BudgetLevel:
        """Ask for budget level"""
        print("\nSelect budget level:")
        print("  [1] Low (Cost-optimized)")
        print("  [2] Medium (Balanced)")
        print("  [3] High (Best quality)")
        
        if not self.interactive:
            return BudgetLevel.MEDIUM
        
        while True:
            try:
                choice = int(input("\nEnter number: "))
                if choice == 1:
                    return BudgetLevel.LOW
                elif choice == 2:
                    return BudgetLevel.MEDIUM
                elif choice == 3:
                    return BudgetLevel.HIGH
                else:
                    print("Invalid choice.")
            except ValueError:
                print("Please enter a number.")
    
    def _ask_integrations(self) -> Dict[str, str]:
        """Ask for integrations"""
        integrations = {}
        
        if not self.interactive:
            return integrations
        
        print("\nSelect integrations (comma-separated, or press Enter to skip):")
        print("  slack, discord, notion, github, gmail, database")
        
        choice = input("Integrations: ").strip().lower()
        
        if choice:
            for item in choice.split(","):
                integrations[item.strip()] = ""
        
        return integrations
    
    def _generate_config(
        self, 
        name: str, 
        use_case: UseCase,
        budget: BudgetLevel,
        integrations: Dict[str, str]
    ) -> ProjectConfig:
        """Generate project configuration"""
        template = TEMPLATES.get(use_case)
        
        if template:
            agents = [AgentConfig(**a) if isinstance(a, dict) else a 
                      for a in template.get("agents", [])]
            guardrails = template.get("guardrails", [])
        else:
            agents = []
            guardrails = []
        
        return ProjectConfig(
            name=name,
            use_case=use_case,
            agents=agents,
            guardrails=guardrails,
            integrations=integrations,
            budget=budget,
        )
    
    def _generate_project(self):
        """Generate project files"""
        if not self.config:
            return
        
        # Create project directory
        project_dir = f"./{self.config.name}"
        os.makedirs(project_dir, exist_ok=True)
        
        # Generate config.yaml
        config_content = self._generate_config_yaml()
        with open(f"{project_dir}/config.yaml", "w") as f:
            f.write(config_content)
        
        # Generate main.py
        main_content = self._generate_main_py()
        with open(f"{project_dir}/main.py", "w") as f:
            f.write(main_content)
        
        # Generate requirements.txt
        requirements = self._generate_requirements()
        with open(f"{project_dir}/requirements.txt", "w") as f:
            f.write(requirements)
        
        # Generate README.md
        readme = self._generate_readme()
        with open(f"{project_dir}/README.md", "w") as f:
            f.write(readme)
        
        print(f"\n📁 Generated files in {project_dir}/")
    
    def _generate_config_yaml(self) -> str:
        """Generate config.yaml"""
        agents = []
        for agent in self.config.agents:
            agents.append(f"""  - name: {agent.name}
    role: {agent.role}
    model: {agent.model}""")
        
        integrations = ""
        for name, value in self.config.integrations.items():
            integrations += f"  {name}: {value}\n"
        
        return f"""project:
  name: {self.config.name}
  use_case: {self.config.use_case.value}
  budget: {self.config.budget.value}

agents:
{chr(10).join(agents)}

workflow: {self.config.workflow}

guardrails:
{chr(10).join(f"  - {g}" for g in self.config.guardrails)}

integrations:
{integrations or "  # No integrations configured"}
"""
    
    def _generate_main_py(self) -> str:
        """Generate main.py"""
        return f'''"""Main project file for {self.config.name}"""

import sys
sys.path.insert(0, '/workspace/methodology-v2')

from methodology import Crew, Agent

# Define agents
agents = [
    Agent(name="{self.config.agents[0].name if self.config.agents else 'agent1'}")
]

# Create crew
crew = Crew(
    agents=agents,
    process="{self.config.workflow}"
)

# Run
if __name__ == "__main__":
    result = crew.kickoff()
    print(result)
'''
    
    def _generate_requirements(self) -> str:
        """Generate requirements.txt"""
        return f"""methodology-v2
openai>=1.0.0
anthropic>=0.25.0
"""
    
    def _generate_readme(self) -> str:
        """Generate README.md"""
        return f"""# {self.config.name}

Generated by methodology-v2 Setup Wizard

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

## Project Structure

- `main.py` - Main entry point
- `config.yaml` - Configuration

## Agents

{chr(10).join(f"- {a.name}: {a.role}" for a in self.config.agents)}
"""
    
    def quick_start(self, template: str) -> ProjectConfig:
        """Quick start with predefined template"""
        use_case_map = {
            "customer_service": UseCase.CUSTOMER_SERVICE,
            "coding": UseCase.CODING,
            "research": UseCase.RESEARCH,
            "data_analysis": UseCase.DATA_ANALYSIS,
        }
        
        use_case = use_case_map.get(template.lower(), UseCase.CUSTOMER_SERVICE)
        
        self.config = self._generate_config(
            f"my_{template}_project",
            use_case,
            BudgetLevel.MEDIUM,
            {}
        )
        
        return self.config
    
    def from_template(self, template_name: str) -> ProjectConfig:
        """Create config from template"""
        return self.quick_start(template_name)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Methodology-v2 Setup Wizard")
    parser.add_argument("--template", help="Quick start template")
    parser.add_argument("--non-interactive", action="store_true", help="Non-interactive mode")
    
    args = parser.parse_args()
    
    wizard = SetupWizard(interactive=not args.non_interactive)
    
    if args.template:
        config = wizard.quick_start(args.template)
        wizard._generate_project()
        print(f"✅ Created project from template: {args.template}")
    else:
        wizard.run()
