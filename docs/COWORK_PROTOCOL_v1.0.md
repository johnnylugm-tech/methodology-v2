# 跨Agent Co-Work 完整設計方案 (v1.0)

> **版本**: v1.0
> **日期**: 2026-03-31
> **整合**: v6.14 + v6.15 + v6.16
> **用途**: 跨Agent間的Co-Work設計

---

## 一、核心設計原則

### 1.1 最小執行單位
- **Step**（5W1H中的一個步驟）為最小執行單位
- 每個Step可獨立Commit/Resume
- 任何模型都能接力執行

### 1.2 GitHub的三重角色
| 角色 | 說明 |
|------|------|
| **事實中介** | Agent A ↔ Agent B 之間的不可篡改證據 |
| **狀態持久化** | 任何Step完成都上傳，中斷可恢復 |
| **接力點** | 任何模型都可接力，無單點故障 |

### 1.3 防作假機制
| 機制 | 說明 |
|------|------|
| 七維度審計 | 外部獨立驗證 |
| 完整跡證 | 過程、中間產物、決策rationale |
| 不可篡改 | GitHub Commit時間戳 + 內容Hash |

---

## 二、狀態管理架構

### 2.1 STATE.md（全域狀態）

```markdown
# 專案執行狀態

## 基本資訊
- project_name: {name}
- methodology_version: v6.14+
- last_updated: {ISO8601}

## 當前進度
- current_phase: 3
- current_step: 2
- current_agent: claude-sonnet
- checkpoint_id: phase-3-step-2-abc1234

## Step歷史
| Phase | Step | Agent | Model | Status | Commit | Timestamp |
|-------|------|-------|-------|--------|--------|-----------|
| 1 | 1 | architect | gpt-4o | ✅ | abc1234 | 2026-03-31T10:00 |
| 1 | 2 | architect | gpt-4o | ✅ | def5678 | 2026-03-31T10:15 |
...

## Checkpoint鏈
- phase-1-step-1: ✅ (def5678)
- phase-1-step-2: ✅ (ghi9012)
- phase-2-step-1: ✅ (jkl3456)
- phase-3-step-1: ✅ (mno7890)
- phase-3-step-2: 🔄 (current)

## 審計追蹤
| Phase | 審計者 | 結論 | 時間 |
|-------|--------|--------|------|
| 1 | claude-opus | APPROVE | 2026-03-31T11:00 |
```

### 2.2 Checkpoint結構

```
.checkpoints/
├── phase-1/
│   ├── step-1/
│   │   ├── COMPLETE.lock          # 完成鎖定
│   │   ├── artifacts/            # 中間產物
│   │   │   ├── SRS_draft_v1.md
│   │   │   └── decisions.md
│   │   ├── METADATA.json         # 執行資料
│   │   └── VERIFY.lock           # 審計鎖定
│   └── step-2/
│       └── ...
├── phase-2/
│   └── ...
└── .metadata/
    ├── agent_info.json           # Agent身份
    ├── model_selection.json      # 模型選擇邏輯
    └── audit_trail.json          # 審計軌跡
```

### 2.3 METADATA.json格式

```json
{
  "checkpoint_id": "phase-3-step-2-abc1234",
  "phase": 3,
  "step": 2,
  "step_name": "Agent A 實作模組A",
  "agent": {
    "id": "agent-uuid",
    "persona": "developer",
    "model": "claude-sonnet-20250710",
    "gateway": "openclaw-1"
  },
  "execution": {
    "started_at": "2026-03-31T14:00:00Z",
    "completed_at": "2026-03-31T14:30:00Z",
    "duration_seconds": 1800,
    "command_outputs": [
      {
        "command": "pytest tests/test_module_a.py --cov",
        "output_hash": "sha256:abc123...",
        "exit_code": 0
      }
    ],
    "artifacts": [
      "src/module_a.py",
      "tests/test_module_a.py"
    ]
  },
  "verification": {
    "self_check": {
      "5w1h_compliant": true,
      "confidence_score": 85,
      "issues_found": []
    },
    "external_review": null
  },
  "integrity": {
    "git_commit": "abc1234",
    "content_hash": "sha256:def456...",
    "timestamp": "2026-03-31T14:35:00Z"
  }
}
```

