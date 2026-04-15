# Ralph Mode × run-phase 整合方案

> **版本**: v1.2
> **日期**: 2026-04-15
> **Framework**: methodology-v2
> **狀態**: 待 Johnny 確認實作

---

## 1. 背景與目標

### 1.1 問題陳述

methodology-v2 的 `plan-phase` 和 `run-phase` 目前存在以下問題：

| 問題 | 說明 |
|------|------|
| 無進度追蹤 | 用戶說「執行 Phase 3」後，主代理 sessions_spawn 執行，但沒有任何背景監控 |
| 幽靈行程 | Ralph Mode 之前有實作，但從未真正啟動過，變成空殼 |
| 狀態不一致 | 如果執行中斷，不知道 sessions_spawn.log 的實際狀態 |
| 超時無 Alert | HR-13（執行時間 > 預估 ×3）無法被及時發現 |
| 衝突無檢測 | 如果用戶重啟同一 Phase，沒有防重複機制 |
| 產出無驗證 | sub-agent 說完成了，但檔案可能根本不存在或損壞 |

### 1.2 設計原則

| 原則 | 說明 |
|------|------|
| **plan-phase 純淨** | `plan-phase` 只產生執行計劃，不觸發任何 Ralph 行為 |
| **run-phase 內嵌 Ralph** | Ralph 是 `run-phase` 的內部實現，用戶完全無感知 |
| **無感啟動/終止** | Ralph 在背景運作，用戶只在有問題時收到 Alert |
| **MVP 先行** | 先實作 3 個核心條件，其餘預設處理方案 |
| **Quality Gate 優先** | Ralph 不接管 Constitution Runner 的職責 |
| **Schema 穩定** | sessions_spawn.log 必須有 Schema Versioning |

---

## 2. 核心原則：誰是做事的？

### 2.1 職責分離

| 系統 | 職責 | Ralph 關係 |
|------|------|-----------|
| **Constitution Runner** | 執行 Quality Gate，決定 Phase 能否進入下一步 | ❌ Ralph 不接管 |
| **cmd_run_phase** | 協調執行流程，包含 Pre/Post-flight | ❌ Ralph 不接管 |
| **sessions_spawn.log** | 記錄 sub-agent 執行狀態（事實來源）| ✅ Ralph 只讀取 |
| **Ralph Mode** | 被動監控者，只讀 log + 發 Alert | ✅ 純監控 |

### 2.2 兩個不打架的原則

```
原則 1：Ralph 是「旁觀者」
- Ralph 只讀 sessions_spawn.log
- Ralph 不執行任何 lint/coverage/Constitution
- 如果要做事，告訴 cmd_run_phase 去做

原則 2：sessions_spawn.log 是事實來源
- 如果 log 說 COMPLETED，那就是 COMPLETED
- Ralph 不會自己去驗證檔案（除非是 L2 Output 驗證）
- log schema 必須穩定（見第 8 章）
```

---

## 3. 三層驗證架構

### 3.1 層級定義

| 層級 | 元件 | 觸發時機 | 檢查內容 | 執行時間 | 重量 |
|------|------|---------|---------|---------|------|
| **L1: Ralph 監控** | RalphScheduler | 每 60s | sessions_spawn.log 讀取進度 | < 1s | ⚡極輕 |
| **L2: Output 驗證** | OutputVerifier | FR 完成時 | 檔案存在 + 基本結構 | 2-5s | 🪶輕量 |
| **L3: Quality Gate** | Constitution Runner | Phase 完成/post-flight | lint + coverage + Constitution | 30s-5m | 🐘重型 |

### 3.2 層級分工

```
L1: Ralph 監控（每 60s）
- 只讀 sessions_spawn.log
- 不做任何執行！不block任何東西！
- 重量: < 1 秒

L2: Output 驗證（每個 FR 完成時）
- L2a: 檔案存在？（< 1s）
- L2b: 檔案大小 > 100 bytes？（< 1s）
- L2c: .py 檔案有 import/class/def？（< 2s）
- 不做：lint / type check / pytest
- 重量: 2-5 秒

L3: Quality Gate（Phase 完成 / post-flight）
- 這是 Constitution Runner 的職責，Ralph 不接管！
- 重量: 30s - 5m
```

