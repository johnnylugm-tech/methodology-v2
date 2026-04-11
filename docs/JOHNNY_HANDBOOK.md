# Johnny HandBook

**版本**: v7.18
**用途**: Johnny 需要知道並操作的內容

---

## 🚀 快速命令

### 執行 Phase

```bash
# 進入專案目錄
cd /path/to/project

# 執行 Phase（包含 Constitution + BVS + HR-09 + CQG + SAB Drift）
python cli.py run-phase --phase {N} --resume

# 手動觸發品質檢查
python cli.py quality-gate --phase {N}

# 手動產生 STAGE_PASS.md
python cli.py stage-pass --phase {N}
```

### 常用命令速查

| 情境 | 命令 |
|------|------|
| 執行 Phase 3 | `python cli.py run-phase --phase 3 --resume` |
| 繼續執行 | `python cli.py run-phase --phase 3 --resume` |
| 品質檢查 | `python cli.py quality-gate --phase 3` |
| STAGE_PASS | `python cli.py stage-pass --phase 3` |
| Constitution | `python cli.py enforce --level BLOCK` |

---

## ⚠️ 必須遵守的規則

### HR-01 ~ HR-15

| 規則 | 內容 | 違規 |
|------|------|------|
| HR-01 | A/B 必須不同 Agent，禁止自寫自審 | ❌ |
| HR-02 | Quality Gate 必須有實際命令輸出 | ❌ |
| HR-03 | Phase 必須順序執行，不可跳過 | ❌ |
| HR-07 | DEVELOPMENT_LOG 必須記錄 session_id | ❌ |
| HR-08 | 每個 Phase 結束必須執行 Quality Gate | ❌ |
| HR-09 | Claims Verifier 驗證必須通過 | ❌ |
| HR-10 | sessions_spawn.log 必須存在且有 A/B 記錄 | ❌ |
| HR-15 | citations 必須含行號 + artifact_verification | ❌ |

### 紅線（禁止）

| 項目 | 說明 |
|------|------|
| ❌ 不准刪除記憶 | memory/ 下的檔案 |
| ❌ 不准強制推送 | `git push --force` |
| ❌ 不准破壞架構 | 任意刪除 Phase 交付物 |

---

## 📋 Phase 門檻

### Phase 3（實作）

| 項目 | 門檻 | 自動檢查 |
|------|-------|-----------|
| Constitution Score | ≥80% | ✅ |
| 測試通過率 | =100% | ✅ |
| 單元測試覆蓋率 | ≥70% | ✅ |
| 代碼↔SAD 映射率 | =100% | ✅ (SAB Drift) |
| Linter | 0 errors | ✅ (CQG) |
| Complexity | ≤15 | ✅ (CQG) |

### Phase 4（驗證）

| 項目 | 門檻 | 自動檢查 |
|------|-------|-----------|
| FR↔測試映射率 | ≥90% | ✅ |

---

## 🎯 STAGE_PASS.md 檢查清單

每次 Phase 完成後，檢查 STAGE_PASS.md 是否有以下章節：

### H2 主章節（7個）

- [ ] 階段目標達成
- [ ] Agent A 自評
- [ ] Agent B 審查
- [ ] Phase Challenges & Resolutions
- [ ] Johnny 介入（如有）
- [ ] artifact_verification（HR-15）
- [ ] SIGN-OFF

### H3 子章節（10個）

- [ ] Phase Completion Summary
- [ ] 5W1H 合規性檢查
- [ ] 發現的問題
- [ ] 交付物清單
- [ ] Agent A Confidence Summary
- [ ] 疑問清單
- [ ] 審查結論
- [ ] Agent B Confidence Summary
- [ ] Phase Summary (50字內)
- [ ] 附：實際工具結果

---

## 🔧 自動化功能（自動執行）

| 功能 | 版本 | 何時執行 | 需要 Johnny 動作 |
|------|------|----------|------------------|
| BVS | v6.62 | Phase 3+ Constitution | ❌ 無 |
| HR-09 | v6.63 | Phase 3+ Constitution | ❌ 無 |
| CQG | v6.61 | Phase 3+ Constitution | ❌ 無 |
| SAB Drift | P0-3 | Phase 3+ Constitution | ❌ 無 |
| FR↔Test | - | Phase 4 Constitution | ❌ 無 |

---

## ⏰ 時程門檻

| 規則 | 內容 | 觸發 |
|------|------|------|
| HR-12 | A/B 審查同一 Phase 超過 5 輪 | → PAUSE，等待 Johnny 裁決 |
| HR-13 | Phase 執行時長超過預估時間的 3 倍 | → PAUSE，等待 Johnny 裁決 |
| HR-14 | Integrity 分數降至 < 40 | → FREEZE，全面審計 |

---

## 📁 交付物檢查

### Phase 3 完成後必須存在

```
00-summary/Phase3_STAGE_PASS.md
03-development/src/
03-development/tests/
sessions_spawn.log
DEVELOPMENT_LOG.md
```

### 交付物路徑（Convention）

| Phase | 目錄 |
|-------|------|
| 1 | 01-requirements/ |
| 2 | 02-architecture/ |
| 3 | 03-development/ |
| 4 | 04-verification/ |

---

## 🔍 常見問題處理

### Q: Constitution Score 低於 80%？

A: 檢查 violation 列表，修復後重新執行 `python cli.py stage-pass --phase {N}`

### Q: 發現代碼與 SAD 不符？

A: 執行 `python cli.py trace-check --phase 3` 確認 drift 位置

### Q: Integrity 分數低？

A: 檢查是否有 Phase 跳過、未完成、或品質 Gate 失敗

---

## 📞 緊急聯絡

| 項目 | 說明 |
|------|------|
| GitHub | https://github.com/johnnylugm-tech/methodology-v2 |
| Issues | https://github.com/johnnylugm-tech/methodology-v2/issues |

---

## 📝 版本歷史

| 版本 | 日期 | 重要更新 |
|------|------|-----------|
| v7.18 | 2026-04-11 | CQG + Phase 4 FR mapping 整合 |
| v7.17 | 2026-04-11 | SAB Drift Detection 自動執行 |
| v7.13 | 2026-04-11 | artifact_verification HR-15 |
| v7.10 | 2026-04-10 | Phase Summary 強制 |

---

*最後更新: 2026-04-11*