---

## 三、模型分工策略

### 3.1 模型選擇器

```python
MODEL_SELECTION = {
    # Phase 1: 需求規格
    "phase_1": {
        "default": "gpt-4o",
        "fallback": "claude-opus",
        "criteria": ["長上下文理解", "規格撰寫"]
    },
    # Phase 2: 架構設計
    "phase_2": {
        "default": "claude-opus",
        "fallback": "gpt-4o",
        "criteria": ["深度推理", "複雜分析"]
    },
    # Phase 3: 代碼實作
    "phase_3": {
        "default": "claude-sonnet",
        "fallback": "gpt-4o",
        "criteria": ["代碼能力", "性價比"]
    },
    # 審計者
    "auditor": {
        "default": "claude-opus",
        "fallback": "gpt-4o",
        "criteria": ["批判性思維", "獨立判斷"]
    }
}

def select_model(phase: int, step: int, context: dict) -> str:
    """根據Phase和Step選擇最適模型"""
    key = f"phase_{phase}"
    model = MODEL_SELECTION.get(key, MODEL_SELECTION["auditor"])
    
    # 檢查Token使用量，自動降級
    if context.get("token_usage", 0) > 0.8 * context.get("token_limit"):
        model = model.get("fallback", model["default"])
    
    return model["default"]
```

### 3.2 模型能力矩陣

| 模型 | 推理 | 代碼 | 分析 | 創意 | 性價比 | 適合Step |
|------|------|------|------|------|--------|----------|
| Claude Opus | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | 💰💰💰 | Phase 2, 6, 7 |
| Claude Sonnet | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | 💰💰 | Phase 3, 4, 5 |
| GPT-4o | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 💰💰💰 | 通用 |
| Gemini 1.5 | ⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ | 💰 | Phase 1, 8 |
| o3-mini | ⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐ | 💰 | 簡單任務 |

---

## 四、七維度審計方法

### 4.1 維度一：DEVELOPMENT_LOG品質

```bash
# 檢查命令+輸出配對
grep -A5 "Command:" DEVELOPMENT_LOG.md | wc -l
grep -A10 "Output:" DEVELOPMENT_LOG.md | wc -l

# 量化數值存在性
grep -c "Compliance Rate:" DEVELOPMENT_LOG.md
grep -c "Score:" DEVELOPMENT_LOG.md
grep -c "Passed:" DEVELOPMENT_LOG.md
```

### 4.2 維度二：A/B分離驗證

```python
def verify_ab_separation(checkpoint: dict) -> bool:
    """驗證A/B確實不同Agent"""
    agent_a = checkpoint["agent_a"]
    agent_b = checkpoint["agent_b"]
    
    return (
        agent_a["id"] != agent_b["id"] and
        agent_a["session_id"] != agent_b["session_id"] and
        agent_a["gateway"] != agent_b["gateway"]  # 可選：跨Gateway
    )
```

### 4.3 維度三：Quality Gate重新執行

```python
def rerun_quality_gates(phase: int) -> dict:
    """重新執行所有Quality Gate，比對結果"""
    results = {
        "doc_checker": subprocess.run(["python", "quality_gate/doc_checker.py"]),
        "constitution": subprocess.run(["python", "quality_gate/constitution/runner.py", "--type", "all"]),
        "pytest": subprocess.run(["pytest", "--tb=short"]),
        "coverage": subprocess.run(["pytest", "--cov", "--cov-report=term-missing"])
    }
    
    # 比對與記錄的值
    for name, result in results.items():
        recorded = get_recorded_value(name)
        actual = parse_output(result.stdout)
        if recorded != actual:
            return {"mismatch": True, "name": name, "recorded": recorded, "actual": actual}
    
    return {"consistent": True}
```

### 4.4 維度四：產物完整性

