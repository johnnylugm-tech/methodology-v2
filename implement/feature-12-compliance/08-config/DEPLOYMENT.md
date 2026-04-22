# Feature #12 - Phase 8: Deployment Configuration

**Layer 6: Compliance**
**Regulatory Frameworks:** EU AI Act Art.14, NIST AI RMF, Anthropic RSP v3.0
**Modules:** eu_ai_act.py, nist_rmf.py, compliance_matrix.py, compliance_reporter.py, killswitch_compliance.py, audit_trail.py
**Date:** 2026-04-22
**Status:** Draft → Ready for Review

---

## 1. Deployment Environment Requirements

### 1.1 Target Environments

| Environment | Purpose | Access Level |
|-------------|---------|--------------|
| `development` | Local dev, feature testing | Developer |
| `staging` | Pre-production integration testing | Engineering + QA |
| `production` | Live compliance enforcement | Operations + SRE |

### 1.2 Compute Requirements

| Component | Minimum | Recommended |
|-----------|---------|--------------|
| CPU | 2 vCPU | 4 vCPU |
| Memory (RAM) | 4 GB | 8 GB |
| Storage | 50 GB SSD | 100 GB SSD |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| Python | 3.10+ | 3.11+ |

### 1.3 Network Requirements

| Port/Protocol | Service | Notes |
|---------------|---------|-------|
| 443/TCP | HTTPS | Production API endpoint |
| 5432/TCP | PostgreSQL | Primary database |
| 6379/TCP | Redis | Cache + queue backend |
| 8000/TCP | Health check | `/health` endpoint only |

### 1.4 Security Requirements

- [ ] TLS 1.2+ enforced for all external connections
- [ ] Database encryption at rest (AES-256)
- [ ] Secret management via environment variables or vault (no hardcoded secrets)
- [ ] Network segmentation: compliance layer isolated from public internet
- [ ] Kill switch endpoint accessible only via internal network or VPN

---

## 2. Dependencies

### 2.1 Python Packages

```
# requirements-compliance.txt

# Core Framework
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Compliance Modules
psycopg2-binary>=2.9.9       # PostgreSQL adapter
redis>=5.0.0                 # Redis cache/queue
sqlalchemy>=2.0.25           # ORM
alembic>=1.13.0              # Database migrations

# EU AI Act Module
httpx>=0.26.0                # Async HTTP client

# NIST AI RMF Module
numpy>=1.26.0                # Numerical calculations
pandas>=2.1.0                # Data analysis

# Compliance Matrix & Reporter
jinja2>=3.1.0                # Template rendering
weasyprint>=52.0             # PDF export (HTML to PDF)
markdown>=3.5.0              # Markdown rendering

# Audit Trail
cryptography>=41.0.0         # Hash chaining (SHA-256)
python-json-logger>=2.0.0    # Structured JSON logging

# Kill Switch
celery>=5.3.0                # Async task queue
kombu>=5.3.0                 # Message transport

# Monitoring & Observability
prometheus-client>=0.19.0    # Prometheus metrics
sentry-sdk[fastapi]>=1.40.0  # Error tracking
structlog>=24.1.0            # Structured logging

# Testing
pytest>=7.4.0
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0
httpx>=0.26.0                # Test client

# Development
black>=23.0
ruff>=0.1.0
mypy>=1.8.0
```

### 2.2 System Requirements

```bash
# Ubuntu 22.04 LTS base packages
apt-get install -y \
    build-essential \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    python3.11-dev \
    nodejs \
    npm

# WeasyPrint additional dependencies (for PDF export)
apt-get install -y \
    python3-cffi \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgtk-3-0 \
    libgsf-1-dev \
    libffi-dev \
    shared-mime-info
```

### 2.3 Infrastructure Services

| Service | Version | Purpose |
|---------|---------|---------|
| PostgreSQL | 14+ | Compliance data persistence |
| Redis | 7+ | Cache layer + Celery broker |
| Prometheus | 2.45+ | Metrics collection |
| Grafana | 9+ | Metrics visualization |

---

## 3. Environment Variables Configuration

### 3.1 Required Environment Variables

