---
name: vertical-templates
description: Vertical Domain Templates for methodology-v2. Use when: (1) Building customer service AI agents, (2) Creating legal document agents, (3) Developing domain-specific AI solutions, (4) Following methodology-v2 development framework. Provides pre-built templates for customer service, legal, and other vertical domains with workflow automation.
---

# Vertical Domain Templates

Pre-built templates for high-value vertical AI agents, built on methodology-v2.

## Quick Start

```python
import sys
sys.path.insert(0, '/workspace/methodology-v2')
sys.path.insert(0, '/workspace/vertical-templates/scripts')

from vertical_templates import CustomerServiceAgent, LegalAgent

# Customer Service Agent
cs_agent = CustomerServiceAgent(
    knowledge_base="docs/",
    escalation_threshold=0.3
)
result = cs_agent.handle("我收到的商品壞了")
print(result)

# Legal Agent
legal = LegalAgent(
    jurisdiction="TW",
    practice_area="contract"
)
analysis = legal.analyze_contract("lease_agreement.txt")
```

## Available Templates

### 1. Customer Service Agent

| Component | Function |
|-----------|----------|
| IntentClassifier | Classify customer intent (refund, inquiry, complaint, tech support) |
| KnowledgeBaseRAG | Search product docs automatically |
| EscalationManager | Route complex issues to humans |
| ResponseGenerator | Generate personalized responses |
| SentimentAnalyzer | Detect emotion, adjust tone |

**Features**:
- 70-80% auto-resolution rate
- Multi-language support
- Integration with Slack, Discord, email

### 2. Legal Agent

| Component | Function |
|-----------|----------|
| ContractAnalyzer | Identify contract risks |
| CaseLawSearch | Find similar cases |
| DocumentGenerator | Generate legal documents |
| ComplianceChecker | Check regulatory compliance |

**Features**:
- Support for TW, US, EU jurisdictions
- Common contract types: NDA, MSA, SOW, Lease
- Risk scoring with mitigation suggestions

### 3. Healthcare Agent (Coming Soon)

| Component | Function |
|-----------|----------|
| PatientTriage | Initial symptom assessment |
| AppointmentScheduler | Book/reschedule appointments |
| MedicationReminder | Send medication reminders |
|HIPAACompliance | Ensure data privacy |

## Integration with methodology-v2

```python
from methodology import Crew, Agent
from vertical_templates import CustomerServiceAgent

# Create vertical agent
cs = CustomerServiceAgent(
    knowledge_base="docs/",
    escalation_threshold=0.3
)

# Use in Crew workflow
crew = Crew(
    agents=[cs, qa_agent],
    process="sequential"
)
result = crew.kickoff()
```

## Pricing Model (Optional)

Support outcome-based pricing:

```python
# Pay per resolution
cs = CustomerServiceAgent(
    pricing="per_resolution",
    rate=0.50
)

# Pay per savings
legal = LegalAgent(
    pricing="per_savings",
    rate=0.10  # 10% of律师 hours saved
)
```

## Configuration

```python
from vertical_templates import TemplateConfig

config = TemplateConfig(
    language="zh-TW",  # or "en-US", "ja-JP"
    tone="professional",  # or "friendly", "formal"
    auto_escalate=True,
    sentiment_tracking=True
)
```

## CLI Usage

```bash
# Initialize customer service agent
python vertical_templates.py init cs --kb docs/

# Initialize legal agent
python vertical_templates.py init legal --jurisdiction TW

# Run agent
python vertical_templates.py run cs --input "我要退貨"
```

## Expected ROI

| Template | Setup Time | Auto-Resolution | Cost Savings |
|----------|------------|-----------------|--------------|
| Customer Service | 1 week | 70-80% | $60M/yr (Klarna case) |
| Legal | 2 weeks | 50-60% | 40% lawyer time |

## See Also

- [references/customer_service_workflow.md](references/customer_service_workflow.md)
- [references/legal_workflow.md](references/legal_workflow.md)
- [references/pricing_models.md](references/pricing_models.md)
