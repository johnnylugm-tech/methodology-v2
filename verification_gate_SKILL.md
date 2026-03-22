# Verification Gates - 驗證關卡

> AI-native 工作流品質保障機制

---

## 核心理念

**條件觸發，不阻礙流程；自動檢查，不增加負擔。**

驗證關卡是輕量化的品質檢查點，分為「阻斷式」和「見證式」兩種：
- **見證式**：記錄狀態，不阻斷流程（預設）
- **阻斷式**：失敗時停止後續（可選配置）

---

## 快速開始

### 基本用法

```python
from verification_gate import VerificationGates, Gate, GateStatus

# 建立閘道管理器
gates = VerificationGates()

# 註冊關卡
gates.register_gate("task_created", Gate(
    name="任務建立",
    required_output="task_spec"  # 檢查 context 中是否存在此鍵
))
gates.gate_sequence = ["task_created"]

# 執行檢查
context = {"task_spec": {"title": "分析報告"}}
results = gates.execute_sequence(context)

# 查看狀態
print(gates.get_status())
```

### 使用驗證器

```python
def quality_validator(context: dict) -> bool:
    """自訂品質檢查邏輯"""
    result = context.get("result", {})
    score = result.get("quality_score", 0)
    return score >= 80

gates.register_gate("quality_check", Gate(
    name="品質檢查",
    validator=quality_validator
))
```

### 自動通過關卡

```python
gates.register_gate("quick_task", Gate(
    name="快速任務",
    auto_pass=True  # 永遠通過
))
```

---

## 預設關卡

| ID | 名稱 | 觸發條件 |
|----|------|----------|
| `task_created` | 任務建立 | `task_spec` in context |
| `agent_assigned` | 分派代理 | `assignment` in context |
| `output_generated` | 產出產生 | `result` in context |
| `quality_check` | 品質檢查 | 需自訂 validator |
| `human_approved` | 人類審批 | `approval` in context |
| `completed` | 任務完成 | `final_result` in context |

---

## 預設流程

### HITL Gates（需要人類審批）

```python
from verification_gate import HITLGates

hitl = HITLGates()
# 流程：task_created → output_generated → human_approved → completed
```

### Autonomous Gates（全自動）

```python
from verification_gate import AutonomousGates

auto = AutonomousGates()
# 流程：task_created → agent_assigned → output_generated → quality_check → completed
```

---

## 與 HITLController 整合

```python
from hitl_controller import HITLController
from verification_gate import HITLGates

# 初始化
controller = HITLController()
gates = HITLGates()

# 在工作流中嵌入檢查
def process_task(task_spec):
    # Gate 1: 任務建立
    gates.check_gate("task_created", {"task_spec": task_spec})

    # 執行任務...
    result = execute_task(task_spec)

    # Gate 2: 產出產生
    gates.check_gate("output_generated", {"result": result})

    # 提交審批
    controller.submit_for_review(result)

    # 等待人類審批
    approval = controller.wait_for_approval(result.id)

    # Gate 3: 人類審批
    gates.check_gate("human_approved", {"approval": approval})

    # 完成
    gates.check_gate("completed", {"final_result": result})

    return gates.get_status()
```

---

## API 參考

### GateStatus

```python
class GateStatus(Enum):
    NOT_REACHED = "not_reached"  # 尚未觸發
    PASSED = "passed"            # 已通過
    FAILED = "failed"            # 已失敗
    BYPASSED = "bypassed"        # 已繞過
```

### Gate

```python
gate = Gate(
    name="關卡名稱",
    required_output="需要的輸出鍵",  # 可選
    validator=callable,             # 可選
    auto_pass=False                # 可選
)

gate.check(context)   # 執行檢查
gate.bypass("原因")   # 繞過關卡
gate.reset()          # 重置狀態
```

### VerificationGates

```python
gates = VerificationGates()

gates.register_gate(gate_id, gate)           # 註冊關卡
gates.register_default_gates(["task_created"])  # 註冊預設關卡
gates.execute_sequence(context)                # 執行所有關卡
gates.check_gate(gate_id, context)            # 檢查單一關卡
gates.get_status()                            # 取得狀態
gates.reset_all()                             # 重置所有關卡
```

---

## 最佳實踐

1. **不要過度使用**：每個工作流 3-5 個關卡為宜
2. **區分見證與阻斷**：大多數場景用見證式，關鍵決策點用阻斷式
3. **記錄 evidence**：方便事後審計和除錯
4. **自訂 validator**：用於業務邏輯驗證，而非只靠 required_output

---

## 與其他模組的關係

```
verification_gate
├── HITLController (整合人類審批關卡)
├── auto_quality_gate (品質檢查關卡)
└── audit_logger (審計日誌)
```