```bash
# .env.example — DO NOT commit actual values

# ===== Application =====
APP_ENV=production                      # development|staging|production
APP_DEBUG=false
APP_HOST=0.0.0.0
APP_PORT=8000
APP_SECRET_KEY=                         # Generate: python -c "import secrets; print(secrets.token_urlsafe(32))"

# ===== Database =====
DATABASE_URL=postgresql://user:pass@localhost:5432/compliance_db
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# ===== Redis =====
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# ===== Compliance Configuration =====
# EU AI Act
EU_AI_ACT_RISK_THRESHOLD=0.7            # Risk score threshold for flagging
EU_AI_ACT_HITL_ENABLED=true             # Human-in-the-loop enforcement

# NIST AI RMF
NIST_RMF_MEASURE_INTERVAL_SECONDS=300   # Risk measurement interval

# Anthropic RSP
ANTHROPIC_API_KEY=                     # API key for Anthropic integration
ANTHROPIC_RSP_VERSION=3.0
ANTHROPIC_POLICY_CHECK_ENABLED=true

# Kill Switch
KILLSWITCH_SLA_MILLISECONDS=500        # Max kill switch latency
KILLSWITCH_AUTHORIZED_ROLES=            # Comma-separated role names
KILLSWITCH_EMERGENCY_WEBHOOK_URL=       # Optional external alert URL

# Audit Trail
AUDIT_TRAIL_HASH_ALGO=SHA256
AUDIT_TRAIL_RETENTION_DAYS=2555         # ~7 years (regulatory requirement)
AUDIT_TRAIL_ENABLE_TAMPER_CHECK=true

# ===== Observability =====
SENTRY_DSN=                             # Sentry error tracking
PROMETHEUS_ENABLED=true
METRICS_PORT=9090
LOG_LEVEL=INFO
LOG_FORMAT=json

# ===== External Integrations =====
COMPLIANCE_REPORTER_EXPORT_FORMAT=pdf    # pdf|html|markdown
COMPLIANCE_REPORTER_OUTPUT_DIR=/var/compliance/reports
```

### 3.2 Environment-Specific Overrides

| Variable | development | staging | production |
|----------|-------------|---------|-------------|
| `APP_DEBUG` | `true` | `false` | `false` |
| `APP_ENV` | `development` | `staging` | `production` |
| `DATABASE_URL` | localhost | staging RDS | production RDS |
| `LOG_LEVEL` | `DEBUG` | `INFO` | `WARNING` |
| `AUDIT_TRAIL_ENABLE_TAMPER_CHECK` | `false` | `true` | `true` |
| `KILLSWITCH_SLA_MILLISECONDS` | `2000` | `1000` | `500` |

---

## 4. Deployment Procedure

### 4.1 Pre-Deployment Checklist

```
□ All CI/CD pipeline stages passing (lint, unit, integration, coverage)
□ Database migrations tested in staging environment
□ Kill switch SLA benchmark test passed (< 500ms p99)
□ Compliance matrix edge case tests passing (100% coverage)
□ Audit trail hash chaining verified
□ EU AI Act classification letter obtained from legal counsel
□ NIST AI RMF gap assessment reviewed
□ Anthropic RSP v3.0 policy alignment confirmed
□ Penetration test completed on kill switch endpoint
□ Rollback procedure documented and tested
□ On-call runbook reviewed by operations team
□ Go/No-Go meeting completed with stakeholders
```

### 4.2 Deployment Steps

#### Step 1: Backup

```bash
# Backup current database state
./scripts/backup_compliance_db.sh --env ${TARGET_ENV}

# Backup current configuration
cp -r /opt/compliance/config /opt/compliance/config.backup.$(date +%Y%m%d%H%M%S)
```

#### Step 2: Database Migration

```bash
# Run pending Alembic migrations
alembic upgrade head --tag feature-12-compliance

# Verify migration success
alembic current --tag feature-12-compliance
```

#### Step 3: Dependency Installation

```bash
# Install Python dependencies
pip install -r requirements-compliance.txt --quiet

# Install system dependencies (if not already present)
sudo ./scripts/install_system_deps.sh
```

