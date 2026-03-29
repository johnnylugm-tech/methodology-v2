# Phase 1（功能規格）完整 5W1H 計劃框架

> 設計者：Reviewer Agent  
> 日期：2026-03-28  
> 依據：methodology-v2 SKILL.md

---

## 1. What（什麼）- Phase 1 要完成什麼

### 1.1 交付物清單

| 交付物 | 檔案名稱 | 說明 | Quality Gate 檢查 |
|--------|----------|------|-------------------|
| **需求規格說明書** | `SRS.md` | Software Requirements Specification，包含功能需求、非功能需求、介面規格 | Phase 1 |
| **規格追蹤矩陣** | `SPEC_TRACKING.md` | 追蹤外部規格書（PDF）與實作對應關係 | All Phase |
| **領域知識檢查清單** | 自動產生 | 對照領域知識清單（附錄 X）確認需求合理性 | Phase 1 |
| **開發日誌** | `DEVELOPMENT_LOG.md` | 記錄開發過程、決策、衝突點 | All Phase |

### 1.2 Quality Gate 檢查項目

| 檢查項目 | 命令 | 門檻 |
|----------|------|------|
| ASPICE 文檔檢查 | `python3 quality_gate/doc_checker.py` | Compliance Rate ≥ 80% |
| Constitution 檢查（SRS） | `python3 quality_gate/constitution/runner.py --type srs` | 總分 ≥ 60% |
| SPEC_TRACKING 檢查 | `python3 quality_gate/spec_tracking_checker.py` | 完整性 ≥ 90% |
| Decision Framework 檢查 | `python3 .methodology/decisions/check_decisions.py` | MEDIUM/HIGH 風險已確認 |

### 1.3 Phase 1 完成標準

```
✅ SRS.md 完成（功能需求、非功能需求、介面規格）
✅ SPEC_TRACKING.md 初始化（對照外部規格書）
✅ ASPICE 文檔檢查通過（Compliance Rate ≥ 80%）
✅ Constitution 檢查通過（總分 ≥ 60%）
✅ 領域知識檢查完成（對照附錄 X）
✅ DEVELOPMENT_LOG.md 記錄完整
```

---

## 2. Why（為什麼）- 為什麼需要 Phase 1

### 2.1 目的和價值

| 目的 | 價值 |
|------|------|
| **明確定義需求** | 避免開發過程中需求漂移，降低返工成本 |
| **建立可追溯性** | 規格 → 實作 → 測試 全链路可追溯 |
| **品質把關起點** | Phase 1 是品質基線，後續 Phase 品質不能低於此 |
| **領域知識確認** | 確認需求符合領域最佳實踐（如 TTS 領域：標點保留、輸出≤輸入） |

### 2.2 與後續 Phase 的關係

```
Phase 1 (功能規格)
    ↓
    ├─ 輸出：SRS.md → Phase 2 輸入
    ├─ 輸出：SPEC_TRACKING.md → Phase 3-8 全流程使用
    └─ 輸出：領域知識檢查清單 → Phase 3 代碼實作依據

Phase 2 (架構設計)
    ↓ 依賴 Phase 1 的 SRS.md

Phase 3 (代碼實現)
    ↓ 依賴 Phase 1 的 SRS.md + SPEC_TRACKING.md
    ↓ 使用領域知識檢查清單（附錄 X）自我檢查

Phase 4-8 (測試/驗證/交付/品質/配置)
    ↓ 依賴 Phase 1-3 的所有產出
```

### 2.3 失敗後果

| 風險 | 說明 |
|------|------|
| 需求不明確 | Phase 3 代碼實作需反覆確認，浪費時間 |
| 無法追溯 | Phase 5-8 無法驗證規格覆蓋率 |
| 領域知識缺失 | Phase 3 可能違反領域規則（如 TTS 輸出>輸入） |

---

## 3. Who（誰）- 誰來執行

### 3.1 Developer 角色和職責

