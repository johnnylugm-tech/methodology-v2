# Case 32: Traceability Matrix - ASPICE 追溯性矩陣

## 概述

本案例展示如何在 AI-native Multi-Agent 系統中實現 ASPICE 合規的追溯性矩陣，實現「零負擔、自動化」的執行鏈記錄。

## 問題背景

傳統軟體開發中，追溯性矩陣通常需要大量手動維護：
- 手動記錄每個需求的設計實現
- 手動更新追溯表格
- 難以追蹤動態的 Agent 執行過程

**挑戰：**
1. AI-native 系統中，Agent 行為是動態的，很難事先定義完整追溯
2. 過多的手動記錄會降低開發效率
3. 需要同時滿足人類可讀性和機器可解析性

## 解決方案：AI-native Traceability Matrix

### 核心思想

```
┌─────────────────────────────────────────────────────────┐
│                    Traceability Matrix                  │
│                                                          │
│  task ──→ agent ──→ output ──→ verification ──→ signed  │
│    │                                            │        │
│    └──────────────── 自動記錄 ──────────────────┘        │
│                                                          │
│  零額外負擔：每個操作自動建立追溯鏈接                      │
└─────────────────────────────────────────────────────────┘
```

### 實現架構

```python
# traceability_matrix.py

class TraceabilityMatrix:
    def __init__(self):
        self.links = {}  # link_id -> TraceLink
        self.task_outputs = {}  # task_id -> [output_ids]
    
    def add_link(self, source_type, source_id, target_type, target_id):
        # 自動建立追溯鏈
        link_id = f"TRL-{uuid.uuid4().hex[:8]}"
        self.links[link_id] = TraceLink(...)
        return link_id
```

## 使用場景

### 場景 1：任務分配追溯

```python
from traceability_matrix import get_traceability_matrix

trace = get_traceability_matrix()

# 當任務被分配給 Agent 時
task_id = "task-001"
agent_id = "architect-001"

link_id = trace.add_link(
    source_type="task",
    source_id=task_id,
    target_type="agent",
    target_id=agent_id
)

print(f"已建立追溯鏈: {link_id}")
# 輸出: 已建立追溯鏈: TRL-a1b2c3d4
```

### 場景 2：產出追溯

```python
# 當 Agent 完成任務產生輸出時
output_id = "output-001"
trace.add_link(
    source_type="agent",
    source_id=agent_id,
    target_type="output",
    target_id=output_id
)
```

### 場景 3：驗證狀態追蹤

```python
# 當 Quality Gate 通過時
trace.mark_verified(link_id, verifier="quality-gate")

# 當 Quality Gate 失敗時
trace.mark_failed(failed_link_id, reason="output format mismatch")
```

### 場景 4：查詢完整追溯鏈

```python
# 查詢某任務的完整執行歷史
chain = trace.get_trace("task-001")

for link in chain:
    print(f"{link.source_id} -> {link.target_id} [{link.status.value}]")
```

### 場景 5：完整性驗證

```python
# 驗證所有鏈接是否都已追溯
completeness = trace.verify_completeness()

print(f"總鏈接數: {completeness['total_links']}")
print(f"已驗證: {completeness['verified']}")
print(f"完成率: {completeness['complete_rate']}")
```

## ASPICE 合規報告

```python
# 生成 ASPICE 合規報告
report = trace.get_aspice_report()

# 報告結構
{
    "project_id": "my-project",
    "aspice_compliance": {
        "traceability_complete": True,
        "verification_complete": True,
        "coverage": {
            "tasks_with_agent_assignment": 10,
            "tasks_with_outputs": 10
        }
    },
    "summary": {
        "total_links": 20,
        "verified": 20,
        "complete_rate": "100.0%"
    }
}
```

## 完整範例