#### Step 4: Configuration

```bash
# Copy environment-specific configuration
cp config/compliance.${TARGET_ENV}.yaml /opt/compliance/config/compliance.yaml

# Validate configuration
python -m compliance.config validate /opt/compliance/config/compliance.yaml

# Set secrets (from vault or secrets manager)
./scripts/load_secrets.sh --env ${TARGET_ENV}
```

#### Step 5: Service Restart

```bash
# Restart compliance service
sudo systemctl restart compliance-layer

# Verify service is running
sudo systemctl status compliance-layer --no-pager

# Check application logs
tail -n 100 /var/log/compliance/compliance.log | grep ERROR
```

#### Step 6: Health Verification

```bash
# Run health check
curl -f http://localhost:8000/health

# Run smoke tests
pytest tests/smoke/ -v --tb=short

# Verify kill switch latency
python scripts/benchmark_killswitch.py --sla-ms 500
```

#### Step 7: Post-Deployment Monitoring

```bash
# Verify metrics are being collected
curl -s http://localhost:9090/metrics | grep compliance

# Check Grafana dashboard
# Navigate to: https://grafana.internal/d/compliance-layer

# Verify audit trail writes are flowing
psql $DATABASE_URL -c "SELECT COUNT(*) FROM audit_trail WHERE created_at > NOW() - INTERVAL '5 minutes';"
```

### 4.3 Rollback Procedure

```bash
# Rollback to previous migration
alembic downgrade -1 --tag feature-12-compliance

# Restore previous configuration
cp -r /opt/compliance/config.backup.* /opt/compliance/config/

# Restart service
sudo systemctl restart compliance-layer

# Verify rollback
curl -f http://localhost:8000/health
```

### 4.4 Docker Deployment (Optional)

```dockerfile
# compliance.Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for WeasyPrint
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 libpangocairo-1.0-0 libgtk-3-0 \
    libgsf-1-dev shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-compliance.txt .
RUN pip install --no-cache-dir -r requirements-compliance.txt

COPY . .

CMD ["uvicorn", "compliance.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and deploy
docker build -f compliance.Dockerfile -t compliance-layer:${VERSION} .
docker run -d --name compliance-layer \
    --env-file .env.production \
    -p 8000:8000 \
    compliance-layer:${VERSION}
```

---

## 5. Monitoring Configuration

### 5.1 Metrics (Prometheus)

```python
# compliance/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Info

# Service info
SERVICE_INFO = Info(
    'compliance_layer',
    'Compliance layer service information'
).labels(version='1.0.0', env=APP_ENV)

# Request metrics
REQUEST_COUNT = Counter(
    'compliance_requests_total',
    'Total compliance checks',
    ['endpoint', 'method', 'status']
)

REQUEST_LATENCY = Histogram(
    'compliance_request_seconds',
    'Request latency in seconds',
    ['endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

# Kill switch metrics
KILLSWITCH_TRIGGERS = Counter(
    'killswitch_triggers_total',
    'Total kill switch activations',
    ['reason', 'status']
)

KILLSWITCH_LATENCY = Histogram(
    'killswitch_latency_milliseconds',
    'Kill switch execution latency',
    buckets=[100, 200, 300, 400, 500, 750, 1000]
)

# Compliance matrix metrics
COMPLIANCE_SCORE = Gauge(
    'compliance_matrix_score',
    'Current compliance score (0-100)',
    ['framework']  # eu_ai_act, nist_rmf, anthropic_rsp
)

RISK_FLAGS = Counter(
    'compliance_risk_flags_total',
    'Total risk flags raised',
    ['risk_id', 'severity']
)

# Audit trail metrics
AUDIT_TRAIL_WRITES = Counter(
    'audit_trail_writes_total',
    'Total audit trail writes',
    ['status']  # success, failure, partial
)

AUDIT_TRAIL_TAMPER_CHECKS = Counter(
    'audit_trail_tamper_checks_total',
    'Audit trail tamper checks',
    ['result']  # passed, failed
)
```

### 5.2 Alerting Rules (Prometheus Alertmanager)

