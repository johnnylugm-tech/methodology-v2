# Main Agent Playbook — Sub-Agent 管理最佳實踐

> **目標**：消滅「主代理自己注意」的模糊地帶。每一個管理行為都有明確觸發時機、標準流程、產出格式。

---

## 核心理念

```
工具不缺，缺的是什麼時候用、怎麼用。

本文件 = 觸發時機決策樹 + 標準化流程 + 產出格式
```

---

## 四大工具定位

| 工具 | 解決的問題 | 觸發時機 |
|------|-----------|---------|
| `KnowledgeCurator` | 知識一致性 | 任務開始前 + 任何知識疑惑時 |
| `ContextManager` | 上下文膨脹 | 每 30 輪 或 自覺迷失時 |
| `SubagentIsolator` | 結果污染 / 合併混亂 | 每次 spawn 前 + 收集結果時 |
| `PermissionGuard` | 危險操作失控 | 任何 exec / rm / network 操作前 |

---

## 標準工作流

### Phase 1: 任務接收

```
1. Johnny 說任務
       ↓
2. KnowledgeCurator.load_skill() → 確認 SKILL 版本
       ↓
3. KnowledgeCurator.verify_coverage() → 驗證 FR 覆蓋率
       ↓
4. 若覆蓋率 < 90% → 報警，拒絕開始
       ↓
5. 建立 TaskContext（ContextManager.create_task）
       ↓
6. 規劃 Subagent 角色分配（用 SubagentIsolator）
```

### Phase 2: Subagent 派遣

```
1. SubagentIsolator.spawn()
   - role = DEVEROPER / REVIEWER / TESTER / VERIFIER
   - context = TaskContext ID + 關鍵產物路徑
   - timeout = 依據 Phase 估算（見附錄）
       ↓
2. 記錄 session_key → state.json["active_subagents"]
       ↓
3. Subagent 執行中（不干預）
       ↓
4. 結果返回 → SubagentIsolator.merge()
   - 只提取 result / confidence / citations / summary
   - 拋棄其餘雜訊
```

### Phase 3: 結果驗收

```
1. 若 confidence < 6 → 重新派遣（最多 3 次）
       ↓
2. 若 citations 為空 → 降級標記（可能存在幻覺）
       ↓
3. ContextManager.compress() → 訊息 > 50 條時
       ↓
4. 產物寫入 Git → SubagentIsolator 記錄 artifact path
       ↓
5. ContextManager.complete_task() → 更新 TaskContext 狀態
```

### Phase 4: 危險把關

```
任何時刻執行 exec / rm / network 前：
       ↓
PermissionGuard.check(Operation(...))
       ↓
若 status == DENIED → 立即停止，報告 Johnny
若 status == PENDING → 等待審批，最多 30 秒
若 status == BLOCKED → 全面停止，觸發 HR-14
```

---

## 觸發時機決策樹

### 上下文何時該壓縮？

```
context_length > 200  →  L3（存檔）
context_length > 100  →  L2（提取關鍵資訊）
context_length > 50   →  L1（摘要）
context_length < 50   →  不動
```

### 何時懷疑 Subagent 結果？

```
confidence < 6         →  重新派遣
citations 為空         →  標記「未經證實」
citations > 10         →  正常
同一 task 失敗 3 次    →  上報 Johnny
```

### 何時該新建 Subagent？

```
任務可獨立切割（無依賴）  →  同時派遣多個
任務有前後依賴           →  順序派遣
任務需要不同專業          →  按角色派遣（Architect → Dev → Reviewer）
```

---

## 程式碼範本

### 完整任務流程

```python
from knowledge_curator import KnowledgeCurator
from context_manager import ContextManager
from subagent_isolator import SubagentIsolator, AgentRole
from permission_guard import PermissionGuard, Permission, Operation, ApprovalStatus

# === INIT ===
kc = KnowledgeCurator()
cm = ContextManager(state_path=".methodology/state.json")
si = SubagentIsolator()
pg = PermissionGuard()

# === Phase 1: 任務接收 ===
skill = kc.load_skill("methodology-v2")
coverage = kc.verify_coverage(["01", "02", "03"])

if coverage["coverage"] < 0.9:
    raise Exception(f"FR 覆蓋率不足: {coverage['missing']}")

task = cm.create_task(
    task_id="task-001",
    title="Implement FR-01",
    dependencies=[]
)

# === Phase 2: 派遣 ===
result = si.spawn(
    role=AgentRole.DEVELOPER,
    task="Implement FR-01 based on SRS",
    context={
        "task_id": task.task_id,
        "fr": "FR-01",
        "srs_path": "docs/SRS.md"
    },
    timeout=300  # 5 分鐘
)

# === Phase 3: 驗收結果 ===
if result.confidence < 6:
    print(f"⚠️ confidence 低，重新派遣")
    result = si.spawn(role=AgentRole.DEVELOPER, task="...", timeout=300)

merged = si.merge(result)
print(f"Status: {merged['status']}, Summary: {merged['summary']}")

cm.add_message(task.task_id, {
    "role": "assistant",
    "content": merged["summary"]
})

# === Phase 4: 完成 ===
cm.complete_task(task.task_id, artifacts={
    "fr01_code": "src/FR01.py"
})

# === 危險把關 ===
op = Operation(
    type="exec",
    permission=Permission.EXEC_BASH,
    target="rm -rf /"
)
guard_result = pg.check(op)
if guard_result.status == ApprovalStatus.DENIED:
    print(f"🚫 危險操作被拒絕: {guard_result.decision}")
```

