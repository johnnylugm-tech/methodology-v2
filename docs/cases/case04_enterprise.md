# 案例四：企業整合

## 情境描述

企業需要整合現有的 CI/CD 系統、MCP 服務，以及合規的部署環境。

---

## 案例 4.1：建立 CI/CD 流程

### 背景
需要為新專案建立完整的 CI/CD 流程。

### 使用方式

```python
from methodology import CICDIntegration

cicd = CICDIntegration(project_path="/path/to/project")

# 1. 建立 GitHub Actions
cicd.create_github_actions_workflow(
    workflow_name="CI/CD",
    trigger="push",
    python_version="3.11"
)
print("✅ GitHub Actions workflow created")

# 2. 建立 Docker Compose
compose = cicd.generate_docker_compose(
    services=["api", "worker", "monitor"],
    port=8000
)
print("✅ docker-compose.yml generated")

# 3. 或一次建立所有
cicd.setup_all(provider="github")
print("✅ All CI/CD files created")
```

### 產出檔案

```
.github/workflows/
├── ci.yml          # 自動建置、測試、部署
├── security.yml    # 安全掃描
└── release.yml     # 發布流程

docker-compose.yml  # 本地開發環境
Dockerfile          # 容器化
```

---

## 案例 4.2：多語言專案支援

### 背景
團隊使用 Python、Go、JavaScript 三種語言，需要統一管理。

### 使用方式

```python
from methodology import MultiLanguageSupport

ml = MultiLanguageSupport()

# 檢測專案語言
languages = ml.detect_project_languages("/path/to/project")
print("專案使用的語言:")
for lang, count in languages:
    print(f"  {lang.value}: {count} 檔案")

# 根據任務自動路由到合適 Agent
tasks = [
    "build a Python FastAPI backend",
    "create a React component",
    "implement a Go microservice",
]

for task in tasks:
    route = ml.route_to_agent(task)
    print(f"\n任務: {task}")
    print(f"  → Language: {route['recommended_language']}")
    print(f"  → Agent: {route['agent_type']}")
    print(f"  → Confidence: {route['confidence']:.0%}")

# 生成多語言專案結構
project_structure = ml.generate_polyglot_project("ecommerce-platform")
print("\n建議的專案結構:")
for path in list(project_structure.keys())[:5]:
    print(f"  {path}")
```

### 輸出範例
```
專案使用的語言:
  python: 45 檔案
  typescript: 32 檔案
  go: 12 檔案

任務: build a Python FastAPI backend
  → Language: python
  → Agent: developer-python
  → Confidence: 67%

任務: create a React component
  → Language: typescript
  → Agent: developer-ts
  → Confidence: 75%

任務: implement a Go microservice
  → Language: go
  → Agent: developer-go
  → Confidence: 80%
```

---

## 案例 4.3：企業 MCP 服務整合

### 背景
需要連接 Slack、Notion、GitHub 等企業服務。

### 使用方式

```python
from methodology import Extensions

ext = Extensions()

# 連接 Slack
slack = ext.connect_service(
    "slack",
    token="xoxb-...",
    channel="#ai-projects"
)
print(f"✅ Slack connected: {slack['status']}")

# 連接 GitHub
github = ext.connect_service(
    "github",
    token="ghp_...",
    owner="acme-corp",
    repo="ai-platform"
)
print(f"✅ GitHub connected: {github['status']}")

# 跨服務執行任務
result = ext.execute_across_services(
    task="建立本月的技術報告並發布到 Slack 和 Notion"
)
print(f"\n執行結果: {result['completed']}")
print(f"服務: {', '.join(result['services'])}")
```

---

## 相關功能

| 功能 | 模組 |
|------|------|
| CI/CD 建立 | `CICDIntegration` |
| 多語言支援 | `MultiLanguageSupport` |
| MCP 整合 | `MCPAdapter` |
| Docker 部署 | `LocalDeploy` |
