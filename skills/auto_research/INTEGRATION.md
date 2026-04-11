# AutoResearch 整合進 methodology-v2

> **Version**: v2.0.0
> **Date**: 2026-04-11
> **Author**: Musk Agent
> **Purpose**: 將 AutoResearch 整合為 methodology-v2 的全域品質監控選項

---

## 當前狀態（v7.35/v7.36）

| 元件 | 狀態 | 說明 |
|------|------|------|
| CLI `auto-research` 命令 | ✅ 已實作 | `python cli.py auto-research --project /path --phase 3` |
| `--no-autoresearch` 標誌 | ✅ 已實作 | `run-phase --no-autoresearch` |
| 全域開關 | ✅ 已實作 | `project-config.yaml` 中設定 |
| Phase-aware scoring | ✅ 已實作 | 每個 Phase 只計算活躍維度 |
| POST-FLIGHT 觸發 | ✅ 已實作 | Phase 完成後自動執行 |

---

## 設定檔案格式

### project-config.yaml

```yaml
# AutoResearch 全域設定
auto_research:
  enabled: true              # 全域開關，預設 true
  
  # Phase-specific 配置
  phases:
    3:
      dimensions: [D1, D5, D6, D7]
      target: 85
    4:
      dimensions: [D1, D2, D3, D4, D5, D6, D7]
      target: 85
    5:
      dimensions: all
      target: 85
```

### CLI 覆寫

```bash
# 使用全域設定（預設）
python3 cli.py run-phase --phase 3 --repo /path

# 停用 AutoResearch
python3 cli.py run-phase --phase 3 --repo /path --no-autoresearch

# 單獨執行 AutoResearch
python3 cli.py auto-research --project /path --phase 3 --iterations 3
```

---

## 執行流程

### 流程圖

```
┌─────────────────────────────────────────────────────────────┐
│ run-phase --phase N                                       │
├─────────────────────────────────────────────────────────────┤
│ 1. 執行 Phase N 邏輯                                      │
│ 2. 進入 POST-FLIGHT                                        │
│ 3. 讀取 project-config.yaml 的 auto_research.enabled       │
│    └─→ false → 顯示「Enabled: no」並跳過                   │
│ 4. 根據 Phase 取得活躍維度                                  │
│    Phase 3 → [D1, D5, D6, D7]                             │
│    Phase 4 → [D1, D2, D3, D4, D5, D6, D7]                 │
│    Phase 5+ → [D1, D2, D3, D4, D5, D6, D7, D8, D9]        │
│ 5. 執行 AutoResearch（最多 3 輪）                          │
│ 6. 報告結果                                                │
└─────────────────────────────────────────────────────────────┘
```

### Phase-aware Scoring

```python
# Phase 3：只計算 4 個維度
total_score = (D1 + D5 + D6 + D7) / 4 * 100

# Phase 4：計算 7 個維度
total_score = (D1 + D2 + D3 + D4 + D5 + D6 + D7) / 7 * 100

# Phase 5+：計算全部 9 個維度
total_score = (D1 + D2 + D3 + D4 + D5 + D6 + D7 + D8 + D9) / 9 * 100
```

---

## 實作細節

### CLI 命令

```bash
# auto-research 命令
$ python3 cli.py auto-research --help
usage: cli.py auto-research [-h] --project PROJECT [--phase PHASE]
                          [--iterations ITERATIONS] [--dimensions DIMENSIONS]

# run-phase 命令（新增 --no-autoresearch）
$ python3 cli.py run-phase --help
usage: cli.py run-phase [--repo REPO] [--resume] [--no-autoresearch]
```

### AgentDrivenAutoResearch 初始化

```python
from quality_dashboard.agent_auto_research import AgentDrivenAutoResearch

# Phase 3（只計算 D1, D5, D6, D7）
agent = AgentDrivenAutoResearch('/path/to/project', phase=3)

# Phase 5+（計算全部 9 維度）
agent = AgentDrivenAutoResearch('/path/to/project', phase=5)

result = agent.run(max_iterations=3)
```

---

## 範例輸出

### `run-phase` POST-FLIGHT

```
=== POST-FLIGHT: AutoResearch Quality Check ===
   Enabled: yes (project-config.yaml)
   Phase: 3
   Active dimensions: D1_Linting, D5_Complexity, D6_Architecture, D7_Readability
   
🚀 Agent-Driven AutoResearch Loop 啟動
   專案: tts-kokoro-v613
   Phase: 3
   活躍維度: D1_Linting, D5_Complexity, D6_Architecture, D7_Readability
   目標: 85% (及格: 70%)

📊 當前分數 (Phase 3 活躍維度):
   ✅ D1_Linting: 90.0%
   ✅ D5_Complexity: 100.0%
   ✅ D6_Architecture: 100.0%
   ✅ D7_Readability: 100.0%

   Phase 3 分數: 97.5% / 目標: 85%
🎉 達成目標分數 85%！
```

### `auto-research` 獨立命令

```bash
$ python3 cli.py auto-research --project /path --phase 3

🔬 AutoResearch Quality Improvement
   Project: /path
   Phase: 3
   Active dimensions: D1_Linting, D5_Complexity, D6_Architecture, D7_Readability
   Max iterations: 3
   Enabled: True

🚀 Agent-Driven AutoResearch Loop 啟動
...
```

---

## 版本歷史

| 版本 | 改進 |
|------|------|
| v7.34 | 整合規劃文件 |
| v7.35 | CLI 命令實作（auto-research, --no-autoresearch, 全域開關）|
| v7.36 | Phase-aware scoring（每個 Phase 只計算活躍維度）|

---

## Quick Reference

| 設定 | 預設值 | 說明 |
|------|--------|------|
| `auto_research.enabled` | `true` | 全域開關 |
| `--no-autoresearch` | `false` | CLI 覆寫 |
| `iterations.max` | `3` | 最大迭代次數 |
| `scoring.target` | `85` | 目標分數 |
| `scoring.pass` | `70` | 及格分數 |

---

*最後更新: 2026-04-11*
