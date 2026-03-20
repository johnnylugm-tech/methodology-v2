# 案例五：錯誤處理與監控

## 情境描述

系統需要自動分類和處理錯誤，預防問題發生，並在異常時及時警報。

---

## 案例 5.1：L1-L4 錯誤分類

### 背景
API 偶爾會遇到各種類型的錯誤，需要自動分類並採取適當處理。

### 使用方式

```python
from methodology_base import ErrorClassifier, ErrorHandler, ErrorLevel

classifier = ErrorClassifier()
handler = ErrorHandler()

# 模擬錯誤
errors = [
    Exception("Invalid input: email format"),           # L1
    Exception("Connection timeout"),                     # L2
    Exception("Out of memory"),                          # L3
    Exception("Database unavailable"),                   # L4
]

for error in errors:
    # 分類錯誤
    level = classifier.classify(error)
    print(f"錯誤: {error}")
    print(f"  等級: {level.value}")
    
    # 取得處理建議
    action = handler.get_action(level)
    print(f"  處理: {action}\n")
```

### 輸出範例
```
錯誤: Invalid input: email format
  等級: L1
  處理: 立即返回錯誤訊息給用戶

錯誤: Connection timeout
  等級: L2
  處理: 重試 3 次，指數退避

錯誤: Out of memory
  等級: L3
  處理: 降級處理，釋放資源

錯誤: Database unavailable
  等級: L4
  處理: 熔斷電路，發送警報
```

---

## 案例 5.2：預測監控

### 背景
希望在問題發生前就能預測並預防。

### 使用方式

```python
from methodology import PredictiveMonitor

monitor = PredictiveMonitor()

# 模擬歷史指標
metrics = [
    {"timestamp": "10:00", "error_rate": 0.5, "latency": 120},
    {"timestamp": "11:00", "error_rate": 0.8, "latency": 150},
    {"timestamp": "12:00", "error_rate": 1.2, "latency": 200},
    {"timestamp": "13:00", "error_rate": 1.5, "latency": 280},
]

# 記錄指標
for m in metrics:
    monitor.record(
        metric_name="api_health",
        value=m["error_rate"],
        tags={"latency": m["latency"]}
    )

# 取得預測
forecast = monitor.predict("api_health", horizon="1h")
print(f"未來 1 小時錯誤率預測: {forecast['predicted_value']:.2f}%")
print(f"信心度: {forecast['confidence']:.0%}")

# 取得建議
recommendations = forecast.get("recommendations", [])
if recommendations:
    print(f"\n建議行動:")
    for rec in recommendations:
        print(f"  ⚠️ {rec}")
```

### 輸出範例
```
未來 1 小時錯誤率預測: 2.10%
信心度: 78%

建議行動:
  ⚠️ 錯誤率持續上升，建議擴展容量
  ⚠️ 延遲增加，建議檢查資料庫連接池
```

---

## 案例 5.3：熔斷與故障轉移

### 背景
當某個模型服務不可用時，自動切換到備用方案。

### 使用方式

```python
from methodology import FailoverManager, ModelEndpoint

failover = FailoverManager()

# 註冊主要和備用端點
failover.register_model(
    name="gpt-4o",
    provider="openai",
    api_key="sk-...",
    priority=1
)

failover.register_model(
    name="claude-3-opus",
    provider="anthropic",
    api_key="sk-ant-...",
    priority=2
)

# 設定備用規則
failover.set_fallback("gpt-4o", "claude-3-opus")

# 執行帶故障轉移的任務
def call_llm(prompt):
    # 模擬 LLM 呼叫
    return {"response": "Hello!", "model": "gpt-4o"}

result = failover.execute_with_failover(
    call_llm,
    payload="Say hello",
    timeout=5
)

print(f"回應: {result['response']}")
print(f"使用的模型: {result.get('model', 'primary')}")
print(f"故障轉移: {result.get('failover_triggered', False)}")
```

---

## 相關功能

| 功能 | 模組 |
|------|------|
| 錯誤分類 | `ErrorClassifier` |
| 錯誤處理 | `ErrorHandler` |
| 預測監控 | `PredictiveMonitor` |
| 熔斷管理 | `FailoverManager` |
| 風險儀表板 | `RiskDashboard` |
