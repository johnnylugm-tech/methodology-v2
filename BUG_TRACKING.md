# methodology-v2 Bug Tracking

> 持續追蹤 methodology-v2 發現的所有 bug 與修復記錄

---

## 📊 Bug 統計（2026-03）

| 狀態 | 數量 |
|------|------|
| 🔴 Open | 3 |
| 🟡 In Progress | 0 |
| ✅ Fixed | 11+ |

---

## 🔴 Open Bugs（待修復）

### BUG-001: PhaseEnforcer 自動化未觸發
| 項目 | 內容 |
|------|------|
| **嚴重程度** | 🟡 中 |
| **發現日期** | 2026-03-24 |
| **模組** | PhaseEnforcer |
| **描述** | Quality Gate 設計為「每次存檔自動觸發」，但 Agent 不會主動開 daemon，導致從未觸發 |
| **根因** | 需要 `quality_watch.py daemon` 啟動，但 Agent 不知道要開 |
| **影響** | Phase 4-6 檢查從未真正執行 |
| **解決方案** | Prompt 明確要求執行 Quality Gate，或設定 git hook |

---

### BUG-002: 測試覆蓋率未 enforce
| 項目 | 內容 |
|------|------|
| **嚴重程度** | 🟡 中 |
| **發現日期** | 2026-03-24 |
| **模組** | Agent Quality Guard |
| **描述** | 有 coverage_threshold 檢查，但 enforcement.json 未啟用 |
| **根因** | enforcement.json 的 `coverage_threshold` 檢查未設定 |
| **影響** | 覆蓋率低於 70% 仍可通過 |
| **解決方案** | 啟用 enforcement.json 的 coverage_threshold 檢查 |

---

### BUG-003: Agent Quality Guard LLM 模式需 API Key
| 項目 | 內容 |
|------|------|
| **嚴重程度** | 🟢 低 |
| **發現日期** | 2026-03-19 |
| **模組** | Agent Quality Guard |
| **描述** | LLM 模式需要有效 API Key，目前提供的 Key 格式不適用於 MiniMax |
| **根因** | API Key 格式問題 |
| **影響** | 無法使用 LLM 模式進行深度 Code Review |
| **解決方案** | 提供正確格式的 API Key |

---

## ✅ Fixed Bugs（已修復）

### FIX-001: Doc 檢查路徑問題
| 項目 | 內容 |
|------|------|
| **Commit** | `83b85c7` |
| **版本** | v5.96 |
| **描述** | doc_checker.py 路徑問題 |
| **修復內容** | v5.75-v5.95 審計修正 |

---

### FIX-002: ASPICE Compliance 參數
| 項目 | 內容 |
|------|------|
| **Commit** | `27df584` |
| **版本** | v5.52 |
| **描述** | ASPICE compliance 參數缺失 |
| **修復內容** | 整合 ASPICE traceability 到 FrameworkEnforcer |

---

### FIX-003: AutoQualityGate print-debug 多重註釋
| 項目 | 內容 |
|------|------|
| **Commit** | `128bd79` |
| **版本** | v5.x |
| **描述** | print-debug 多重註釋 bug |
| **修復內容** | 修復多重註釋問題 |

---

### FIX-004: 還原被破壞的檔案
| 項目 | 內容 |
|------|------|
| **Commit** | `b292853` |
| **版本** | v5.x |
| **描述** | AutoQualityGate 破壞了某些檔案 |
| **修復內容** | 還原被破壞的檔案 |

---

### FIX-005: Constitution Passed 邏輯 Bug
| 項目 | 內容 |
|------|------|
| **Commit** | `95cabf6` |
| **版本** | v5.x |
| **描述** | Constitution 判斷邏輯錯誤 |
| **修復內容** | 修復 Passed 判斷邏輯 |

---

### FIX-006: 還原 cli.py 版本
| 項目 | 內容 |
|------|------|
| **Commit** | `8b4ef51` |
| **版本** | v5.3 → v5.4 |
| **描述** | cli.py 版本錯誤 |
| **修復內容** | 還原版本 v5.3.0 → v5.4.0 |

---

### FIX-007: nested quotes in f-string
| 項目 | 內容 |
|------|------|
| **Commit** | `0375b3a` |
| **版本** | v5.x |
| **描述** | line 282 f-string nested quotes 錯誤 |
| **修復內容** | 修復巢狀引號問題 |

---

### FIX-008: add conftest.py
| 項目 | 內容 |
|------|------|
| **Commit** | `c7b37b6` |
| **版本** | v5.31 |
| **描述** | pytest 缺少 conftest.py |
| **修復內容** | 新增 conftest.py |

---

### FIX-009: observability/__init__.py 缺少
| 項目 | 內容 |
|------|------|
| **Commit** | `8897916` |
| **版本** | v5.x |
| **描述** | 模組 export 失敗 |
| **修復內容** | 新增 observability/__init__.py |

---

### FIX-010: framework_bridge.py 命名衝突
| 項目 | 內容 |
|------|------|
| **Commit** | `2406c4e` |
| **版本** | v5.x |
| **描述** | 命名衝突 |
| **修復內容** | rename to crewai_bridge.py |

---

### FIX-011: spec_logic_checker 閾值問題
| 項目 | 內容 |
|------|------|
| **Commit** | `260d378` |
| **版本** | v5.96 |
| **描述** | P1-P2 審計發現的 spec_logic_checker 問題 |
| **修復內容** | 修正閾值、SUP.8 補充 |

---

## 📋 月度修復統計

| 月份 | 修復數量 |
|------|----------|
| 2026-03 | 11+ |

---

## 🔧 建議改進

### 1. 自動化 enforcement
- [ ] 啟用 enforcement.json 的 coverage_threshold 檢查
- [ ] 設定 git hook 阻擋未通過 Quality Gate 的 commit
- [ ] 預設開啟 quality_watch.py daemon

### 2. 測試覆蓋
- [ ] 增加 PhaseEnforcer 單元測試
- [ ] 增加 Quality Gate 整合測試

### 3. 文件完善
- [ ] 建立每個 bug 的詳細分析報告
- [ ] 建立 Regression Test 清單

---

*最後更新：2026-03-30*