| 職責 | 具體行動 |
|------|----------|
| **撰寫 SRS.md** | 根據使用者需求，撰寫完整的功能需求、非功能需求、介面規格 |
| **初始化 SPEC_TRACKING.md** | 對照外部規格書（PDF），建立規格追蹤矩陣 |
| **領域知識確認** | 實作前查閱領域知識清單（附錄 X），確認需求合理性 |
| **執行 Quality Gate** | 執行 `python3 quality_gate/doc_checker.py` 等檢查命令 |
| **記錄開發日誌** | 將開發過程記錄到 DEVELOPMENT_LOG.md |

### 3.2 Reviewer 角色和職責

| 職責 | 具體行動 |
|------|----------|
| **審查 SRS.md** | 確認需求完整性、一致性、可實現性 |
| **驗證 Constitution 檢查** | 執行 `python3 quality_gate/constitution/runner.py --type srs`，確認總分 ≥ 60% |
| **確認領域知識檢查** | 確認 Developer 已對照附錄 X 完成檢查 |
| **檢查 SPEC_TRACKING.md** | 確認規格追蹤完整性 ≥ 90% |
| **批准進入 Phase 2** | 確認所有 Quality Gate 通過後，批准進入下一階段 |

### 3.3 A/B 協作流程

```
┌─────────────────────────────────────────────────────────────┐
│                    Phase 1 A/B 協作流程                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Step 1: Developer 啟動                                     │
│  ├─ 閱讀使用者需求                                           │
│  ├─ 查閱領域知識清單（附錄 X）                                 │
│  └─ 撰寫 SRS.md                                             │
│                                                             │
│  Step 2: Developer 執行 Self-Quality Gate                   │
│  ├─ python3 quality_gate/doc_checker.py                    │
│  ├─ python3 quality_gate/constitution/runner.py --type srs │
│  └─ 記錄結果到 DEVELOPMENT_LOG.md                           │
│                                                             │
│  Step 3: Reviewer 審查                                       │
│  ├─ 閱讀 SRS.md                                             │
│  ├─ 執行 Constitution 檢查（複驗）                            │
│  ├─ 確認領域知識檢查清單已覆蓋                                  │
│  └─ 確認 SPEC_TRACKING.md 完整性                            │
│                                                             │
│  Step 4: Reviewer 批准/退回                                  │
│  ├─ 通過 → 進入 Phase 2                                      │
│  └─ 退回 → Developer 修復，循環 Step 2-4                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.4 角色分工表

| 角色 | 主要輸出 | 檢查點 |
|------|----------|--------|
| Developer | SRS.md, SPEC_TRACKING.md, DEVELOPMENT_LOG.md | Self-Quality Gate |
| Reviewer | 審查報告、批准決定 | Constitution 檢查、領域知識確認 |

---

## 4. Where（哪裡）- 在哪裡執行

### 4.1 專案目錄結構

```
/workspace/<專案名稱>/
│
├── 01-requirements/           # Phase 1 產出
│   ├── SRS.md                 # 需求規格說明書
│   ├── SPEC_TRACKING.md       # 規格追蹤矩陣
│   └── DOMAIN_CHECKLIST.md    # 領域知識檢查清單
│
├── 02-architecture/           # Phase 2 產出
│   └── SAD.md                 # 架構設計說明書
│
├── 03-implementation/         # Phase 3 產出
│   └── src/                   # 原始碼
│
├── 04-testing/                # Phase 4 產出
│   ├── TEST_PLAN.md
│   └── TEST_RESULTS.md
│
├── 05-verify/                 # Phase 5 產出
│   └── VERIFICATION_REPORT.md
│
├── 06-delivery/               # Phase 6 產出
│   └── DELIVERY_REPORT.md
│
├── 07-quality/                # Phase 7 產出
│   ├── QUALITY_REPORT.md
│   └── RISK_ASSESSMENT.md
│
├── 08-config/                 # Phase 8 產出
│   └── CONFIG_RECORDS.md
│
├── DEVELOPMENT_LOG.md         # 開發日誌（跨 Phase）
│
├── quality_gate/              # 品質閘道工具（methodology-v2）
│   ├── doc_checker.py
│   ├── constitution/runner.py
│   └── spec_tracking_checker.py
│
└── .methodology/              # 方法論配置
    └── decisions/            # 決策框架
