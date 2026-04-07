---
name: api-gateway
description: API Gateway for methodology-v2. Provides rate limiting, authentication, request/response transformation, and monitoring for AI agent APIs.
---

# API Gateway

API Gateway for methodology-v2 agents.

## Quick Start

```python
from api_gateway import APIGateway, RateLimiter, AuthMiddleware

# Create gateway
gateway = APIGateway(port=8080)

# Add rate limiting
limiter = RateLimiter(requests=100, window=60)
gateway.use(limiter)

# Add authentication
auth = AuthMiddleware(api_key="sk-xxx")
gateway.use(auth)

# Register agent
@gateway.route("/agent/{agent_id}")
async def handle_agent(agent_id, request):
    return await agent.run(agent_id, request.json())

# Start
gateway.run()
```

## Features

### 1. Rate Limiting

```python
limiter = RateLimiter(
    requests=100,    # per window
    window=60,       # seconds
    strategy="sliding"  # or "fixed"
)
```

### 2. Authentication

```python
# API Key
auth = AuthMiddleware(api_key="sk-xxx")

# JWT
jwt_auth = JWTAuth(secret="secret", algorithm="HS256")

# OAuth
oauth = OAuthMiddleware(provider="google")
```

### 3. Request/Response Transformation

```python
transformer = ResponseTransformer(
    format="json",
    compression=True,
    add_headers={"X-API-Version": "2.0"}
)
```

### 4. Monitoring

```python
monitor = RequestMonitor()
monitor.track(request, response, duration)
```

## CLI Usage

```bash
# Start gateway
python api_gateway/gateway.py --port 8080

# Dashboard
python api_gateway/dashboard.py
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  Gateway    │────▶│   Agent     │
│             │     │             │     │             │
│ - Rate Limit│     │ - Auth      │     │ - Execute   │
│ - Auth      │     │ - Transform │     │ - Response  │
│ - Monitor   │     │ - Log       │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Best Practices

1. **Always rate limit** - Prevent abuse
2. **Use HTTPS** - Security in transit
3. **Log everything** - Audit trail
4. **Monitor metrics** - Performance tracking
