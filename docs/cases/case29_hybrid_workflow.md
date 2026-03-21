# Case 29: Hybrid Workflow - 智慧分流工作流

## 情境

開發團隊需要一個智能的 A/B 審查工作流：
- 小改動（< 10 行）自動通過，節省時間
- 大改動（> 30 行或安全相關）必須審查
- 安全相關變更（auth、password、token）永遠審查

## 解決方案

```python
from hybrid_workflow import HybridWorkflow, WorkflowMode

# 初始化（預設 HYBRID 模式）
workflow = HybridWorkflow(
    mode=WorkflowMode.HYBRID,
    small_change_threshold=10,
    large_change_threshold=30
)

# 模擬一個 diff
diff = """
+def authenticate_user(username, password):
+    token = generate_token(username)
+    return {"status": "success", "token": token}
- def old_auth():
-     pass
"""

# 分析變更
analysis = workflow.analyze_change(diff)
print(f"類型: {analysis.type.value}")
print(f"行數: {analysis.lines_changed}")
print(f"原因: {analysis.reason}")

# 執行（自動路由）
def code_func():
    return "code_executed"

result = workflow.execute(diff, code_func)
print(f"狀態: {result['status']}")
# => 狀態: needs_review (因為包含 auth 關鍵字)
```

## 三種模式

| 模式 | 行為 |
|------|------|
| `OFF` | 單一 Agent，所有變更自動通過 |
| `HYBRID` | 智慧分流，小改自動，大改審查 |
| `ON` | 強制 A/B 審查，所有變更都需要審查 |

## 小改自動通過

```python
# 小改動示例（< 10 行）
small_diff = """
+def helper():
+    return True
"""

result = workflow.execute(small_diff, lambda: "done")
print(result["status"])
# => "auto_approved"
print(result["message"])
# => "自動通過：改動 < 10 行"
```

## 大改需要審查

```python
# 大改動示例（> 30 行或有安全關鍵字）
large_diff = """
+def new_auth():
+    # 50+ 行認證邏輯
+    ...
"""

result = workflow.execute(large_diff, lambda: "done")
print(result["status"])
# => "needs_review"
print(result["message"])
# => "需要審查：改動 > 30 行"
```

## 結合 ApprovalFlow

```python
from hybrid_workflow import HybridWorkflow
from approval_flow import ApprovalFlow

workflow = HybridWorkflow(mode=WorkflowMode.HYBRID)
approval = ApprovalFlow()

diff = "+def new_payment(): ..."

result = workflow.execute(diff, lambda: execute_code())

if result["status"] == "needs_review":
    approval.create_request(
        name=f"Code Review: {result['analysis'].reason}",
        approval_type="code_review",
        requester="agent-1",
        requester_name="AI Agent"
    )
    print("已創建審批請求，等待人類審查...")
else:
    print("自動通過，代碼已執行")
```

## 統計監控

```python
stats = workflow.get_stats()
print(stats)
# {
#     "auto_approved": 45,
#     "review_required": 12,
#     "total_tasks": 57,
#     "auto_approve_rate": "78.9%",
#     "review_rate": "21.1%"
# }
```

## CLI

```bash
# 查看審批統計
python cli.py approval stats

# 列出待審批
python cli.py approval list
```

## 功能

| 功能 | 說明 |
|------|------|
| 智慧分流 | 小改自動，大改審查 |
| 安全優先 | 安全關鍵字永遠審查 |
| 統計報表 | 追蹤審批通過率 |
| 模式切換 | OFF/HYBRID/ON 三種模式 |

## Related

- hybrid_workflow.py
- approval_flow.py
- hybrid_workflow/SKILL.md
