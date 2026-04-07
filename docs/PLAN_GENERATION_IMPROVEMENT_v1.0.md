# Plan Generation 改善與優化方案

> **日期**: 2026-04-04
> **版本**: v6.47
> **依據**: Phase 3 實際問題 + 7 大面向評估

---

## Executive Summary

### 現況覆蓋率

| 面向 | 覆蓋率 | 問題 |
|------|---------|------|
| SKILL.md 100% 落實 | 70% | 只有 Phase 3 有詳細 Prompt |
| 8 階段適用 | 75% | Phase 1-2, 4-8 只有通用模板 |
| 上階段產出承接 | 50% | FR 解析器只支援 Phase 3 |
| A/B 協作 | 90% | Role map 完整但 Prompt 不區分 Phase |
| 子代理管理 | 60% | 只有通用原則，無具體時機 |
| 工具使用 | 40% | Section 9 缺乏動態觸發 |
| 迭代修復 | 50% | HR-12 已知但流程不完整 |

---

## 七大面向評估與改善方案

---

## 面向 1：100% 落實 SKILL.md

### 現況問題

| SKILL.md 規則 | plan-phase 落實 | 狀態 |
|---------------|-----------------|------|
| HR-01 A/B 不同 Agent | ✅ Role map | 完整 |
| HR-02 QG 實際命令 | ✅ QG commands | 完整 |
| HR-03 Phase 順序 | ✅ Pre-flight | 完整 |
| HR-04 HybridWorkflow | ⚠️ 有提到 | 不夠強制 |
| HR-05 methodology-v2 優先 | ❌ 未強調 | 缺失 |
| HR-06 禁外框架 | ⚠️ Forbidden | 不完整 |
| HR-07 session_id | ⚠️ 有提到 | 未強調 |
| HR-08 QG 執行 | ✅ stage-pass | 完整 |
| HR-09 Claims Verifier | ❌ 未落實 | 缺失 |
| HR-10 sessions_spawn.log | ✅ 有格式 | 完整 |
| HR-11 Phase Truth <70% | ✅ Pre-flight | 完整 |
| HR-12 >5 輪 PAUSE | ⚠️ 有提到 | 流程不完整 |
| HR-13 >3x 時間 PAUSE | ⚠️ 有提到 | 未自動計算 |
| HR-14 Integrity <40 FREEZE | ⚠️ 有檢查 | 未自動 |
| HR-15 citations 行號 | ✅ Prompt 強調 | 完整 |
| TH-01~17 門檻 | ✅ TH map | 完整 |

### 改善方案

| 問題 | 改善 |
|------|------|
| HR-05 未強調 | Prompt 加上「衝突時 methodology-v2 為準」|
| HR-09 Claims Verifier | 加入「Claims Verifier 驗證步驟」|
| HR-12 流程 | 加入「5 輪後自動暫停 + 通知」流程 |
| HR-13/14 自動計算 | 加入「時間追蹤 + Integrity 計算」|

---

## 面向 2：全部 8 階段適用

### 現況問題

| Phase | Prompt | FR Parser | Role | TH |
|-------|--------|----------|------|-----|
| 1 | ❌ 通用 | ❌ 無 | ✅ | ✅ |
| 2 | ❌ 通用 | ⚠️ SAD only | ✅ | ✅ |
| 3 | ✅ 完整 | ✅ SRS+SAD | ✅ | ✅ |
| 4 | ❌ 通用 | ❌ 無 | ✅ | ✅ |
| 5 | ❌ 通用 | ❌ 無 | ✅ | ✅ |
| 6 | ❌ 通用 | ❌ 無 | ✅ | ✅ |
| 7 | ❌ 通用 | ❌ 無 | ✅ | ✅ |
| 8 | ❌ 通用 | ❌ 無 | ✅ | ✅ |

### 改善方案

