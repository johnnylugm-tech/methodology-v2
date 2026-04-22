# Feature #13 — Risk Register

## 風險概覽

| ID | 風險描述 | 嚴重性 | 可能性 | 緩解措施 |
|----|---------|--------|--------|---------|
| RR-13-01 | SQLite 寫入失敗（磁碟滿）| 高 | 低 | flush 失敗只 log stderr，buffer 保留不丟 |
| RR-13-02 | decision_log sequence counter 記憶體重啟丢失 | 中 | 低 | 第一次 write 時掃描目錄重建 counter |
| RR-13-03 | threading.Timer 導致程序無法退出 | 低 | 中 | daemon=True + caller 需在 shutdown 時 cancel |
| RR-13-04 | YAML 序列化失敗時 fallback JSON 可能破坏格式 | 低 | 低 | fallback 只在 YAML 失敗時觸發，YAML 可用則不用 |

---

## 風險細節

### RR-13-01: SQLite 寫入失敗（磁碟滿）

**嚴重性:** 高  
**可能性:** 低  
**根本原因:** 磁碟空間耗盡時，`sqlite3.connect()` 或 `cursor.execute()` 拋出 `OperationalError`  
**觸發條件:** 長時間運行累積大量 effort records，且未定期 flush  
**影響範圍:** effort_metrics 無法寫入，指標丢失  
**緩解措施:**
- `EffortTracker.flush()` 失敗時只 log 到 stderr，不拋异常
- Buffer 內的 records 保留在記憶體，下次 flush 重試
- 建議監控磁碟使用率

**殘餘風險:** 記憶體 buffer 撐爆（需 caller 定期 flush）

---

### RR-13-02: decision_log sequence counter 記憶體重啟丢失

**嚴重性:** 中  
**可能性:** 低  
**根本原因:** `_seq` counter 存在記憶體，程序重啟後歸零  
**觸發條件:** 程序崩潰或重啟後繼續寫入  
**影響範圍:** decision_log 檔案可能衝突（同一 seq 寫入不同內容）  
**緩解措施:**
- `DecisionLogWriter.__init__` 時若目錄已存在，掃描所有 `.jsonl` 檔案
- 找到最大 seq 值，加 1 作為起始 counter
- 新程序啟動時自動重建，不丢失連續性

**殘餘風險:** 檔案損壞或不存在時 counter 重置為 0

---

### RR-13-03: threading.Timer 導致程序無法退出

**嚴重性:** 低  
**可能性:** 中  
**根本原因:** `EffortTracker` 內部 Timer 為非 daemon 執行緒，阻止程序退出  
**觸發條件:** caller 完成工作但未呼叫 `flush()` + `cancel()`  
**影響範圍:** 程序僵死，需強制作廢（`SIGKILL`）  
**緩解措施:**
- `EffortTracker._timer = threading.Timer(..., daemon=True)` — daemon=True
- 文件明確說明 caller 需在 shutdown 時呼叫 `effort.flush(); effort._timer.cancel()`
- 若無 caller 介入，最多等 60 秒後自動釋放

**殘餘風險:** caller 忘記 cancel 時仍會阻塞 60 秒

---

### RR-13-04: YAML 序列化失敗時 fallback JSON 可能破坏格式

**嚴重性:** 低  
**可能性:** 低  
**根本原因:** `YAMLGoalNodeCodec.dumps()` 失敗時 fallback 到 `json.dumps`  
**觸發條件:** YAML library 故障或特殊字元觸發序列化異常  
**影響範圍:** decision_log 輸出格式不一致（部分為 YAML，部分為 JSON）  
**緩解措施:**
- Fallback 邏輯在 try/except 內，YAML 可用時一定用 YAML
- JSON fallback 只在 YAML 完全失敗時觸發
- 讀取端 `loads()` 支援 yaml.safe_load / json.loads 自動識別

**殘餘風險:** 低（YAML 通常不會失敗）

---

## 風險矩阵

```
可能性 →
嚴重性 ↓    低    中    高
  高        -    RR-13-01 (低可能)
  中   RR-13-02   RR-13-03   -
  低        RR-13-04   -      -
```

---

## 審查狀態

- RR-13-01: ACCEPT（高嚴重/低可能性，buffer 設計可接受）
- RR-13-02: ACCEPT（中嚴重/低可能性，目錄掃描重建可接受）
- RR-13-03: ACCEPT（低嚴重/中可能性，daemon=True 緩解）
- RR-13-04: ACCEPT（低嚴重/低可能性，fallback 為保守設計）