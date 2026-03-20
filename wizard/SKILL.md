---
name: wizard
description: Guided setup wizard for methodology-v2. Use when: (1) New users setting up their first agent project, (2) Developers who want step-by-step guidance, (3) Teams onboarding new members. Provides interactive wizard, template selection, and quick start templates.
---

# Setup Wizard

Guided setup wizard for methodology-v2 to reduce learning curve.

## Quick Start

```python
from wizard import SetupWizard

wizard = SetupWizard()

# Start interactive setup
wizard.run()

# Or use non-interactive mode
wizard.run_interactive=False
config = wizard.quick_start("customer_service")
```

## Features

### 1. Interactive Wizard

```python
wizard = SetupWizard()

# Step 1: Select use case
wizard.ask_use_case()
# Options: customer_service, coding, research, data_analysis, custom

# Step 2: Configure agents
wizard.ask_agent_config()

# Step 3: Set up integrations
wizard.ask_integrations()

# Step 4: Generate project
project = wizard.generate_project()
```

### 2. Quick Start Templates

| Template | Use Case | Agents |
|----------|----------|--------|
| `customer_service` | FAQ, ticket routing | classifier, responder, escalator |
| `coding` | Code review, debugging | coder, reviewer, tester |
| `research` | Market research, competitive analysis | researcher, synthesizer |
| `data_analysis` | Data processing, reporting | processor, analyst, reporter |

### 3. Non-Interactive Mode

```python
wizard = SetupWizard()

# Use predefined template
config = wizard.from_template("customer_service")

# Customize
config.set_budget("low")
config.add_agent("custom_agent", role="specialist")

# Generate
wizard.generate(config)
```

## Guided Workflow

### Step 1: Use Case Selection

```
╔══════════════════════════════════════╗
║     Welcome to methodology-v2!      ║
╠══════════════════════════════════════╣
║  What do you want to build?          ║
║                                       ║
║  [1] Customer Service Agent          ║
║  [2] Code Review Agent               ║
║  [3] Research Assistant               ║
║  [4] Data Analysis Pipeline          ║
║  [5] Custom Configuration            ║
║                                       ║
║  Enter number: _                     ║
╚══════════════════════════════════════╝
```

### Step 2: Configuration

Based on selection, wizard asks relevant questions:
- Team size
- Budget constraints
- Integration needs
- Security requirements

### Step 3: Project Generation

Wizard generates:
- `project.py` - Main project file
- `agents.py` - Agent configurations
- `config.yaml` - Settings
- `requirements.txt` - Dependencies
- `README.md` - Documentation

## Template Library

### Customer Service Template

```python
{
    "name": "customer_service_bot",
    "agents": [
        {
            "name": "classifier",
            "role": "intent_classification",
            "model": "gpt-4o-mini"
        },
        {
            "name": "responder", 
            "role": "generate_response",
            "model": "gpt-4o"
        },
        {
            "name": "escalator",
            "role": "human_handoff",
            "model": "gpt-4o"
        }
    ],
    "workflow": "sequential",
    "guardrails": ["sentiment", "pii_filter", "content_filter"]
}
```

### Coding Template

```python
{
    "name": "code_review_agent",
    "agents": [
        {
            "name": "coder",
            "role": "generate_code",
            "model": "claude-3.5-sonnet"
        },
        {
            "name": "reviewer",
            "role": "code_review",
            "model": "claude-3.5-sonnet"
        },
        {
            "name": "tester",
            "role": "generate_tests",
            "model": "gpt-4o-mini"
        }
    ],
    "workflow": "sequential",
    "guardrails": ["security_scan", "syntax_check"]
}
```

## Integration Setup

### Supported Integrations

| Service | Setup Required | Config Key |
|---------|----------------|------------|
| Slack | Webhook URL | `slack.webhook_url` |
| Discord | Webhook URL | `discord.webhook_url` |
| Notion | API Key | `notion.api_key` |
| GitHub | Personal Access Token | `github.pat` |
| Gmail | OAuth | `gmail.credentials` |
| Database | Connection String | `database.url` |

## CLI Usage

```bash
# Start wizard
python wizard.py

# Quick start with template
python wizard.py --template customer_service

# Generate from config
python wizard.py --config my_config.yaml

# Export template
python wizard.py --export customer_service
```

## Error Handling

| Error | Handling |
|-------|----------|
| Invalid template | Show available templates |
| Missing config | Prompt for required fields |
| Network error | Offer offline mode |

## Best Practices

1. **Start with template** - Use predefined templates for quick setup
2. **Customize incrementally** - Start simple, add complexity later
3. **Test in dev first** - Use development mode before production
4. **Monitor from day one** - Enable dashboard early

## See Also

- [guides/getting-started.md](guides/getting-started.md)
- [examples/](examples/) - Sample projects
- [templates/](templates/) - Template library