```python
REQUIRED_ARTIFACTS = {
    1: ["SRS.md", "SPEC_TRACKING.md", "TRACEABILITY_MATRIX.md"],
    2: ["SAD.md", "ADR.md"],
    3: ["src/", "tests/", "COMPLIANCE_MATRIX.md"],
    4: ["TEST_PLAN.md", "TEST_RESULTS.md"],
    5: ["BASELINE.md", "VERIFICATION_REPORT.md", "MONITORING_PLAN.md"],
    6: ["QUALITY_REPORT.md"],
    7: ["RISK_ASSESSMENT.md", "RISK_REGISTER.md"],
    8: ["CONFIG_RECORDS.md", "RELEASE_CHECKLIST.md"]
}

def verify_artifacts(phase: int) -> dict:
    """驗證必要產物存在且有內容"""
    required = REQUIRED_ARTIFACTS[phase]
    for artifact in required:
        if not Path(artifact).exists():
            return {"missing": artifact}
        if is_empty(artifact):
            return {"empty": artifact}
        if is_template_only(artifact):
            return {"template_only": artifact}
    return {"complete": True}
```

### 4.5 維度五：Constitution重新驗證

```python
def rerun_constitution(phase: int) -> dict:
    """重新執行Constitution檢查"""
    result = subprocess.run([
        "python", "quality_gate/constitution/runner.py",
        "--type", PHASE_TYPES[phase],
        "--json"
    ], capture_output=True)
    
    score = parse_score(result.stdout)
    threshold = {"phase_1": 100, "phase_5": 80}
    
    return {
        "score": score,
        "threshold": threshold.get(f"phase_{phase}", 80),
        "passed": score >= threshold.get(f"phase_{phase}", 80)
    }
```

### 4.6 維度六：Phase進入條件鏈

```python
def verify_phase_chain(current_phase: int) -> dict:
    """驗證前置Phase都已完成"""
    for prev_phase in range(1, current_phase):
        checkpoint = load_checkpoint(prev_phase)
        if checkpoint["status"] != "APPROVED":
            return {
                "blocked": True,
                "reason": f"Phase {prev_phase} not APPROVED",
                "checkpoint": checkpoint
            }
    return {"chain_valid": True}
```

### 4.7 維度七：Anti-Cheat主動檢驗

```python
def run_anti_cheat(phase: int) -> dict:
    """執行Anti-Cheat檢驗"""
    results = []
    
    # Claims Verifier
    claims = ClaimsVerifier(".").verify_all()
    results.append(("claims", claims.passed))
    
    # AB Enforcer
    ab = ABEnforcer(".").verify_ab_separation()
    results.append(("ab_separation", ab.passed))
    
    # Phase Truth
    truth = PhaseTruthVerifier(".", phase).verify()
    results.append(("truth_score", truth.score >= 70))
    
    return {
        "all_passed": all(r[1] for r in results),
        "details": results
    }
```

---

## 五、CLI工具設計

### 5.1 Commit（提交Step）

```bash
# 基本用法
python scripts/cowork.py commit --step 3.2 --model claude-sonnet

# 輸出
# ✅ Step 3.2 committed to GitHub
# 📦 artifacts: src/module_b.py, tests/test_module_b.py
# 🔗 checkpoint: phase-3-step-2-abc1234
# ⏱️ duration: 15m 30s
```

### 5.2 Pull/Resume（接力執行）

```bash
# 基本用法
python scripts/cowork.py pull --resume

# 輸出
# 📍 Resuming from Phase 3, Step 2
# 🔗 checkpoint: phase-3-step-2-abc1234
# 🤖 Next model: gpt-4o
# 📋 Pending tasks:
#    - Continue module B implementation
#    - Run pytest
```

### 5.3 Audit（審計）

