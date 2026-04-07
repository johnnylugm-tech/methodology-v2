# Git 版本規範

## 產物版本格式

### Commit Message 格式

```
[Phase N] [Step X] {產物名}@{version} — {簡短描述}

可選：{詳細描述}
```

### 範例

```bash
# Phase 1 完成 SRS
git commit -m "[Phase 1] [Step 1] SRS.md@v1.0.0 — 完成需求規格"

# Phase 2 完成 SAD
git commit -m "[Phase 2] [Step 1] SAD.md@v1.0.0 — 完成架構設計"

# Phase 3 完成 Module 1
git commit -m "[Phase 3] [Step 1] LexiconMapper.py@v1.0.0 — 完成詞彙映射模組"

# Phase 4 完成測試
git commit -m "[Phase 4] [Step 1] test_lexicon.py@v1.0.0 — 完成 FR-01 測試"
```

## 版本號規範

| 類型 | 格式 | 範例 |
|------|------|------|
| 初始版本 | v1.0.0 | v1.0.0 |
| 小改動 | v1.0.1 | v1.0.1 |
| 中改動 | v1.1.0 | v1.1.0 |
| 大改動 | v2.0.0 | v2.0.0 |

## Tag 規範

每個 Phase 封版時：

```bash
git tag -a Phase1-v1.0.0 -m "Phase 1 完成，SRS/SPEC_TRACKING/TRACEABILITY 交付"
git tag -a Phase2-v1.0.0 -m "Phase 2 完成，SAD/ADR 交付"
```

## 與 state.json 的對應

當執行 `git commit` 後，應同步更新 `state.json`：

```bash
# Commit 後自動呼叫
python cli.py update-artifact --name SRS.md --version v1.0.0 --path SRS.md --summary "完成需求規格"
```

### update-artifact CLI 命令

```bash
python cli.py update-artifact --name SRS.md --version v1.0.0 --path SRS.md --summary "完成需求規格"
```

## 常見錯誤

| 錯誤 | 正確做法 |
|------|---------|
| `git commit -m "fix bug"` | `git commit -m "[Phase 3] [Step 4] SynthEngine.py@v1.0.1 — 修復 CircuitBreaker 邏輯"` |
| 忘記同步 state.json | Commit 後立即執行 `python cli.py update-artifact` |
| 版本號跳號 | 嚴格按照 MAJOR.MINOR.PATCH 遞增 |