```python
# Phase-specific prompt templates
prompts = {
    1: {  # 需求規格
        "developer": {
            "task": "制定 SRS",
            "output": ["SRS.md", "SPEC_TRACKING.md"],
            "read": ["TASK_INITIALIZATION_PROMPT.md"],
            "verify": ["trace-check"]
        },
        "reviewer": {
            "reject_if": ["SRS 不完整", "缺少 trace"],
            "verify": ["SRS quality gate"]
        }
    },
    2: {  # 架構設計
        "developer": {
            "task": "制定 SAD + ADR",
            "output": ["SAD.md", "ADR.md"],
            "read": ["SRS.md"],
            "verify": ["sad_constitution_checker"]
        },
        "reviewer": {
            "reject_if": ["SRS↔SAD 不一致"],
            "verify": ["trace-check"]
        }
    },
    3: {  # 代碼實現（已完整）
        ...
    },
    4: {  # 測試
        "developer": {
            "task": "制定測試計畫",
            "output": ["TEST_PLAN.md", "TEST_RESULTS.md"],
            "read": ["SRS.md", "SAD.md", "src/"],
            "verify": ["test_constitution_checker"]
        },
        ...
    },
    5: {  # 驗證交付
        "developer": {
            "task": "建立 Baseline + Monitoring",
            "output": ["BASELINE.md", "MONITORING_PLAN.md"],
            "read": ["TEST_RESULTS.md"],
            ...
        },
        ...
    },
    6: {  # 品質保證
        "developer": {
            "task": "生成品質報告",
            "output": ["QUALITY_REPORT.md"],
            "read": ["TEST_RESULTS.md", "BASELINE.md"],
            ...
        },
        ...
    },
    7: {  # 風險管理
        "developer": {
            "task": "識別並追蹤風險",
            "output": ["RISK_REGISTER.md"],
            "read": ["QUALITY_REPORT.md"],
            ...
        },
        ...
    },
    8: {  # 配置管理
        "developer": {
            "task": "建立配置記錄",
            "output": ["CONFIG_RECORDS.md", "requirements.lock"],
            "read": ["RISK_REGISTER.md"],
            ...
        },
        ...
    },
}
```

---

## 面向 3：正確承接上階段產出

### 現況問題

Phase 3 的 parse_srs_fr_sections() 只能解析：
- FR 標題
- 描述
- 測試案例

但沒有解析：
- NFR（非功能需求）
- 介面規格
- 約束條件

### 改善方案

```python
# 完整的上階段產出解析器
def parse_phase_artifacts(phase: int, repo_path: Path) -> dict:
    """解析上階段所有產出"""
    artifacts = {}
    
    if phase >= 1:
        # Phase 1 產出
        artifacts['srs'] = parse_srs(repo_path / "SRS.md")
        artifacts['spec_tracking'] = parse_spec_tracking(repo_path / "SPEC_TRACKING.md")
        artifacts['traceability'] = parse_traceability(repo_path / "TRACEABILITY_MATRIX.md")
    
    if phase >= 2:
        # Phase 2 產出
        artifacts['sad'] = parse_sad(repo_path / "02-architecture" / "SAD.md")
        artifacts['adr'] = parse_adr(repo_path / "ADR.md")
    
    if phase >= 3:
        # Phase 3 產出
        artifacts['code'] = list((repo_path / "app").glob("**/*.py"))
        artifacts['tests'] = list((repo_path / "tests").glob("**/*.py"))
    
    if phase >= 4:
        artifacts['test_plan'] = parse_test_plan(repo_path / "TEST_PLAN.md")
        artifacts['test_results'] = parse_test_results(repo_path / "TEST_RESULTS.md")
    
    # ... etc for phases 5-8
    
    return artifacts

def parse_srs(path: Path) -> dict:
    """完整解析 SRS.md"""
    content = path.read_text()
    
    # FR sections
    frs = extract_sections(content, pattern=r'### FR-(\d+)')
    
    # NFR sections
    nfrs = extract_sections(content, pattern=r'### NFR-(\d+)')
    
    # Interface specs
    interfaces = extract_interfaces(content)
    
    # Constraints
    constraints = extract_constraints(content)
    
    # Traceability matrix
    traceability = extract_traceability_matrix(content)
    
    return {
        'frs': frs,
        'nfrs': nfrs,
        'interfaces': interfaces,
        'constraints': constraints,
        'traceability': traceability
    }
```

