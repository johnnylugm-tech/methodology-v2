# Auto Optimizer - 自動優化器

每小時自動分析 AI 趨勢、收集痛點、產生改進提案並實施。

## 功能

- 趨勢收集：追蹤 AI 領域最新動態
- 痛點分析：從 HEARTBEAT.md 提取待解決問題
- 提案生成：根據趨勢 + 痛點產生改進建議
- 自動實施：實施高優先級改進
- 文檔生成：自動更新進化日誌

## 使用方式

```python
from auto_optimizer import AutoOptimizer

optimizer = AutoOptimizer()
results = optimizer.run()
```

## Cron 設定

每小時執行：
```cron
0 * * * * cd /workspace && python auto_optimizer/auto_optimizer.py
```

## Lock 機制

避免重複執行：`.last_run` 檔案記錄最後執行時間
