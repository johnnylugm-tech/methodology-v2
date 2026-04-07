# 案例六：知識管理

## 情境描述

建立團隊的知識庫，累積最佳實踐，透過 Pattern 學習新技術。

---

## 案例 6.1：查詢類似情境

### 背景
遇到新問題時，希望從知識庫中找到類似案例。

### 使用方式

```python
from methodology import KnowledgeBase

kb = KnowledgeBase()

# 搜尋相關模式
scenario = "I need to coordinate multiple agents to build a complex system"
pattern = kb.find_similar_scenario(scenario)

if pattern:
    print(f"找到相似案例: {pattern.name}")
    print(f"\n問題: {pattern.problem}")
    print(f"解決方案: {pattern.solution}")
    print(f"\n評分: {pattern.rating} ★")
    print(f"使用次數: {pattern.usage_count}")
```

### 輸出範例
```
找到相似案例: Sequential Agent Flow

問題: 需要多個 Agent 順序執行任務
解決方案: 使用 Sequential Workflow，確保每個步驟完成後再執行下一個
評分: 4.5 ★
使用次數: 12
```

---

## 案例 6.2：建立最佳實踐庫

### 背景
團隊需要累積並分享最佳實踐。

### 使用方式

```python
from methodology import KnowledgeBase, BestPractice

kb = KnowledgeBase()

# 新增自訂最佳實踐
practice = BestPractice(
    id="bp-custom-001",
    title="AI 客服系統開發標準流程",
    category="development",
    description="建立 AI 客服系統的標準開發流程",
    steps=[
        "1. 需求分析與對話流程設計",
        "2. 選擇合適的模型與策略",
        "3. 實作對話管理系統",
        "4. 整合知識庫檢索",
        "5. 單元測試與整合測試",
        "6. 上線前的 A/B 測試"
    ],
    do_list=[
        "使用結構化的對話狀態管理",
        "實作完善的錯誤處理",
        "記錄對話歷史用於分析"
    ],
    dont_list=[
        "不要 hardcode 對話邏輯",
        "不要忽略隱私合規要求"
    ],
    use_cases=["新客服專案立項", "技術分享"],
    effectiveness=0.92
)

kb.add_best_practice(practice)
kb.save()

# 搜尋最佳實踐
results = kb.search_best_practices("AI 客服")
print(f"找到 {len(results)} 個相關實踐:")
for bp in results:
    print(f"\n📌 {bp.title}")
    print(f"   效果: {bp.effectiveness:.0%}")
    print(f"   適用: {', '.join(bp.use_cases[:2])}")
```

### 輸出範例
```
找到 2 個相關實踐:

📌 AI 客服系統開發標準流程
   效果: 92%
   適用: 新客服專案立項, 技術分享

📌 PM Daily Workflow
   效果: 90%
   適用: 日常管理, 例會準備
```

---

## 案例 6.3：版本控制與 Rollback

### 背景
需要追蹤程式碼變更，並在出錯時能夠回滾。

### 使用方式

```python
from methodology import DeliveryTracker

vc = DeliveryTracker()

# 提交版本
v1 = vc.commit(
    artifact_id="auth-module",
    content="def login(user, pass): return True",
    author="dev@company.com",
    message="init: 基本登入功能"
)
print(f"v1: {v1}")

v2 = vc.commit(
    artifact_id="auth-module",
    content="def login(user, pass, mfa=None): return True",
    author="dev@company.com",
    message="feat: 新增 MFA 支援"
)
print(f"v2: {v2}")

v3 = vc.commit(
    artifact_id="auth-module",
    content="def login(user, pass, mfa=None, remember=False): return True",
    author="dev@company.com",
    message="feat: 新增 remember me"
)
print(f"v3: {v3}")

# 標記穩定版本
vc.tag_version("auth-module", "v1.0.0", "stable")
vc.tag_version("auth-module", "v1.0.0", "release")

# 版本比較
comp = vc.compare_versions("auth-module")
print(f"\n總版本數: {comp['total_versions']}")
for c in comp['comparisons']:
    print(f"  {c['from']} → {c['to']}: {c['message']}")

# Rollback
rollback = vc.rollback(
    artifact_id="auth-module",
    version="v1.0.0",
    reason="v1.1.0 發現安全漏洞"
)
print(f"\n回滾到: {rollback}")

# 查看歷史
history = vc.get_history("auth-module")
print(f"\n歷史記錄 ({len(history)} 個版本):")
for v in history:
    print(f"  {v} - {v.message} ({v.author})")
```

### 輸出範例
```
v1: v0.0.1
v2: v0.0.2
v3: v0.0.3

總版本數: 3
  v0.0.1 → v0.0.2: feat: 新增 MFA 支援
  v0.0.2 → v0.0.3: feat: 新增 remember me

回滾到: v1.0.0

歷史記錄 (3 個版本):
  v0.0.3 - feat: 新增 remember me (dev@company.com)
  v0.0.2 - feat: 新增 MFA 支援 (dev@company.com)
  v0.0.1 - init: 基本登入功能 (dev@company.com)
```

---

## 相關功能

| 功能 | 模組 |
|------|------|
| 知識庫 | `KnowledgeBase`, `Pattern`, `BestPractice` |
| 版本控制 | `DeliveryTracker`, `Artifact`, `Version` |
| 模式庫 | 內建 15+ 種常見模式 |