```

### 4.2 文件位置

| 檔案 | 位置 | 說明 |
|------|------|------|
| SRS.md | `01-requirements/SRS.md` | Phase 1 主交付物 |
| SPEC_TRACKING.md | `01-requirements/SPEC_TRACKING.md` | 規格追蹤（初始化於 Phase 1） |
| DEVELOPMENT_LOG.md | 根目錄 | 跨 Phase 開發日誌 |
| Quality Gate 工具 | `quality_gate/` | 由 methodology-v2 提供 |
| Constitution 工具 | `quality_gate/constitution/` | 由 methodology-v2 提供 |

---

## 5. When（何時）- 何時完成

### 5.1 Phase 1 內部時間線

| 階段 | 預估時間 | 交付物 |
|------|----------|--------|
| **Step 1: 需求分析** | 20% 時間 | 需求整理清單 |
| **Step 2: SRS 撰寫** | 40% 時間 | SRS.md 初稿 |
| **Step 3: 領域知識確認** | 10% 時間 | 領域知識檢查清單 |
| **Step 4: Self-Quality Gate** | 10% 時間 | 檢查結果記錄 |
| **Step 5: Reviewer 審查** | 15% 時間 | 審查報告 |
| **Step 6: 修正與批准** | 5% 時間 | 最終版 SRS.md |

**總時間**：取決於專案規模，原則上需求越詳細，Phase 1 越順利

### 5.2 與 Phase 2 的銜接點

| 銜接條件 | 說明 |
|----------|------|
| **SRS.md 通過** | Reviewer 批准進入 Phase 2 |
| **SPEC_TRACKING.md 完整性 ≥ 90%** | 才能進入 Phase 2 |
| **Constitution 總分 ≥ 60%** | 才能進入 Phase 2 |
| **開發日誌已記錄** | 確認開發過程有記錄 |

### 5.3 銜接時機

```
Phase 1 完成
    ↓
    └─→ Phase 2 啟動條件：
        ✅ SRS.md 批准
        ✅ SPEC_TRACKING.md 完整性 ≥ 90%
        ✅ Constitution 總分 ≥ 60%
        ✅ DEVELOPMENT_LOG.md 已記錄
```

---

## 6. How（如何）- 如何執行

### 6.1 步驟-by-步驟流程

#### Step 1: 需求分析

```
1.1 閱讀使用者需求文檔（如有 PDF 規格書）
1.2 識別功能需求（FR-01, FR-02, ...）
1.3 識別非功能需求（NFR-01, NFR-02, ...）
1.4 識別介面需求（API, UI, etc.）
1.5 產出：需求整理清單（internal）
```

#### Step 2: SRS 撰寫（依據 ASPICE 模板）

```markdown
# SRS.md 結構

## 1. 介紹
## 2. 總體描述
## 3. 功能需求
## 4. 非功能需求
## 5. 介面需求
## 6. 其他需求
```

#### Step 3: 領域知識確認（對照附錄 X）

| 領域 | 檢查項 | 驗證方法 |
|------|--------|----------|
| **TTS** | 標點保留 | 輸出長度 ≤ 輸入長度 |
| **TTS** | 合併不多於原文 | 合併後字符數 ≤ 原始字符數 |
| **通用** | 輸出 ≤ 輸入 | 字串操作不插入額外字符 |
| **通用** | 分支一致 | if len(x)==1 與一般情况一致 |

#### Step 4: Self-Quality Gate（Developer 執行）

```bash
# 4.1 ASPICE 文檔檢查
python3 quality_gate/doc_checker.py

# 4.2 Constitution 檢查（SRS）
python3 quality_gate/constitution/runner.py --type srs

# 4.3 SPEC_TRACKING 檢查
python3 quality_gate/spec_tracking_checker.py

# 4.4 記錄結果到 DEVELOPMENT_LOG.md
```

#### Step 5: Reviewer 審查

```
5.1 閱讀 SRS.md
5.2 執行 Constitution 檢查（複驗）
5.3 確認領域知識檢查清單
5.4 檢查 SPEC_TRACKING.md 完整性
5.5 產出：審查報告
```

#### Step 6: 修正與批准

```
6.1 若有問題 → Developer 修正 → 回到 Step 4
6.2 若全部通過 → Reviewer 批准 → 進入 Phase 2
```

### 6.2 Quality Gate 命令

```bash
# Phase 1 Quality Gate 命令清單

