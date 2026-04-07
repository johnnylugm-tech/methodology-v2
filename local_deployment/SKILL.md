---
name: local-deployment
description: Local Deployment Suite for methodology-v2. Use when: (1) Deploying methodology-v2 locally for privacy/GDPR compliance, (2) Setting up offline AI agents, (3) Running local LLM with Ollama, (4) Building air-gapped AI solutions. Provides Docker compose templates, Ollama integration, and data isolation.
---

# Local Deployment Suite

Deploy methodology-v2 locally with Docker and Ollama for privacy-first AI solutions.

## Quick Start

```bash
# Clone and deploy
git clone https://github.com/johnnylugm-tech/methodology-v2-local
cd methodology-v2-local
docker-compose up -d

# Access services
# - API: http://localhost:8000
# - Dashboard: http://localhost:8080
```

## Features

| Feature | Description |
|---------|-------------|
| Docker Compose | One-command deployment |
| Ollama Integration | Local LLM support |
| Data Isolation | Keep data on-premise |
| Offline Mode | Work without internet |
| SSL/TLS | Secure local communication |

## Architecture

```
┌─────────────────────────────────────┐
│         methodology-v2-local         │
├─────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐          │
│  │  API    │  │Dashboard│          │
│  │ (FastAPI)│  │ (React) │          │
│  └────┬────┘  └────┬────┘          │
│       │            │                │
│  ┌────┴────────────┴────┐          │
│  │   methodology-v2     │          │
│  │   (Python Core)       │          │
│  └──────────┬───────────┘          │
│             │                      │
│  ┌──────────┴───────────┐          │
│  │      Ollama         │          │
│  │   (Local LLMs)      │          │
│  └─────────────────────┘          │
└─────────────────────────────────────┘
```

## Configuration

### Environment Variables

```bash
# .env file
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3
DATABASE_PATH=/data/storage.db
LOG_LEVEL=INFO
API_PORT=8000
DASHBOARD_PORT=8080
```

### Docker Compose Options

```yaml
# docker-compose.yml
services:
  api:
    image: methodology-v2-api
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_MODEL=llama3
  
  ollama:
    image: ollama/ollama
    volumes:
      - ollama-data:/root/.ollama
  
  dashboard:
    image: methodology-v2-dashboard
    ports:
      - "8080:8080"
```

## Usage with Ollama

### 1. Pull Models

```bash
docker-compose exec ollama ollama pull llama3
docker-compose exec ollama ollama pull mistral
```

### 2. Use Local Models

```python
from methodology import SmartRouter

router = SmartRouter(config={
    "default_model": "ollama/llama3",
    "ollama_base_url": "http://localhost:11434"
})

result = router.complete("Hello")
# Uses local Llama3!
```

### 3. Switch Models

```python
# Use different local models
router = SmartRouter()
router.set_default_model("ollama/mistral")
```

## Deployment Modes

### 1. Minimal (API Only)

```bash
docker-compose up -d api
```

### 2. Standard (API + Dashboard)

```bash
docker-compose up -d api dashboard
```

### 3. Full (API + Dashboard + Ollama)

```bash
docker-compose up -d api dashboard ollama
```

### 4. Enterprise (Full + Monitoring)

```bash
docker-compose -f docker-compose.enterprise.yml up -d
```

## Offline Setup

### 1. Pull images offline

```bash
# On connected machine
docker-compose pull

# Save to tar
docker-compose save -o methodology-v2.tar

# Transfer to offline machine
# Load
docker-compose load -i methodology-v2.tar
```

### 2. Pull Ollama models

```bash
# On connected machine
docker-compose exec ollama ollama pull llama3

# Save model
docker-compose exec ollama ollama save llama3.tar llama3

# Transfer and load
docker-compose exec -T ollama ollama load < llama3.tar
```

## Security

### Network Isolation

```yaml
# docker-compose.secure.yml
services:
  api:
    networks:
      - internal
    expose:
      - "8000"

networks:
  internal:
    driver: bridge
    internal: true
```

### SSL/TLS

```bash
# Generate self-signed cert
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365

# Use in compose
docker-compose -f docker-compose.ssl.yml up -d
```

## Data Privacy

### Volume Mounts

```yaml
volumes:
  - ./data:/data  # Local storage
  - ./logs:/logs  # Local logs
```

### Disable External Calls

```python
# In your code
import os
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
os.environ["DISABLE_TELEMETRY"] = "true"
```

## Monitoring

### Health Checks

```bash
# Check service health
curl http://localhost:8000/health

# Check Ollama
curl http://localhost:11434/api/tags
```

### Logs

```bash
# View logs
docker-compose logs -f api
docker-compose logs -f ollama

# View with timestamps
docker-compose logs -t -f
```

## CLI Usage

```bash
# Initialize local deployment
python local_deploy.py init --mode full

# Start services
python local_deploy.py start

# Stop services
python local_deploy.py stop

# Check status
python local_deploy.py status

# Pull Ollama models
python local_deploy.py pull-model llama3

# Backup data
python local_deploy.py backup --output backup.tar
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Ollama not starting | Increase Docker memory to 4GB+ |
| Model not found | Pull model: `docker-compose exec ollama ollama pull llama3` |
| Port conflict | Change ports in .env |
| Slow inference | Use GPU-enabled Docker |

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16 GB |
| Disk | 20 GB | 50 GB |
| GPU | Optional | NVIDIA 8GB+ |

## See Also

- [references/docker_config.md](references/docker_config.md)
- [references/ollama_models.md](references/ollama_models.md)
