# Feature #11: Langfuse Observability — Configuration Records

**Version:** 1.0.0  
**Feature ID:** FR-11  
**Phase:** 08-config  
**Author:** methodology-v2 Agent  
**Date:** 2026-04-22  
**Status:** Phase 1  

---

## 1. Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LANGFUSE_PUBLIC_KEY` | Yes (cloud) | — | Langfuse cloud public key |
| `LANGFUSE_SECRET_KEY` | Yes (cloud) | — | Langfuse cloud secret key |
| `LANGFUSE_HOST` | Yes (self-hosted) | — | Self-hosted base URL |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | No | Langfuse cloud OTLP | OTLP collector endpoint |
| `OTEL_SERVICE_NAME` | No | `methodology-v2` | Service name on spans |
| `LANGFUSE_TRACE_SAMPLING_RATE` | No | `1.0` | Fraction of spans to sample (0.0–1.0) |
| `LANGFUSE_DASHBOARD_POLL_INTERVAL_SECONDS` | No | `5` | Dashboard polling interval |
| `LANGFUSE_AUDIT_RETENTION_DAYS` | No | `90` | Audit log retention period |

---

## 2. config.yaml Schema (Optional)

If using `config.yaml` instead of env vars, place under the `ml_langfuse` key:

```yaml
ml_langfuse:
  mode: cloud                    # cloud | self_hosted
  public_key: ""                # LANGFUSE_PUBLIC_KEY
  secret_key: ""                # LANGFUSE_SECRET_KEY
  host: ""                      # LANGFUSE_HOST (self-hosted)
  otel_exporter_endpoint: ""   # OTEL_EXPORTER_OTLP_ENDPOINT
  otel_service_name: methodology-v2
  trace_sampling_rate: 1.0
  dashboard_poll_interval_seconds: 5
  audit_retention_days: 90
```

Priority order (high → low): `env var` > `config.yaml` > `hardcoded default`.

---

## 3. Local Development Setup

```bash
# Clone the repo
cd projects/methodology-v2

# Set env vars (cloud mode — get keys from Langfuse dashboard)
export LANGFUSE_PUBLIC_KEY=pk_prod_xxxxx
export LANGFUSE_SECRET_KEY=sk_prod_xxxxx

# For self-hosted mode:
export LANGFUSE_HOST=https://langfuse.yourcompany.com

# For custom OTLP endpoint:
export OTEL_EXPORTER_OTLP_ENDPOINT=https://collector.example.com:4318

# Verify initialization
PYTHONPATH="implement/feature-11-langfuse/03-implement:$PYTHONPATH" \
  python -c "from ml_langfuse import get_langfuse_client; c = get_langfuse_client(); print('OK')"
```

---

## 4. Docker / Deployment Notes

```dockerfile
# In Dockerfile
ENV LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY}
ENV LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY}
ENV LANGFUSE_TRACE_SAMPLING_RATE=0.1   # Sample 10% in production
ENV OTEL_SERVICE_NAME=methodology-v2-production
```

---

## 5. CI Configuration

```yaml
# .github/workflows/ci.yml (example)
env:
  LANGFUSE_PUBLIC_KEY: ${{ secrets.LANGFUSE_PUBLIC_KEY_TEST }}
  LANGFUSE_SECRET_KEY: ${{ secrets.LANGFUSE_SECRET_KEY_TEST }}
  OTEL_SERVICE_NAME: methodology-v2-ci
  LANGFUSE_TRACE_SAMPLING_RATE: 1.0   # Sample all in CI
```

---

## 6. Package Dependencies (pyproject.toml)

```toml
[project.optional-dependencies]
langfuse = [
    "langfuse>=3.0",
    "opentelemetry-api>=1.20",
    "opentelemetry-sdk>=1.20",
    "opentelemetry-exporter-otlp>=1.20",
    "opentelemetry-propagate>=1.20",
    "pydantic>=2.0",
]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "pytest-mock>=3.10",
    "pytest-cov>=4.0",
]
```
