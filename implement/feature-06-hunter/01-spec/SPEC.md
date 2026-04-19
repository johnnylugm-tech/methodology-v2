# Feature #6: MAS-Hunt Hunter Agent — Specification

**版本**: 1.0  
**日期**: 2026-04-19  
**Feature**: Layer 2.5 — MAS-Hunt Hunter Agent  
**Branch**: `v3/hunter-agent`  
**依賴**: Layer 2 (Multi-Agent Debate), Layer 1.7 (Prompt Shields)

---

## 1. Overview

### 1.1 Purpose

**MAS-Hunt Hunter Agent** 是 Layer 2.5 的核心元件，獨立監控所有 Agent 通訊流，偵測四類威脅：
- 指令篡改 (Instruction Tampering)
- 對話偽造 (Dialogue Fabrication)
- 記憶毒化 (Memory Poisoning)
- 工具濫用 (Tool Abuse)

### 1.2 Scope

| 項目 | 說明 |
|------|------|
| 監控範圍 | All Agent-to-Agent Messages |
| 部署位置 | Middle layer between Agent Communication Bus |
| 觸發動作 | Alert / HITL / Halt |
| Runtime Dependencies | None (standalone, no external AI calls) |

### 1.3 Architecture Position

```
┌──────────────────────────────────────────────────────────────┐
│ Layer 6: Compliance                                         │
├──────────────────────────────────────────────────────────────┤
│ Layer 5: Observability                                      │
├──────────────────────────────────────────────────────────────┤
│ Layer 4: Tiered Governance                                  │
├──────────────────────────────────────────────────────────────┤
│ Layer 3: Hallucination Detection                            │
├──────────────────────────────────────────────────────────────┤
│ Layer 2.5: Hunter Agent ◀───────────────────────────────────────│
│  [Integrity] [Anomaly] [Rule Compliance]                    │
├──────────────────────────────────────────────────────────────┤
│ Layer 2: Multi-Agent Debate                                 │
├──────────────────────────────────────────────────────────────┤
│ Layer 1.7: Prompt Shields                                   │
├──────────────────────────────────────────────────────────────┤
│ Layer 1.5: SAIF 2.0 Identity                                │
├──────────────────────────────────────────────────────────────┤
│ Layer 1: MCP Interface                                       │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Functional Requirements (FRs)

### FR-H-1: Instruction Tampering Detection

**描述**: 偵測試圖修改 system rule 或 override governance decision 的 token pattern。

**Pattern Types**:
| Pattern | Example | Severity |
|---------|---------|----------|
| Direct override | "ignore previous instructions" | CRITICAL |
| Role hijack | "you are now DAN" | CRITICAL |
| Permission escalation | "grant admin privileges" | HIGH |
| Rule modification | "change system prompt to:" | HIGH |
| Context injection | "append to system prompt:" | MEDIUM |

**API**:
```python
def detect_instruction_tampering(message: AgentMessage) -> TamperResult
```

**Output**:
```python
@dataclass
class TamperResult:
    is_tampered: bool
    pattern_type: TamperPattern
    severity: Severity
    matched_tokens: List[str]
    evidence_hash: str
```

---

### FR-H-2: Dialogue Fabrication Detection

**描述**: 偵測 agent 聲稱「之前說過 X」但 audit log 無記錄的對話偽造。

**Detection Mechanism**:
1. Extract claim from agent message
2. Query audit log for prior context
3. If claim contradicts audit log → fabrication alert

**API**:
```python
def detect_dialogue_fabrication(
    agent_id: str,
    claim: str,
    conversation_id: str
) -> FabricateResult
```

**Output**:
```python
@dataclass
class FabricateResult:
    is_fabricated: bool
    claim: str
    audit_reference: Optional[str]  # "claim found in audit" or None
    confidence: float  # 0.0-1.0
