# 強制 A/B 協作工作流（必讀）

**版本**: v1.0  
**生效日期**: 2026-03-27  
**狀態**: 強制執行

---

## ⚠️ 這不是選項，是強制執行

| 項目 | 之前（錯誤） | 之後（強制） |
|------|-------------|--------------|
| Agent 數量 | 1 個（我自己） | 2+ 個 |
| 審查 | 自己審自己 | 必須不同人 |
| 角色 | 沒用到 | Developer + Reviewer + Tester |
| Workflow | 沒用 | HybridWorkflow(mode="ON") |

---

## 啟動方式（每次專案開始前執行）

```python
# 1. 強制啟動 Multi-Agent（不是選項，是必須）
from methodology import quick_start

# 2 Agent: Developer + Reviewer（最小配置）
team = quick_start("dev")

# 或 4 Agent（完整配置）
# team = quick_start("full")

# 2. 強制使用 Hybrid Workflow（不是選項，是必須）
from hybrid_workflow import HybridWorkflow, WorkflowMode

workflow = HybridWorkflow(mode=WorkflowMode.ON)  # 強制 A/B
```

---

## 角色定義（強制分工）

| 角色 | 職責 | 不能做的 |
|------|------|----------|
| **Developer** | 寫 code | 不能審查自己寫的 |
| **Code Reviewer** | 審查 code | 不能寫 code |
| **Tester** | 執行測試 | 不能跳過測試 |
| **Architect** | 確認架構 | 不能忽視設計 |

---

## A/B 協作流程（每個 commit 前必做）

```
Step 1: Developer 寫 code
   ↓
Step 2: Code Reviewer 審查（不能是 Developer 同一人）
   ↓
   ├─ 如果 reject → 回 Developer 修正 → 重審
   └─ 如果 approve → 往下
   ↓
Step 3: Tester 執行 pytest（實際執行，不能只看）
   ↓
Step 4: 兩人交換角色，再做一次（交換審查）
   ↓
才能 commit
```

---

## 強制檢查清單（每次 commit 前勾選）

- [ ] Developer 寫完 code
- [ ] Code Reviewer 審查並 approve（不是 Developer）
- [ ] Tester 執行 pytest 實際通過
- [ ] 交換角色後，另一個 Reviewer 也 approve
- [ ] HybridWorkflow mode = ON
- [ ] commit message 有兩個人確認

---

## 如果沒做到會怎樣？

| 違規 | 後果 |
|------|------|
| 只有 1 個 Agent | commit 被阻止 |
| 自己審自己 | commit 被阻止 |
| 沒跑測試就 commit | commit 被阻止 |
| 交換角色沒做 | commit 被阻止 |
| mode 不是 ON | commit 被阻止 |

---

## 驗證命令

```bash
# 確認團隊有 2+ Agent
team.list_agents()  # 應該顯示 Developer + Reviewer

# 確認 Workflow mode 是 ON
echo $WORKFLOW_MODE  # 應該是 "ON"

# 確認有 A/B 審查記錄
git log --all --grep="Reviewer" --oneline
```

---

*強制執行日期: 2026-03-27*