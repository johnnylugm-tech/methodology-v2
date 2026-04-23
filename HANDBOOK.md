# methodology-v2 HandBook

**版本**: v9.1
**更新**: 2026-04-11

---

## 🚀 快速開始

### 執行 Phase

```bash
cd /path/to/project
python cli.py run-phase --phase {N} --resume
```

### 常用命令

| 命令 | 用途 |
|------|------|
| `python cli.py run-phase --phase 3 --resume` | 執行 Phase 3 |
| `python cli.py stage-pass --phase 3` | 產生 STAGE_PASS.md |
| `python cli.py quality-gate --phase 3` | 執行品質檢查 |
| `python cli.py trace-check --phase 3` | SAB Drift 檢查 |
| `python cli.py enforce --level BLOCK` | 執行 Constitution |

---

## 📋 Phase 執行流程

### Phase 1-8

| Phase | 名稱 | Constitution | 自動檢查 |
|-------|------|-------------|-----------|
| 1 | 需求規格 | SRS | - |
| 2 | 架構設計 | SAD | - |
| 3 | 實作 | Implementation | **CQG + SAB Drift + BVS + HR-09** |
| 4 | 驗證 | Test Plan | **FR↔Test** |
| 5 | 系統測試 | Verification | - |
| 6 | 品質評估 | Quality Report | - |
| 7 | 風險管理 | Risk Management | - |
| 8 | 配置管理 | Configuration | - |

---

## 🔧 自動化功能 (v6.61+)

| 功能 | 版本 | 觸發方式 | Phase |
|------|------|----------|-------|
| **BVS** | v6.62 | 自動（Constitution）| 3+ |
| **HR-09** | v6.63 | 自動（Constitution）| 3+ |
| **CQG** | v6.61 | 自動（Constitution）| 3+ |
| **SAB Drift** | P0-3 | 自動（Constitution）| 3+ |
| **FR↔Test** | - | 自動（Constitution）| 4 |
| **AutoResearch** | P1-3 | 手動 | 3+ |
| **Verify_Agent** | v6.21 | 當 Agent B > 20 輪 | 3+ |

---

## 📊 Constitution Thresholds

| TH | 項目 | 門檻 | Phase |
|----|------|------|-------|
| TH-01 | ASPICE 合規率 | >80% | 1-2 |
| TH-03 | Constitution 正確性 | =100% | 1-4 |
| TH-10 | 測試通過率 | =100% | 3 |
| TH-11 | 單元測試覆蓋率 | ≥70% | 3 |
| TH-16 | 代碼↔SAD 映射率 | =100% | 3 |
| TH-17 | FR↔測試映射率 | ≥90% | 4 |

---

## 📁 交付物結構

```
{project}/
├── 00-summary/
│   └── Phase{N}_STAGE_PASS.md    # Phase 通過憑證
├── 01-requirements/
│   ├── SRS.md                    # 需求規格
│   └── SPEC_TRACKING.md          # 規格追蹤
├── 02-architecture/
│   └── SAD.md                    # 架構設計
├── 03-development/
│   ├── src/                      # 源代碼
│   └── tests/                    # 測試
├── 04-verification/
│   ├── TEST_PLAN.md
│   └── TEST_RESULTS.md
├── sessions_spawn.log            # A/B session 記錄
└── DEVELOPMENT_LOG.md           # 開發日誌
```

---

## ✅ STAGE_PASS.md 章節結構

**H2 主章節（7個）**:
1. 階段目標達成
2. Agent A 自評
3. Agent B 審查
4. Phase Challenges & Resolutions
5. Johnny 介入（如有）
6. artifact_verification（HR-15）
7. SIGN-OFF

**H3 子章節（10個）**:
- Phase Completion Summary
- 5W1H 合規性檢查
- 發現的問題
- 交付物清單
- Agent A Confidence Summary
- 疑問清單
- 審查結論
- Agent B Confidence Summary
- Phase Summary (50字內)
- 附：實際工具結果

---

## 🎯 審計分數計算

| 組件 | 分數 |
|------|------|
| Constitution Score | ≥80% |
| STAGE_PASS 章節 | 100%（需 7+2 章節）|
| sessions_spawn.log | A/B 不同 session |
| artifact_verification | HR-15 |

---

## 🔗 相關連結

| 項目 | URL |
|------|-----|
| GitHub | https://github.com/johnnylugm-tech/methodology-v2 |
| Releases | https://github.com/johnnylugm-tech/methodology-v2/releases |
| SKILL.md | `docs/SKILL.md` |
| CHANGELOG | `CHANGELOG.md` |

---

## 📝 版本歷史

| 版本 | 日期 | 內容 |
|------|------|------|
| v7.18 | 2026-04-11 | CQG + Phase 4 FR mapping |
| v7.17 | 2026-04-11 | SAB Drift Detection |
| v7.16 | 2026-04-11 | plan_phase_template SAB 說明 |
| v7.15 | 2026-04-11 | v6.61+ 自動化功能章節 |
| v7.14 | 2026-04-11 | STAGE_PASS 章節完整化 |
| v7.13 | 2026-04-11 | artifact_verification HR-15 |
| v7.12 | 2026-04-10 | Phase 3 Constitution type/dir 修正 |
| v7.11 | 2026-04-10 | confidence 格式驗證 |
| v7.10 | 2026-04-10 | Phase Summary |

---

*Last updated: 2026-04-11*