---

## 4. MVP：核心終止條件（3 種）

### 4.1 MVP 終止條件（V1 實作）

| # | 情況 | Ralph 行為 | Alert 等級 |
|---|------|-----------|-----------|
| **M1** | 所有 FR COMPLETED | **STOP** + SUCCESS | ✅ SUCCESS |
| **M2** | HR-13 超時（> 預估 ×3）| **Alert**，等待用戶回應 | 🔴 CRITICAL |
| **M3** | 用戶手動終止 | **STOP** + INFO | ✅ INFO |

### 4.2 MVP 流程圖

```
                            ┌──────────────────┐
                            │ Ralph 正在監控   │
                            └────────┬─────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
         ▼                           ▼                           ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ 所有 FR COMPLETED │      │ HR-13 超時？    │      │ 用戶手動終止？   │
└────────┬────────┘      └────────┬────────┘      └────────┬────────┘
         │                         │                         │
    YES  │                    YES  │                    YES  │
         ▼                         ▼                         ▼
    [STOP]                    [Alert]                   [STOP]
    SUCCESS                   🔴 CRITICAL               INFO
```

---

## 5. 其他終止條件：預設處理方案（V2+）

### 5.1 完整終止條件（11 種）

| # | 情況 | MVP 處理 | V2+ 行為 |
|---|------|---------|---------|
| T1 | 所有 FR 完成 + L2 驗證通過 | ✅ M1 已涵蓋 | 同 M1 |
| T2 | post-flight 通過 | ❌ **Ralph 不處理** | cmd_run_phase 職責，Ralph 只發 Alert |
| T3 | post-flight 失敗 | ❌ **Ralph 不處理** | cmd_run_phase 職責，Ralph 只發 Alert |
| T4 | 用戶放棄整個 Phase | ✅ M3 已涵蓋 | 同 M3 |
| T5 | HR-13 超時 | ✅ M2 已涵蓋 | 同 M2 |
| T6 | HR-12 超過 5 輪審查 | ⚠️ **預設：Alert + 繼續** | Alert，等待用戶回應 |
| T7 | 用戶手動停止 | ✅ M3 已涵蓋 | 同 M3 |
| T8 | 系統錯誤/Crash | ⚠️ **預設：Alert + STOP** | Crash Recovery 選項（V2）|
| T9 | Phase 順序錯誤 | ⚠️ **預設：BLOCK** | Alert + 阻止執行（cmd_run_phase 職責）|
| T10 | 孤兒 Ralph（>4 小時無活動）| ⚠️ **預設：Auto-STOP** | Auto-STOP + Alert（V2）|
| T11 | 用戶重新開始同一 Phase | ⚠️ **預設：reuse（繼續）** | 詢問 reuse/restart/discard（V2）|

### 5.2 預設處理矩陣

| 條件 | 預設處理 | 預設理由 |
|------|---------|---------|
| T2/T3 post-flight 結果 | **Ralph 不處理** | Constitution Runner 職責，Ralph 只發 Alert |
| T6 HR-12 超過 5 輪 | **Alert + 繼續監控** | 用戶決定是否放棄 |
| T8 Crash | **Alert + Auto-STOP** | 避免幽靈行程 |
| T9 Phase 順序錯誤 | **BLOCK** | cmd_run_phase 負責檢查，Ralph 只 Alert |
| T10 孤兒 >4 小時 | **Auto-STOP** | 避免資源浪費 |
| T11 同一 Phase 重啟 | **reuse（繼續）** | 最安全的預設值 |

### 5.3 V2 迭代計劃

| 迭代 | 新增條件 | 預估時間 |
|------|---------|---------|
| V2.1 | T6 HR-12 Alert + T11 Conflict Detection | 1.5 小時 |
| V2.2 | T8 Crash Recovery + T10 Orphan Cleanup | 1.5 小時 |
| V2.3 | T9 Phase Sequence Guard | 1 小時 |