### Phase-to-Phase 產出繼承

| Phase | 讀取上階段 | 寫入本階段 |
|-------|-----------|-------------|
| 1 | TASK_INITIALIZATION_PROMPT.md | SRS.md, SPEC_TRACKING.md, TRACEABILITY.md |
| 2 | SRS.md | SAD.md, ADR.md |
| 3 | SRS.md, SAD.md | src/, tests/ |
| 4 | SRS.md, SAD.md, src/ | TEST_PLAN.md, TEST_RESULTS.md |
| 5 | TEST_RESULTS.md, BASELINE.md | VERIFICATION_REPORT.md, MONITORING_PLAN.md |
| 6 | QUALITY_REPORT.md | QUALITY_ASSURANCE_REPORT.md |
| 7 | RISK_REGISTER.md | RISK_MITIGATION_PLANS.md |
| 8 | CONFIG_RECORDS.md | DEPLOYMENT_CHECKLIST.md, requirements.lock |

---

## 面向 4：A/B 協作優化

### 現況問題

- Role map 正確（8 Phase 各有不同組合）
- 但 Developer/Reviewer Prompt 只有 Phase 3 完整
- 其他 Phase 的 A/B 職責不明確

### 改善方案

```python
# Phase-specific A/B prompts
ab_prompts = {
    1: {
        "A": {
            "role": "architect",
            "task": "制定需求規格",
            "prompt": """
【On Demand 讀取】
- TASK_INITIALIZATION_PROMPT.md（只讀目標和約束）

【產出】
- SRS.md：完整需求規格
- SPEC_TRACKING.md：規格追蹤矩陣

【驗證】
- Constitution SRS ≥80%
- Traceability 每個 FR 有對應測試案例
            """,
            "forbidden": ["遺漏 FR", "NFR 不完整"]
        },
        "B": {
            "role": "reviewer",
            "task": "審查需求規格",
            "verify": """
1. 每個 FR 有明確的驗收標準
2. NFR 可追蹤到 FR
3. Traceability 矩陣完整
4. Constitution SRS ≥80%
            """,
            "reject_if": ["FR 遺漏", "NFR 模糊", "Traceability 不完整"]
        }
    },
    2: {
        "A": {
            "role": "architect",
            "task": "制定系統架構",
            "prompt": """
【On Demand 讀取】
- SRS.md（只讀 FR 需求和介面）
- 任務初始化提示

【產出】
- SAD.md：系統架構文件
- ADR.md：架構決策記錄

【驗證】
- 每個 FR 有對應的 Module
- SAD↔SRS 一致性 100%
            """,
            "forbidden": ["偏離 SRS", "模組邊界模糊"]
        },
        "B": {
            "role": "reviewer",
            "task": "審查系統架構",
            "verify": """
1. SAD↔SRS 一致性 =100%
2. 每個 Module 有明確職責
3. ADR 記錄關鍵決策
4. Constitution SAD ≥80%
            """,
            "reject_if": ["SRS↔SAD 不一致", "Module 職責重疊"]
        }
    },
    # ... phases 3-8 follow same pattern
}
```

---

## 面向 5：子代理管理優化

### 現況問題

- SubagentIsolator.spawn() 有內建 log
- 但沒有明確的：
  - 派遣前檢查（Pre-flight）
  - 派遣後驗證
  - 失敗重試邏輯

### 改善方案

