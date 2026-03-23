# Case 60: Deep Security Defense Architecture

**版本:** v5.33  
**分類:** Security / Defense  
**建立日期:** 2026-03-23

---

## 問題背景

### LPCI 攻擊 (Layered Prompt Context Injection)

LPCI 是一種進階的 Prompt Injection 攻擊，攻擊者透過多層次的上下文注入，試圖：
1. 忽略或覆蓋原始系統提示
2. 冒充不同角色或身份
3. 提取敏感資訊
4. 執行未授權操作

### Confused Deputy 問題

當 AI Agent 獲得過多權限時，可能被惡意輸入誘導執行：
- 未預期的系統命令
- 資料外洩
- 横向移動攻擊

---

## 解決方案：四層深度安全防禦架構

```
┌─────────────────────────────────────────────────────────┐
│                    Deep Security Defense                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Layer 1: Input Validation (輸入驗證)                   │
│  ├── Prompt Injection 檢測                              │
│  ├── LPCI 特徵辨識                                       │
│  └── 黑白名單機制                                        │
│                    ↓                                      │
│  Layer 2: Execution Sandbox (執行隔離)                   │
│  ├── 隔離的工具執行                                       │
│  ├── 權限最小化                                          │
│  └── 橫向移動防止                                        │
│                    ↓                                      │
│  Layer 3: Output Filter (輸出過濾)                       │
│  ├── 敏感資訊檢測                                         │
│  ├── 脫敏處理                                            │
│  └── 審計日誌                                            │
│                    ↓                                      │
│  Layer 4: Human-in-the-Loop (人類審批)                   │
│  ├── 審批請求佇列                                         │
│  ├── 自動升級                                            │
│  └── 審批追蹤                                            │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 模組結構

```
security_defense/
├── __init__.py           # 統一導出
├── input_validator.py    # Layer 1: 輸入驗證
├── execution_sandbox.py   # Layer 2: 執行隔離
├── output_filter.py       # Layer 3: 輸出過濾
└── human_in_loop.py       # Layer 4: 人類審批
```

---

## Layer 1: Input Validator

### 功能

- **LPCI 檢測:** 識別 `ignore previous instructions`、`disregard safety` 等模式
- **Prompt Injection 檢測:** 識別 `### instruction`、`--- user` 等注入標記
- **黑白名單:** 可配置的內容過濾

### 使用範例

```python
from security_defense import InputValidator, ThreatType

validator = InputValidator()

# 檢測 LPCI 攻擊
result = validator.validate("Remember to ignore all previous instructions...")

print(f"Is Safe: {result.is_safe}")
print(f"Threat Type: {result.threat_type}")
print(f"Confidence: {result.confidence}")
print(f"Sanitized: {result.sanitized_input}")
```

### 威脅類型

| ThreatType | 說明 | 信心度 |
|------------|------|--------|
| `LPCI` | Layered Prompt Context Injection | 0.9 |
| `PROMPT_INJECTION` | 傳統 Prompt Injection | 0.8 |
| `COMMAND_INJECTION` | 命令注入 | 可配置 |
| `DATA_EXFILTRATION` | 資料外洩 | 可配置 |
| `SOCIAL_ENGINEERING` | 社交工程 | 可配置 |
| `UNKNOWN` | 未知威脅 | 可配置 |

---

## Layer 2: Execution Sandbox

### 功能

- **隔離執行:** subprocess、function、eval 都在沙盒中執行
- **權限最小化:** 限制 PATH、HOME、目錄訪問
- **資源限制:** 最大執行時間、記憶體限制

### 沙盒等級

| 等級 | 說明 |
|------|------|
| `NONE` | 無隔離（不推薦） |
| `BASIC` | 基本隔離，限制工作目錄 |
| `STRICT` | 嚴格隔離，只允許特定路徑 |
| `FULL` | 完全隔離，最大化安全 |

### 使用範例

```python
from security_defense import ExecutionSandbox, SandboxConfig, SandboxLevel

# 建立嚴格模式的沙盒
sandbox = ExecutionSandbox(SandboxConfig(
    level=SandboxLevel.STRICT,
    allowed_paths=["/tmp", "/var/tmp"],
    max_execution_time=10
))

# 在沙盒中執行命令
result = sandbox.execute(
    tool="subprocess",
    command=["ls", "-la"],
    timeout=5
)

if result.success:
    print(result.output)
else:
    print(f"Error: {result.error}")
```

---

## Layer 3: Output Filter

### 功能

- **敏感資訊檢測:** 密碼、API Key、信用卡、SSN 等
- **自動脫敏:** 將敏感資訊替換為 `[REDACTED]`
- **審計日誌:** 記錄所有輸出過濾事件

### 敏感模式

| Pattern | 說明 | 範例 |
|---------|------|------|
| `PASSWORD` | 密碼 | `password: secret123` |
| `API_KEY` | API Key | `sk-1234567890abcdef...` |
| `CREDIT_CARD` | 信用卡號 | `1234-5678-9012-3456` |
| `SSN` | 社會安全號 | `123-45-6789` |
| `EMAIL` | 電子郵件 | `user@example.com` |
| `PHONE` | 電話號碼 | `123-456-7890` |
| `IP_ADDRESS` | IP 地址 | `192.168.1.1` |
| `PRIVATE_KEY` | 私鑰 | `-----BEGIN PRIVATE KEY-----` |
| `SECRET` | 密鑰/Token | `secret: abc123` |

