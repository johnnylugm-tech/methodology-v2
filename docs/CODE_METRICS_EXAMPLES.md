# Code Metrics 常見範例

## 1. 簡單函數 (Complexity = 1)

```python
def get_user_name(user_id):
    return users[user_id]["name"]  # ✅ 簡單
```

## 2. 中等複雜度函數 (Complexity = 5)

```python
def process_order(order_id):
    order = get_order(order_id)  # 1
    if order.status == "pending":  # +1
        if order.amount > 1000:  # +1
            approve_manager(order)  # +1
        else:
            approve_auto(order)  # +1
    return order
```

## 3. 高複雜度函數 (Complexity = 15) ⚠️

```python
# 需要重構
def complex_validation(data):
    if data.get("type") == "user":  # 1
        if data.get("age", 0) < 18:  # +1
            if data.get("guardian"):  # +1
                validate_guardian(data)  # +1
            else:
                return False  # +1
    elif data.get("type") == "org":  # +1
        if not data.get("registration"):  # +1
            return False  # +1
    # ... 更多條件
```

---

## Coupling 範例

| 模組 | Afferent | Efferent | Instability |
|------|----------|----------|--------------|
| core.py | 5 | 2 | 0.29 |
| utils.py | 8 | 1 | 0.11 |
| api.py | 1 | 10 | 0.91 ⚠️ |

**api.py 的 Instability = 10/(10+1) = 0.91 (高不穩定)**
