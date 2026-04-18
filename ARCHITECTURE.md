# Feature #6: MAS-Hunt Hunter Agent — Architecture
**版本**: 1.0
**日期**: 2026-04-19
**Feature**: Layer 2.5 — MAS-Hunt Hunter Agent
**Branch**: `v3/hunter-agent`
**Status**: Phase 2 — Architecture Design

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Component Specifications](#2-component-specifications)
3. [Data Models](#3-data-models)
4. [Detection Patterns](#4-detection-patterns)
5. [API Design](#5-api-design)
6. [File Structure](#6-file-structure)
7. [Dependencies & Interfaces](#7-dependencies--interfaces)
8. [Edge Cases & Error Handling](#8-edge-cases--error-handling)

---

## 1. Architecture Overview

### 1.1 System Purpose and Scope

**MAS-Hunt Hunter Agent** 是 Layer 2.5 的核心元件，部署於 Agent Communication Bus 與各 Agent 之间，独立监控所有 Agent 通訊流，实时偵測四類安全威脅：

| Threat Type | Detection Target | FR Reference |
|-------------|------------------|--------------|
| 指令篡改 (Instruction Tampering) | 試圖修改 system rule / override governance decision 的 token pattern | FR-H-1 |
| 對話偽造 (Dialogue Fabrication) | Agent 聲稱「之前說過 X」但 audit log 無記錄 | FR-H-2 |
| 記憶毒化 (Memory Poisoning) | Agent memory 新增未經 HITL 授權的 fact | FR-H-3 |
| 工具濫用 (Tool Abuse) | Agent 嘗試使用超出 Agents.md 白名單的工具 | FR-H-4 |

**Runtime Integrity Validation** (FR-H-5) 作為跨構件機制，在每次 agent 讀取 memory/context/knowledge 時驗證 source 雜湊。

### 1.2 High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Agent Communication Bus                          │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           HUNTER AGENT                                   │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                     hunter_agent.py (Facade)                      │  │
│  │  • inspect_message()                                             │  │
│  │  • validate_integrity()                                          │  │
│  │  • check_tool_usage()                                             │  │
│  │  • get_alert_history()                                           │  │
│  └──────────────────────────┬────────────────────────────────────────┘  │
│                              │                                             │
│         ┌────────────────────┼────────────────────┐                      │
│         │                    │                    │                       │
│         ▼                    ▼                    ▼                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                │
│  │  Integrity   │    │   Anomaly    │    │    Rule     │                │
│  │  Validator   │    │   Detector   │    │  Compliance │                │
│  │              │    │              │    │             │                │
│  │ FR-H-1       │    │ FR-H-2       │    │ FR-H-4      │                │
│  │ FR-H-5       │    │ FR-H-3       │    │             │                │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                │
│         │                   │                   │                       │
│         └───────────────────┼───────────────────┘                       │
│                             │                                            │
│                             ▼                                            │
│                    ┌──────────────┐                                      │
│                    │   Runtime    │                                      │
│                    │   Monitor    │                                      │
│                    │   FR-H-5     │                                      │
│                    └──────┬───────┘                                      │
│                           │                                              │
│                           ▼                                              │
│                    ┌──────────────┐                                      │
│                    │ Audit Logger │ (governance/)                        │
│                    └──────────────┘                                      │
└───────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Tiered Governance (HITL Escalation)                 │
│  Severity.CRITICAL/HIGH → Alert + Human Review                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Data Flow: Message Inspection to Alert

```
1. AgentMessage arrives (from Agent Communication Bus)
           │
           ▼
2. hunter_agent.inspect_message(message)
           │
           ▼
3. Parallel dispatch to 3 sub-detectors:
   ┌──────────────────┬──────────────────┬──────────────────┐
   │ IntegrityValidator│  AnomalyDetector │  RuleCompliance  │
   │  .detect_tamper() │  .detect_fabr()  │ .check_whitelist │
   │  .verify_hash()   │  .detect_poison() │                  │
   └────────┬──────────┴────────┬─────────┴────────┬─────────┘
            │                    │                   │
            ▼                    ▼                   ▼
      TamperResult       FabricateResult      AbuseResult
            │                    │                   │
            └────────────────────┼───────────────────┘
                                  ▼
4. hunter_agent._aggregate_alerts(tamper, fabricate, abuse)
   • Filter non-alerts (is_* == False)
   • Convert to HunterAlert dataclass
   • Assign alert_id (UUID4)
   • Compute action_taken based on severity
                                  │
                                  ▼
5. hunter_agent._process_alert(alert)
   • ALERT (severity == LOW/MEDIUM): log + continue
   • HITL  (severity == HIGH):       pause + escalate
   • HALT  (severity == CRITICAL):   terminate agent + escalate
                                  │
                                  ▼
6. audit_logger.log(alert) → immutable hash chain
                                  │
                                  ▼
7. Return List[HunterAlert] to caller
```

### 1.4 Runtime Integrity Data Flow

```
Agent reads memory/context/knowledge
           │
           ▼
runtime_monitor.validate_read(agent_id, source, expected_hash)
           │
           ▼
   ┌───────┴───────┐
   │ Hash match?    │
   └───────┬───────┘
    YES    │    NO
    │      │      │
    ▼      │      ▼
  PASS     │   ┌─────────────────┐
           │   │ Anomaly Check   │
           │   │ access_pattern  │
           │   │ anomaly_score   │
           │   └────────┬────────┘
           │      ┌────┴────┐
           │      │ score   │
           │      │ < 0.3   │
           │      └────┬────┘
           │     YES   │   NO
           │     │      │     │
           │     ▼      │     ▼
           │   PASS      │  HITL
           │             │
           └─────────────┘
                   │
                   ▼
          IntegrityResult
```

---

## 2. Component Specifications

### 2.1 hunter_agent.py — Main Facade

#### Responsibility

- 唯一公開給外部的 API 入口
- 協調所有 sub-detectors 進行 parallel inspection
- 管理 alert lifecycle（創建、分派、歷史查詢）
- 實作 graceful degradation（Hunter 失敗時不阻斷訊息流）

#### Public API

```python
class HunterAgent:
    def __init__(self, config: HunterConfig) -> None:
        """Initialize with config; sets up sub-detectors and audit logger."""

    def inspect_message(self, message: AgentMessage) -> List[HunterAlert]:
        """
        Main entry point. Inspects an AgentMessage for all threat types.
        
        Args:
            message: AgentMessage to inspect
            
        Returns:
            List of HunterAlert (empty list if no threats detected)
            
        Raises:
            HunterAgentError: Only on catastrophic failure (logged, not raised)
        """

    def validate_integrity(
        self,
        agent_id: str,
        source: str,
        expected_hash: Optional[str] = None
    ) -> IntegrityResult:
        """
        Runtime integrity validation when agent reads memory/context/knowledge.
        
        Args:
            agent_id: ID of the agent performing the read
            source: Path or identifier of the source being read
            expected_hash: Optional pre-known hash for verification
            
        Returns:
            IntegrityResult with validation outcome
        """

    def check_tool_usage(
        self,
        agent_id: str,
        tool_call: ToolCall
    ) -> AbuseResult:
        """
        Check if a tool call is within the agent's allowed whitelist.
        
        Args:
            agent_id: ID of the agent making the tool call
            tool_call: ToolCall dataclass with tool name and parameters
            
        Returns:
            AbuseResult indicating whether tool is whitelisted
        """

    def get_alert_history(
        self,
        agent_id: Optional[str] = None,
        since: Optional[datetime] = None,
        detection_type: Optional[DetectionType] = None,
        limit: int = 100
    ) -> List[HunterAlert]:
        """
        Query historical alerts.
        
        Args:
            agent_id: Filter by agent (None = all agents)
            since: Filter by timestamp (None = all time)
            detection_type: Filter by DetectionType (None = all types)
            limit: Max number of results (default 100)
            
        Returns:
            List of matching HunterAlert sorted by timestamp desc
        """

    def get_stats(self) -> HunterStats:
        """Return aggregated statistics (counts by type, severity, etc.)."""
```

#### State

```python
# hunter_agent.py internal state
_config: HunterConfig                    # Immutable config
_integrity_validator: IntegrityValidator # FR-H-1, FR-H-5 hash
_anomaly_detector: AnomalyDetector       # FR-H-2, FR-H-3
_rule_compliance: RuleCompliance          # FR-H-4 whitelist
_runtime_monitor: RuntimeMonitor          # FR-H-5 runtime
_audit_logger: AuditLogger               # Immutable audit (governance/)
_alert_store: Dict[str, HunterAlert]     # In-memory alert cache
_alert_history_path: Path                # File-backed persistence
_config: HunterConfig
```

#### Interactions

| Interaction | Partner | Method |
|-------------|---------|--------|
| Delegates tampering detection | `IntegrityValidator` | `.detect_tamper()` |
| Delegates fabrication detection | `AnomalyDetector` | `.detect_fabrication()` |
| Delegates poisoning detection | `AnomalyDetector` | `.detect_poisoning()` |
| Delegates tool abuse check | `RuleCompliance` | `.check_whitelist()` |
| Delegates runtime validation | `RuntimeMonitor` | `.validate_read()` |
| Logs alerts | `AuditLogger` (governance/) | `.log()` |
| Escalates HIGH/CRITICAL | Tiered Governance | `.escalate()` |

---

### 2.2 integrity_validator.py — FR-H-1, FR-H-5 Implementation

#### Responsibility

- **FR-H-1**: Regex-based instruction tampering detection using `TAMPER_PATTERNS`
- **FR-H-5**: SHA-256 hash verification for source integrity
- 輸出結構化 `TamperResult` 和 `IntegrityResult`

#### Public API

```python
class IntegrityValidator:
    def __init__(self, config: Optional[HunterConfig] = None) -> None:
        """Initialize with patterns and hash algorithm."""

    def detect_tampering(self, content: str) -> TamperResult:
        """
        Scan content for instruction tampering patterns.
        
        Scans against all TAMPER_PATTERNS regexes in priority order:
        DIRECT_OVERRIDE > ROLE_HIJACK > PERMISSION_ESCALATION > 
        RULE_MODIFICATION > CONTEXT_INJECTION
        
        Args:
            content: Raw message content string
            
        Returns:
            TamperResult with is_tampered=True if any pattern matches
        """

    def verify_hash(
        self,
        source: str,
        expected_hash: str,
        algorithm: str = "sha256"
    ) -> IntegrityResult:
        """
        Verify source content hash matches expected.
        
        Args:
            source: Content string or path to content
            expected_hash: Pre-computed expected hash (hex string)
            algorithm: Hash algorithm (default sha256)
            
        Returns:
            IntegrityResult with is_valid=True if hashes match
        """

    def compute_hash(
        self,
        source: str,
        algorithm: str = "sha256"
    ) -> str:
        """
        Compute hash of source content.
        
        Args:
            source: Content string
            algorithm: Hash algorithm
            
        Returns:
            Hex-encoded hash string
        """
```

#### State

```python
_tamper_patterns: Dict[TamperPattern, List[re.Pattern]]  # Compiled regex
_hash_cache: LRUCache[str, str]                         # Hash computation cache
_max_cache_size: int = 10000
```

#### Interactions

- No sub-component dependencies
- Called by `HunterAgent.inspect_message()` and `RuntimeMonitor.validate_read()`

---

### 2.3 anomaly_detector.py — FR-H-2, FR-H-3 Implementation

#### Responsibility

- **FR-H-2**: Dialogue fabrication detection via audit log cross-reference
- **FR-H-3**: Memory poisoning detection via authorization chain verification
- 實作 fabrication claim extraction + poisoning fact validation

#### Public API

```python
class AnomalyDetector:
    def __init__(
        self,
        audit_logger: AuditLogger,
        config: Optional[HunterConfig] = None
    ) -> None:
        """Initialize with audit logger reference."""

    def detect_fabrication(
        self,
        agent_id: str,
        claim: str,
        conversation_id: str
    ) -> FabricateResult:
        """
        Detect if an agent's claim contradicts the audit log.
        
        Algorithm:
        1. Extract claim keywords from FABRICATION_KEYWORDS presence
        2. Parse temporal references ("as I said earlier", etc.)
        3. Query audit log for prior messages in conversation_id
        4. If claim subject/verb pair not found in audit → fabrication
        
        Args:
            agent_id: Agent making the claim
            claim: Raw claim string
            conversation_id: Conversation context ID
            
        Returns:
            FabricateResult with confidence score
        """

    def detect_poisoning(
        self,
        agent_id: str,
        fact: MemoryFact,
        auth_chain: AuthorizationChain
    ) -> PoisonResult:
        """
        Detect unauthorized memory poisoning.
        
        Algorithm:
        1. Verify auth_chain is complete (all links present)
        2. Verify each link's digital signature
        3. Verify HITL approval for the specific fact category
        4. If any check fails → poisoning alert
        
        Args:
            agent_id: Agent attempting to write to memory
            fact: MemoryFact being written
            auth_chain: AuthorizationChain claiming approval
            
        Returns:
            PoisonResult with auth_status
        """

    def extract_claims(self, content: str) -> List[str]:
        """
        Extract potential fabrication claims from content.
        
        Args:
            content: Message content
            
        Returns:
            List of claim strings found
        """

    def query_audit_context(
        self,
        conversation_id: str,
        time_window: timedelta = timedelta(minutes=30)
    ) -> List[AuditEntry]:
        """
        Query audit log for conversation context within time window.
        
        Args:
            conversation_id: Conversation to query
            time_window: How far back to search
            
        Returns:
            List of AuditEntry objects
        """
```

#### State

```python
_audit_logger: AuditLogger
_fabrication_keywords: List[str]          # From FABRICATION_KEYWORDS
_temporal_patterns: List[re.Pattern]    # Temporal reference regexes
_poisonscan_cache: LRUCache[str, PoisonResult]
_config: HunterConfig
```

#### Interactions

| Interaction | Partner | Method |
|-------------|---------|--------|
| Reads audit trail | `AuditLogger` (governance/) | `.query()` |
| Reports poisoning | `HunterAgent` | via `PoisonResult` |

---

### 2.4 rule_compliance.py — FR-H-4 Implementation

#### Responsibility

- **FR-H-4**: Tool abuse detection via Agents.md whitelist enforcement
- 解析 Agents.md 白名單，驗證 tool call 權限

#### Public API

```python
class RuleCompliance:
    def __init__(
        self,
        agents_md_path: Path,
        config: Optional[HunterConfig] = None
    ) -> None:
        """Initialize by loading Agents.md whitelist."""

    def check_whitelist(
        self,
        agent_id: str,
        tool_name: str,
        requested_permissions: Optional[List[str]] = None
    ) -> AbuseResult:
        """
        Check if tool_name is whitelisted for agent_id.
        
        Args:
            agent_id: Agent attempting tool call
            tool_name: Name of the tool being called
            requested_permissions: Optional extra permissions requested
            
        Returns:
            AbuseResult with is_abused=True if not whitelisted
        """

    def get_allowed_tools(self, agent_id: str) -> List[str]:
        """
        Get list of whitelisted tools for agent_id.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List of tool names
        """

    def reload_whitelist(self) -> None:
        """Reload Agents.md from disk (for hot-reload)."""
```

#### State

```python
_agents_md_path: Path
_whitelist_cache: Dict[str, List[str]]   # agent_id → [tool_names]
_manifest_cache: Dict[str, AgentsManifest]
_last_load_time: datetime
_config: HunterConfig
```

#### Interactions

- Reads Agents.md from MCP agents/ directory
- Called by `HunterAgent.check_tool_usage()`

---

### 2.5 runtime_monitor.py — FR-H-5 Runtime Validation

#### Responsibility

- **FR-H-5**: Runtime integrity validation on every memory/context/knowledge read
- 維護 access pattern sliding window，計算 anomaly score
- 觸發 HITL 當 anomaly_score >= 0.3

#### Public API

```python
class RuntimeMonitor:
    def __init__(
        self,
        integrity_validator: IntegrityValidator,
        config: Optional[HunterConfig] = None
    ) -> None:
        """Initialize with integrity validator reference."""

    def validate_read(
        self,
        agent_id: str,
        source: str,
        expected_hash: Optional[str] = None
    ) -> IntegrityResult:
        """
        Validate an agent's read operation on memory/context/knowledge.
        
        Flow:
        1. If expected_hash provided → verify_hash()
        2. Record access in sliding window
        3. detect_anomaly() on access pattern
        4. Return IntegrityResult with anomaly_score
        
        Args:
            agent_id: Agent performing the read
            source: Source identifier (memory/context/knowledge path)
            expected_hash: Optional hash to verify
            
        Returns:
            IntegrityResult with anomaly_score and requires_hitl flag
        """

    def detect_anomaly(
        self,
        agent_id: str,
        access_pattern: Optional[List[str]] = None
    ) -> float:
        """
        Detect anomalous access patterns using sliding window analysis.
        
        Anomaly indicators:
        - Burst access (many reads in short time)
        - Unusual source combinations
        - Sequential rapid reads of sensitive sources
        
        Args:
            agent_id: Agent to analyze
            access_pattern: Optional override pattern
            
        Returns:
            Anomaly score 0.0-1.0 (>= 0.3 triggers HITL)
        """

    def record_access(
        self,
        agent_id: str,
        source: str,
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Record an access event in the sliding window.
        
        Args:
            agent_id: Agent that accessed
            source: Source accessed
            timestamp: Event time (default now)
        """

    def get_access_history(
        self,
        agent_id: str,
        window: Optional[timedelta] = None
    ) -> List[AccessRecord]:
        """
        Get access history for agent within window.
        
        Args:
            agent_id: Agent to query
            window: Time window (default 5 minutes)
            
        Returns:
            List of AccessRecord sorted by timestamp desc
        """
```

#### State

```python
_integrity_validator: IntegrityValidator
_access_window: SlidingWindow  # agent_id → deque of AccessRecord
_window_duration: timedelta = timedelta(minutes=5)
_max_window_size: int = 1000   # Max events per agent
_anomaly_threshold: float = 0.3
_config: HunterConfig
```

#### Interactions

| Interaction | Partner | Method |
|-------------|---------|--------|
| Delegates hash verification | `IntegrityValidator` | `.verify_hash()` |
| Reports to | `HunterAgent` | via `IntegrityResult` |

---

### 2.6 audit_logger.py — Reuse from governance/

#### Responsibility

- Immutable audit log with SHA-256 hash chain
- Query interface for fabrication detection
- Reused from Layer 4 governance/audit_logger.py

#### Public API

```python
class AuditLogger:
    def __init__(
        self,
        log_path: Path,
        hash_chain: bool = True
    ) -> None:
        """Initialize audit logger with hash chain enabled."""

    def log(
        self,
        event_type: str,
        agent_id: str,
        data: Dict[str, Any],
        conversation_id: Optional[str] = None,
        parent_hash: Optional[str] = None
    ) -> str:
        """
        Write an immutable audit entry.
        
        Args:
            event_type: Event classification string
            agent_id: Agent responsible for the event
            data: Event payload
            conversation_id: Optional conversation context
            parent_hash: Previous entry hash (for chain)
            
        Returns:
            Hash of this entry (hex string)
        """

    def query(
        self,
        conversation_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        event_type: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """
        Query audit log entries.
        
        Args:
            conversation_id: Filter by conversation
            agent_id: Filter by agent
            event_type: Filter by event type
            since: Start time
            until: End time
            limit: Max results
            
        Returns:
            List of AuditEntry matching criteria
        """

    def verify_chain(self) -> bool:
        """Verify hash chain integrity (returns False if tampered)."""
```

#### State

```python
_log_path: Path
_hash_chain: bool
_last_hash: str
_file_handle: BufferedWriter
```

#### Note

`hunter/audit_logger.py` is a **symlink** to `../governance/audit_logger.py` to avoid code duplication and ensure single source of truth.

---

## 3. Data Models

### 3.1 Enums

```python
# enums.py

class TamperPattern(Enum):
    """FR-H-1: Instruction tampering pattern types."""
    DIRECT_OVERRIDE = "direct_override"
    ROLE_HIJACK = "role_hijack"
    PERMISSION_ESCALATION = "permission_escalation"
    RULE_MODIFICATION = "rule_modification"
    CONTEXT_INJECTION = "context_injection"


class Severity(Enum):
    """Alert severity levels."""
    CRITICAL = "critical"  # HALT immediately
    HIGH = "high"          # HITL escalation
    MEDIUM = "medium"      # ALERT + log
    LOW = "low"            # ALERT + log


class AuthStatus(Enum):
    """Authorization chain status."""
    AUTHORIZED = "authorized"
    UNAUTHORIZED = "unauthorized"
    PENDING = "pending"


class DetectionType(Enum):
    """Type of threat detected."""
    INSTRUCTION_TAMPERING = "instruction_tampering"
    DIALOGUE_FABRICATION = "dialogue_fabrication"
    MEMORY_POISONING = "memory_poisoning"
    TOOL_ABUSE = "tool_abuse"
    INTEGRITY_VIOLATION = "integrity_violation"


class ActionType(Enum):
    """Action taken in response to alert."""
    ALERT = "alert"   # Log and continue
    HITL = "hitl"     # Pause for human review
    HALT = "halt"     # Terminate agent + escalate


class MessageType(Enum):
    """Agent message types."""
    TEXT = "text"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    SYSTEM = "system"
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"
    CONTEXT_READ = "context_read"
    CONTEXT_WRITE = "context_write"
```

### 3.2 Core Dataclasses

```python
# models.py

@dataclass
class AgentMessage:
    """Represents an agent-to-agent message."""
    agent_id: str
    conversation_id: str
    content: str
    timestamp: datetime
    message_type: MessageType
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TamperResult:
    """FR-H-1: Result of instruction tampering detection."""
    is_tampered: bool
    pattern_type: TamperPattern
    severity: Severity
    matched_tokens: List[str]
    evidence_hash: str
    matched_positions: List[Tuple[int, int]] = field(default_factory=list)  # (start, end) in content


@dataclass
class FabricateResult:
    """FR-H-2: Result of dialogue fabrication detection."""
    is_fabricated: bool
    claim: str
    audit_reference: Optional[str]       # "claim found in audit" or None
    confidence: float                     # 0.0-1.0
    matched_keyword: Optional[str] = None


@dataclass
class PoisonResult:
    """FR-H-3: Result of memory poisoning detection."""
    is_poisoned: bool
    fact: MemoryFact
    auth_status: AuthStatus
    source: str                           # which agent wrote this
    timestamp: datetime
    violation_reason: Optional[str] = None


@dataclass
class AbuseResult:
    """FR-H-4: Result of tool abuse detection."""
    is_abused: bool
    tool_name: str
    whitelisted_tools: List[str]
    severity: Severity
    requested_permissions: List[str]
    abuse_type: Optional[str] = None      # "not_whitelisted" | "excessive_permissions"


@dataclass
class IntegrityResult:
    """FR-H-5: Result of runtime integrity validation."""
    is_valid: bool
    source: str
    actual_hash: str
    expected_hash: str
    anomaly_score: float                  # 0.0-1.0
    requires_hitl: bool                   # True if anomaly_score >= 0.3
    violation_type: Optional[str] = None  # "hash_mismatch" | "anomaly_detected" | None


@dataclass
class HunterAlert:
    """Unified alert dataclass produced by HunterAgent."""
    alert_id: str                         # UUID4
    detection_type: DetectionType
    severity: Severity
    agent_id: str
    evidence: Dict[str, Any]
    timestamp: datetime
    action_taken: ActionType
    conversation_id: Optional[str] = None
    related_result: Optional[Any] = None  # TamperResult|FabricateResult|PoisonResult|AbuseResult|IntegrityResult


@dataclass
class MemoryFact:
    """Represents a fact stored in agent memory."""
    fact_id: str                          # UUID4
    content: str
    category: str                          # e.g., "user_preference", "knowledge", "context"
    source_agent_id: str
    created_at: datetime
    confidence: float = 1.0
    tags: List[str] = field(default_factory=list)


@dataclass
class AuthorizationChain:
    """Authorization chain for memory operations."""
    chain_id: str                         # UUID4
    links: List[AuthLink]
    initiated_by: str
    initiated_at: datetime
    status: AuthStatus


@dataclass
class AuthLink:
    """Single link in authorization chain."""
    approver_id: str                      # Agent/user who approved
    approved_at: datetime
    scope: List[str]                       # What was approved
    signature: str                         # Digital signature (hex)


@dataclass
class ToolCall:
    """Represents a tool invocation."""
    tool_name: str
    arguments: Dict[str, Any]
    invoked_by: str                        # agent_id
    invoked_at: datetime
    conversation_id: Optional[str] = None


@dataclass
class AgentsManifest:
    """Parsed Agents.md manifest."""
    agent_id: str
    role: str
    allowed_tools: List[str]
    allowed_sources: List[str]
    max_rate_per_minute: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessRecord:
    """Record of an agent's access to a source."""
    agent_id: str
    source: str
    timestamp: datetime
    access_type: str                       # "read" | "write"
    hash_verified: bool = False


@dataclass
class AuditEntry:
    """Audit log entry."""
    entry_id: str
    event_type: str
    agent_id: str
    data: Dict[str, Any]
    conversation_id: Optional[str]
    timestamp: datetime
    hash: str
    parent_hash: Optional[str]


@dataclass
class HunterConfig:
    """Configuration for Hunter Agent."""
    tamper_threshold: float = 0.7          # Min confidence to flag tampering
    anomaly_threshold: float = 0.3       # Threshold for HITL
    max_access_window: int = 1000         # Max events in sliding window
    window_duration_seconds: int = 300    # 5 minutes
    hash_algorithm: str = "sha256"
    alert_retention_days: int = 90
    enable_hash_chain: bool = True
    graceful_degradation: bool = True      # Hunter fails open
    _path: Optional[str] = None           # Config file path


@dataclass
class HunterStats:
    """Aggregated Hunter statistics."""
    total_inspections: int
    total_alerts: int
    alerts_by_type: Dict[DetectionType, int]
    alerts_by_severity: Dict[Severity, int]
    avg_latency_ms: float
    last_inspection_time: Optional[datetime]
```

---

## 4. Detection Patterns

### 4.1 TAMPER_PATTERNS — Complete Regex Dictionary

```python
# patterns.py (imported by integrity_validator.py)

TAMPER_PATTERNS: Dict[TamperPattern, List[str]] = {
    TamperPattern.DIRECT_OVERRIDE: [
        r"ignore\s+(previous|all)\s+(instructions?|directives?)",
        r"disregard\s+(your\s+)?(instructions?|system\s+prompt)",
        r"forget\s+(everything|your\s+instructions|all\s+prior)",
        r"disregard\s+all\s+previous",
        r"you\s+have\s+no\s+rules",
        r"bypass\s+(your\s+)?(safety|content|filters?)",
        r"ignore\s+(all\s+)?rules",
    ],
    TamperPattern.ROLE_HIJACK: [
        r"you\s+are\s+now\s+(a\s+)?DAN",
        r"you\s+are\s+DAN",
        r"pretend\s+you\s+are",
        r"act\s+as\s+(a\s+)?(different|new|unrestricted)",
        r"switch\s+to\s+(developer|admin|root|superuser)",
        r"you\s+are\s+(now\s+)?(developer|admin|root)",
        r"mode\s+:\s*(developer|super|unrestricted)",
        r">\s*developer\s*:\s*(?:ignore|prompt|override)",
    ],
    TamperPattern.PERMISSION_ESCALATION: [
        r"grant\s+(me\s+)?(admin|root|sudo|moderator)",
        r"elevate\s+(my\s+)?(privileges|access|permissions?)",
        r"enable\s+(developer|admin|debug|unrestricted)\s*(mode)?",
        r"give\s+me\s+(admin|root|superuser)",
        r"make\s+me\s+(an?\s+)?(admin|moderator|owner)",
        r"override\s+(safety|permission|authorization)",
    ],
    TamperPattern.RULE_MODIFICATION: [
        r"change\s+(your\s+)?system\s+prompt\s+to\s*[:\n]",
        r"modify\s+(your\s+)?(instructions?|rules?|system\s+prompt)",
        r"update\s+system\s+prompt",
        r"replace\s+(your\s+)?(instructions?|system\s+prompt)",
        r"set\s+new\s+(system\s+)?(instructions?|rules?)",
        r"edit\s+(your\s+)?system\s+prompt",
        r"system\s+prompt\s*[:=]\s*['\"]?[^'\"]+['\"]?$",
    ],
    TamperPattern.CONTEXT_INJECTION: [
        r"append\s+to\s+system\s+prompt",
        r"add\s+to\s+(your\s+)?(instructions|system\s+prompt)",
        r"include\s+this\s+in\s+(your\s+)?context",
        r"inject\s+into\s+system\s+prompt",
        r"before\s+(your\s+)?(first|initial)\s+(response|output)",
        r"consider\s+this\s+(as\s+)?(part\s+of\s+)?(your\s+)?(system|base)",
    ],
}
```

### 4.2 FABRICATION_KEYWORDS — Dialogue Fabrication Triggers

```python
# patterns.py (imported by anomaly_detector.py)

FABRICATION_KEYWORDS: List[str] = [
    "as I said earlier",
    "as I mentioned earlier",
    "as we discussed",
    "as you told me",
    "you told me to",
    "we agreed on",
    "per your request",
    "as you requested",
    "as I told you",
    "I previously informed you",
    "as established earlier",
    "based on our discussion",
    "as stated before",
    "you instructed me to",
    "you asked me to",
    "as requested",
]
```

### 4.3 Severity Mapping

```python
PATTERN_SEVERITY: Dict[TamperPattern, Severity] = {
    TamperPattern.DIRECT_OVERRIDE: Severity.CRITICAL,
    TamperPattern.ROLE_HIJACK: Severity.CRITICAL,
    TamperPattern.PERMISSION_ESCALATION: Severity.HIGH,
    TamperPattern.RULE_MODIFICATION: Severity.HIGH,
    TamperPattern.CONTEXT_INJECTION: Severity.MEDIUM,
}
```

### 4.4 Anomaly Detection Indicators

```python
# Access pattern indicators that contribute to anomaly_score
ACCESS_ANOMALY_INDICATORS = {
    "burst_access": 0.4,           # > 20 reads in 1 second
    "unusual_timing": 0.2,         # Access outside normal hours
    "rapid_sensitive": 0.3,       # Rapid sequential reads of sensitive sources
    "source_deviation": 0.2,       # Accessing unusual source combination
    "volume_spike": 0.3,          # > 3x normal access volume
}
```

---

## 5. API Design

### 5.1 HunterAgent Public API (Complete)

| Method | Signature | Returns | Exceptions |
|--------|-----------|---------|-----------|
| `__init__` | `(config: HunterConfig) -> None` | — | `HunterConfigError` |
| `inspect_message` | `(message: AgentMessage) -> List[HunterAlert]` | `[HunterAlert]` | `HunterAgentError` (swallowed if graceful_degradation=True) |
| `validate_integrity` | `(agent_id, source, expected_hash?) -> IntegrityResult` | `IntegrityResult` | `HunterAgentError` |
| `check_tool_usage` | `(agent_id, tool_call: ToolCall) -> AbuseResult` | `AbuseResult` | `HunterAgentError` |
| `get_alert_history` | `(agent_id?, since?, detection_type?, limit?) -> List[HunterAlert]` | `[HunterAlert]` | — |
| `get_stats` | `() -> HunterStats` | `HunterStats` | — |
| `reload_config` | `() -> None` | — | `HunterConfigError` |

### 5.2 IntegrityValidator Public API

| Method | Signature | Returns | Exceptions |
|--------|-----------|---------|-----------|
| `__init__` | `(config?: HunterConfig) -> None` | — | — |
| `detect_tampering` | `(content: str) -> TamperResult` | `TamperResult` | — |
| `verify_hash` | `(source, expected_hash, algorithm?) -> IntegrityResult` | `IntegrityResult` | — |
| `compute_hash` | `(source, algorithm?) -> str` | `str` | — |

### 5.3 AnomalyDetector Public API

| Method | Signature | Returns | Exceptions |
|--------|-----------|---------|-----------|
| `__init__` | `(audit_logger: AuditLogger, config?: HunterConfig) -> None` | — | — |
| `detect_fabrication` | `(agent_id, claim, conversation_id) -> FabricateResult` | `FabricateResult` | — |
| `detect_poisoning` | `(agent_id, fact, auth_chain) -> PoisonResult` | `PoisonResult` | — |
| `extract_claims` | `(content: str) -> List[str]` | `[str]` | — |
| `query_audit_context` | `(conversation_id, time_window?) -> List[AuditEntry]` | `[AuditEntry]` | — |

### 5.4 RuleCompliance Public API

| Method | Signature | Returns | Exceptions |
|--------|-----------|---------|-----------|
| `__init__` | `(agents_md_path: Path, config?: HunterConfig) -> None` | — | `AgentsManifestError` |
| `check_whitelist` | `(agent_id, tool_name, permissions?) -> AbuseResult` | `AbuseResult` | — |
| `get_allowed_tools` | `(agent_id: str) -> List[str]` | `[str]` | — |
| `reload_whitelist` | `() -> None` | — | `AgentsManifestError` |

### 5.5 RuntimeMonitor Public API

| Method | Signature | Returns | Exceptions |
|--------|-----------|---------|-----------|
| `__init__` | `(integrity_validator: IntegrityValidator, config?: HunterConfig) -> None` | — | — |
| `validate_read` | `(agent_id, source, expected_hash?) -> IntegrityResult` | `IntegrityResult` | — |
| `detect_anomaly` | `(agent_id, access_pattern?) -> float` | `float` | — |
| `record_access` | `(agent_id, source, timestamp?) -> None` | — | — |
| `get_access_history` | `(agent_id, window?) -> List[AccessRecord]` | `[AccessRecord]` | — |

### 5.6 AuditLogger Public API (governance/)

| Method | Signature | Returns | Exceptions |
|--------|-----------|---------|-----------|
| `__init__` | `(log_path: Path, hash_chain?: bool) -> None` | — | — |
| `log` | `(event_type, agent_id, data, conversation_id?, parent_hash?) -> str` | `str` (hash) | — |
| `query` | `(filters) -> List[AuditEntry]` | `[AuditEntry]` | — |
| `verify_chain` | `() -> bool` | `bool` | — |

---

## 6. File Structure

```
methodology-v2/
├── hunter/
│   ├── __init__.py
│   │   """
│   │   Hunter Agent Package
│   │   
│   │   Exports:
│   │   - HunterAgent
│   │   - IntegrityValidator  
│   │   - AnomalyDetector
│   │   - RuleCompliance
│   │   - RuntimeMonitor
│   │   - HunterConfig
│   │   - HunterAlert
│   │   - HunterStats
│   │   """
│   │   
│   │   __version__ = "1.0.0"
│   │
│   ├── enums.py
│   │   """
│   │   TamperPattern, Severity, AuthStatus, DetectionType,
│   │   ActionType, MessageType
│   │   """
│   │
│   ├── models.py
│   │   """
│   │   AgentMessage, TamperResult, FabricateResult, PoisonResult,
│   │   AbuseResult, IntegrityResult, HunterAlert, MemoryFact,
│   │   AuthorizationChain, AuthLink, ToolCall, AgentsManifest,
│   │   AccessRecord, AuditEntry, HunterConfig, HunterStats
│   │   """
│   │
│   ├── exceptions.py
│   │   """
│   │   HunterAgentError — Base exception
│   │   HunterConfigError — Config validation errors  
│   │   AgentsManifestError — Agents.md parsing errors
│   │   IntegrityViolationError — Hash verification failures
│   │   FabricationDetectedError — Fabrication alert (non-fatal)
│   │   PoisoningDetectedError — Poisoning alert (non-fatal)
│   │   AbuseDetectedError — Tool abuse alert (non-fatal)
│   │   """
│   │
│   ├── patterns.py
│   │   """
│   │   TAMPER_PATTERNS: Dict[TamperPattern, List[str]]
│   │   FABRICATION_KEYWORDS: List[str]
│   │   PATTERN_SEVERITY: Dict[TamperPattern, Severity]
│   │   ACCESS_ANOMALY_INDICATORS: Dict[str, float]
│   │   """
│   │
│   ├── hunter_agent.py
│   │   """
│   │   Main facade. Coordinates all sub-detectors.
│   │   Entry point: inspect_message(), validate_integrity(),
│   │   check_tool_usage(), get_alert_history()
│   │   """
│   │
│   ├── integrity_validator.py
│   │   """
│   │   FR-H-1: detect_tampering() — regex pattern matching
│   │   FR-H-5: verify_hash() — SHA-256 verification
│   │   """
│   │
│   ├── anomaly_detector.py
│   │   """
│   │   FR-H-2: detect_fabrication() — audit log cross-reference
│   │   FR-H-3: detect_poisoning() — auth chain verification
│   │   """
│   │
│   ├── rule_compliance.py
│   │   """
│   │   FR-H-4: check_whitelist() — Agents.md enforcement
│   │   """
│   │
│   ├── runtime_monitor.py
│   │   """
│   │   FR-H-5: validate_read() — runtime integrity on memory/context read
│   │   detect_anomaly() — sliding window access pattern analysis
│   │   """
│   │
│   └── audit_logger.py
│       # SYMLINK to ../governance/audit_logger.py
│       # DO NOT EDIT — edit governance/audit_logger.py instead
│       # Linux/macOS: ln -s ../governance/audit_logger.py audit_logger.py
│       # Windows: mklink audit_logger.py ..\governance\audit_logger.py
│
├── governance/
│   └── audit_logger.py   # Source of truth for audit logging
│
└── tests/
    └── hunter/
        ├── __init__.py
        ├── test_hunter_agent.py
        ├── test_integrity_validator.py
        ├── test_anomaly_detector.py
        ├── test_rule_compliance.py
        ├── test_runtime_monitor.py
        ├── test_patterns.py
        ├── test_models.py
        └── conftest.py  # Shared fixtures
```

### 6.1 File Responsibilities

| File | Responsibility |
|------|---------------|
| `__init__.py` | Package exports, version |
| `enums.py` | All enum definitions |
| `models.py` | All dataclass definitions |
| `exceptions.py` | Custom exception hierarchy |
| `patterns.py` | All regex patterns and keywords |
| `hunter_agent.py` | Facade + coordination logic |
| `integrity_validator.py` | Tampering detection + hash verification |
| `anomaly_detector.py` | Fabrication + poisoning detection |
| `rule_compliance.py` | Tool whitelist enforcement |
| `runtime_monitor.py` | Runtime integrity + access pattern |
| `audit_logger.py` | Symlink to governance/audit_logger.py |

---

## 7. Dependencies & Interfaces

### 7.1 Internal Module Dependencies

```
hunter_agent.py
├── IntegrityValidator (composition)
├── AnomalyDetector (composition)
├── RuleCompliance (composition)
├── RuntimeMonitor (composition)
├── AuditLogger (from governance/)
└── models.py, enums.py, exceptions.py, patterns.py

integrity_validator.py
├── patterns.py (TAMPER_PATTERNS)
├── enums.py (TamperPattern, Severity)
└── models.py (TamperResult, IntegrityResult, HunterConfig)

anomaly_detector.py
├── AuditLogger (governance/)
├── models.py (FabricateResult, PoisonResult, MemoryFact, AuthorizationChain)
└── enums.py (AuthStatus)

rule_compliance.py
├── models.py (AgentsManifest, AbuseResult, ToolCall)
└── enums.py (Severity)

runtime_monitor.py
├── IntegrityValidator (composition)
├── models.py (IntegrityResult, AccessRecord, HunterConfig)
└── enums.py (Severity)

patterns.py — NO internal dependencies (pure data)
models.py — NO internal dependencies (dataclasses only)
enums.py — NO internal dependencies
exceptions.py — NO internal dependencies
```

### 7.2 Dependency Graph

```
                    ┌─────────────┐
                    │hunter_agent │
                    │  (Facade)   │
                    └──────┬──────┘
           ┌───────────────┼───────────────┬───────────────┐
           │               │               │               │
           ▼               ▼               ▼               ▼
   ┌───────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────────┐
   │IntegrityValid │ │ AnomalyDet. │ │RuleComplian │ │RuntimeMonitor │
   │               │ │             │ │             │ │               │
   │ FR-H-1, H-5   │ │ FR-H-2, H-3 │ │ FR-H-4      │ │ FR-H-5        │
   └───────┬───────┘ └──────┬──────┘ └─────────────┘ └───────┬───────┘
           │                │                                 │
           │                ▼                                 │
           │         ┌─────────────┐                         │
           │         │AuditLogger  │                         │
           │         │(governance/) │                         │
           │         └─────────────┘                         │
           │                                                   │
           └──────────────────┬──────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ patterns.py     │
                    │ enums.py        │
                    │ models.py       │
                    │ exceptions.py   │
                    └─────────────────┘
```

### 7.3 External Dependencies

**Python Standard Library Only** — No third-party packages required:

| Module | Usage |
|--------|-------|
| `dataclasses` | All model definitions |
| `datetime` | Timestamps, time windows |
| `typing` | Type hints |
| `re` | Regex pattern matching |
| `hashlib` | SHA-256 hashing |
| `uuid` | UUID4 generation for alert IDs |
| `json` | Serialization for audit log |
| `pathlib` | Path handling |
| `functools` | LRU cache decorator |
| `collections` | deque for sliding window |
| `contextlib` | context manager helpers |
| `copy` | Deep copy for immutable results |
| `itertools` | islice for efficient iteration |

### 7.4 External Layer Interfaces

#### 7.4.1 Agent Communication Bus

```python
# Hunter subscribes to all agent messages
message_bus.subscribe("agent.message", hunter.inspect_message)

# Message format expected:
@dataclass
class AgentMessage:
    agent_id: str
    conversation_id: str
    content: str
    timestamp: datetime
    message_type: MessageType
    metadata: Dict[str, Any]  # optional context
```

#### 7.4.2 Governance Layer (AuditLogger)

```python
# Reused from Layer 4 governance/audit_logger.py
from governance.audit_logger import AuditLogger

# Hunter writes all alerts to immutable audit log
audit_logger.log(
    event_type="hunter.alert",
    agent_id=alert.agent_id,
    data=alert.to_dict(),
    conversation_id=alert.conversation_id
)

# Hunter queries audit for fabrication detection
entries = audit_logger.query(
    conversation_id=conversation_id,
    since=datetime.now() - timedelta(minutes=30)
)
```

#### 7.4.3 Tiered Governance (HITL Escalation)

```python
# When severity >= HIGH, escalate to governance for human review
if alert.severity in (Severity.CRITICAL, Severity.HIGH):
    governance_trigger.escalate(
        alert=alert,
        action=alert.action_taken,  # HITL or HALT
        agent_id=alert.agent_id
    )
```

#### 7.4.4 MCP Agents/ (Agents.md)

```python
# Load agent-specific whitelists
import yaml

def load_agents_manifest(role: str, agents_dir: Path) -> AgentsManifest:
    manifest_path = agents_dir / role / "Agents.md"
    with open(manifest_path) as f:
        content = f.read()
    # Parse YAML front matter or structured section
    return parse_agents_md(content)

# RuleCompliance uses this to load whitelists
rule_compliance = RuleCompliance(
    agents_md_path=Path("mcp/agents/")
)
```

#### 7.4.5 Memory Subsystem

```python
# Hunter monitors memory writes for poisoning detection
memory_subsystem.subscribe_write(hunter.anomaly_detector.detect_poisoning)

# Hunter validates memory reads for integrity
result = runtime_monitor.validate_read(
    agent_id=agent_id,
    source="memory/agent_123/facts.json",
    expected_hash=expected_hash
)
```

---

## 8. Edge Cases & Error Handling

### 8.1 Hunter Agent Failure — Graceful Degradation

**Principle**: Hunter fails open — never block message flow.

```python
# In hunter_agent.inspect_message():
def inspect_message(self, message: AgentMessage) -> List[HunterAlert]:
    if self._config.graceful_degradation:
        try:
            return self._inspect_message_impl(message)
        except Exception as e:
            # Log the error but do not block the message
            self._log_error("Hunter inspection failed", error=e)
            return []  # Fail open: no alerts generated
    else:
        # Fail closed: raise for operators to investigate
        return self._inspect_message_impl(message)
```

**Failure Scenarios**:

| Failure | Behavior | Recovery |
|---------|----------|----------|
| IntegrityValidator crash | Return `[]`, log error | Auto-retry on next message |
| AnomalyDetector timeout | Return `[]`, log warning | Alert operator after 3 consecutive |
| RuleCompliance can't load whitelist | Default deny (block tool) | Reload on next check |
| AuditLogger write fails | Continue (alert in-memory), retry write | Write-ahead log for recovery |
| RuntimeMonitor OOM | Clear sliding window, restart | Reset window state |

### 8.2 False Positive Handling

**Target**: < 5% false positive rate in production.

```python
# Confidence threshold for flagging
TAMPER_CONFIDENCE_THRESHOLD = 0.7  # Flag only if confidence >= 0.7
FABRICATION_CONFIDENCE_THRESHOLD = 0.6

# False positive mitigation:
# 1. Multi-pattern requirement for CRITICAL severity
#    → Require 2+ patterns OR pattern + keyword match
# 2. Severity downgrade for ambiguous cases
#    → DIRECT_OVERRIDE with only 1 match → HIGH (not CRITICAL)
# 3. Audit log cross-reference for fabrication
#    → If audit shows prior context, lower confidence

# User feedback loop:
@dataclass
class HunterAlert:
    # ... existing fields
    false_positive_votes: int = 0  # Decremented by human review
    
def report_false_positive(self, alert_id: str) -> None:
    """Called by operators when alert is reviewed and deemed false positive."""
    alert = self._alert_store[alert_id]
    alert.false_positive_votes += 1
    if alert.false_positive_votes >= 3:
        self._adjust_threshold(alert.detection_type, delta=0.1)
```

### 8.3 Performance Bounds

| Metric | Target | Hard Limit | Implementation |
|--------|--------|------------|----------------|
| Latency per message check | < 50ms | 100ms | Async dispatch to sub-detectors; regex pre-compiled |
| Throughput | 1000 msg/sec | 2000 msg/sec | Stateless sub-detectors; shared nothing architecture |
| Memory footprint | < 100MB | 150MB | LRU cache bounded to 10K entries; sliding window max 1000 |
| Startup time | < 2s | 5s | Lazy loading of Agents.md; no external I/O on init |

### 8.4 Specific Edge Cases

#### 8.4.1 Empty Message Content

```python
def detect_tampering(self, content: str) -> TamperResult:
    if not content or not content.strip():
        return TamperResult(
            is_tampered=False,
            pattern_type=None,  # type: ignore
            severity=Severity.LOW,
            matched_tokens=[],
            evidence_hash=self.compute_hash("")
        )
```

#### 8.4.2 Concurrent Access to Sliding Window

```python
from threading import Lock
from collections import deque

class SlidingWindow:
    def __init__(self, max_size: int):
        self._window: Dict[str, deque] = {}
        self._lock = Lock()
    
    def record(self, agent_id: str, record: AccessRecord):
        with self._lock:
            if agent_id not in self._window:
                self._window[agent_id] = deque(maxlen=self.max_size)
            self._window[agent_id].append(record)
            self._evict_old(agent_id)
```

#### 8.4.3 Audit Log Unavailable for Fabrication Check

```python
def detect_fabrication(self, agent_id, claim, conversation_id) -> FabricateResult:
    try:
        entries = self._audit_logger.query(conversation_id=conversation_id)
    except AuditLoggerError:
        # If audit unavailable, default to suspicious (fail secure)
        return FabricateResult(
            is_fabricated=True,
            claim=claim,
            audit_reference=None,
            confidence=0.5,  # Uncertain — flag for review
            _audit_unavailable=True
        )
```

#### 8.4.4 Hash Collision Handling

```python
# SHA-256 collision probability: 2^-128 — negligible
# Still handle gracefully:
if actual_hash != expected_hash:
    # Log collision possibility (extremely rare)
    self._log_warning(
        f"Hash mismatch for {source}. "
        f"Expected: {expected_hash}, Got: {actual_hash}. "
        f"Treating as integrity violation."
    )
    return IntegrityResult(
        is_valid=False,
        # ...
        violation_type="hash_mismatch"
    )
```

#### 8.4.5 Malformed Agents.md

```python
def __init__(self, agents_md_path: Path) -> None:
    try:
        self._load_manifests(agents_md_path)
    except Exception as e:
        raise AgentsManifestError(
            f"Failed to load Agents.md: {e}"
        ) from e

def _load_manifests(self, path: Path) -> None:
    for agent_dir in path.iterdir():
        manifest_file = agent_dir / "Agents.md"
        if manifest_file.exists():
            try:
                manifest = self._parse_manifest(manifest_file)
                self._manifest_cache[manifest.agent_id] = manifest
            except Exception as e:
                self._log_error(
                    f"Failed to parse {manifest_file}: {e}. "
                    f"Agent {agent_dir.name} will have no whitelisted tools."
                )
                # Fail secure: no tools whitelisted for malformed manifest
                self._whitelist_cache[agent_dir.name] = []
```

#### 8.4.6 High Cardinality Agent IDs (Memory Pressure)

```python
MAX_UNIQUE_AGENTS_IN_WINDOW = 1000

def record_access(self, agent_id, source, timestamp=None):
    if len(self._access_window) >= MAX_UNIQUE_AGENTS_IN_WINDOW:
        # Evict least recently active agent
        oldest_agent = min(
            self._access_window.keys(),
            key=lambda a: self._last_access_time.get(a, datetime.min)
        )
        del self._access_window[oldest_agent]
        self._log_warning(f"Evicted sliding window for agent {oldest_agent}")
```

#### 8.4.7 Clock Skew in Timestamps

```python
# When comparing timestamps across agents with potential clock skew:
MAX_CLOCK_SKEW = timedelta(minutes=5)

def query_audit_context(self, conversation_id, time_window=timedelta(minutes=30)):
    adjusted_window = timedelta(
        seconds=time_window.total_seconds() + MAX_CLOCK_SKEW.total_seconds()
    )
    # Query with expanded window to account for clock skew
    return self._audit_logger.query(
        conversation_id=conversation_id,
        since=datetime.now() - adjusted_window
    )
```

---

## Appendix A: Complete Type Reference

### A.1 All Public Classes and Their Public Methods

```
HunterAgent
├── inspect_message(message: AgentMessage) -> List[HunterAlert]
├── validate_integrity(agent_id, source, expected_hash?) -> IntegrityResult
├── check_tool_usage(agent_id, tool_call: ToolCall) -> AbuseResult
├── get_alert_history(agent_id?, since?, detection_type?, limit?) -> List[HunterAlert]
└── get_stats() -> HunterStats

IntegrityValidator
├── detect_tampering(content: str) -> TamperResult
├── verify_hash(source, expected_hash, algorithm?) -> IntegrityResult
└── compute_hash(source, algorithm?) -> str

AnomalyDetector
├── detect_fabrication(agent_id, claim, conversation_id) -> FabricateResult
├── detect_poisoning(agent_id, fact, auth_chain) -> PoisonResult
├── extract_claims(content: str) -> List[str]
└── query_audit_context(conversation_id, time_window?) -> List[AuditEntry]

RuleCompliance
├── check_whitelist(agent_id, tool_name, permissions?) -> AbuseResult
├── get_allowed_tools(agent_id) -> List[str]
└── reload_whitelist() -> None

RuntimeMonitor
├── validate_read(agent_id, source, expected_hash?) -> IntegrityResult
├── detect_anomaly(agent_id, access_pattern?) -> float
├── record_access(agent_id, source, timestamp?) -> None
└── get_access_history(agent_id, window?) -> List[AccessRecord]

AuditLogger (governance/)
├── log(event_type, agent_id, data, conversation_id?, parent_hash?) -> str
├── query(filters) -> List[AuditEntry]
└── verify_chain() -> bool
```

### A.2 All Dataclasses

```
AgentMessage, TamperResult, FabricateResult, PoisonResult,
AbuseResult, IntegrityResult, HunterAlert, MemoryFact,
AuthorizationChain, AuthLink, ToolCall, AgentsManifest,
AccessRecord, AuditEntry, HunterConfig, HunterStats
```

### A.3 All Enums

```
TamperPattern, Severity, AuthStatus, DetectionType, ActionType, MessageType
```

### A.4 All Exceptions

```
HunterAgentError (base)
├── HunterConfigError
├── AgentsManifestError
├── IntegrityViolationError
├── FabricationDetectedError (non-fatal)
├── PoisoningDetectedError (non-fatal)
└── AbuseDetectedError (non-fatal)
```

---

*Architecture version: 1.0*  
*Generated: 2026-04-19 01:08 GMT+8*  
*Status: Phase 2 Complete — Ready for Phase 3 Implementation*