# 專案結構模板

> Spec Kit 風格的標準化專案結構

---

## 標準目錄結構

```
project/
├── 01-constitution/          # 團隊憲章
├── 02-specify/               # 需求規格
├── 03-plan/                 # 規劃
├── 04-tasks/                # 任務
├── 05-verification/         # 驗證記錄
└── 06-outputs/              # 產出
```

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
