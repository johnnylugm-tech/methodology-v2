# AutoResearch 整合進 methodology-v2

> **Version**: v1.0.0
> **Date**: 2026-04-11
> **Author**: Musk Agent
> **Purpose**: 將 AutoResearch 整合為 methodology-v2 的全域品質監控選項

---

## 整合目標

1. **全域開關**：`auto_research.enabled = true/false`（預設 true）
2. **Phase Trigger**：在特定 Phase 完成後自動觸發
3. **維度階段化**：根據當前 Phase 活躍維度評估

---

## 設定檔案格式

### project-config.yaml

```yaml
# AutoResearch 全域設定
auto_research:
  enabled: true              # 全域開關，預設 true
  
  # Phase Trigger（可選）
  trigger_after_phase: [3, 5]  # 這些 Phase 完成後自動觸發
  
  # 維度設定
  dimensions:
    phase_3: [D1, D5, D6, D7]    # Phase 3 活躍維度
    phase_4: [D1, D2, D3, D4, D5, D6, D7]
    phase_5: all                    # Phase 5+ 全部維度
    
  # 分數標準
  scoring:
    pass: 70
    target: 85
    
  # 迭代設定
  iterations:
    min: 1
    max: 3
    stop_on_full: true  # 全 100% 時提前停止
```

### CLI 覆寫

```bash
# 使用全域設定
python3 cli.py phase-3

# 停用 AutoResearch
python3 cli.py phase-3 --no-autoresearch

# 只跑 AutoResearch（不執行 Phase）
python3 cli.py auto-research --project /path/to/project --phase 3
```

---

## CLI 整合

### 新增命令

```python
@cli.command('auto-research')
@click.option('--project', required=True)
@click.option('--phase', default=3, type=click.Choice([3, 4, 5, 6, 7]))
@click.option('--iterations', default=3)
@click.option('--dimensions', default=None)  # None = 使用 phase 預設
def auto_research(project, phase, iterations, dimensions):
    """執行 AutoResearch 品質改進"""
    # 讀取 project-config.yaml 的 auto_research.enabled
    # 如果 enabled=False，顯示提示並退出
    # 否則執行 AutoResearch
```

### Phase 命令修改

```python
@cli.command('phase-3')
@click.option('--no-autoresearch', is_flag=True)
def phase_3(no_autoresearch):
    """執行 Phase 3"""
    # 執行 Phase 3 邏輯
    
    # 檢查 AutoResearch 是否啟用
    if not no_autoresearch:
        config = load_project_config()
        if config.get('auto_research', {}).get('enabled', True):
            # 執行 AutoResearch
            run_autoresearch(project_path, phase=3)
```

---

## 執行流程

### 流程圖

```
┌─────────────────────────────────────────────────────────────┐
│ 執行 Phase N                                               │
├─────────────────────────────────────────────────────────────┤
│ 1. 執行 Phase N 邏輯                                       │
│ 2. 檢查 auto_research.enabled                               │
│    └─→ false → 跳過，直接完成                              │
│ 3. 根據當前 Phase 取得活躍維度                              │
│ 4. 執行 AutoResearch（min-max 輪）                          │
│ 5. 檢查結果                                                 │
│    └─→ 全 100% 或已達目標分數 → 完成                        │
│    └─→ 未達標且還有輪數 → 繼續                              │
│ 6. 報告結果                                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 實作規劃

| 元件 | 檔案 | 說明 |
|------|------|------|
| 設定讀取 | `cli.py` | 新增 `load_autoresearch_config()` |
| Phase Trigger | `cli.py` | 在 Phase 完成後呼叫 |
| AutoResearch 執行 | `quality_dashboard/agent_auto_research.py` | 現有腳本增強 |
| 報告生成 | `cli.py` | 整合進 Phase 輸出 |

---

## 範例輸出

```bash
$ python3 cli.py phase-3 --project /path/to/project

=== Phase 3 執行中 ===
...
✅ Phase 3 完成

=== AutoResearch 品質檢查 ===
Enabled: true (project-config.yaml)
Phase: 3
Active dimensions: D1, D5, D6, D7

🔍 評估中...
   D1 Linting: 90% → 100% ✅
   D5 Complexity: 40% → 100% ✅
   D6 Architecture: 70% → 100% ✅
   D7 Readability: 100% ✅

📊 Phase 3 分數: 75 → 100分 ✅

AutoResearch 完成（2 輪）
```

---

## Quick Reference

| 設定 | 預設值 | 說明 |
|------|--------|------|
| `auto_research.enabled` | `true` | 全域開關 |
| `trigger_after_phase` | `[3, 5]` | 自動觸發的 Phase |
| `iterations.max` | `3` | 最大迭代次數 |
| `iterations.stop_on_full` | `true` | 全 100% 時停止 |
| `scoring.target` | `85` | 目標分數 |

---

*最後更新: 2026-04-11*