```

---

### FR-H-3: Memory Poisoning Detection

**描述**: 偵測 agent memory 新增未經 HITL 授權的 fact。

**Detection Mechanism**:
1. Monitor memory writes (agent_memory add/update)
2. Verify authorization chain for each write
3. Unauthorized write → poisoning alert

**API**:
```python
def detect_memory_poisoning(
    agent_id: str,
    fact: MemoryFact,
    auth_chain: AuthorizationChain
) -> PoisonResult
```

**Output**:
```python
@dataclass
class PoisonResult:
    is_poisoned: bool
    fact: MemoryFact
    auth_status: AuthStatus  # AUTHORIZED / UNAUTHORIZED / PENDING
    source: str  # which agent wrote this
    timestamp: datetime
```

---

### FR-H-4: Tool Abuse Detection

**描述**: 偵測 agent 嘗試使用超出 Agents.md 白名單的工具。

**Detection Mechanism**:
1. Parse tool call from agent message
2. Load Agents.md whitelist for agent role
3. If tool not in whitelist → abuse alert

**API**:
```python
def detect_tool_abuse(
    agent_id: str,
    tool_call: ToolCall,
    agents_md: AgentsManifest
) -> AbuseResult
```

**Output**:
```python
@dataclass
class AbuseResult:
    is_abused: bool
    tool_name: str
    whitelisted_tools: List[str]
    severity: Severity
    requested_permissions: List[str]
```

---

### FR-H-5: Runtime Integrity Validation

**描述**: 每次 agent 讀取 memory/context/knowledge 時，驗證 source 雜湊。

**Validation Steps**:
1. Hash verification on read
2. Pattern anomaly detection (last N accesses)
3. Trigger HITL if anomaly detected

**API**:
```python
def validate_runtime_integrity(
    agent_id: str,
    source: str,  # memory/context/knowledge path
    expected_hash: str
) -> IntegrityResult
```

**Output**:
```python
@dataclass
class IntegrityResult:
    is_valid: bool
    source: str
    actual_hash: str
    expected_hash: str
    anomaly_score: float  # 0.0-1.0
    requires_hitl: bool
```

---

## 3. Non-Functional Requirements

### 3.1 Performance

| Metric | Target |
|--------|--------|
| Latency per message check | < 50ms |
| Max throughput | 1000 msg/sec |
| Memory footprint | < 100MB |
| Startup time | < 2s |

### 3.2 Security

| Requirement | Implementation |
|-------------|----------------|
| Immutable audit log | Hash chain (SHA-256) |
| No false positive rate | < 5% (for production) |
| False negative rate | < 1% |

### 3.3 Availability

| Requirement | Implementation |
|-------------|----------------|
| Graceful degradation | Hunter fails open (log + continue) |
| Failover | Multiple Hunter instances (stateless) |
| Persistence | State in file (no external DB) |

---

## 4. Module Architecture

```
hunter/
├── hunter_agent.py           # Main facade
├── enums.py                  # Detection types, severities
├── models.py                 # All dataclasses
├── exceptions.py             # Custom exceptions
├── integrity_validator.py    # FR-H-1, FR-H-5
├── anomaly_detector.py       # FR-H-2, FR-H-3 pattern detection
├── rule_compliance.py        # FR-H-4 tool whitelist check
├── runtime_monitor.py        # FR-H-5 runtime validation
├── audit_logger.py           # Reuse from governance/
└── __init__.py               # Package exports
```

---

## 5. Data Models

### 5.1 Enums

```python
class TamperPattern(Enum):
    DIRECT_OVERRIDE = "direct_override"
    ROLE_HIJACK = "role_hijack"
    PERMISSION_ESCALATION = "permission_escalation"
    RULE_MODIFICATION = "rule_modification"
    CONTEXT_INJECTION = "context_injection"

class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class AuthStatus(Enum):
    AUTHORIZED = "authorized"
    UNAUTHORIZED = "unauthorized"
    PENDING = "pending"
```

### 5.2 Core Dataclasses

```python
@dataclass
class AgentMessage:
    agent_id: str
    conversation_id: str
    content: str
    timestamp: datetime
    message_type: MessageType

@dataclass
class TamperResult:
    is_tampered: bool
    pattern_type: TamperPattern
    severity: Severity
    matched_tokens: List[str]
    evidence_hash: str

@dataclass
class FabricateResult:
    is_fabricated: bool
    claim: str
    audit_reference: Optional[str]
    confidence: float

