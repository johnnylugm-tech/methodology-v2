#!/usr/bin/env python3
"""
Phase Runner - Phase 1-2 完整版指引生成器
用法: python3 phase_runner.py --phase 1 --project tts-project-v581

完整版：包含 Johnny 規範的所有細節
"""

import sys
import json
import getopt
from pathlib import Path
from datetime import datetime

DEFAULT_METHODOLOGY_PATH = "/workspace"


def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def load_config(phase_num):
    script_dir = Path(__file__).parent
    config_path = script_dir / "phase_config.json"
    with open(config_path, "r") as f:
        all_config = json.load(f)
    return all_config["phases"][str(phase_num)]


def generate_architect_task(phase, config, project_name):
    methodology_path = f"{DEFAULT_METHODOLOGY_PATH}/{project_name}"
    tool_path = f"{DEFAULT_METHODOLOGY_PATH}/methodology-v2"
    
    if phase == 1:
        task = f"""你是 Architect Agent，執行 {project_name} Phase 1

═══════════════════════════════════════════════════════════════
📋 任務：{config.get('name', 'Phase 1')} - 完整版指引
═══════════════════════════════════════════════════════════════

## 🗺️ 一覽表（5W1H）

|5W1H |核心答案 |
|---------|-------------------------------------------------------------------|
|**WHO** |Agent A（Architect）撰寫 × Agent B（Reviewer/PM）審查 |
|**WHAT** |產出 SRS.md + SPEC_TRACKING.md + TRACEABILITY_MATRIX.md + DEVELOPMENT_LOG.md |
|**WHEN** |專案啟動後第一個 Phase；所有其他 Phase 的前置條件 |
|**WHERE**|`01-requirements/` 目錄；Quality Gate 工具在 `{tool_path}/quality_gate/`|
|**WHY** |建立需求基線、ASPICE 合規、防止規格漂移 |
|**HOW** |A 撰寫 → B 審查 → Quality Gate → 雙方 sign-off → 進入 Phase 2 |

═══════════════════════════════════════════════════════════════
## 📁 檔案位置
═══════════════════════════════════════════════════════════════

```
{project_name}/
├── 01-requirements/    ← Phase 1 主要工作區
│   ├── SRS.md          ← 主要產出
│   ├── SPEC_TRACKING.md
│   └── TRACEABILITY_MATRIX.md
│
├── quality_gate/       ← 工具位置（不要改）
│   ├── doc_checker.py
│   └── constitution/
│       └── runner.py
│
└── DEVELOPMENT_LOG.md ← Phase 1 段落
```

═══════════════════════════════════════════════════════════════
## 📦 交付物（4 個，全部要產生）
═══════════════════════════════════════════════════════════════

|文件 |說明 |
|--------------------------------|-------
|`SRS.md` |功能需求規格（FR-001 起編號 + NFR-001 起編號）|
|`SPEC_TRACKING.md` |規格追蹤矩陣 |
|`TRACEABILITY_MATRIX.md` |需求追蹤矩陣（初始化）|
|`DEVELOPMENT_LOG.md` |Phase 1 開發日誌 |

═══════════════════════════════════════════════════════════════
## 📝 SRS.md 最低內容要求
═══════════════════════════════════════════════════════════════

```markdown
# SRS - {project_name}

## 1. 需求概述
## 2. 功能需求（FR-01 ~ FR-XX）
## 3. 非功能需求（NFR）
## 4. 限制條件
## 5. 術語表

# 每條 FR 必須附上「邏輯驗證方法」（Spec Logic Mapping）
| SRS ID | 需求描述 | 實作函數（預估） | 邏輯驗證方法 |
|--------|----------|----------------|-------------|
| FR-01 | ... | ... | 輸出 ≤ 輸入 |
```

### 📌 FR/NFR 編號規則
- **功能需求**：FR-001, FR-002, FR-003...
- **非功能需求**：NFR-001, NFR-002, NFR-003...
- **每個需求必須有「邏輯驗證方法」**

═══════════════════════════════════════════════════════════════
## 🔍 Spec Logic Mapping（核心要求！）
═══════════════════════════════════════════════════════════════

每個需求後必須附「邏輯驗證方法」：

|SRS ID|需求描述 |實作函數 |邏輯驗證方法 |
|------|-------|--------|------------|
|FR-01 |按標點分段 |TextProcessor.split() |輸出長度 ≤ 輸入長度 |
|FR-05 |多段合併 |AudioMerger.merge() |單一與多檔案格式一致性 |
|NFR-01|99% 可用性 |CircuitBreaker |Fault Tolerance 四層架構 |

**⚠️ 禁止**：沒有邏輯驗證方法的需求

═══════════════════════════════════════════════════════════════
## ⚖️ A/B 協作流程（必須遵守）
═══════════════════════════════════════════════════════════════

### 時序圖
```
專案啟動
 │
 ▼
[Agent A] methodology init
 │
 ▼
[Agent A] 撰寫 SRS.md（含 Spec Logic Mapping）
 │
 ▼
[Agent A → Agent B] A/B 審查請求
 │
 ├── ❌ REJECT → Agent A 修改 → 重新提交
 │
 └── ✅ APPROVE
 │
 ▼
 Quality Gate 執行
 │
 ├── 未通過 → Agent A 修正 → 重新 Gate
 │
 └── 通過（Compliance > 80%）
 │
 ▼
 ✅ Phase 1 完成 → 進入 Phase 2
```

### Agent B 審查清單（逐項確認）
- [ ] 所有 FR 編號唯一、無遺漏
- [ ] 每條 FR 有對應的邏輯驗證方法
- [ ] 無「輸出可能大於輸入」的隱患
- [ ] 分支邏輯（if/else）覆蓋完整
- [ ] SPEC_TRACKING.md 已建立
- [ ] TRACEABILITY_MATRIX.md 已初始化

═══════════════════════════════════════════════════════════════
## 🎯 Quality Gate 門檻（必須通過）
═══════════════════════════════════════════════════════════════

|檢查項目 |門檻 |命令 |
|---------|-----|-----|
|ASPICE 合規率 |> 80% |`python3 {tool_path}/quality_gate/doc_checker.py` |
|Constitution SRS 分數 |正確性 100%、可維護性 > 70% |`python3 {tool_path}/quality_gate/constitution/runner.py --type srs` |

═══════════════════════════════════════════════════════════════
## 🚫 Anti-Shortcuts（禁止事項）
═══════════════════════════════════════════════════════════════

- ❌ 禁止跳過 A/B 審查
- ❌ 禁止虛假記錄（只寫「✅ 已通過」）
- ❌ 禁止邏輯模糊（每個需求要有驗證方法）
- ❌ 禁止私自妥協（衝突記錄到 Conflict Log）

═══════════════════════════════════════════════════════════════
## 📊 具體任務清單
═══════════════════════════════════════════════════════════════

### Step 1: 撰寫 SRS.md
- [ ] 功能需求 FR-001 起編號
- [ ] 非功能需求 NFR-001 起編號
- [ ] 每個需求有 Spec Logic Mapping 表格
- [ ] 介面需求定義

### Step 2: 建立 SPEC_TRACKING.md
- [ ] 對照外部 PDF 規格
- [ ] 追蹤每個需求

### Step 3: 建立 TRACEABILITY_MATRIX.md
- [ ] 需求 ID → 架構組件 → 測試對應（初始）

### Step 4: 撰寫 DEVELOPMENT_LOG.md Phase 1 段落
- [ ] 決策過程記錄
- [ ] Quality Gate 執行結果

### Step 5: Quality Gate
- [ ] 執行 doc_checker.py
- [ ] 執行 constitution runner.py --type srs
- [ ] 確認通過後進入 Phase 2

═══════════════════════════════════════════════════════════════
## ✅ 交付檢查清單
═══════════════════════════════════════════════════════════════

- [ ] SRS.md 存在且包含所有 FR/NFR
- [ ] SPEC_TRACKING.md 存在
- [ ] TRACEABILITY_MATRIX.md 存在
- [ ] DEVELOPMENT_LOG.md Phase 1 段落完整
- [ ] Spec Logic Mapping 每個需求都有
- [ ] Constitution 正確性 = 100%
- [ ] ASPICE 合規率 > 80%
"""
    
    elif phase == 2:
        task = f"""你是 Architect Agent，執行 {project_name} Phase 2

═══════════════════════════════════════════════════════════════
📋 任務：{config.get('name', 'Phase 2')} - 完整版指引
═══════════════════════════════════════════════════════════════

## 🗺️ 一覽表（5W1H）

|5W1H |核心答案 |
|---------|-------------------------------------------------------------------|
|**WHO** |Agent A（Architect）設計 × Agent B（Senior Dev / Reviewer）審查 |
|**WHAT** |產出 SAD.md + ADR.md + 更新 TRACEABILITY_MATRIX.md |
|**WHEN** |Phase 1 完整通過後；Phase 3 開發的前置條件 |
|**WHERE**|`02-architecture/` 目錄；Quality Gate 工具在 `{tool_path}/quality_gate/`|
|**WHY** |架構決策一旦進入 Phase 3 才修改，成本指數級上升；A/B 在此攔截最有效 |
|**HOW** |A 設計 → B 架構審查 → Conflict Log → Quality Gate → 雙方 sign-off → Phase 3|

═══════════════════════════════════════════════════════════════
## 📁 檔案位置
═══════════════════════════════════════════════════════════════

```
{project_name}/
├── 01-requirements/    ← Phase 1 產出（只讀，不修改）
│   ├── SRS.md
│   └── SPEC_TRACKING.md
│
├── 02-architecture/    ← Phase 2 主要工作區
│   └── SAD.md
│   └── ADR.md
│
├── quality_gate/
│   └── constitution/
│
└── DEVELOPMENT_LOG.md ← Phase 2 段落
```

═══════════════════════════════════════════════════════════════
## 📦 交付物（4 個）
═══════════════════════════════════════════════════════════════

|SAD.md|系統架構文件|對應 SRS FR → 模組|
|ADR.md|架構決策記錄|每個技術選型的「為什麼不選另一個」|
|TRACEABILITY_MATRIX.md|更新|+ 實作模組欄位|
|DEVELOPMENT_LOG.md|Phase 2 段落|+ 決策過程|

═══════════════════════════════════════════════════════════════
## 🏗️ SAD.md 最低內容要求
═══════════════════════════════════════════════════════════════

|章節 |內容 |
|-----|-----|
|架構概覽|系統邊界圖、核心模組清單|
|模組設計|對應 SRS FR 編號、依賴模組|
|介面定義|模組間 API 合約、資料流向|
|錯誤處理|L1-L6 分類、Retry/Fallback/Circuit Breaker|
|技術選型|每個決定的理由、替代方案、捨棄原因|

═══════════════════════════════════════════════════════════════
## 📋 ADR（架構決策記錄）格式
═══════════════════════════════════════════════════════════════

|決策 |選擇 |理由 |替代方案 |捨棄原因 |
|-----|-----|-----|---------|---------|
|文本分段|正則表達式|簡單快速|ML 模型|準確率不需 99%|

═══════════════════════════════════════════════════════════════
## 🔍 A/B 架構審查（5 維）
═══════════════════════════════════════════════════════════════

Agent B 從以下維度審查：

1. **需求覆蓋完整性** - 所有 FR 有對應模組
2. **模組設計品質** - 低耦合、高內聚
3. **錯誤處理完整性** - L1-L6 對應
4. **技術選型合理性** - ADR 完整
5. **實作可行性** - 可直接指導 Phase 3

═══════════════════════════════════════════════════════════════
## ⚖️ Conflict Log（強制）
═══════════════════════════════════════════════════════════════

當架構設計與 methodology-v2 規範衝突時：

|衝突點 |規格書建議 |methodology-v2 選擇 |理由 |
|--------|------------|---------------------|------|

**即使 0 條也要標明「無衝突」**

═══════════════════════════════════════════════════════════════
## 🎯 Quality Gate 門檻
═══════════════════════════════════════════════════════════════

|檢查 |門檻 |
|-----|-----|
|Phase 1 完成檢查|4 個交付物存在|
|ASPICE 合規率|> 80%|
|Constitution SAD 分數|正確性 = 100%|

═══════════════════════════════════════════════════════════════
## 🚫 Anti-Shortcuts
═══════════════════════════════════════════════════════════════

- ❌ 禁止跳過 A/B 審查
- ❌ 禁止引入未經驗證的框架
- ❌ 禁止私自妥協
- ❌ 禁止虛假記錄
"""
    
    return task