```python
# 子代理派遣標準流程
class SubagentManager:
    def spawn_with_guardrails(self, role: AgentRole, task: dict, phase: int) -> dict:
        """帶護欄的派遣流程"""
        
        # 1. Pre-flight check
        preflight = self.preflight_check(task, phase)
        if not preflight['pass']:
            return {
                'status': 'blocked',
                'reason': preflight['reason']
            }
        
        # 2. Spawn with timeout
        result = self.spawn(
            role=role,
            task_id=task['id'],
            artifact_paths=task['read'],
            timeout=task.get('timeout', 600)
        )
        
        # 3. Post-flight verification
        if result['status'] == 'completed':
            verify = self.verify_output(result, task)
            if not verify['pass']:
                return self.handle_rejection(verify)
        
        # 4. Log to sessions_spawn.log
        self.log_spawn(result)
        
        return result
    
    def preflight_check(self, task: dict, phase: int) -> dict:
        """派遣前檢查"""
        checks = []
        
        # Check 1: KnowledgeCurator coverage
        kc = KnowledgeCurator()
        coverage = kc.verify_coverage(task['fr_list'])
        checks.append(('coverage', coverage >= 0.8))
        
        # Check 2: ContextManager
        cm = ContextManager()
        if cm.count_messages() > 50:
            cm.compress()
        checks.append(('context', cm.count_messages() < 100))
        
        # Check 3: PermissionGuard
        pg = PermissionGuard()
        for op in task.get('operations', []):
            if not pg.check(op):
                return {'pass': False, 'reason': f'Permission denied: {op}'}
        
        all_pass = all(c[1] for c in checks)
        return {'pass': all_pass, 'checks': checks}
    
    def handle_rejection(self, verify: dict, max_retries=3) -> dict:
        """處理被拒絕的情況"""
        if verify.get('retry_count', 0) < max_retries:
            # Auto-retry with feedback
            return {
                'status': 'retry',
                'feedback': verify['violations']
            }
        else:
            # HR-12: >5 rounds triggers pause
            return {
                'status': 'paused',
                'reason': 'HR-12: Max retries exceeded'
            }
```

---

## 面向 6：對的工具在對的時機

### 現況問題

Section 9 有工具調用時機，但：
- 只是靜態描述
- 沒有動態觸發
- 沒有錯誤處理

### 改善方案

```python
# 動態工具觸發器
class ToolDispatcher:
    """根據上下文自動觸發正確的工具"""
    
    def on_spawn(self, role: AgentRole, task_id: str):
        """派遣時觸發"""
        # SubagentIsolator 派遣
        si = SubagentIsolator()
        si.log_spawn(role, task_id, 'PENDING')
        
        # SessionManager save
        sm = SessionManager()
        sm.save(f"task_{task_id}", {
            'role': role,
            'task_id': task_id,
            'timestamp': datetime.now(),
            'phase': self.current_phase
        })
    
    def on_message(self, message_count: int):
        """訊息計數變化時觸發"""
        # ContextManager 壓縮
        if message_count > 50:
            cm = ContextManager()
            cm.compress_if_needed()
        
        # 100 -> L2 摘要
        if message_count > 100:
            cm = ContextManager()
            cm.extract_key_info()
        
        # 200 -> L3 存檔
        if message_count > 200:
            cm = ContextManager()
            cm.archive_and_new()
    
    def on_error(self, error: Exception):
        """錯誤發生時觸發"""
        # PermissionGuard 阻擋
        if isinstance(error, PermissionError):
            pg = PermissionGuard()
            pg.alert(f'Unauthorized: {error}')
        
        # 錯誤分類
        classifier = ErrorClassifier()
        level = classifier.classify(error)
        
        if level >= 3:
            # L3+ 錯誤：降級 + 上報
            self.degrade_and_report(error)
    
    def on_complete(self, task_id: str, result: dict):
        """任務完成時觸發"""
        # 驗證輸出
        if result.get('confidence', 0) < 6:
            # Auto-retry
            self.spawn_with_guardrails(
                role=result['role'],
                task={'id': task_id},
                phase=self.current_phase
            )
        
        # Log completion
        si = SubagentIsolator()
        si.log_spawn(result['role'], task_id, 'COMPLETED')
        
        # KnowledgeCurator 更新
        kc = KnowledgeCurator()
        kc.update(result)
```

