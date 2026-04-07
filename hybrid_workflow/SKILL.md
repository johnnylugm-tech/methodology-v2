---
name: hybrid-workflow
description: Hybrid A/B Workflow for methodology-v2. Smart routing for code changes - small changes auto-approve, large changes require review.
---

# Hybrid Workflow

智慧分流工作流 - 小改自動通過，大改需審查

## Quick Start

```python
from hybrid_workflow import HybridWorkflow, WorkflowMode

# Initialize with HYBRID mode (default)
workflow = HybridWorkflow(mode=WorkflowMode.HYBRID)

# Analyze a diff
diff = """
+def new_feature():
+    pass
- old_code()
"""

analysis = workflow.analyze_change(diff)
print(f"Change type: {analysis.type.value}")
print(f"Lines: {analysis.lines_changed}")
print(f"Reason: {analysis.reason}")

# Execute with routing decision
def code_func():
    return "executed"

result = workflow.execute(diff, code_func)
print(result["status"])  # "auto_approved" or "needs_review"
```

## Workflow Modes

| Mode | Behavior |
|------|----------|
| `OFF` | 單一 Agent，所有變更自動通過 |
| `HYBRID` | 智慧分流，小改自動，大改審查 |
| `ON` | 強制 A/B 審查，所有變更都需要審查 |

## Change Classification

| Type | Criteria |
|------|----------|
| **SMALL** | 改動 < 10 行，且無安全相關關鍵字 |
| **LARGE** | 改動 > 30 行，或包含安全相關/新功能關鍵字 |

### 安全關鍵字 (強制大改)
- `auth`, `password`, `token`, `permission`, `security`

### 新功能關鍵字 (強制大改)
- `def new_`, `class new_`, `# 新增`, `# new`

## API Reference

### HybridWorkflow

```python
class HybridWorkflow:
    def __init__(
        self,
        mode: WorkflowMode = WorkflowMode.HYBRID,
        small_change_threshold: int = 10,
        large_change_threshold: int = 30
    )
```

### Methods

#### `analyze_change(diff: str) -> ChangeAnalysis`
分析變更內容，返回詳細分析。

#### `should_review(analysis: ChangeAnalysis) -> bool`
根據分析結果判斷是否需要審查。

#### `execute(diff: str, code_func: Callable) -> dict`
執行變更，自動路由。

#### `get_stats() -> dict`
取得統計數據。

### ChangeAnalysis

```python
@dataclass
class ChangeAnalysis:
    type: ChangeType           # SMALL or LARGE
    lines_changed: int        # 總行數變更
    files_affected: int       # 受影響檔案數
    is_security_related: bool # 是否涉及安全
    is_new_feature: bool      # 是否為新功能
    reason: str               # 分類原因
```

## CLI Usage

```bash
# Import into CLI for workflow management
python cli.py workflow --mode hybrid --diff "file.diff"
```

## Integration

### With ApprovalFlow

```python
from hybrid_workflow import HybridWorkflow
from approval_flow import ApprovalFlow

workflow = HybridWorkflow(mode=WorkflowMode.HYBRID)
approval = ApprovalFlow()

result = workflow.execute(diff, code_func)

if result["status"] == "needs_review":
    approval.create_request(
        name=f"Code Review: {result['analysis'].reason}",
        approval_type="code_review"
    )
```

### With AgentTeam

```python
from hybrid_workflow import HybridWorkflow
from agent_team import AgentTeam

team = AgentTeam()
workflow = HybridWorkflow(mode=WorkflowMode.HYBRID)

# Agent 执行前检查
def agent_task():
    diff = team.generate_diff()
    result = workflow.execute(diff, lambda: team.execute_task())
    
    if result["status"] == "needs_review":
        team.pause_and_review()
    return result

team.register_pre_execution_hook(agent_task)
```

## Statistics

```python
stats = workflow.get_stats()
# {
#     "auto_approved": 45,
#     "review_required": 12,
#     "total_tasks": 57,
#     "auto_approve_rate": "78.9%",
#     "review_rate": "21.1%"
# }
```

## Best Practices

1. **調整閾值** - 根據團隊規模調整 `small_change_threshold` 和 `large_change_threshold`
2. **安全優先** - 安全相關關鍵字永遠觸發審查
3. **監控統計** - 定期檢查 `auto_approve_rate`，調整模式
4. **結合審批** - HYBRID 模式建議配合 `approval_flow.py` 使用