```bash
# 基本用法
python scripts/cowork.py audit --phase 3

# 輸出
# 📊 Phase 3 Audit Report
# ├─ 維度1: DEVELOPMENT_LOG ✅
# ├─ 維度2: A/B Separation ✅
# ├─ 維度3: Quality Gate ✅
# ├─ 維度4: Artifacts ✅
# ├─ 維度5: Constitution ❌ (score: 65 < 80)
# ├─ 維度6: Phase Chain ✅
# └─ 維度7: Anti-Cheat ⚠️
# ⚠️ 總結: 需要修復後再審
```

### 5.4 Status（狀態查看）

```bash
# 基本用法
python scripts/cowork.py status

# 輸出
# 📍 Current: Phase 3, Step 2
# 🤖 Current Agent: claude-sonnet
# 🔗 Checkpoint: abc1234
# 📊 Progress:
#    Phase 1: ✅ APPROVED
#    Phase 2: ✅ APPROVED
#    Phase 3: 🔄 2/5 steps
#    Phase 4-8: ⏸️ pending
```

---

## 六、完整性保障機制

### 6.1 不可篡改性

```python
def verify_immutability(checkpoint_id: str) -> bool:
    """驗證Checkpoint未被篡改"""
    # 1. 比對Git Commit Hash
    commit = get_git_commit(checkpoint_id)
    stored_hash = get_stored_hash(checkpoint_id)
    
    # 2. 比對內容Hash
    content_hash = compute_hash(load_checkpoint(checkpoint_id))
    stored_content_hash = get_content_hash(checkpoint_id)
    
    return commit == stored_hash and content_hash == stored_content_hash
```

### 6.2 恢復驗證

```python
def verify_resume(checkpoint_id: str) -> dict:
    """驗證Checkpoint可完整恢復"""
    checkpoint = load_checkpoint(checkpoint_id)
    
    # 1. 所有artifacts存在
    for artifact in checkpoint["artifacts"]:
        if not Path(artifact).exists():
            return {"recoverable": False, "reason": f"missing {artifact}"}
    
    # 2. 所有command可重放
    for cmd in checkpoint["commands"]:
        if not can_replay(cmd):
            return {"recoverable": False, "reason": f"non-replayable command"}
    
    # 3. Agent狀態可重建
    if not can_restore_agent_state(checkpoint["agent"]):
        return {"recoverable": False, "reason": "agent state missing"}
    
    return {"recoverable": True}
```

### 6.3 衝突檢測

```python
def detect_conflicts(checkpoint_a: dict, checkpoint_b: dict) -> list:
    """檢測兩個Checkpoint間的衝突"""
    conflicts = []
    
    # 1. 同一Step被兩個Agent執行
    if checkpoint_a["step"] == checkpoint_b["step"]:
        conflicts.append("duplicate_step_execution")
    
    # 2. 順序衝突（Step N依賴Step N-1但先執行）
    if checkpoint_a["step"] < checkpoint_b["step"]:
        if not checkpoint_a["completed"]:
            conflicts.append("dependency_violation")
    
    # 3. 模型衝突（聲稱用A但實際用B）
    if checkpoint_a["model"] != checkpoint_b["model"]:
        conflicts.append("model_mismatch")
    
    return conflicts
```

---

## 七、錯誤處理與恢復

### 7.1 錯誤分類

| 等級 | 類型 | 處理 |
|------|------|------|
| L1 | 輸入錯誤 | 立即返回，提示修正 |
| L2 | 工具錯誤 | 重試3次，自動降級 |
| L3 | 執行錯誤 | Commit當前狀態，發送警報 |
| L4 | 系統錯誤 | 完整Checkpoint，進入人工審計 |

### 7.2 自動恢復流程

```
錯誤發生
    ↓
L2: 重試機制啟動
    ↓
L3: Commit當前狀態 + 警報
    ↓
GitHub狀態完整
    ↓
新Agent接手
    ↓
從Checkpoint恢復
    ↓
繼續執行
```

---

## 八、Johnny介入點

### 8.1 自動介入條件

| 條件 | 觸發 |
|------|------|
| 連續3次L3錯誤 | Johnny警報 |
| Phase Truth < 50 | Johnny介入 |
| 審計不通過 | Johnny決定 |
| 跨模型衝突 | Johnny裁決 |

