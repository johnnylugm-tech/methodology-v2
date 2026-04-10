# 專案結構模板

> Spec Kit 風格的標準化專案結構

---

## 標準目錄結構

```
project/
├── 00-summary/             # 摘要
├── 01-requirements/        # Phase 1: 需求分析 (SRS.md)
├── 02-architecture/       # Phase 2: 架構設計 (SAD.md)
├── 03-development/          # Phase 3: 代碼實作 (src/, tests/)
├── 04-testing/            # Phase 4: 測試驗證
├── 05-deployment/         # Phase 5: 部署
├── 06-maintenance/         # Phase 6+: 維運
└── .methodology/          # Framework 狀態追蹤
```

> ⚠️ 注意：Phase 編號與目錄前綴對齊（Phase N → 0N-xxx/）

---

## 02-Specify 模板

### requirements.md

```markdown
# 需求規格

## 專案名稱
[名稱]

## 功能需求

### FR-001: [功能名稱]
- **優先級**: P0 / P1 / P2
- **驗收標準**: [可測試的標準]
```

---

## 03-Plan 模板

### architecture.md

```markdown
# 架構設計

## 系統概覽
[系統架構圖]

## 元件設計

### Component: [名稱]
- **職責**: [職責描述]
```

---

## 04-Tasks 模板

### sprint_01.md

```markdown
# Sprint 1

## 目標
[迭代目標]

## Sprint Backlog

- [ ] US-001: [標題] (故事點: 5)
```

---

## 05-Verification 模板

### gates.md

```markdown
# 驗證關卡報告

## Gate 1: Code Quality

| 檢查項 | 狀態 |
|--------|------|
| 語法檢查 | ✅ |
```

---

*模板版本: 1.0.0*
