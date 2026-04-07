# Provider 配置指南

## 支援的 Provider

| Provider | 模型 | 特色 | 適合場景 |
|---------|------|------|---------|
| Anthropic Claude | claude-opus-4, claude-sonnet-4 | 深度推理、代碼能力強 | Phase 2/3/6 |
| OpenAI GPT | gpt-4o, o3-mini, gpt-4o-mini | 多模態、便宜 | Phase 4/7/8 |
| Zhipu GLM | glm-4, glm-4-flash | 中文支援、極便宜 | 簡單任務、中文場景 |

## Phase → Provider 映射

| Phase | Provider | Model | 理由 |
|-------|----------|-------|------|
| 1 | Anthropic | claude-sonnet-4 | 長上下文、便宜 |
| 2 | Anthropic | claude-opus-4 | 深度推理 |
| 3 | Anthropic | claude-sonnet-4 | 代碼能力強、性價比高 |
| 4 | OpenAI | gpt-4o | 多模態平衡 |
| 5 | Anthropic | claude-sonnet-4 | 性價比高 |
| 6 | Anthropic | claude-opus-4 | 深度分析 |
| 7 | OpenAI | o3-mini | 推理+便宜 |
| 8 | OpenAI | gpt-4o-mini | 簡單任務 |

## 環境變數

```bash
# Anthropic
export ANTHROPIC_API_KEY=sk-...

# OpenAI
export OPENAI_API_KEY=sk-...

# Zhipu GLM
export GLM_API_KEY=...
```

## CLI 用法

```bash
# 查詢 Phase 3 推薦模型
python cli.py model-recommend --phase 3

# 顯示詳細資訊 (JSON)
python cli.py model-recommend --phase 3 --provider

# 指定 repo
python cli.py model-recommend --phase 3 --repo /path/to/repo

# 任務提示 (降級到便宜模型)
python cli.py model-recommend --phase 3 --task-hint simple

# 獨立使用 provider_abstraction.py
python provider_abstraction.py --phase 3 --provider
```