# 1. ASPICE 文檔檢查
python3 quality_gate/doc_checker.py

# 2. Constitution 檢查（SRS）
python3 quality_gate/constitution/runner.py --type srs

# 3. SPEC_TRACKING 檢查
python3 quality_gate/spec_tracking_checker.py

# 4. Decision Framework 檢查（推薦）
python3 .methodology/decisions/check_decisions.py

# 5. 整合檢查（一次執行全部）
python3 quality_gate/unified_gate.py

# 6. Framework Enforcement（BLOCK 等級）
methodology quality
```

### 6.3 Constitution 檢查命令

```bash
# Constitution 檢查（SRS 類型）
python3 quality_gate/constitution/runner.py --type srs

# 檢查維度：
# - 正確性（100%）
# - 安全性（100%）
# - 可維護性（>70%）
# - 測試覆蓋率（>80%）

# 門檻：總分 ≥ 60%
```

### 6.4 Enforcement 等級

| 等級 | 檢查項目 | 觸發條件 | 失敗行為 |
|------|----------|----------|----------|
| 🔴 BLOCK | SPEC_TRACKING.md 存在 | 每次 quality 執行 | 阻擋 |
| 🔴 BLOCK | 規格完整性 > 90% | 每次 quality 執行 | 阻擋 |
| 🔴 BLOCK | Constitution Score > 60% | 每次 quality 執行 | 阻擋 |
| 🟡 WARN | Decision Framework 存在 | 每次 quality 執行 | 警告 |

### 6.5 完整執行命令序列

```bash
# Phase 1 完整執行序列

# Step 1: 初始化（若需要）
methodology init

# Step 2: 初始化 SPEC_TRACKING（若需要）
methodology spec-track init

# Step 3: 撰寫 SRS.md（手動）

# Step 4: Self-Quality Gate
python3 quality_gate/doc_checker.py
python3 quality_gate/constitution/runner.py --type srs
python3 quality_gate/spec_tracking_checker.py

# Step 5: 記錄到 DEVELOPMENT_LOG.md（手動）

# Step 6: Reviewer 審查（手動）

# Step 7: Framework Enforcement（最終檢查）
methodology quality
```

---

## 7. 附件：領域知識檢查清單（Phase 1 專用）

### 7.1 TTS 領域（附錄 X.1）

| 檢查項 | 說明 | Phase 1 行動 |
|--------|------|--------------|
| 標點保留 | 標點=停頓信號，刪除會破壞韻律 | 確認 SRS 中有規範 |
| 合併不多於原文 | 合併時不插入額外字符 | 確認 SRS 中有規範 |
| 格式一致性 | 單一檔案與多檔案格式相同 | 確認 SRS 中有規範 |
| Lazy Check | 外部依賴不在 __init__ 直接呼叫 | 確認 SRS 中有規範 |

### 7.2 通用領域（附錄 X.2）

| 檢查項 | 說明 | Phase 1 行動 |
|--------|------|--------------|
| 輸出 ≤ 輸入 | 字串操作不插入額外字符 | 確認 SRS 中有規範 |
| 分支一致 | if len(x)==1 與一般情况一致 | 確認 SRS 中有規範 |
| Lazy Init | 外部依賴在實際需要時才檢查 | 確認 SRS 中有規範 |

---

## 8. 總結

### Phase 1 成功要素

| 要素 | 關鍵行動 |
|------|----------|
| **需求明確** | SRS.md 完整、清楚、可實現 |
| **可追溯** | SPEC_TRACKING.md 完整性 ≥ 90% |
| **品質達標** | Constitution 總分 ≥ 60% |
| **領域知識正確** | 對照附錄 X 檢查 |
| **記錄完整** | DEVELOPMENT_LOG.md 記錄所有開發過程 |

### Phase 1 → Phase 2 銜接確認清單

```
□ SRS.md 已批准
□ SPEC_TRACKING.md 完整性 ≥ 90%
□ Constitution 總分 ≥ 60%
□ ASPICE 文檔檢查通過
□ 領域知識檢查完成
□ DEVELOPMENT_LOG.md 已記錄
□ Reviewer 已批准
```

---

*本框架依據 methodology-v2 SKILL.md v5.56 設計*