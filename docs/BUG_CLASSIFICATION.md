# Bug 分類框架

## 等級定義

| 等級 | 定義 | 回應時間 | 發版策略 |
|------|------|---------|---------|
| **P0** | Framework 完全無法運行（crash, core functionality broken） | 立即修復 | 立即發版 |
| **P1** | Phase 無法完成（Stage Pass 阻斷但有 workaround） | 24小時內 | 盡快發版 |
| **P2** | 部分功能受影響（Constitution 分數不準確但能跑） | 1週內 | 累積後發版 |
| **P3** | 優化/改進（不影響功能） | 規劃中 | 隨版本更新 |

---

## P0 等級（立即處理）

### 定義
- Framework 完全無法運行
- 核心功能（Phase flow, Constitution, STAGE_PASS）完全損壞
- 沒有 workaround

### 範例
- `import` 錯誤導致完全無法載入
- Phase flow 完全阻斷，沒有任何輸出
- STAGE_PASS generator crash

### 回應流程
1. 立即修復
2. 完整測試
3. 立即發版
4. 通知所有用戶

---

## P1 等級（24小時內）

### 定義
- 特定 Phase 無法完成
- Constitution 檢查報告錯誤結果
- 有 workaround 但不理想

### 範例
- 路徑 bug 導致 Constitution 找不到檔案（v7.79-v7.88）
- Phase EXIT 條件不正確
- Constitution 不是 hard blocker

### 回應流程
1. 分析根因
2. 修復 + 測試
3. 24小時內發版
4. 記錄於 CHANGELOG

---

## P2 等級（1週內）

### 定義
- 功能受影響但可以繞過
- 非核心功能問題
- 影響部分用戶

### 範例
- 某個 Constitution checker 輸出不準確
- 某些路徑沒有在 alternate 列表中
- 文件不一致

### 回應流程
1. 分析根因
2. 規劃修復範圍
3. 累積多個相關修復
4. 1週內發版

---

## P3 等級（規劃中）

### 定義
- 優化或改進
- 不影響現有功能
- 長期改進

### 範例
- 新增測試
- 重構代碼
- 文件更新
- 效能優化

### 回應流程
1. 評估優先級
2. 加入 backlog
3. 隨版本更新

---

## 修復流程

```
發現問題
    ↓
分類（P0/P1/P2/P3）
    ↓
根因分析
    ↓
影響範圍評估（哪些工具/Phase/功能受影響）
    ↓
規劃修復
    ↓
修復 + 測試
    ↓
發版或累積
```

---

## Commit Message 格式

```
<type>(<scope>): <description>

Types:
- fix: 錯誤修復
- feat: 新功能
- docs: 文件更新
- refactor: 重構
- test: 測試
- chore: 其他

Scope:
- path: 路徑相關
- constitution: Constitution 相關
- phase-X: 特定 Phase
- skill: SKILL.md 相關
- test: 測試相關

Examples:
fix(path): add 05-verify to Phase 5 alt_dirs
fix(constitution): use PHASE_ARTIFACT_PATHS in verification_checker
feat(test): add path contract tests
refactor(phase_paths): centralize path definitions
```

---

## 版本發布策略

### 緊急修復（P0/P1）
- 直接發版到 main
- Tag: vX.Y+1
- 通知用戶

### 一般修復（P2）
- 累積到一定數量或時間
- 完整測試後發版
- Tag: vX.Y+1

### 改進（P3）
- 隨版本更新
- Tag: vX.Y.Z（Z++）

---

## 決策樹

```
問題影響我的工作嗎？
    │
    ├─ 是 → 緊急程度？
    │       │
    │       ├─ 完全阻斷 → P0
    │       ├─ 部分阻斷 → P1
    │       └─ 可繞過 → P2
    │
    └─ 否 → 影響其他用戶嗎？
            │
            ├─ 是 → P2
            └─ 否 → P3
```
