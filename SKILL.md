# methodology-v2

> Multi-Agent Collaboration Development Methodology v5.13

---

## 📊 版本歷史

| 版本 | 日期 | 說明 |
|------|------|------|
| v5.14 | 2026-03-22 | Async Executor 非同步執行器 |
| v5.13 | 2026-03-22 | ASPICE 實踐：traceability_matrix, verification_gate, work_product |
| v5.12 | 2026-03-22 | 正確性保障：Timeout、A/B雙重驗證、Kickoff檢查；錯誤處理：HITL機制、L1-L6分類、斷點設計；P2P協作 |
| v5.11 | 2026-03-22 | HITL (Human-in-the-Loop) 系統 |
| v5.10 | 2026-03-22 | Unified Config 統一配置 |
| v5.9 | 2026-03-22 | Hybrid A/B Workflow 混合分流工作流 |
| v5.8 | 2026-03-20 | CrewAI 整合 |
| v5.6 | 2026-03-21 | Three-Phase Executor, Fault Tolerant, Smart Orchestrator |
| v5.4 | 2026-03-20 | 初始版本 |

---

## 概述

這是一個標準化的多 Agent 協作開發方法論，定義了錯誤分類、開發流程、協作模式、品質把關和監控警報。

整合了三個核心 Skill：
- **ai-agent-toolkit**：工具集
- **multi-agent-toolkit**：協作框架
- **methodology-v2**：方法論核心

---

## 核心原則

- **錯誤分類**：L1-L6 六級分類（含 HITL）
- **開發流程**：6 階段標準化
- **協作模式**：Sequential / Parallel / Hierarchical / P2P
- **品質把關**：Agent Quality Guard + Quality Gate
- **監控警報**：健康評分 + 三級警報
- **工具整合**：Model Router、Quality Guard、Monitor
- **正確性保障**：Timeout、A/B雙重驗證、Kickoff檢查
- **企業級支援**：ASPICE、Contract Testing、Traceability

---

## 使用方式

### 錯誤分類

```python
from methodology import ErrorClassifier

classifier = ErrorClassifier()

# 分類錯誤
level = classifier.classify(error)
# 返回: L1, L2, L3, 或 L4
```

### 任務生命週期

```python
from methodology import TaskLifecycle

lifecycle = TaskLifecycle()

# 執行任務
result = lifecycle.execute(task)
# 經過: 需求 → 規劃 → 執行 → 協調 → 品質 → 完成
```

### Agent 協作

```python
from methodology import Crew, Agent

crew = Crew(
    agents=[dev, reviewer, qa],
    process="sequential"  # 或 "parallel", "hierarchical"
)

result = crew.kickoff()
```

---

## 方法論要點

### L1-L4 錯誤分類

| 等級 | 類型 | 處理 |
|------|------|------|
| L1 | 輸入錯誤 | 立即返回 |
| L2 | 工具錯誤 | 重試 3 次 |
| L3 | 執行錯誤 | 降級處理 |
| L4 | 系統錯誤 | 熔斷 + 警報 |

### 開發流程

```
需求 → 優先級 → 開發 → 品質 → 文檔 → 發布
```

### 發布檢查清單

- [ ] 版本號更新
- [ ] CHANGELOG 記錄
- [ ] README 更新
- [ ] docs/ 同步
- [ ] 測試通過
- [ ] GitHub Release
- [ ] (可選) ClawHub

---

## 整合的專案

### 專案狀態

| 專案 | 版本 | 功能數 | GitHub |
|------|------|--------|--------|
| Agent Quality Guard | v1.0.3 | 10+ | ✅ |
| Model Router | v1.0.1 | 12+ | ✅ |
| Agent Monitor v2 | v2.1.0 | 12+ | ✅ |
| Agent Monitor v3 | v3.2.0 | 18+ | ✅ |
| ai-agent-toolkit | v2.1.0 | 6+ | ⏳ |

### 架構

```
methodology-v2
    │
    ├── ai-agent-toolkit/     (工具集)
    │   ├── Model Router       (智慧路由)
    │   ├── Quality Guard      (品質把關)
    │   └── Monitor            (監控)
    │
    ├── multi-agent-toolkit/   (協作框架)
    │   ├── Planner            (規劃)
    │   ├── Executor           (執行)
    │   └── Communication      (通訊)
    │
    └── methodology.py         (核心)
        ├── ErrorClassifier    (錯誤分類)
        ├── ErrorHandler       (錯誤處理)
        ├── TaskLifecycle      (生命週期)
        ├── QualityGate        (品質把關)
        ├── Crew               (協作)
        └── Monitor            (監控)
```

