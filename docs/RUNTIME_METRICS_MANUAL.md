# Runtime Metrics 操作手冊

> **版本**: v6.15.1  
> **日期**: 2026-04-02  
> **適用專案**: 所有使用 methodology-v2 的專案

---

## 目錄

1. [系統概覽](#1-系統概覽)
2. [安裝設定](#2-安裝設定)
3. [使用方式](#3-使用方式)
4. [煞車系統（安全閥）](#4-煞車系統安全閥)
5. [預警規則](#5-預警規則)
6. [預警範例](#6-預警範例)
7. [故障排除](#7-故障排除)

---

## 1. 系統概覽

### 1.1 系統定位

```
┌─────────────────────────────────────────────────────────┐
│  methodology-v2 (方法論框架)                             │
│  • 定義 Phase 流程 (1-8)                               │
│  • 定義 Quality Gate 規則                              │
│  • 定義 HR-01~HR-14 硬規則                             │
│  • 提供 UnifiedGate Python API                         │
│  • ⬆️ 為監控系統提供「觀測點」鉤子                     │
└─────────────────────────────────────────────────────────┘
                    │
                    │ UnifiedGate 執行時自動觸發
                    ▼
┌─────────────────────────────────────────────────────────┐
│  Runtime Metrics 監控系統 (獨立的環境監控工具)             │
│  • .methodology/state.json (狀態檔)                    │
│  • state_monitor.py (Cron Job)                        │
│  • Telegram 預警通知                                   │
│  • ⬆️ 觀測 methodology-v2 的執行狀態                  │
└─────────────────────────────────────────────────────────┘
```

### 1.2 系統組成

| 檔案 | 說明 | 位置 |
|------|------|------|
| `state.json` | Phase 執行狀態 | `.methodology/state.json` |
| `unified_gate.py` | 寫入鉤子（自動） | `quality_gate/unified_gate.py` |
| `state_monitor.py` | Cron Job 腳本 | `.methodology/state_monitor.py` |

### 1.3 追蹤指標

| 指標 | 說明 | 觸發時機 |
|------|------|----------|
| `blocks` | BLOCK 次數 | FrameworkEnforcer 返回 BLOCK |
| `ab_rounds` | A/B 來回次數 | A↔B 對話一次 |
| `elapsed_minutes` | 已耗費時間 | 自動計算 |
| `last_gate_score` | 最後分數 | Quality Gate 完成 |
| `integrity_score` | Integrity 分數 | 計算邏輯正確性 |

---

## 2. 安裝設定

### 2.1 前置需求

- Python 3.10+
- methodology-v2 v6.15.0+
- OpenClaw（用於 Telegram 通知）

### 2.2 初始化 state.json

第一次在專案執行 Quality Gate 時，state.json 會自動建立：

```bash
cd /path/to/project
python3 -c "
import sys
sys.path.insert(0, '/path/to/methodology-v2')
from quality_gate import UnifiedGate
gate = UnifiedGate('.')
gate._ensure_state()  # 初始化 state.json
"
```

或直接執行 Quality Gate：

```bash
python3 -c "
import sys
sys.path.insert(0, '/path/to/methodology-v2')
from quality_gate import UnifiedGate
gate = UnifiedGate('.')
result = gate.check_all(phase=1)
"
```

### 2.3 設定 Crontab（自動化）

```bash
# 編輯 crontab
crontab -e

# 加入以下行（每 5 分鐘執行一次）
*/5 * * * * cd /path/to/project && python3 /path/to/methodology-v2/scripts/state_monitor.py --check-trends >> /tmp/state_monitor.log 2>&1
```

### 2.4 驗證 Crontab 設定

```bash
# 查看 crontab 列表
crontab -l

# 測試執行
python3 /path/to/methodology-v2/scripts/state_monitor.py --check-trends --project-path /path/to/project
```

---

## 3. 使用方式

### 3.1 CLI 命令

#### 查看 Phase 執行狀態

```bash
python3 cli.py phase-status --phase 2
```

**輸出範例：**

```
╔══════════════════════════════════════════════════════════════╗
║  Phase 2 Runtime Status                                  ║
╠══════════════════════════════════════════════════════════════╣
║  Current Phase:     2                                      ║
║  Started At:        2026-04-02T08:00:00+00:00             ║
║  Elapsed:           45 min                                 ║
╠══════════════════════════════════════════════════════════════╣
║  Metrics                                                        ║
║  ├── BLOCK Count:      3                                   ║
║  ├── A/B Rounds:      2                                   ║
║  ├── Warnings:        1                                   ║
║  └── Last Gate Score: 87                                  ║
╠══════════════════════════════════════════════════════════════╣
║  Alerts (1)                                                  ║
║  🚨 BLOCK_COUNT_HIGH: 3 (threshold: 5)                    ║
╚══════════════════════════════════════════════════════════════╝
```

#### 查看 A/B 來回歷史

```bash
python3 cli.py ab-history --phase 2
```

**輸出範例：**

```
╔══════════════════════════════════════════════════════════════╗
║  Phase 2 A/B History                                       ║
╠══════════════════════════════════════════════════════════════╣
║  1. 🚀 [2026-04-02T08:00] PHASE_START   Phase started      ║
║  2. 🔴 [2026-04-02T08:15] BLOCK         violations: 2       ║
║  3. ↔️  [2026-04-02T08:20] AB_ROUND     A/B exchange      ║
║  4. 🔴 [2026-04-02T08:30] BLOCK         violations: 1       ║
╚══════════════════════════════════════════════════════════════╝
```

#### 檢查 Phase 時長

```bash
python3 cli.py time-check --phase 2 --threshold 120
```

**輸出範例：**

```
╔══════════════════════════════════════════════════════════════╗
║  Phase 2 Time Check                                         ║
╠══════════════════════════════════════════════════════════════╣
║  Threshold: 120 minutes                                      ║
║  Elapsed:   45 minutes                                      ║
║                                                                        ║
║  ✅ OK                                                            ║
╚══════════════════════════════════════════════════════════════════╝
```

#### 跨專案失敗熱圖（框架）

```bash
python3 cli.py audit-heatmap
```

### 3.2 state_monitor.py 命令

#### 手動執行趨勢檢查

```bash
python3 state_monitor.py --check-trends --project-path /path/to/project
```

#### 查看幫助

```bash
python3 state_monitor.py --help
```

### 1.4 Phase 狀態機

```
┌────────────┐  HR-12/13觸發  ┌────────────┐
│  RUNNING   │ ────────────▶ │   PAUSE    │
└────────────┘               └────────────┘
     ▲                            │
     │                            │ Johnny 裁決
     │                            ▼
     │                      ┌────────────┐
     └───────────────────── │  RESUMING  │
                            └────────────┘

┌────────────┐  HR-14觸發   ┌────────────┐
│   任意狀態   │ ───────────▶ │   FREEZE   │
└────────────┘              └────────────┘
                                  │
                                  │ 全面稽核通過
                                  ▼
                            ┌────────────┐
                            │   THAWED   │
                            └────────────┘
```

---

## 4. 煞車系統（安全閥）

### 4.1 HR-12/13/14 規則定義

HR-01~HR-11 定義了「違反哪些規則會終止」，但沒有定義「誰來執行終止」。 HR-12/13/14 是實質的煞車機制。

| ID | 規則 | 閾值 | 違反後果 | 執行者 |
|----|------|------|----------|--------|
| **HR-12** | A/B 審查輪次上限 | > 5 輪/Phase | 強制 PAUSE，通知 Johnny | state_monitor.py |
| **HR-13** | Phase 執行時間上限 | > 3× 預估 | 強制 checkpoint，輸出 BLOCKER 清單，PAUSE | state_monitor.py |
| **HR-14** | Integrity 分數底線 | < 40 | FREEZE 專案，全面審計後才能繼續 | state_monitor.py |

### 4.2 Johnny 介入條件（§6.5 擴充版）

| 觸發條件 | 自動行為 | Johnny 動作 |
|---------|---------|------------|
| Agent B 有重大疑問無法解決 | 暫停執行 | 人工裁決 |
| 分數 < 50 | 禁止進入下一 Phase | 審查 Agent A 工作 |
| 作假跡象（L6 錯誤） | 終止 + 記錄 | 調查 session log |
| A/B 輪次 > 5（HR-12） | 自動 PAUSE | 判斷是否重新分工或 RESET |
| Phase 時間 > 3× 預估（HR-13） | 自動 PAUSE | 評估是否簡化範圍 |
| Integrity < 40（HR-14） | FREEZE 專案 | 全面稽核 |
| BLOCK 數 > 5 且同一維度 | 觸發 Phase Reset | 評估 SRS/SAD 品質 |

### 4.3 煞車觸發後的流程

```
HR-12/13/14 觸發
       ↓
state_monitor.py 檢測到
       ↓
寫入 state.json history[]（不可刪除）
       ↓
發送 Telegram 預警給 Johnny
       ↓
Johnny 登入 OpenClaw 人工裁決
       ↓
執行 phase-resume / phase-reset / phase-thaw
```

### 4.4 Phase Reset vs FREEZE

| 動作 | 觸發條件 | 影響範圍 | Johnny 動作 |
|------|----------|----------|-------------|
| **Phase Reset** | BLOCK > 5 同一維度 | 單一 Phase | 評估 SRS/SAD 品質後重跑 |
| **FREEZE** | Integrity < 40 | 全專案 | 全面稽核後才能繼續 |

---

## 5. 預警規則

### 4.1 預警阈值

| 指標 | 阈值 | 預警類型 |
|------|------|----------|
| BLOCK 次數 | ≥ 5 | `BLOCK_COUNT_HIGH` |
| A/B 來回 | ≥ 5 | `AB_ROUND_HIGH` |
| Phase 執行時間 | ≥ 120 分鐘 | `PHASE_TIMEOUT` |

### 4.2 觸發邏輯

```
每次 Quality Gate 執行
       ↓
更新 state.json
       ↓
Crontab 每 5 分鐘執行
       ↓
檢查阈值
       ↓
有觸發 → 發送 Telegram 預警
```

### 4.3 修改預警阈值

編輯 `state_monitor.py` 頂部的阈值設定：

```python
THRESHOLDS = {
    "blocks": 5,           # BLOCK 次數警戒線
    "ab_rounds": 5,        # A/B 來回警戒線
    "elapsed_minutes": 120,  # Phase 執行時間警戒線（分鐘）
}
```

---

## 5. 預警範例

### 5.1 BLOCK 過多

```
🚨  [Phase 2 Runtime Alert]

🚨 BLOCK_COUNT_HIGH
   BLOCK 次數過高: 6 (警戒線: 5)
   建議：檢查 FrameworkEnforcer 輸出

📊  當前狀態:
   - BLOCK: 6 次
   - A/B 來回: 3 輪
   - 已耗時: 45 分鐘
   - 最後分數: 72%

💡  建議: 檢查 FrameworkEnforcer 輸出或考慮分割 Phase
```

### 5.2 A/B 來回過多

```
🚨  [Phase 2 Runtime Alert]

⚠️  A/B 來回過多: 6 (警戒線: 5)
   建議：檢查 Agent B 是否有 blocking 問題

📊  當前狀態:
   - BLOCK: 2 次
   - A/B 來回: 6 輪
   - 已耗時: 80 分鐘
   - 最後分數: 85%

💡  建議: 考慮簡化範圍或分割 Phase
```

### 5.3 Phase 執行過久

```
🚨  [Phase 2 Runtime Alert]

⏱️  Phase 執行過久: 125 分鐘 (警戒線: 120)
   建議：考慮簡化範圍或分割 Phase

📊  當前狀態:
   - BLOCK: 1 次
   - A/B 來回: 4 輪
   - 已耗時: 125 分鐘
   - 最後分數: 90%

💡  建議: 考慮分割 Phase 或簡化驗收標準
```

---

## 6. 故障排除

### 6.1 state.json 不存在

**問題**：執行 `phase-status` 時顯示 "state.json not found"

**原因**：Quality Gate 還沒執行過

**解決**：
```bash
cd /path/to/project
python3 -c "
import sys
sys.path.insert(0, '/path/to/methodology-v2')
from quality_gate import UnifiedGate
gate = UnifiedGate('.')
result = gate.check_all(phase=1)
"
```

### 6.2 Crontab 沒執行

**問題**：預警沒有發送到 Telegram

**檢查步驟**：

```bash
# 1. 確認 crontab 設定正確
crontab -l

# 2. 手動執行測試
python3 /path/to/methodology-v2/scripts/state_monitor.py --check-trends --project-path /path/to/project

# 3. 查看日誌
cat /tmp/state_monitor.log
```

### 6.3 Telegram 通知失敗

**問題**：state_monitor.py 顯示 "Telegram notification failed"

**解決**：

1. 確認 OpenClaw 已啟動
2. 確認 Telegram Bot 已設定
3. 使用 `--dry-run` 模式測試

```bash
python3 state_monitor.py --check-trends --dry-run
```

### 6.4 預警一直重複發送

**問題**：同一個預警被發送多次

**原因**：預警觸發後沒有「已消除」機制

**解決**：目前設計是「達標後只發送一次」，如果問題消除後又達標，會再次發送。

---

## 附錄

### A. state.json 結構

```json
{
  "version": "1.0",
  "project": "tts-kokoro-v613",
  "current_phase": 2,
  "phase_state": {
    "started_at": "2026-04-02T08:00:00Z",
    "elapsed_minutes": 45,
    "ab_rounds": 2,
    "blocks": 3,
    "warnings": 1,
    "last_gate_score": 87,
    "last_check_at": "2026-04-02T08:45:00Z"
  },
  "trend_alerts": ["BLOCK_COUNT_HIGH"],
  "history": [
    {"timestamp": "2026-04-02T08:00:00Z", "event": "PHASE_START", "phase": 2},
    {"timestamp": "2026-04-02T08:15:00Z", "event": "BLOCK", "phase": 2, "violations": 2},
    {"timestamp": "2026-04-02T08:45:00Z", "event": "GATE_CHECK", "phase": 2, "score": 87}
  ]
}
```

### B. 版本歷史

| 版本 | 日期 | 變更 |
|------|------|------|
| v6.15.0 | 2026-04-02 | 初始版本 |

---

*最後更新：2026-04-02*