---

## 6. L2: Output 驗證（輕量）

### 6.1 驗證時機

| 時機 | 誰觸發 | 驗證內容 |
|------|--------|---------|
| sub-agent 返回 COMPLETED | sessions_spawn logger | L2a + L2b |
| FR COMPLETED 後 | Ralph check_func | L2a + L2b + L2c |

### 6.2 驗證等級

| 等級 | 檢查 | 速度 | 失敗怎麼辦 |
|------|------|------|-----------|
| **L2a** | 檔案存在？ | < 1s | Alert ⚠️ WARNING |
| **L2b** | 檔案大小 > 100 bytes？ | < 1s | Alert ⚠️ WARNING |
| **L2c** | .py 有 import/class/def？ | < 2s | Alert ⚠️ WARNING |

### 6.3 OutputVerifier 實作

```python
class OutputVerifier:
    """輕量驗證：只檢查檔案存在 + 基本結構"""
    
    def verify_fr(self, fr_task: dict) -> VerificationResult:
        expected_files = self._parse_expected_outputs(fr_task)
        errors = []
        
        for filepath in expected_files:
            # L2a: 存在性
            if not Path(filepath).exists():
                errors.append(f"Missing: {filepath}")
                continue
            
            # L2b: 大小
            size = Path(filepath).stat().st_size
            if size < 100:
                errors.append(f"Too small ({size} bytes): {filepath}")
                continue
            
            # L2c: 基本結構（只針對 .py）
            if filepath.endswith(".py"):
                content = Path(filepath).read_text()
                has_code = any(kw in content for kw in ["import", "class ", "def "])
                if not has_code:
                    errors.append(f"No code found: {filepath}")
        
        return VerificationResult(
            passed=(len(errors) == 0),
            fr=fr_task["fr_id"],
            errors=errors,
            verification_level="L2"
        )
```

---

## 7. Ralph Mode 生命週期

### 7.1 觸發點（只有 run-phase）

```
cmd_run_phase --phase 3
         ↓
    [PRE-FLIGHT 檢查完成]
         ↓
    [Ralph START] ← 這裡啟動（後台 daemon）
         ↓
    [sessions_spawn() 執行 FR]
         ↓
    [Ralph 每 60s 監控 sessions_spawn.log] ← L1
         ↓
    [FR 完成 → L2 Output 驗證] ← 每個 FR 完成時
         ↓
    [所有 FR COMPLETED → M1 觸發 → Ralph STOP] ← 正常終止
    [HR-13 超時 → M2 Alert → 用戶決定] ← 異常終止
```

### 7.2 Ralph 啟動時攜帶的 Metadata

```python
{
    "task_id": "phase-3-20260415-194100",
    "phase": 3,
    "repo_path": "/Users/johnny/.../tts-kokoro-v613",
    "fr_list": ["FR-01", "FR-02", "FR-03"],
    "estimated_minutes": 60,
    "start_time": "2026-04-15T19:41:00"
}
```

---

## 8. sessions_spawn.log Schema 穩定性

### 8.1 Schema Versioning

```json
{
    "schema_version": "1.0",
    "schema_definition": {
        "required": ["timestamp", "session_id", "fr", "status"],
        "status_values": ["PENDING", "RUNNING", "COMPLETED", "FAILED"]
    },
    "entries": []
}
```

### 8.2 Ralph Schema Validator

```python
class SessionsSpawnLogValidator:
    CURRENT_SCHEMA = "1.0"
    SUPPORTED_SCHEMAS = ["1.0", "0.9"]
    
    def validate(self, log_path: Path) -> ValidationResult:
        content = json.loads(log_path.read_text())
        schema = content.get("schema_version", "unknown")
        
        if schema not in self.SUPPORTED_SCHEMAS:
            return ValidationResult(
                ok=False,
                error=f"Unsupported schema: {schema}. Supported: {self.SUPPORTED_SCHEMAS}"
            )
        
        return ValidationResult(ok=True)
```