### 8.2 Johnny審核清單

```markdown
## Phase {N} Johnny審核

### 必要檢視
- [ ] STATE.md當前狀態
- [ ] 最近的Checkpoint
- [ ] 七維度審計報告
- [ ] Agent執行日誌

### 決定
- [ ] ✅ CONFIRMED - 繼續執行
- [ ] ⚠️ QUERY - 有疑問需澄清
- [ ] ❌ REJECT - 返回修復
```

---

## 九、部署架構

### 9.1 目錄結構

```
{project}/
├── .cowork/                  # Co-Work系統目錄
│   ├── STATE.md
│   ├── .checkpoints/
│   │   ├── phase-1/
│   │   │   ├── step-1/
│   │   │   │   ├── COMPLETE.lock
│   │   │   │   ├── METADATA.json
│   │   │   │   └── artifacts/
│   │   │   └── step-2/
│   │   │       └── ...
│   │   └── ...
│   └── .metadata/
│       ├── agent_registry.json
│       ├── model_config.json
│       └── audit_trail.json
├── scripts/
│   ├── cowork.py             # 主CLI
│   ├── model_selector.py     # 模型選擇
│   ├── checkpoint_manager.py # Checkpoint管理
│   └── audit_engine.py       # 審計引擎
├── docs/
│   ├── COWORK_PROTOCOL.md    # 協同協議
│   └── AUDIT_CHECKLIST.md   # 審計清單
└── quality_gate/
    ├── claims_verifier.py
    ├── ab_enforcer.py
    ├── phase_truth_verifier.py
    └── integrity_tracker.py
```

### 9.2 依賴套件

```toml
[dependencies]
github-cli = ">=2.0"
pydantic = ">=2.0"
pytest = ">=7.0"
pyyaml = ">=6.0"
```

---

## 十、實作優先順序

| 優先 | 模組 | 說明 |
|------|------|------|
| P0 | STATE.md + Checkpoint | 核心狀態管理 |
| P0 | cowork.py commit/pull | 基本CLI |
| P1 | model_selector.py | 模型選擇 |
| P1 | 七維度審計 | 品質把關 |
| P2 | 衝突檢測 | 完整性保障 |
| P2 | 自動恢復 | 錯誤處理 |
| P3 | Johnny介入系統 | Human-in-loop |

---

## 十一、驗證方法

### 11.1 單元測試

```python
def test_state_persistence():
    """驗證STATE.md正確更新"""
    # 1. 執行Step
    # 2. Commit
    # 3. 讀取STATE.md
    # 4. 驗證更新正確

def test_checkpoint_recovery():
    """驗證Checkpoint可恢復"""
    # 1. 創建Checkpoint
    # 2. 模擬中斷
    # 3. Resume
    # 4. 驗證狀態一致
```

### 11.2 整合測試

```python
def test_cross_model_workflow():
    """驗證跨模型接力"""
    # 1. Model A 執行 Step 1
    # 2. Commit to GitHub
    # 3. Model B Pull
    # 4. Model B 繼續 Step 2
    # 5. 驗證完整性
```

---

## 附錄A：九個常見作弊手法偵測

| # | 作弊手法 | 偵測方法 |
|---|----------|----------|
| 1 | 空殼Quality Gate | DEVELOPMENT_LOG有命令但無輸出 |
| 2 | 自寫自審 | Agent A和B的session_id相同 |
| 3 | 跳過Phase前置條件 | Phase N+1缺少Phase N的確認 |
| 4 | 分數造假 | 重新執行Constitution分數不同 |
| 5 | 空殼文件 | FR數量<5或只有模板標題 |
| 6 | 假A/B審查 | Reviewer欄位空白或複製 |
| 7 | 時間線倒填 | Git commit時間≠執行時間 |
| 8 | sessions_spawn.log缺失 | 沒有啟動過Sub-agent |
| 9 | Constitution解析失敗被忽略 | parse_constitution回傳0但仍通過 |

---

*方案版本: v1.0*
*最後更新: 2026-03-31*
