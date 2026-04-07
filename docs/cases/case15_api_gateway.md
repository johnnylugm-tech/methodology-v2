# 案例 15：API Gateway (api_gateway)

## 概述

API Gateway for AI agent APIs with rate limiting, authentication, and monitoring.

---

## 快速開始

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
```

---

## 核心功能

| 功能 | 說明 |
|------|------|
| Rate Limiting | 請求限流 |
| Authentication | 認證中介 |
| Request/Response Transform | 請求轉換 |
| Monitoring | 即時監控 |

---

## 與現有模組整合

| 模組 | 整合點 |
|------|--------|
| enterprise_hub | 企業整合 |
| guardrails | 安全過濾 |
| observability | API 監控 |

---

## CLI 使用

```bash
# 查看 API 狀態
python cli.py gateway status

# 查看流量
python cli.py gateway stats --period 1h
```

---

## 相關模組

- enterprise_hub.py
- guardrails.py
- observability.py