---

## 9. Alert 等級與通知

| 等級 | 觸發條件 | 通知方式 | 等待用戶回應 |
|------|---------|---------|------------|
| ✅ SUCCESS | M1 所有 FR 完成 | Telegram（可選）| 否 |
| ✅ INFO | M3 用戶手動終止 | Telegram（可選）| 否 |
| ⚠️ WARNING | L2 驗證失敗, T6 HR-12 | Telegram | 是（可選）|
| 🔴 CRITICAL | M2 HR-13 超時 | Telegram + 飛書 | 是（必須）|
| ❌ ERROR | T8/T9 系統錯誤 | Telegram + 飛書 | 是（必須）|

---

## 10. 新增元件清單

### 10.1 V1 MVP 元件（P0）

| 元件 | 檔案 | 職責 |
|------|------|------|
| `SessionsSpawnLogValidator` | `ralph_mode/schema_validator.py` | 確保 log schema 穩定 |
| `AlertManager` | `ralph_mode/alert_manager.py` | 統一 Alert 發送（Telegram/飛書/Console）|
| `RalphLifecycleManager` | `ralph_mode/lifecycle.py` | 統一管理 start/stop（M1/M2/M3）|
| `OutputVerifier` (L2) | `ralph_mode/output_verifier.py` | 輕量驗證：檔案存在 + 基本結構 |
| `TaskOutputParser` | `ralph_mode/task_parser.py` | 從 task description 提取預期輸出 |

### 10.2 V2+ 元件（預設處理，後續迭代）

| 元件 | 檔案 | 職責 | 對應條件 |
|------|------|------|---------|
| `PhaseConflictDetector` | `ralph_mode/conflict.py` | 檢測 Phase 衝突、孤兒 | T10, T11 |
| `CrashRecoveryHandler` | `ralph_mode/recovery.py` | Crash 後的恢復邏輯 | T8 |
| `HR12Monitor` | `ralph_mode/hr12_monitor.py` | HR-12 超過 5 輪 Alert | T6 |

---

## 11. 實作計畫

### 11.1 V1 MVP

| 順序 | 元件 | 預估時間 |
|------|------|---------|
| 1 | `SessionsSpawnLogValidator` | 0.5 小時 |
| 2 | `AlertManager` | 1 小時 |
| 3 | `TaskOutputParser` + `OutputVerifier` | 1.5 小時 |
| 4 | `RalphLifecycleManager` (MVP) | 2 小時 |
| 5 | `cmd_run_phase` 整合 | 1.5 小時 |
| 6 | 測試驗證 | 1.5 小時 |

**V1 MVP 總計：8 小時**

### 11.2 V2 迭代

| 迭代 | 新增條件 | 預估時間 |
|------|---------|---------|
| V2.1 | T6 HR-12 Alert + T11 Conflict | 1.5 小時 |
| V2.2 | T8 Crash Recovery + T10 Orphan | 1.5 小時 |

**V2 總計：3 小時**

---

## 12. 結論與建議

### 12.1 Ralph Mode MVP 啟用的好處

| 好處 | 說明 |
|------|------|
| **用戶無感知** | Ralph 是內嵌於 run-phase，用戶只需要說「執行 Phase X」 |
| **狀態透明** | 用戶隨時知道執行進度（通過 Alert 或直接問主代理） |
| **HR-13 Alert** | M2 及時 Alert，用戶可以及早決定是否放棄 |
| **L2 產出驗證** | 確保 sub-agent 產出到位，不只是「說完成」 |
| **Schema 穩定** | SessionsSpawnLogValidator 確保 log 格式不會被破壞 |
| **Quality Gate 不受影響** | Constitution Runner 職責不被打擾 |
| **預設處理** | V2+ 尚未實作的功能有預設值，不會掛死 |

### 12.2 最終建議

**建議啟用 Ralph Mode (V1 MVP)**，實作時間：8 小時