```python
#!/usr/bin/env python3
"""
ASPICE 追溯性矩陣完整範例
"""

from traceability_matrix import TraceabilityMatrix

def main():
    # 初始化
    trace = TraceabilityMatrix(project_id="autonomous-driving-v2")
    
    # ===== 任務生命週期 =====
    
    # 1. 定義任務
    tasks = [
        {"id": "task-001", "name": "感知模組設計"},
        {"id": "task-002", "name": "決策模組設計"},
        {"id": "task-003", "name": "控制模組設計"},
    ]
    
    # 2. 分配 Agent
    agents = [
        {"id": "agent-perception", "task": "task-001"},
        {"id": "agent-decision", "task": "task-002"},
        {"id": "agent-control", "task": "task-003"},
    ]
    
    for agent in agents:
        # 建立 task → agent 追溯
        trace.add_link("task", agent["task"], "agent", agent["id"])
    
    # 3. Agent 執行並產生輸出
    for agent in agents:
        output_id = f"output-{agent['id'].split('-')[1]}"
        # 建立 agent → output 追溯
        trace.add_link("agent", agent["id"], "output", output_id)
    
    # 4. 驗證 Quality Gate
    for link in trace.links.values():
        if link.link_type.value == "agent→output":
            trace.mark_verified(link.link_id, verifier="quality-gate")
    
    # 5. 生成 ASPICE 合規報告
    report = trace.get_aspice_report()
    
    print("=== ASPICE 追溯性報告 ===")
    print(f"專案: {report['project_id']}")
    print(f"追溯完整性: {report['aspice_compliance']['traceability_complete']}")
    print(f"驗證完成率: {report['aspice_compliance']['verification_complete']}")
    print(f"總鏈接數: {report['summary']['total_links']}")
    print(f"已驗證: {report['summary']['verified']}")
    print(f"完成率: {report['summary']['complete_rate']}")
    
    # 6. 保存報告
    trace.save("aspice_trace_report.json")
    print("\n報告已保存至 aspice_trace_report.json")

if __name__ == "__main__":
    main()
```

## 輸出示例

```
=== ASPICE 追溯性報告 ===
專案: autonomous-driving-v2
追溯完整性: True
驗證完成率: True
總鏈接數: 6
已驗證: 3
完成率: 50.0%
(其他3個鏈接為 task→agent，尚未產生 output)

報告已保存至 aspice_trace_report.json
```

## 與現有系統整合

### 與 AutoQualityGate 整合

```python
# 在 auto_quality_gate.py 中
from traceability_matrix import get_traceability_matrix

class AutoQualityGate:
    def __init__(self):
        self.trace = get_traceability_matrix()
    
    def verify_output(self, output, context):
        result = self.run_quality_checks(output)
        
        if result.passed:
            # 自動標記為已驗證
            link_id = context.get("link_id")
            if link_id:
                self.trace.mark_verified(link_id, verifier="auto-quality-gate")
        
        return result
```

### 與 HITL Controller 整合

```python
# 在 hitl_controller.py 中
from traceability_matrix import get_traceability_matrix

class HITLController:
    def __init__(self):
        self.trace = get_traceability_matrix()
    
    def approve_output(self, output_id, approver):
        # 建立 output → verification 追溯
        link_id = self.trace.add_link(
            "output", output_id,
            "verification", f"verify-{output_id}"
        )
        
        # 人類審批後標記為已驗證
        self.trace.mark_verified(link_id, verifier=approver)
```

## 優勢總結

| 傳統方式 | AI-native Traceability |
|---------|------------------------|
| 手動維護表格 | 自動記錄 |
| 容易遺漏 | 不會遺漏 |
| 更新不及時 | 實時更新 |
| 難以追溯動態行為 | 支持動態追溯 |
| 人類可讀性差 | 人機雙友好 |

## 結論

Traceability Matrix 實現了：
- ✅ **零負擔**：無需手動記錄，自動建立追溯鏈
- ✅ **ASPICE 合規**：滿足汽車行業軟體流程標準
- ✅ **客觀證據**：每次操作都有可追溯的記錄
- ✅ **完整性驗證**：自動檢測追溯缺口
- ✅ **報告生成**：一鍵生成合規報告