---

## 面向 7：迭代修復處理

### 現況問題

HR-12（5 輪限制）只有警告，沒有：
- 自動追蹤輪數
- 到達限制時的明確流程
- 修復歷史記錄

### 改善方案

```python
# 迭代修復管理
class IterationManager:
    """管理迭代修復流程"""
    
    def __init__(self, phase: int, fr: str):
        self.phase = phase
        self.fr = fr
        self.iterations_file = Path(f".methodology/iterations/phase{phase}.json")
        self.history = self.load_history()
    
    def load_history(self) -> list:
        """載入迭代歷史"""
        if self.iterations_file.exists():
            return json.loads(self.iterations_file.read_text())
        return []
    
    def add_attempt(self, attempt: dict):
        """記錄一次嘗試"""
        attempt['timestamp'] = datetime.now().isoformat()
        attempt['round'] = len(self.history) + 1
        
        self.history.append(attempt)
        self.save()
        
        # Check HR-12
        if attempt['round'] >= 5:
            self.trigger_hr12_pause()
    
    def trigger_hr12_pause(self):
        """HR-12 觸發：5 輪後暫停"""
        fsm = FSMStateMachine()
        fsm.transition_to('PAUSED', reason='HR-12: Max iterations exceeded')
        
        # 通知
        self.notify(f"Phase {self.phase} {self.fr} 已達 5 輪限制，請人工介入")
    
    def get_repair_suggestions(self) -> list:
        """基於歷史生成修復建議"""
        violations = []
        for attempt in self.history:
            if attempt.get('status') == 'rejected':
                violations.extend(attempt.get('violations', []))
        
        # 統計最常見的問題
        from collections import Counter
        counter = Counter(violations)
        
        return [
            f"常見問題：{violation}（{count}次）"
            for violation, count in counter.most_common(3)
        ]
    
    def repair_flow(self) -> str:
        """生成修復流程"""
        suggestions = self.get_repair_suggestions()
        
        return f"""
## 修復流程（迭代 {len(self.history)}）

### 已嘗試 {len(self.history)} 輪，最近問題：
{suggestions}

### 修復步驟：
1. 分析上述常見問題的根本原因
2. 檢視失敗的具體 violations
3. 修復後重新提交

### HR-12 限制：
- 已嘗試：{len(self.history)}/5 輪
- 剩餘：{5 - len(self.history)} 輪

⚠️ 超過 5 輪將自動暫停（HR-12）
        """
```

---

## 實作優先順序

| 優先 | 改善項目 | 工作量 | 影響 |
|------|---------|--------|------|
| P0 | Phase-specific prompts (1-8) | 高 | 核心功能 |
| P0 | 上階段產出解析器 | 高 | 正確傳承 |
| P1 | 動態工具觸發器 | 中 | 執行正確性 |
| P1 | IterationManager | 中 | 修復效率 |
| P2 | HR-05/09 強調 | 低 | 合規性 |
| P2 | 自動化 HR-13/14 計算 | 中 | 監控完整性 |

---

## 總結

### 現況覆蓋率

| 面向 | 現況 | 目標 |
|------|------|------|
| SKILL.md 100% | 70% | 100% |
| 8 階段適用 | 12.5% (1/8) | 100% |
| 上階段產出 | 50% | 100% |
| A/B 協作 | 50% | 100% |
| 子代理管理 | 60% | 100% |
| 工具使用 | 40% | 100% |
| 迭代修復 | 50% | 100% |

### 預期產出

實作完成後：
- `plan-phase --phase N` 產生 100% 符合 SKILL.md 的 plan
- 每個 Phase 有獨立的 Developer/Reviewer Prompt
- 上階段產出自動解析並傳承
- 工具在對的時機自動觸發
- 迭代修復有完整追蹤

---

*本文件基於 Phase 3 實際問題 + 7 大面向分析*