```yaml
# prometheus/alerts/compliance_alerts.yml
groups:
  - name: compliance_layer_alerts
    rules:
      # Kill switch SLA breach
      - alert: KillSwitchSLABreach
        expr: histogram_quantile(0.99, compliance_killswitch_latency_milliseconds) > 500
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Kill switch SLA breach detected"
          description: "p99 latency {{ $value }}ms exceeds 500ms SLA"

      # Compliance score degradation
      - alert: ComplianceScoreDegraded
        expr: compliance_matrix_score < 60
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Compliance score degraded"
          description: "Framework {{ $labels.framework }} score is {{ $value }}"

      # Audit trail write failures
      - alert: AuditTrailWriteFailure
        expr: rate(audit_trail_writes_total{status="failure"}[5m]) > 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Audit trail write failures detected"

      # Kill switch activation (any activation is notable)
      - alert: KillSwitchActivated
        expr: increase(killswitch_triggers_total[1m]) > 0
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "Kill switch activated"
          description: "Kill switch triggered by {{ $labels.reason }}"

      # Service health check failure
      - alert: ComplianceServiceDown
        expr: up{job="compliance-layer"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Compliance service is down"

      # High error rate
      - alert: HighErrorRate
        expr: rate(compliance_requests_total{status="error"}[5m]) / rate(compliance_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate in compliance layer"
          description: "Error rate is {{ $value | humanizePercentage }}"
```

### 5.3 Structured Logging (structlog)

```python
# compliance/logging_config.py
import structlog
from structlog.processors import JSONRenderer, TimeStamper, add_log_level

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)
```

### 5.4 Health Check Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Basic liveness check |
| `/health/ready` | GET | Readiness check (includes DB + Redis) |
| `/health/live` | GET | Liveness check (process alive) |
| `/metrics` | GET | Prometheus metrics |

```python
# compliance/main.py — health endpoints

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0", "env": APP_ENV}

@app.get("/health/ready")
async def health_ready():
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "audit_trail": await check_audit_trail_writes(),
    }
    all_ok = all(checks.values())
    return {"status": "ready" if all_ok else "not_ready", "checks": checks}

@app.get("/health/live")
async def health_live():
    return {"status": "alive"}
```

### 5.5 Grafana Dashboard Panels

```
Dashboard: Compliance Layer - Production

Row 1: Service Health
  - Panel 1: Service Uptime (up{job="compliance-layer"})
  - Panel 2: Request Rate (rate(compliance_requests_total[5m]))
  - Panel 3: Error Rate (rate with status=error)

Row 2: Kill Switch
  - Panel 4: Kill Switch Latency (histogram_quantile(0.99, ...))
  - Panel 5: Kill Switch Triggers (increase over 1h)
  - Panel 6: SLA Compliance % (latency < 500ms)

Row 3: Compliance Scores
  - Panel 7: EU AI Act Score (gauge 0-100)
  - Panel 8: NIST AI RMF Score (gauge 0-100)
  - Panel 9: Anthropic RSP Score (gauge 0-100)

Row 4: Audit Trail
  - Panel 10: Write Rate (rate per minute)
  - Panel 11: Tamper Check Results (passed vs failed)
  - Panel 12: Storage Used (bytes)

Row 5: Risk Flags
  - Panel 13: Active Risk Flags by Severity
  - Panel 14: Risk Flag Trend (7 day)
```

---

## Appendix A: Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-04-22 | Developer Agent | Initial deployment configuration |

## Appendix B: Quick Reference

```bash
# Quick deployment commands
make deploy ENV=production VERSION=1.0.0

# Quick rollback
make rollback ENV=production

# Quick health check
curl -f http://localhost:8000/health/ready | jq .

# Quick metrics
curl -s http://localhost:9090/metrics | grep -E "^compliance_" | head -20
```

## Appendix C: Contacts

| Role | Name | Contact |
|------|------|---------|
| Engineering Lead | TBD | tbd@company.com |
| Compliance Officer | TBD | compliance@company.com |
| On-Call SRE | PagerDuty | compliance-oncall |
| Legal (EU AI Act) | TBD | legal@company.com |