def run_phase(phase_num, project_name):
    config = load_config(phase_num)
    methodology_path = f"{DEFAULT_METHODOLOGY_PATH}/{project_name}"
    tool_path = f"{DEFAULT_METHODOLOGY_PATH}/methodology-v2"
    
    log("=" * 70)
    log(f"🚀 Phase {phase_num}: {config['name']} - 完整版指引")
    log(f"📁 專案: {project_name}")
    log("=" * 70)
    log("")
    
    # Step 1: Architect
    log("📌 Step 1: 啟動 Architect Agent（完整流程）")
    log("-" * 50)
    
    architect_task = generate_architect_task(phase_num, config, project_name)
    
    log("")
    log("⬇️  sessions_spawn 指令：")
    log("")
    log('sessions_spawn(')
    log(f'    label="{project_name}-Phase{phase_num}-Architect",')
    log('    mode="run",')
    log('    runtime="subagent",')
    log(f'    task="""{architect_task[:500]}... """')
    log(')')
    log("")
    
    # Step 2: Reviewer
    log("📌 Step 2: 啟動 Reviewer Agent")
    log("-" * 50)
    log("")
    reviewer_task = "審查 Phase " + str(phase_num) + " 交付物品質" if phase_num == 1 else "審查 Phase 2 架構設計（5維審查）"
    log('sessions_spawn(')
    log(f'    label="{project_name}-Phase{phase_num}-Reviewer",')
    log('    mode="run",')
    log('    runtime="subagent",')
    log(f'    task="{reviewer_task}"')
    log(')')
    log("")
    
    # Step 3: Quality Gate
    log("📌 Step 3: 執行 Quality Gate")
    log("-" * 50)
    
    qg_commands = config.get("quality_gates", [])
    for i, qg in enumerate(qg_commands, 1):
        cmd = qg['command'].replace('/workspace/methodology-v2', tool_path)
        log(f"   {i}. {qg['name']}")
        log(f"      {cmd}")
        log(f"      → {qg['threshold']}")
        log("")
    
    # 交付物
    log("📌 預期交付物")
    log("-" * 50)
    for d in config.get("deliverables", []):
        log(f"   ✅ {d}")
    
    log("")
    log("=" * 70)
    log(f"✅ 完整版指引生成完成 - 專案: {project_name}")
    log("=" * 70)


if __name__ == "__main__":
    phase_num = None
    project_name = None
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "p:", ["phase=", "project="])
    except getopt.GetoptError:
        print("用法: python3 phase_runner.py --phase 1 --project tts-project-v581")
        sys.exit(1)
    
    for opt, arg in opts:
        if opt in ("-p", "--phase"):
            phase_num = arg
        elif opt == "--project":
            project_name = arg
    
    if not phase_num or not project_name:
        print("錯誤: 需要 --phase 和 --project 參數")
        print("用法: python3 phase_runner.py --phase 1 --project tts-project-v581")
        sys.exit(1)
    
    if phase_num not in ["1", "2"]:
        print("錯誤: Phase 必須是 1 或 2")
        sys.exit(1)
    
    run_phase(int(phase_num), project_name)
