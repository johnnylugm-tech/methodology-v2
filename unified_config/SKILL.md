# SKILL.md - Unified Config

## Metadata

```yaml
name: unified-config
description: 統一配置中心。集中管理所有全域設定，方便團隊使用。
```

## When to Use

- 需要集中管理所有設定
- 團隊需要統一的預設配置
- 需要快速切換不同場景（POC/團隊/企業）

## Quick Start

```python
from unified_config import UnifiedConfig

# 載入設定
config = UnifiedConfig.from_json('config.default.json')

# 檢查功能開關
if config.is_p2p_enabled():
    print("P2P 已啟用")

if config.is_hitl_enabled():
    print("HITL 已啟用")

# 便捷方法
config.is_hybrid_enabled()  # Hybrid 模式？
```

## 預設配置

| 場景 | 命令 | P2P | HITL | Hybrid |
|------|------|------|------|--------|
| **POC/小型** | `--poc` | OFF | OFF | OFF |
| **團隊** | `--team` | OFF | ON | Hybrid |
| **企業** | `--enterprise` | ON | ON | ON |

## 設定結構

```json
{
  "p2p": { ... },           // P2P 點對點設定
  "hitl": { ... },           // HITL 人類介入設定
  "hybridWorkflow": { ... },  // Hybrid 工作流設定
  "agentDefaults": { ... },   // Agent 預設值
  "system": { ... }          // 系統設定
}
```

## CLI

```bash
# 產生預設設定檔
python unified_config.py --generate

# 產生不同場景設定
python unified_config.py --poc
python unified_config.py --team
python unified_config.py --enterprise

# 載入並查看
python unified_config.py config.json
```

## 與其他模組整合

```python
# P2P
from p2p_orchestrator import P2POrchestrator
config = UnifiedConfig.from_json('config.json')
if config.is_p2p_enabled():
    orchestrator = P2POrchestrator(config.p2p)

# HITL
from hitl_controller import HITLController
config = UnifiedConfig.from_json('config.json')
if config.is_hitl_enabled():
    controller = HITLController()
    controller.hitl_settings = config.hitl

# Hybrid Workflow
from hybrid_workflow import HybridWorkflow
config = UnifiedConfig.from_json('config.json')
workflow = HybridWorkflow(
    mode=config.hybrid_workflow.default_mode,
    small_threshold=config.hybrid_workflow.small_change_threshold
)
```

## Related

- p2p_orchestrator.py
- hitl_controller.py
- hybrid_workflow.py
- config.default.json
