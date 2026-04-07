---
name: marketplace
description: Marketplace for methodology-v2. Use when: (1) Sharing and discovering agent templates, (2) Building a plugin ecosystem, (3) Community contributions. Provides template marketplace with ratings and reviews.
---

# Marketplace

Template marketplace for methodology-v2.

## Quick Start

```python
from marketplace import Marketplace, Template

# List templates
templates = Marketplace.list_templates(category="customer_service")

# Install template
Marketplace.install("customer-service-bot")

# Publish your template
template = Template(
    name="my-template",
    description="A helpful bot",
    category="customer_service"
)
Marketplace.publish(template)
```

## Features

### 1. Template Discovery

```python
# Search
results = Marketplace.search("chatbot")

# Filter
results = Marketplace.filter(
    category="coding",
    min_rating=4.0,
    free_only=True
)
```

### 2. Ratings & Reviews

```python
# Rate
Marketplace.rate("template-id", rating=5, review="Great!")

# Get reviews
reviews = Marketplace.get_reviews("template-id")
```

### 3. Publishing

```python
template = Template(
    name="my-awesome-agent",
    description="Agent for X task",
    category="general",
    price=0,  # Free
    code_url="https://github.com/..."
)
Marketplace.publish(template)
```

## CLI Usage

```bash
# Search templates
python marketplace.py search chatbot

# Install template
python marketplace.py install customer-service-bot

# Publish
python marketplace.py publish --file template.yaml
```

## Categories

| Category | Description |
|----------|-------------|
| customer_service |客服机器人 |
| coding | 编程助手 |
| research | 研究工具 |
| data_analysis | 数据分析 |
| automation | 自动化 |
| custom | 自定义 |

## Revenue Share

| Seller | Platform |
|--------|-----------|
| 70% | 30% |

## Best Practices

1. **Clear documentation** - Explain what your template does
2. **Test thoroughly** - Ensure reliability
3. **Set fair price** - Free for basic, paid for premium
4. **Respond to reviews** - Build trust
