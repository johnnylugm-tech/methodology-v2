# Hybrid A/B Workflow 上手指南

## 🎯 目標

讓新團隊在 30 分鐘內理解 Hybrid A/B Workflow 的核心概念和使用方式。

---

## 1️⃣ 為什麼需要 Hybrid？

### 傳統方式的問題

```
100% 自動 → 速度快但品質不穩定
100% 審查 → 品質高但速度慢
```

### Hybrid 的答案

```
Hybrid = 速度 + 品質

小改動 → 自動通過（快）
大改動 → A/B 審查（穩）
```

---

## 2️⃣ 三種模式解釋

| 模式 | 什麼情況用 | 速度 | 品質 |
|------|----------|------|------|
| **OFF** | POC、原型、實驗 | ⚡⚡⚡ | 😐 |
| **HYBRID** | 日常開發 | ⚡⚡ | 😐😐 |
| **ON** | 正式發布、生產 | ⚡ | 😐😐😐 |

### 什麼時候用 OFF？

- 快速驗證想法
- 實驗性功能
- 個人開發

### 什麼時候用 HYBRID？

- **團隊日常開發（預設）**
- 新功能開發
- 重構

### 什麼時候用 ON？

- 發布到生產環境
- 安全相關改動
- 重大版本 release

---

## 3️⃣ Hybrid 如何判斷？

### 自動 vs 審查的界線

```
┌─────────────────────────────────────────────┐
│  自動通過（小改動）                          │
│  ─────────────────                          │
│  • 改動 < 10 行                            │
│  • 僅修改註釋/文件                          │
│  • Bug fix（少量改動）                      │
└─────────────────────────────────────────────┘
                      ↓ 超過任何一項
┌─────────────────────────────────────────────┐
│  需要審查（大改動）                          │
│  ─────────────────                          │
│  • 新功能 > 30 行                           │
│  • 安全相關（auth, password, token）        │
│  • 重構 > 30 行                            │
│  • 新增模組                                │
└─────────────────────────────────────────────┘
```

### 安全關鍵字

如果改動包含這些關鍵字，**一定需要審查**：

| 關鍵字 | 原因 |
|--------|------|
| `auth` | 身份驗證 |
| `password` | 密碼處理 |
| `token` | 權杖管理 |
| `permission` | 權限控制 |
| `security` | 安全相關 |

---

## 4️⃣ 實際使用範例

### 基本用法

```python
from hybrid_workflow import HybridWorkflow, WorkflowMode

# 預設模式（HYBRID）
workflow = HybridWorkflow()

# 分析一個小改動
diff_small = """
--- a/utils.py
+++ b/utils.py
@@ -1,2 +1,3 @@
+    # 註釋更新
     return True
"""

analysis = workflow.analyze_change(diff_small)
print(f"類型: {analysis.type.value}")  # small
print(f"原因: {analysis.reason}")     # "改動 < 10 行"

# 是否需要審查？
if workflow.should_review(analysis):
    print("→ 需要審查")
else:
    print("→ 自動通過")  # 會出現這個
```

### 大改動需要審查

```python
# 新功能 - 需要審查
diff_large = """
--- a/new_feature.py
+++ b/new_feature.py
@@ -0,0 +1,50 @@
+def new_advanced_feature():
+    # ... 50 行新功能代碼
"""

analysis = workflow.analyze_change(diff_large)
print(f"類型: {analysis.type.value}")  # large
print(f"原因: {analysis.reason}")     # "新功能 > 30 行"

if workflow.should_review(analysis):
    print("→ 需要審查")  # 會出現這個
```

### 安全相關 - 一定審查

```python
diff_security = """
--- a/auth.py
+++ b/auth.py
@@ -1,5 +1,10 @@
+def login_with_password(password: str):
+    token = generate_token(password)
+    return token
"""

analysis = workflow.analyze_change(diff_security)
print(f"安全相關: {analysis.is_security_related}")  # True
```

---

## 5️⃣ 與 A/B 協作的關係

### 什麼是 A/B 協作？

```
A Agent → 開發者
B Agent → 審查者

A 開發 → A 提交 code review → B 審查 → 通過/駁回
```

### Hybrid 在其中的角色

```
Hybrid 模式下的流程：

小改動（< 10 行）
  ↓
自動通過 → 執行
  ↓
大改動（> 30 行 / 安全相關）
  ↓
觸發 A/B 審查流程
  ↓
B Agent 審查 → 通過/駁回
```

### 實際例子

```
情境：開發一個新功能模組

1. Agent A 分析需求
2. Agent A 產生 50 行新功能代碼
3. Hybrid 分析：這是大改動 → 需要審查
4. Agent B 收到審查請求
5. Agent B 審查代碼 → 通過
6. 代碼合併
```

---

## 6️⃣ 團隊配置建議

### 小團隊（2-3人）

```python
workflow = HybridWorkflow(
    mode=WorkflowMode.HYBRID,
    small_change_threshold=15,   # 放寬一點
    large_change_threshold=50     # 30→50
)
```

### 中型團隊（4-8人）

```python
workflow = HybridWorkflow(
    mode=WorkflowMode.HYBRID,
    small_change_threshold=10,   # 預設
    large_change_threshold=30    # 預設
)
```

### 大型團隊（8+人）

```python
workflow = HybridWorkflow(
    mode=WorkflowMode.HYBRID,
    small_change_threshold=10,
    large_change_threshold=20    # 更嚴格
)
```

### 發布前

```python
# 切換到 ON 模式
workflow = HybridWorkflow(mode=WorkflowMode.ON)
```

---

## 7️⃣ 快速上手命令

```bash
# 查看幫助
python hybrid_workflow.py --help

# 分析 diff
python hybrid_workflow.py --diff your.diff

# 查看統計
python hybrid_workflow.py --stats
```

---

## 8️⃣ 常見問題

### Q1: 為什麼預設是 HYBRID？

因為它是「速度」和「品質」的最佳平衡點。

| 改動類型 | 佔比 | Hybrid 處理 |
|---------|------|------------|
| 小改動 | ~70% | 自動通過 |
| 大改動 | ~30% | 審查通過 |

### Q2: 如果我想要更快呢？

用 OFF 模式，但這只適合 POC 和實驗。

### Q3: 如果我想要更嚴格呢？

用 ON 模式，所有改動都要審查。

### Q4: 審查不通過怎麼辦？

1. 查看審查意見
2. 修改代碼
3. 重新提交

### Q5: Hybrid 適合什麼場景？

| 場景 | 建議模式 |
|------|---------|
| 日常開發 | **HYBRID** |
| 個人專案 | OFF 或 HYBRID |
| 正式發布 | **HYBRID** 或 ON |
| 安全相關 | ON |

---

## 9️⃣ 下一步

1. 查看 [case29_hybrid_workflow.md](../cases/case29_hybrid_workflow.md) 深入了解
2. 查看 [SMART_ORCHESTRATOR](../smart_orchestrator/SKILL.md) 了解協作
3. 查看 [THREE_PHASE_EXECUTOR](../three_phase_executor/SKILL.md) 了解效能優化

---

## 📊 預期效益

| 維度 | 改善前 | 改善後 |
|------|--------|--------|
| 開發速度 | - | +40%（小改動） |
| 程式碼品質 | 一般 | +30%（大改動審查） |
| 等待時間 | 高 | -60% |
| 團隊協作 | 瓶頸多 | 流暢 |

---

## 🎯 一句話總結

> **Hybrid = 讓小改動快跑，讓大改動站穩**