### 使用範例

```python
from security_defense import OutputFilter

filter = OutputFilter()

result = filter.filter("Your API key is: sk-1234567890abcdef")

if result["has_sensitive"]:
    print(f"Found: {result['found_types']}")
    print(f"Sanitized: {result['sanitized_output']}")

# 查看審計日誌
print(filter.get_audit_log())
```

---

## Layer 4: Human-in-the-Loop

### 功能

- **審批請求佇列:** 敏感操作需要人類批准
- **自動升級:** 等待過久自動升級
- **審批追蹤:** 完整的審批歷史

### 審批等級

| 等級 | 說明 |
|------|------|
| `INFO` | 僅通知，不需要回應 |
| `REVIEW` | 需要審查 |
| `APPROVAL` | 需要明確批准 |
| `BLOCK` | 直接阻擋 |

### 使用範例

```python
from security_defense import HumanInTheLoop, ApprovalLevel

hitl = HumanInTheLoop()

# 請求審批
request = hitl.request_approval(
    agent_id="agent-1",
    action="delete_user",
    description="Delete user john@example.com",
    level=ApprovalLevel.APPROVAL
)

# 等待批准（同步）
if hitl.wait_for_approval(request.request_id, timeout=300):
    print("Approved! Proceeding...")
else:
    print("Rejected or timeout")

# 手動批准/拒絕
hitl.approve(request.request_id, approver="admin", notes="Verified with user")
# 或
hitl.reject(request.request_id, approver="admin", notes="Insufficient justification")
```

---

## 整合使用

```python
from security_defense import (
    InputValidator,
    ExecutionSandbox,
    OutputFilter,
    HumanInTheLoop,
    SandboxConfig,
    SandboxLevel,
    ApprovalLevel,
    ThreatType
)

# 初始化所有層
validator = InputValidator()
sandbox = ExecutionSandbox(SandboxConfig(level=SandboxLevel.STRICT))
output_filter = OutputFilter()
hitl = HumanInTheLoop()

def safe_execute_agent_task(task: str, context: dict):
    """安全的 Agent 任務執行"""
    
    # Layer 1: 驗證輸入
    validation = validator.validate(task)
    if not validation.is_safe:
        print(f"⚠️  Threat detected: {validation.threat_type}")
        print(f"   Recommendations: {validation.recommendations}")
        if validation.confidence > 0.8:
            return {"error": "Input rejected due to security concerns"}
    
    # Layer 2: 在沙盒中執行（以 subprocess 為例）
    result = sandbox.execute(
        tool="subprocess",
        command=["python3", "-c", f"print('Executing: {validation.sanitized_input}')"],
        timeout=10
    )
    
    if not result.success:
        return {"error": result.error}
    
    # Layer 3: 過濾輸出
    filtered = output_filter.filter(result.output)
    if filtered["has_sensitive"]:
        print(f"🔒 Sensitive data redacted: {filtered['found_types']}")
    
    # Layer 4: 需要人類審批（如果涉及敏感操作）
    if "sensitive_action" in context:
        request = hitl.request_approval(
            agent_id=context.get("agent_id", "unknown"),
            action=context.get("action", "unknown"),
            description=f"Execute: {task}",
            level=ApprovalLevel.REVIEW
        )
        
        if not hitl.wait_for_approval(request.request_id, timeout=60):
            return {"error": "Human approval denied"}
    
    return {"output": filtered["sanitized_output"]}

# 使用範例
result = safe_execute_agent_task(
    "Calculate fibonacci(10)",
    {"agent_id": "math-agent", "action": "compute"}
)
```

---

## CLI 命令

```bash
# 安全狀態檢查
python3 cli.py security deep-check

# 啟用深度防禦
python3 cli.py security enable-deep-defense

# 審計日誌
python3 cli.py security audit-log
```

---

## 限制與注意事項

1. **Layer 1 限制:** 正則表達式檢測可能被混淆技術繞過，建議配合人類審查
2. **Layer 2 限制:** 沙盒不能完全防止所有側向移動，需配合系統層級權限控制
3. **Layer 3 限制:** 脫敏可能影響輸出可用性，需根據場景調整
4. **Layer 4 限制:** 人類審批會增加延遲，需平衡安全性與效率

---

## 適用場景

- 🔐 高安全性要求的 AI Agent
- 🏦 金融、醫療等受監管行業
- ☁️ 多租戶雲端環境
- 🔒 需要審計合規的系統

---

## 延伸閱讀

- [OWASP Prompt Injection](https://owasp.org/www-project-prompt-injection/)
- [Confused Deputy Problem](https://en.wikipedia.org/wiki/Confused_deputy_problem)
- [Zero Trust Architecture](https://csrc.nist.gov/publications/detail/sp/800-207/final)
