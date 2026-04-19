# Feature Branch Structure — v3.1 Integration

**版本**: v1.0
**日期**: 2026-04-19
**作者**: Johnny Musk Agent

---

## 目標

把所有 Features 整合到 `methodology-v3` 主分支，採用 **Feature Folder Layer** 結構，避免 implement 互相覆蓋的問題。

---

## 正確的 Branch 結構

### 開發流程（2026-04-19 確認）

```
1. 每個 Feature 在 methodology-v3 上開發
2. 用 TDD 驗證
3. 驗證通過後 PR merge 回 main
4. 在 main 做 Real Project Validation
5. 然後繼續下一個 Feature
```

### Feature Folder Structure

每個 Feature 有獨立的資料夾，不會互相覆蓋：

```
methodology-v3/
└── implement/
    ├── feature-06-hunter/           ← Feature #6
    │   ├── 01-spec/SPEC.md
    │   ├── 02-architecture/ARCHITECTURE.md
    │   ├── 03-implement/hunter/       (模組程式碼)
    │   ├── 04-tests/test_hunter/     (測試程式碼)
    │   ├── 05-verify/                (驗證報告)
    │   ├── 06-quality/               (品質報告)
    │   ├── 07-risk/                  (風險登記)
    │   └── 08-deploy/               (部署指南)
    │
    ├── feature-07-uqlm/              ← Feature #7
    │   ├── 01-spec/SPEC.md
    │   ├── 02-architecture/ARCHITECTURE.md
    │   ├── 03-implement/detection/   (模組程式碼)
    │   ├── 04-tests/test_detection/  (測試程式碼)
    │   ├── 05-verify/
    │   ├── 06-quality/
    │   ├── 07-risk/
    │   └── 08-deploy/
    │
    └── feature-08-gap/               ← Future
        └── ...
```

---

## 已完成的 Migration（2026-04-19）

### Feature #6: Hunter Agent
| 項目 | 值 |
|------|-----|
| 新 Branch | `feature-06-hunter` |
| 來源 | `v3/hunter-agent` |
| 結構 | 23 files, 5210 lines |
| Commit | `63d3976` |

### Feature #7: UQLM + Probes
| 項目 | 值 |
|------|-----|
| 新 Branch | `feature-07-uqlm` |
| 來源 | `v3/uqlm-probes` |
| 結構 | 24 files, 10192 lines |
| Commit | `c4095da` |

---

## 待清理的 Old Branches

以下 branches 需要刪除（已 migration 完成）：

- `v3/hunter-agent`
- `v3/uqlm-probes`
- `v3/mcp-saif`
- `v3/prompt-shields`
- `v3/tiered-governance`
- `v3/kill-switch`
- `feature-06-hunter-temp` (如果存在)
- `feature-07-uqlm-temp` (如果存在)

---

## 未來的 Feature 開發規範

### 啟動新 Feature 的流程

```bash
# 1. 從 methodology-v3 建立新 branch
git checkout origin/methodology-v3
git checkout -b feature-XX-name

# 2. 建立標準結構
mkdir -p implement/feature-XX-name/{01-spec,02-architecture,03-implement,04-tests,05-verify,06-quality,07-risk,08-deploy}

# 3. 開發完成後 commit
git add implement/feature-XX-name/
git commit -m "feat: Add Feature #XX description (Phase 1-8 complete)"

# 4. Push 並建立 PR to methodology-v3
git push -u origin feature-XX-name
```

### 命名規則

| 項目 | 格式 |
|------|------|
| Branch | `feature-XX-name`（例：`feature-08-gap-detector`） |
| Folder | `feature-XX-name`（例：`feature-08-gap-detector`） |
| 內部資料夾 | `01-spec`, `02-architecture`, `03-implement/{module}`, `04-tests/{test_module}` |

---

## Phase 對應資料夾

| Phase | 資料夾 | 內容 |
|-------|--------|------|
| Phase 1 | `01-spec/` | SPEC.md |
| Phase 2 | `02-architecture/` | ARCHITECTURE.md |
| Phase 3 | `03-implement/` | 模組程式碼 |
| Phase 4 | `04-tests/` | 測試程式碼 |
| Phase 5 | `05-verify/` | 驗證報告 |
| Phase 6 | `06-quality/` | 品質報告、交付報告 |
| Phase 7 | `07-risk/` | 風險登記 |
| Phase 8 | `08-deploy/` | 部署指南 |

---

## 重要原則

1. **每個 Feature 獨立資料夾** — 不會覆蓋其他 Features
2. **所有 Features 在同一個 Branch** — 最後一次 merge 回 main
3. **Phase 3-4 內含模組資料夾** — 例：`03-implement/hunter/`, `03-implement/detection/`
4. **測試在 04-tests/{test_module}/** — 例：`04-tests/test_hunter/`, `04-tests/test_detection/`

---

## GitHub URL

| Feature | Branch | URL |
|---------|--------|-----|
| #6 Hunter Agent | `feature-06-hunter` | https://github.com/johnnylugm-tech/methodology-v2/tree/feature-06-hunter |
| #7 UQLM + Probes | `feature-07-uqlm` | https://github.com/johnnylugm-tech/methodology-v2/tree/feature-07-uqlm |
| methodology-v3 | `origin/methodology-v3` | https://github.com/johnnylugm-tech/methodology-v2/tree/methodology-v3 |

---

*生成時間: 2026-04-19 14:10 GMT+8*