### 批量派遣（並行）

```python
# 同時派遣三個角色（無依賴）
results = [
    si.spawn(role=AgentRole.ARCHITECT, task="Design architecture", timeout=600),
    si.spawn(role=AgentRole.DEVELOPER, task="Implement core", timeout=600),
    si.spawn(role=AgentRole.TESTER, task="Write tests", timeout=300),
]

# 全部完成後收集
merged_results = si.merge_all()

# 評估整體健康度
integrity = si.get_integrity_score()
print(f"隔離完整性: {integrity:.1%}")
```

### 壓縮觸發

```python
# 每次工具回傳後檢查長度
messages = get_current_messages()  # 你的訊息列表

result = cm.compress(messages, level="auto")
if result.compressed_len < result.original_len:
    print(f"✅ 壓縮: {result.original_len} → {result.compressed_len} (Level: {result.level})")
```

---

## 狀態機整合（FSM）

```
        ┌──────────────────────────────────────────┐
        │                                          │
        ▼                                          │
     INIT ──→ RUNNING ──→ VERIFYING ──→ WRITING ──→ COMPLETED
        │         │            │            │
        │         ▼            ▼            │
        │       PAUSED ◄─────┘             │
        │         │                        │
        │         ▼                        │
        └────── FREEZE (HR-14)             │
        │                                    │
        └────────────────────────────────────┘
```

**狀態轉換規則：**

| 當前狀態 | 條件 | 下一狀態 |
|---------|------|---------|
| INIT | Task 建立 | RUNNING |
| RUNNING | Subagent 回傳 | VERIFYING |
| VERIFYING | Verify_Agent 通過 | WRITING |
| VERIFYING | Verify_Agent 失敗 | RUNNING（重試） |
| WRITING | 產物寫入 | COMPLETED |
| ANY | HR-14 觸發 | FREEZE |

---

## 日誌與可追溯性

每次 Subagent 派遣後，寫入 state.json：

```json
{
  "active_subagents": [
    {
      "session_key": "sub_developer_abc123",
      "role": "developer",
      "task_id": "task-001",
      "started_at": "2026-04-03T06:30:00Z",
      "timeout": 300
    }
  ],
  "tasks": {
    "task-001": {
      "status": "completed",
      "artifacts": {
        "fr01_code": "src/FR01.py"
      },
      "summary": "Implement FR-01..."
    }
  }
}
```

---

## 產出格式標準

Subagent 結果必須包含：

```json
{
  "status": "success | error | unable_to_proceed",
  "result": "實際產出（字串或物件）",
  "confidence": 1-10,
  "citations": ["FR-01", "SRS.md#section"],
  "summary": "50 字內摘要"
}
```

**置信度評估標準：**

| 分數 | 意義 | 動作 |
|------|------|------|
| 9-10 | 高度確定，有引用 | 繼續 |
| 7-8 | 確定，無引用 | 標記，繼續 |
| 5-6 | 不確定 | 重新派遣 |
| 1-4 | 嚴重懷疑 | 上報 Johnny |

---

## 常見錯誤腳本

### ❌ 錯誤：直接使用父 Agent 訊息啟動 Subagent

```python
# 錯誤示範
messages = get_current_messages()  # 繼承了父 Agent 的全部上下文
spawn(role=DEVELOPER, task="...", messages=messages)  # 污染風險
```

### ✅ 正確：Fresh messages[]

```python
# 正確示範
messages = [
    {"role": "system", "content": get_persona(DEVELOPER)},
    {"role": "user", "content": f"任務：{task}\n\n上下文：{context_json}"}
]
spawn(role=DEVELOPER, task="...", messages=messages)  # 乾淨隔離
```

### ❌ 錯誤：Subagent 結果直接使用不驗證

```python
# 錯誤示範
result = spawn(...)
use(result.result)  # 可能含幻覺或錯誤
```

### ✅ 正確：驗收 + Merge

```python
# 正確示範
result = spawn(...)
if result.confidence < 6:
    respawn()  # 重新派遣
merged = merge(result)
verify(merged.result)  # 獨立驗證
```

### ❌ 錯誤：壓縮前不備份長上下文

```python
# 錯誤示範
compress(messages)  # 直接壓縮，原始內容丟失
```

### ✅ 正確：L3 自動存檔

```python
# 正確示範
result = compress(messages, level="L3")
# 自動存檔到 .methodology/archives/
# result.archive_path 可供後續查閱
```

---

## 附錄：Timeout 參考表

| Phase | 複雜度 | 建議 Timeout |
|-------|--------|------------|
| Phase 1 初始化 | 低 | 60s |
| Phase 2 架構設計 | 中 | 300s |
| Phase 3 程式開發 | 高 | 600s |
| Phase 4 測試 | 中 | 300s |
| Phase 5 部署 | 低 | 120s |
| Phase 6 維運監控 | 中 | 180s |

---

## 健康度檢查清單（每次 Heartbeat）

```
□ active_subagents 是否有超時 session？（> timeout）
□ 最近 50 條訊息是否需要壓縮？
□ pending_approval 是否有待審批危險操作？
□ task 狀態是否與實際執行一致？
□ integrity_score 是否 < 0.7？
```

---

*本文件為 Main Agent 專用，其他 Agent 不可讀取*