---

## 使用的 Skills (單獨維護)

這三個核心 Skill 會單獨維護，methodology-v2 的專案運作會使用它們：

| Skill | GitHub | 用途 |
|-------|---------|------|
| **Model Router** (v1.0.2) | johnnylugm-tech/model-router-v2 | 智慧模型路由 + M2.7 |
| **Agent Monitor** | johnnylugm-tech/agent-dashboard-v3 | 監控儀表板 |
| **Agent Quality Guard** | johnnylugm-tech/Agent-Quality-Guard | 品質把關 |

---

## 整合的 Skills

| Skill | 用途 | 整合方式 |
|-------|------|----------|
| **dispatching-parallel-agents** | 任務分配 | 方法論引用 |
| **sessions_spawn** | 建立子 Agent | OpenClawAdapter |
| **sessions_send** | 跨 Agent 溝通 | OpenClawAdapter |
| **verification-before-completion** | 交付前驗證 | AutoQualityGate |
| **requesting-code-review** | 程式碼審查 | 品質把關 |
| **agent-task-manager** | 任務管理 | 整合到 TaskSplitter |
| **long-term-memory** | 長期記憶 | 可與 Storage 搭配 |
| **executing-plans** | 執行計劃 | TaskLifecycle 引用 |
| **planning-with-files** | 規劃管理 | 任務規劃參考 |
| **finishing-a-development-branch** | 開發分支完成 | 發布流程參考 |

---

## 安裝

```bash
# 方式 1: 直接使用
pip install ai-agent-toolkit

# 方式 2: 開發模式
cd skills/methodology-v2
pip install -e .
```

---

## 範例

### 標準錯誤處理

```python
from methodology import ErrorHandler

handler = ErrorHandler()

try:
    result = agent.execute(task)
except Exception as e:
    level = handler.classify(e)
    handler.handle(e, level)
```

### 品質把關

```python
from methodology import QualityGate

gate = QualityGate()

if gate.check(result):
    return result
else:
    return gate.fix(result)
```

### 完整工作流

```python
from methodology import ErrorClassifier, Crew, Monitor, QualityGate

# 1. 錯誤處理
classifier = ErrorClassifier()

# 2. Agent 協作
crew = Crew(agents, process="sequential")
result = crew.kickoff()

# 3. 品質把關
gate = QualityGate()
if not gate.check(result):
    result = gate.fix(result)

# 4. 監控
monitor = Monitor()
monitor.register_agent(agent)
health = monitor.get_health_score(agent.id)
```

### Auto Quality Gate

自動運行 Agent Quality Guard 檢查並修復問題。

```python
from auto_quality_gate import AutoQualityGate

# 預設：自動修復開啟
gate = AutoQualityGate()  # auto_fix=True

# 關閉自動修復（需手動執行）
gate = AutoQualityGate(auto_fix=False)

# 1. 掃描 (如果 auto_fix=True，會自動修復)
report = gate.scan("your_code.py")
print(f"Score: {report.score}/100")

# 2. 手動修復 (auto_fix=False 時使用)
result = gate.fix(report)
print(f"Fixed: {result['success']}/{result['total']}")

# 3. 生成報告
print(gate.generate_report("markdown"))
```

#### 開關說明

| 設置 | 行為 |
|------|------|
| `auto_fix=True` (預設) | 掃描後自動修復可解決問題 |
| `auto_fix=False` | 僅掃描，需手動執行 `gate.fix(report)` |

---

### Agent Output Validator

結構化輸出驗證 + 自動修復，支援 JSON Schema / Pydantic / 自訂規則。

```python
from agent_output_validator import AgentOutputValidator, create_output_schema

# 初始化
validator = AgentOutputValidator()

# 建立 JSON Schema
schema = create_output_schema(
    "user_info",
    {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "email": {"type": "string", "pattern": r"^[\w.-]+@[\w.-]+\.\w+$"},
        "role": {"type": "string", "enum": ["admin", "user", "guest"]},
    },
    required=["id", "email"]
)

# 驗證輸出
report = validator.validate(
    {"id": 123, "name": "John", "email": "john@example.com"},
    schema
)
print(f"Valid: {report.valid}")

# 自動修復
fixed, fix_report = validator.auto_fix(
    {"id": "not_an_int", "email": "invalid"},
    schema
)
print(f"Fixes applied: {fix_report.fix_applied}")
```

#### 驗證類型

| 類型 | 說明 |
|------|------|
| JSON Schema | 標準 JSON Schema Draft-07 |
| Pydantic | BaseModel 子類驗證 |
| 自訂規則 | List[Dict] 定義的規則 |

