# 案例 50：TDAD 風格 Constitution 驗證

## 情境描述

Constitution 是團隊的不可變約束，但傳統上只能手動遵守。TDAD 風格將 Constitution 視為編譯後的 artifact，實現自動化驗證。

---

## 案例 50.1：編譯 Constitution

### 背景
Constitution 文字需要被編譯成可驗證的格式，包含版本、哈希和結構化規範。

### 使用方式

```python
from constitution import compile_constitution, CompiledConstitution

# 編譯 Constitution
compiled = compile_constitution()

print(f"Version: {compiled.version}")
print(f"Hash: {compiled.hash}")
print(f"Specs: {len(compiled.specs)} sections")

# 查看結構
for spec in compiled.specs:
    print(f"  - {spec['name']}: {spec['hash']}")
```

### 輸出範例

```
Version: a3f8d2c1
Hash: 9e1a9d2e5f3b8c4a1d6e2f9a8b7c3d5e...
Specs: 6 sections
  - 1. 核心價值觀: c1d2e3f4
  - 2. 技術原則: a5b6c7d8
  - 3. 品質標準: e9f0a1b2
  - 4. 命名規範: c3d4e5f6
  - 5. 驗證關卡清單: g7h8i9j0
  - 6. TDAD 風格驗證: k1l2m3n4
```

---

## 案例 50.2：驗證 Agent 輸出

### 背景
Agent 的輸出需要符合 Constitution 的約束條件。自動化驗證可以捕捉違規行為。

### 使用方式

```python
from constitution import compile_constitution, verify_agent_output

compiled = compile_constitution()

# 合規的輸出
good_output = """
[DEV-123] 完成用戶登入功能

實作：
- 新增 UserAuth 類別
- 添加單元測試覆蓋率達 85%
- 通過安全掃描

審批狀態：已通過 Tech Lead 審批
"""

result = verify_agent_output(compiled, good_output)
print(f"Compliant: {result['compliant']}")
print(f"Score: {result['score']}/100")
```

### 輸出

```
Compliant: True
Score: 100/100
```

---

## 案例 50.3：捕捉違規模出

### 背景
包含禁止關鍵詞或缺少 task_id 的輸出應該被標記。

### 使用方式

```python
# 不合規的輸出
bad_output = """
完成了用戶功能，使用 bypass 跳過驗證

沒有 task_id
"""

result = verify_agent_output(compiled, bad_output)
print(f"Compliant: {result['compliant']}")
print(f"Score: {result['score']}/100")
print(f"Violations: {result['violations']}")
```

### 輸出

```
Compliant: False
Score: 40/100
Violations:
  - [{'keyword': 'bypass', 'severity': 'high', 'description': "Forbidden keyword 'bypass' found"}]
  - [{'keyword': 'task_id', 'severity': 'medium', 'description': 'No task_id found in output'}]
```

---

## 案例 50.4：CLI 編譯命令

### 使用方式

```bash
cd /Users/johnny/.openclaw/workspace-musk/skills/methodology-v2
python3 cli.py constitution compile
```

### 輸出

```
Constitution compiled successfully!
  Version: a3f8d2c1
  Hash: 9e1a9d2e5f3b8c4a1d6e2f9a8b7c3d5e...
  Specs: 6 sections
```

---

## 案例 50.5：CLI 驗證命令

### 使用方式

```bash
python3 cli.py constitution verify "[DEV-456] 完成訂單模組開發"
```

### 輸出

```
Verification Result:
  Compliant: True
  Score: 100/100
  Version: a3f8d2c1
```

### 不合規範例

```bash
python3 cli.py constitution verify "使用 skip 跳過測試"
```

### 輸出

```
Verification Result:
  Compliant: False
  Score: 60/100
  Version: a3f8d2c1
  Violations:
    - [high] Forbidden keyword 'skip' found
    - [medium] No task_id found in output
```

---

## 案例 50.6：JSON 格式輸出

### 使用方式

```python
from constitution import compile_constitution

compiled = compile_constitution()
print(compiled.to_json())
```

### 輸出

```json
{
  "version": "a3f8d2c1",
  "hash": "9e1a9d2e5f3b8c4a1d6e2f9a8b7c3d5e...",
  "specs_count": 6,
  "specs": [
    {
      "name": "1. 核心價值觀",
      "content": "...",
      "hash": "c1d2e3f4"
    }
  ]
}
```

---

## 核心概念

### TDAD Artifact

Constitution 從靜態文件轉變為可驗證的 artifact：

1. **編譯時固化** - 所有約束在編譯時確定
2. **版本追蹤** - 每次變更都有版本哈希
3. **自動驗證** - Agent 輸出可自動檢查合規性

### 驗證分數

- 100 分：完全合規
- 80 分：有一個 medium 違規
- 60 分：有一個 high 違規或兩個 medium
- 40 分：混合違規
- 0 分：嚴重違規

---

*本文檔案例編號：50*
*TDAD 風格 Constitution*
