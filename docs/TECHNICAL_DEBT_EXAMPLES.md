# Technical Debt 常見範例

## 1. HIGH 嚴重性債務

### 使用 eval()

```python
# ❌ 技術債務
data = eval(user_input)

# ✅ 修復
import ast
data = ast.literal_eval(user_input)
```

### 硬編碼密碼

```python
# ❌ 技術債務
API_KEY = "sk-1234567890abcdef"

# ✅ 修復
API_KEY = os.environ.get("API_KEY")
```

## 2. MEDIUM 嚴重性債務

### 重複代碼

```python
# ❌ 技術債務
def validate_email(email):
    if "@" in email:
        return True
    return False

def validate_email2(email):
    if "@" in email:
        return True
    return False

# ✅ 修復
def validate_email(email):
    return "@" in email
```

## 3. LOW 嚴重性債務

### 缺少文檔

```python
# ❌ 技術債務
def process(x):
    return x * 2

# ✅ 修復
def process(x):
    """Process input by doubling.
    
    Args:
        x: Input value
    Returns:
        Doubled value
    """
    return x * 2
```