#### 自訂規則範例

```python
rules = [
    {"field": "id", "check": "required"},
    {"field": "score", "check": "range", "min": 0, "max": 100},
    {"field": "email", "check": "pattern", "pattern": r"^[\w.-]+@[\w.-]+\.\w+$"},
    {"field": "status", "check": "enum", "values": ["active", "inactive"]},
]
```

#### 整合 StructuredOutputEngine

```python
from structured_output import StructuredOutputEngine

engine = StructuredOutputEngine()

# 驗證輸出（含自動修復）
result = engine.validate_output(
    output=data,
    schema="user_info",
    auto_fix=True
)

# 完整流程：Validator + QualityGate
result = engine.validate_and_fix_with_quality_gate(
    output=data,
    schema="user_info",
    quality_gate=quality_gate_instance,
    file_path="agent_output.py"
)
```

---

### Smart Router

基於 Model Router 的智慧路由，根據任務自動選擇最適合的 LLM。

```python
from smart_router import SmartRouter, TaskType, BudgetLevel

# 初始化 (預設 medium 預算)
router = SmartRouter()

# 或指定預算
router = SmartRouter(budget="low")   # 低成本
router = SmartRouter(budget="high")  # 高品質

# 路由任務
result = router.route("幫我寫一個 Python 函數")
print(f"Model: {result.model}")
print(f"Provider: {result.provider}")
print(f"Est. Cost: ${result.estimated_cost}")

# 強制使用模型
result = router.route(task, force_model="gpt-4")

# 列出可用模型
models = router.list_models()
```

#### 任務類型

| 類型 | 關鍵詞 |
|------|--------|
| CODING | code, program, function, debug |
| REVIEW | review, critique, check |
| WRITING | write, draft, compose |
| ANALYSIS | analyze, compare, evaluate |
| TRANSLATION | translate, convert |
| CREATIVE | idea, brainstorm, creative |

#### 預算等級

| 等級 | 說明 |
|------|------|
| LOW | 低成本模型 |
| MEDIUM | 平衡成本與品質 |
| HIGH | 高品質模型 |

#### 配置開關

```python
from smart_router import SmartRouter

# 預設：自動路由開啟
router = SmartRouter()  # auto_route=True

# 關閉自動路由（使用預設模型）
router = SmartRouter(auto_route=False)

# 自定義配置
router = SmartRouter(config={
    "auto_route": False,
    "default_model": "claude-3-sonnet",
    "budget": "high",
    "fallback_model": "gpt-3.5-turbo"
})
```

#### 預設配置

```python
DEFAULT_CONFIG = {
    "auto_route": True,       # 自動路由（預設開）
    "default_model": "gemini-pro",  # 預設模型
    "budget": "medium",       # 預算等級
    "fallback_model": "gpt-3.5-turbo",  # 備用模型
}
```

| 設置 | 說明 |
|------|------|
| auto_route=True (預設) | 根據任務自動選擇模型 |
| auto_route=False | 使用 default_model 設定 |

#### 命令列

```bash
# 掃描
python auto_quality_gate.py scan your_code.py

# 自動修復
python auto_quality_gate.py fix your_code.py

# 生成報告
python auto_quality_gate.py report
```

---

### 統一 Dashboard

#### 方式 1: 命令列

```bash
# 輕量版 (v2)
python dashboard.py light
python dashboard.py v2

# 完整版 (v3，預設)
python dashboard.py full
python dashboard.py v3

# 從配置文件啟動
python dashboard.py --config config.json

# 訪問 http://localhost:8080
```

#### 預設配置

```python
DEFAULT_CONFIG = {
    "version": "full",     # 版本：light (v2) / full (v3)
    "port": 8080,
    "auto_start": True,
}
```

#### 方式 2: Python API

```python
from methodology import Dashboard

# 預設：完整版 (v3)
dashboard = Dashboard()

# 輕量版 (v2)
dashboard = Dashboard(mode="light")
dashboard = Dashboard(mode="v2")

# 完整版 (v3)
dashboard = Dashboard(mode="full")
dashboard = Dashboard(mode="v3")

# 自定義配置
dashboard = Dashboard(config={
    "version": "light",
    "port": 9000,
    "auto_start": True
})
```

功能：
- 📡 Model Router 指標（請求、成本、快取命中率）
- 🤖 Agent Monitor 指標（健康、任務、警報）
- 📈 趨勢圖表（ECharts）
- 🔄 統一介面封裝 v2/v3 功能

---

---

## 工作產品 (Work Products)

