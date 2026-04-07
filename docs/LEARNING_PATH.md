# Learning Path - 學習路徑

> 根據你的角色推薦的學習順序

---

## 學習者角色

### 🐣 菜鳥開發者（< 1 年經驗）

```
1. GETTING_STARTED_30MIN.md (30 分鐘)
2. TASK_SPLITTER.md (任務分解)
3. QUALITY_GATE.md (品質基礎)
4. CLI_COMMANDS.md (命令參考)
5. 實作：第一個小專案
```

### 🐥 中級工程師（1-3 年經驗）

```
1. GETTING_STARTED_30MIN.md (複習)
2. ARCHITECTURE.md (系統架構)
3. QUALITY_GATE.md (深入)
4. ENFORCEMENT.md (強制執行)
5. DEPLOYMENT.md (部署)
6. 實作：完整專案
```

### 🦅 資深工程師（3+ 年經驗）

```
1. OVERVIEW.md (總覽)
2. SYSTEM_DESIGN.md (系統設計)
3. INTEGRATION.md (整合)
4. CUSTOMIZATION.md (客製化)
5. ADVANCED_TOPICS.md (進階主題)
```

### 🏛️ CTO / 架構師

```
1. EXECUTIVE_SUMMARY.md (執行摘要)
2. OVERVIEW.md (框架總覽)
3. CASE_STUDIES.md (案例研究)
4. ROI_CALCULATION.md (投資回報計算)
5. INTEGRATION_STRATEGY.md (整合策略)
```

---

## 場景驅動學習

### 場景 1: 需要快速交付

```
GETTING_STARTED_30MIN → TASK_SPLITTER → QUALITY_GATE → DEPLOY
```

### 場景 2: 需要高品質

```
QUALITY_GATE → ENFORCEMENT → CONSTITUTION → TESTING
```

### 場景 3: 需要成本控制

```
COST_ALLOCATOR → COST_OPTIMIZATION → ROI_DASHBOARD
```

---

## 模組依賴關係

```
┌─────────────────┐
│   OVERVIEW       │ ← 初學者必讀
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ GETTING_STARTED │ ← 30 分鐘上手
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────┐
│ TASK  │ │QUALITY│
│SPLIT │ │ GATE  │
└───┬───┘ └───┬───┘
    │         │
    ▼         ▼
┌───────┐ ┌───────┐
│AGENT  │ │ENFORCE│
│SPAWNER│ │ MENT  │
└───┬───┘ └───┬───┘
    │         │
    └────┬────┘
         ▼
┌─────────────────┐
│    DEPLOY       │
└─────────────────┘
```

---

*最後更新：2026-03-25*
