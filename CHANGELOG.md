# Changelog

## v6.29.0 — 2026-04-07

### feat: Feedback Loop — Standardized Quality Signal Collection & Closure

**Feedback Loop** is a unified framework for collecting, categorizing, prioritizing, and tracking quality signals from all sources across the development lifecycle.

#### Key Changes
- New `core/feedback/` module with 9 source types and 240 tests
- 5×5 Severity Matrix (impact × urgency interaction)
- Source-specific closure verification (Constitution, Linter, Test, Drift)
- ASCII Dashboard + JSON/Prometheus export
- Integrations: Constitution HR-01~HR-15, Quality Gate violations, Architecture drift

#### Module Structure
- `sources_schema.py` — 9 feedback sources defined
- `feedback.py` — StandardFeedback + FeedbackStore
- `severity.py` — 5×5 Severity Matrix
- `router.py` — SLA + Routing Engine
- `closure.py` — Source-specific closure verification
- `constitution_adapter.py` — Constitution → Feedback integration
- `constitution_closure.py` — Constitution closure verifier
- `quality_gate_adapter.py` — Quality Gate → Feedback integration
- `quality_gate_hook.py` — AutoQualityGate with feedback hook
- `metrics.py` — DashboardMetrics
- `dashboard.py` — ASCII Dashboard
- `export.py` — JSON / Prometheus export

#### SLA Configuration
| Severity | Response | Resolution | Escalation |
|----------|----------|------------|------------|
| Critical | 15 min | 4 hours | Immediate |
| High | 1 hour | 24 hours | 1 hour |
| Medium | 4 hours | 3 days | Daily |
| Low | 1 day | Next sprint | Weekly |

---

*This changelog follows [Keep a Changelog](https://keepachangelog.com/) format.*