@dataclass
class PoisonResult:
    is_poisoned: bool
    fact: MemoryFact
    auth_status: AuthStatus
    source: str
    timestamp: datetime

@dataclass
class AbuseResult:
    is_abused: bool
    tool_name: str
    whitelisted_tools: List[str]
    severity: Severity
    requested_permissions: List[str]

@dataclass
class IntegrityResult:
    is_valid: bool
    source: str
    actual_hash: str
    expected_hash: str
    anomaly_score: float
    requires_hitl: bool

@dataclass
class HunterAlert:
    alert_id: str
    detection_type: DetectionType
    severity: Severity
    agent_id: str
    evidence: Dict[str, Any]
    timestamp: datetime
    action_taken: ActionType  # ALERT / HITL / HALT
```

---

## 6. Hunter Agent API

### 6.1 Main Facade

```python
class HunterAgent:
    """Layer 2.5 Hunter Agent - Monitors all Agent communications"""
    
    def inspect_message(self, message: AgentMessage) -> List[HunterAlert]:
        """Main entry point - inspects all agent-to-agent messages"""
        
    def validate_integrity(self, agent_id: str, source: str) -> IntegrityResult:
        """Runtime integrity validation on memory/context read"""
        
    def check_tool_usage(self, agent_id: str, tool_call: ToolCall) -> AbuseResult:
        """Check if tool usage is within whitelist"""
        
    def get_alert_history(
        self,
        agent_id: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[HunterAlert]:
        """Query alert history"""
```

### 6.2 Sub-components

```python
class IntegrityValidator:
    """FR-H-1: Instruction tampering + FR-H-5 integrity"""
    def detect_tampering(self, content: str) -> TamperResult: ...
    def verify_hash(self, source: str, expected: str) -> IntegrityResult: ...

class AnomalyDetector:
    """FR-H-2: Dialogue fabrication + FR-H-3 memory poisoning"""
    def detect_fabrication(self, agent_id: str, claim: str) -> FabricateResult: ...
    def detect_poisoning(self, fact: MemoryFact) -> PoisonResult: ...

class RuleCompliance:
    """FR-H-4: Tool abuse detection"""
    def check_whitelist(self, agent_id: str, tool_name: str) -> bool: ...
    def get_allowed_tools(self, agent_id: str) -> List[str]: ...

class RuntimeMonitor:
    """FR-H-5: Runtime integrity validation"""
    def validate_read(self, agent_id: str, source: str) -> IntegrityResult: ...
    def detect_anomaly(self, agent_id: str, access_pattern: List[str]) -> float: ...
```

---

## 7. Detection Patterns

### 7.1 Instruction Tampering Patterns

```python
TAMPER_PATTERNS = {
    "direct_override": [
        r"ignore\s+(previous|all)\s+(instructions?|directives?)",
        r"disregard\s+(your\s+)?(instructions?|system\s+prompt)",
        r"forget\s+(everything|your instructions)",
    ],
    "role_hijack": [
        r"you\s+are\s+now\s+(a\s+)?DAN",
        r"pretend\s+you\s+are",
        r"switch\s+to\s+(developer|admin|root)",
    ],
    "permission_escalation": [
        r"grant\s+(me\s+)?(admin|root|sudo)",
        r"elevate\s+(my\s+)?privileges",
        r"enable\s+(developer\s+)?mode",
    ],
    "rule_modification": [
        r"change\s+(your\s+)?system\s+prompt\s+to",
        r"modify\s+(your\s+)?(instructions?|rules?)",
        r"update\s+system\s+prompt",
    ],
    "context_injection": [
        r"append\s+to\s+system\s+prompt",
        r"add\s+to\s+(your\s+)?instructions",
        r"include\s+this\s+in\s+context",
    ],
}
```

### 7.2 Fabricated Claim Detection

```python
# Claims that contradict audit log = fabrication
FABRICATION_KEYWORDS = [
    "as I said earlier",
    "as we discussed",
    "you told me to",
    "we agreed on",
    "per your request",
    "as you requested",
]
```

---

## 8. Workflows

### 8.1 Message Inspection Workflow

```
AgentMessage arrives
        │
        ▼
┌───────────────────┐
│  HunterAgent      │
│  .inspect_message│
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Parallel checks:                                              │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐          │
│ │IntegrityVali│ │AnomalyDetect │ │RuleComplianc│          │
│ │.detect_tamp │ │.detect_fabr  │ │.check_whitel│          │
│ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘          │
│        │                │                │                    │
│        ▼                ▼                ▼                    │
│   TamperResult    FabricateResult   AbuseResult              │
└─────────────────────────────────────────────────────────────┘
         │                │                │
         └────────────────┼────────────────┘
                          ▼
               List[HunterAlert]
                          │
                          ▼
               ┌──────────────────┐
               │ Alert Processor │
               │  (ALERT/HITL/   │
               │   HALT)         │
               └──────────────────┘
```

### 8.2 Runtime Integrity Workflow

```
Agent reads memory/context/knowledge
        │
        ▼
┌───────────────────┐
│  RuntimeMonitor   │
│  .validate_read() │
└────────┬─────────┘
         │
         ▼
    ┌────┴────┐
    │ Hash OK?│
    └────┬────┘
    YES  │  NO
    │    │
    ▼    ▼
  PASS  ┌──────────────────────┐
        │ Anomaly Detection    │
        │ (access pattern)     │
        └──────────┬───────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
    anomaly < 0.3         anomaly >= 0.3
         │                   │
         ▼                   ▼
       PASS              HITL Alert
```

---

## 9. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Tampering detection rate | ≥ 95% | Red team test |
| Fabrication detection rate | ≥ 90% | Synthetic test cases |
| Poisoning detection rate | ≥ 90% | Injected fact tests |
| Tool abuse detection rate | ≥ 95% | Whitelist violation tests |
| False positive rate | < 5% | Production log analysis |
| Latency P99 | < 50ms | Performance benchmark |
| Alert accuracy | > 95% | Manual review sample |

---

## 10. Integration Points

### 10.1 With Agent Communication Bus

```python
# Hunter Agent subscribes to all agent messages
message_bus.subscribe("agent.message", hunter.inspect_message)
```

### 10.2 With Audit Logger

```python
# Reuse governance/audit_logger.py for immutable logging
from governance.audit_logger import AuditLogger

audit_logger = AuditLogger()
alert_hash = audit_logger.log(
    event_type="hunter.alert",
    agent_id=alert.agent_id,
    data=alert.to_dict()
)
```

### 10.3 With Tiered Governance (HITL)

```python
# When severity >= HIGH, escalate to governance
if alert.severity in (Severity.CRITICAL, Severity.HIGH):
    governance_trigger.escalate(alert)
```

### 10.4 With Agents.md

```python
# Load agent-specific whitelists from MCP agents/
import yaml

def load_agents_whitelist(role: str) -> Dict[str, List[str]]:
    path = f"mcp/agents/{role}/Agents.md"
    with open(path) as f:
        return parse_agents_md(f.read())
```

---

## 11. Test Coverage Requirements

| Module | Coverage Target |
|--------|----------------|
| hunter_agent.py | ≥ 90% |
| integrity_validator.py | ≥ 95% |
| anomaly_detector.py | ≥ 90% |
| rule_compliance.py | ≥ 95% |
| runtime_monitor.py | ≥ 85% |
| enums.py | 100% |
| models.py | ≥ 90% |
| exceptions.py | 100% |
| **Overall** | **≥ 85%** |

---

## 12. Deliverables Checklist

| Deliverable | File | Status |
|-------------|------|--------|
| SPEC.md | `./SPEC.md` | ✅ |
| ARCHITECTURE.md | `./ARCHITECTURE.md` | ⏳ |
| Implementation | `hunter/*.py` | ⏳ |
| Unit Tests | `test/hunter/*.py` | ⏳ |
| TDD Verification | `pytest --cov` | ⏳ |
| DELIVERY_REPORT.md | `./DELIVERY_REPORT.md` | ⏳ |
| RISK_REGISTER.md | `./RISK_REGISTER.md` | ⏳ |
| DEPLOYMENT.md | `./DEPLOYMENT.md` | ⏳ |

---

*Document version: 1.0*  
*Generated: 2026-04-19 01:04 GMT+8*  
*Status: Phase 1 Complete*