結構化追蹤 Agent 產出，確保每個產出都有明確的類型、擁有者和驗證狀態。

### 基本使用

```python
from work_product import WorkProductRegistry, ProductType, register_product

# 初始化
registry = WorkProductRegistry()

# 快速註冊
product = register_product(
    name="用戶認證模組",
    product_type=ProductType.CODE,
    owner_agent_id="agent-dev-001",
    content="def authenticate(user, passwd): ...",
    metadata={"language": "python"}
)

# 驗證
product.verify("reviewer-001")

# 查詢
summary = registry.get_verification_summary()
print(f"驗證率: {summary['verification_rate']}")
```

### 產品類型

| 類型 | 說明 |
|------|------|
| CODE | 代碼產出 |
| DOCUMENT | 文檔資料 |
| REPORT | 報告分析 |
| TEST_RESULT | 測試結果 |
| CONFIG | 配置檔案 |
| MODEL | 模型檔案 |
| DATA | 資料檔案 |

### 驗證狀態

| 狀態 | 說明 |
|------|------|
| UNVERIFIED | 待驗證 |
| VERIFIED | 已驗證 |
| FAILED | 驗證失敗 |

### 查詢方式

```python
# 依 Agent 查詢
registry.get_by_agent("agent-dev-001")

# 依類型查詢
registry.get_by_type(ProductType.CODE)

---

## 附錄：正確的模組使用方式

### Fault Tolerant

```python
from fault_tolerant import CircuitBreaker, FaultTolerantExecutor

# 初始化（需要 name 參數）
cb = CircuitBreaker(name="my-circuit")
executor = FaultTolerantExecutor(name="my-executor")

# 使用裝飾器
@with_fault_tolerance(max_retries=3, backoff=2.0)
async def my_function():
    pass
```

### Governance

```python
from governance.governance_agent import GovernanceAgent

agent = GovernanceAgent()
```

### Error Classification

```python
from methodology_base import ErrorClassifier, ErrorLevel

classifier = ErrorClassifier()
level = classifier.classify(ValueError("test"))
# 返回: ErrorLevel.L1, L2, L3, L4, L5, L6
```

# 取得未驗證產品
registry.get_unverified()

# 驗證摘要
registry.get_verification_summary()
```

詳細案例：請參考 `docs/cases/case33_work_products.md`

---

### Async Executor

對標 AutoGen 的 async/await 支援，提供 asyncio 原生的並發任務執行能力。

```python
from async_executor import AsyncExecutor, run_async, run_parallel

# 使用 executor
executor = AsyncExecutor(max_concurrency=5)

async def my_task(name):
    await asyncio.sleep(1)
    return f"{name} done"

# 創建任務
executor.create_task("task1", my_task("A"))
executor.create_task("task2", my_task("B"))

# 執行並取得結果
results = await executor.execute_all()

# 便捷函數
result = await run_async(agent.execute("task"), timeout=30.0)
results = await run_parallel(task1(), task2(), task3(), max_concurrency=10)
```

| 功能 | 說明 |
|------|------|
| 並發執行 | 控制最大並發數，避免資源耗盡 |
| 超時控制 | 支援任務級別的超時設定 |
| 錯誤處理 | 單一任務失敗不影響其他任務 |
| 結果收集 | 統一收集所有任務結果 |

詳細案例：請參考 `docs/cases/case37_async_executor.md`

---

## 統一角色定義 (Agent Role)

對標 CrewAI 的 Role-based Agent 概念，實現統一的角色定義系統。

```python
from agent_role import (
    AgentRole, 
    RoleType, 
    Permission, 
    Skill,
    RoleRegistry
)

# 建立角色
dev_role = AgentRole(
    role_id="role-dev-001",
    name="Developer",
    role_type=RoleType.DEVELOPER,
    goals="Write high-quality code",
    backstory="Experienced software engineer",
    permissions=[Permission.READ, Permission.WRITE, Permission.EXECUTE],
    skills=[Skill("coding", 5), Skill("debugging", 4)]
)

# 檢查權限
dev_role.has_permission(Permission.WRITE)  # True

# 使用角色註冊表
registry = RoleRegistry()
registry.register(dev_role)
role = registry.get("role-dev-001")
```

### 預設角色

| 角色 | ID | 權限 |
|------|-----|------|
| Developer | role-dev | read, write, execute |
| Code Reviewer | role-review | read, approve |
| Project Manager | role-pm | read, write, approve, delete |

詳細案例：請參考 `docs/cases/case34_agent_role.md`

---

*這個方法論幫助團隊標準化多 Agent 協作開發流程*
