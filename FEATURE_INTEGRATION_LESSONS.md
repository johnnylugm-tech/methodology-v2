# Feature Integration — 整合問題與檢討

**Date:** 2026-04-19
**Author:** Johnny + Musk Agent
**Scope:** Features #1-5 → main merge, v3.0 System Overview

---

## 一、發生了什麼問題

### 問題 1：Phase 1-2 Artifacts 丢失

| 預期 | 實際 |
|-------|------|
| 每個 Feature 在 isolated branch 開發 | 5 個 Features 在同一個 branch 順序開發 |
| 每個 Feature 有自己的 SPEC.md, ARCHITECTURE.md | 只有 Feature #5 的 artifacts 存在 |
| Feature merge 時 artifact 跟著進來 | Feature #1-4 的 Phase 1-2 artifacts 從未 commit |

**原因：** 5 個 Features 在同一個 branch（`methodology-v3`）上順序開發，每次只做一個 Feature，commit 時只 commit 當前 Feature 的產物。最終 merge 回 main 時，Features #1-4 的 Phase 1-2 artifacts 沒有被帶進來。

**結果：** Features #1-4 的「為什麼這樣設計」、「需求決策過程」完全丢失。只有實作代碼存在。

---

### 問題 2：Features #1-4 的 SPEC.md 和 ARCHITECTURE.md 無法重建

| 還有什麼 | 沒有了什麼 |
|----------|------------|
| `implement/governance/` 代碼 | 需求決策過程 |
| `implement/kill_switch/` 代碼 | 架構 alternative 分析 |
| `implement/mcp/` 代碼 | Phase 1 的 decision log |
| `implement/security/` 代碼 | Phase 2 的 trade-off 記錄 |
| `test/` 735 個測試 | 原本的 SPEC.md、ARCHITECTURE.md |

**補救：** 從代碼重建了 v3.0 System Overview，但只覆蓋 70% 的資訊（功能行為正確，決策過程丢失）。

---

### 問題 3：Feature Branches 全都指向同一個 Commit

```bash
git log --all --oneline --source --graph
# v3/mcp-saif, v3/prompt-shields, v3/tiered-governance, v3/kill-switch
# 全部指向 450270d（同一個 commit）
```

| Branch | 指向 | 意義 |
|--------|------|------|
| v3/mcp-saif | 450270d | 標籤，不是 isolated 開發 |
| v3/prompt-shields | 450270d | 標籤，不是 isolated 開發 |
| v3/tiered-governance | 450270d | 標籤，不是 isolated 開發 |
| v3/kill-switch | 450270d | 標籤，不是 isolated 開發 |

**原因：** `git checkout -b v3/mcp-saif` 只是建立一個 branch 指標，每次完成一個 Feature 就切換 branch 指標。但代碼都在同一個 commit 歷史裡。

---

## 二、為什麼會這樣

### 設計時的假設 vs 實際開發

| 假設（設計時） | 實際（開發時） |
|---------------|---------------|
| 每個 Feature 在 isolated branch 開發 | 全部在同一個 branch (`methodology-v3`) |
| Feature merge 後 artifact 跟著進來 | 只有最終 Feature (#5) 的 artifacts 被 commit |
| 5 個 Features 可以並行開發 | 順序開發（一次一個 Feature） |
| 每個 Feature 有完整的 8-phase 產物 | Phase 1-2 artifacts 只存在於 Feature #5 |

---

### Framework 的問題

**Framework 的 Phase Artifact 檢查沒有強制執行隔離：**
- Phase 1 → SPEC.md
- Phase 2 → ARCHITECTURE.md
- Phase 3-4 → implement/, test/
- Phase 5 → BASELINE.md, TEST_RESULTS.md

但當 5 個 Features 同時在一個 branch 開發時，這些 artifacts 會互相覆蓋。

---

## 三、正確的流程（未來 Feature #6-15 必須遵守）

### 流程 A：每個 Feature 在 Isolated Branch 開發（推薦）

```
1. git checkout -b v3/feature-N
2. Phase 1: 建立 SPEC.md
   → commit "feat: Feature #N Phase 1 complete - SPEC.md"
3. Phase 2: 建立 ARCHITECTURE.md
   → commit "feat: Feature #N Phase 2 complete - ARCHITECTURE.md"
4. Phase 3-5: implement/ + test/ + pytest
   → commit "feat: Feature #N Phase 3-5 complete"
5. Phase 6-8: DELIVERY_REPORT, RISK_REGISTER, DEPLOYMENT
   → commit "feat: Feature #N Phase 6-8 complete"
6. git push origin v3/feature-N
7. Create PR → main
```

**關鍵紀律：**
- 每個 Phase 完成後馬上 commit
- Phase 1-2 artifacts **必須在 isolated branch 裡**
- PR merge 前確認所有 artifacts 在正確位置

---

### 流程 B：Monorepo 模式（所有 Features 在同一 Branch）

```
1. 所有 Features 都在 main branch
2. 每個 Feature 有自己的目錄：
   features/
   ├── feature-1/
   │   ├── 01-spec/SPEC.md
   │   ├── 02-arch/ARCHITECTURE.md
   │   ├── 03-impl/
   │   ├── 04-test/
   │   ├── 05-verify/
   │   ├── 06-delivery/
   │   ├── 07-risk/
   │   └── 08-deploy/
   ├── feature-2/
   │   └── ...
   └── feature-3/
       └── ...
```

**優點：** 不會有 artifacts 覆蓋問題
**缺點：** 需要確保 framework 的 phase_paths.py 對應到 `features/{name}/`

---

## 四、必須避免的錯誤

### ❌ 錯誤 1：把 Phase 1-2 artifacts 放在 Branch Root

```bash
# 錯
v3/feature-N/
├── SPEC.md        ← 放在 root，merge 時會覆蓋別人的
├── ARCHITECTURE.md
└── implement/

# 對
v3/feature-N/
├── 01-spec/SPEC.md
├── 02-arch/ARCHITECTURE.md
└── implement/
```

### ❌ 錯誤 2：等所有 Features 開發完才 commit Phase 1-2

```bash
# 錯
git checkout -b v3/feature-1
Phase 1-5 → 完成 implement/ + test/
Phase 1-2 artifacts → 一直沒寫
git commit -m "feat: Feature #1 complete"
git checkout -b v3/feature-2
# ... 重複，最後只剩最後一個 Feature 的 artifacts

# 對
Phase 1 → 立即 commit SPEC.md
Phase 2 → 立即 commit ARCHITECTURE.md
Phase 3 → commit implement/
# 每個 Phase 完成後馬上 commit
```

### ❌ 錯誤 3：Branch 指標亂設

```bash
# 錯
git checkout -b v3/feature-1
# 做 Feature #1...
git checkout -b v3/feature-2  # 又建立新指標
# v3/feature-1 指標還在原點，沒有跟著移動

# 對
git checkout -b v3/feature-1
# 做 Feature #1...
git add . && git commit
git push origin v3/feature-1
# 指標就停在 Feature #1 完成的地方
```

---

## 五、Framework 需要強制的事項

### 5.1 Phase Artifact Enforcer 必須檢查目錄結構

```python
# 錯誤時報錯
EXPECTED_PATH = "features/{feature_name}/{phase_dir}/SPEC.md"
# 而不是
EXPECTED_PATH = "SPEC.md"
```

### 5.2 每個 Feature 的 artifacts 必須在 Feature Branch 內

| Phase | 預期路徑 |
|-------|----------|
| 1 | `features/{name}/01-spec/SPEC.md` |
| 2 | `features/{name}/02-arch/ARCHITECTURE.md` |
| 3 | `features/{name}/03-impl/` |
| 4 | `features/{name}/04-test/` |
| 5 | `features/{name}/05-verify/BASELINE.md` |
| 6 | `features/{name}/06-delivery/DELIVERY_REPORT.md` |
| 7 | `features/{name}/07-risk/RISK_REGISTER.md` |
| 8 | `features/{name}/08-deploy/DEPLOYMENT.md` |

### 5.3 Feature Merge PR 必須包含的檢查

```bash
# PR description 必須包含：
1. Phase 1: SPEC.md exists at expected path ✅
2. Phase 2: ARCHITECTURE.md exists at expected path ✅
3. Phase 3-4: implement/ + test/ exist ✅
4. Phase 5: pytest passed (735 tests) ✅
5. Phase 6-8: DELIVERY_REPORT, RISK_REGISTER, DEPLOYMENT exist ✅
6. No cross-feature artifacts in root ✅
```

---

## 六、這次補救的措施

### 措施 1：建立 v3.0 System Overview

從 Feature #5 的代碼和已有的 artifacts 重建了 v3.0 System Overview（SPEC.md + ARCHITECTURE.md）。

覆蓋範圍：
- 5 個 Features 的定位和 interface
- Feature integration diagram
- Layer structure
- 決策記錄（Architecture Decisions）

不涵蓋：
- Features #1-4 的原始需求決策過程
- Phase 1-2 的 alternative analysis
- 每個 Feature 的 decision log

### 措施 2：更新 Phase Paths

Phase artifact paths 已更新為正確的目錄結構（`06-quality/`, `07-risk/`, `08-config/`）。

### 措施 3：建立 INTEGRATION_LESSONS.md

本文檔。確保未來 Feature #6-15 不重蹈覆轍。

---

## 七、Feature #6-15 的行動項目

在開始 Feature #6 之前，必須確認：

- [ ] Framework 的 Phase Artifact Enforcer 支援 `features/{name}/` 目錄結構
- [ ] Feature branch 的 Phase 1-2 artifacts 在 isolated branch 內 commit
- [ ] Feature merge PR 包含完整的 artifact 位置檢查
- [ ] 每個 Feature 的代碼放在 `features/{name}/implement/`
- [ ] 每個 Feature 的測試放在 `features/{name}/test/`
- [ ] Root 目錄沒有 Feature-specific artifacts

---

## 八、總結

| 問題 | 教訓 |
|------|------|
| Phase 1-2 artifacts 丢失 | 每個 Phase 完成後馬上 commit |
| Branch 指標指向同一個 commit | Branch 是開發隔離工具，不是標籤 |
| 所有 Features artifacts 在同一個 root | 必須用 `features/{name}/` 目錄結構 |
| Framework 沒有強制執行 | Phase Artifact Enforcer 必須檢查目錄結構 |

**核心原則：**
> 每個 Feature 是獨立的開發單元。Phase artifacts 必須跟著 Feature 代碼一起 commit，Merge 前不得遺失。

---

*Document: FEATURE_INTEGRATION_LESSONS.md*
*Last Updated: 2026-04-19*
