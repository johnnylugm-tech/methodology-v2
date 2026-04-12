# CLI 指令參考

> **版本**: v6.09.0  
> **用途**: 快速查詢所有可用指令

---

## 1. Phase 驗證指令

### phase-verify（Johnny 必用）

```bash
# 基本用法
python cli.py phase-verify --phase N

# 指定專案目錄
python cli.py phase-verify --phase 3 --project /path/to/project

# 查看幫助
python cli.py phase-verify --help
```

**輸出範例**：
```
============================================================
Phase 3 真相驗證
============================================================

✅ FrameworkEnforcer BLOCK        6 項檢查, 6 項通過
✅ Sessions_spawn.log             10 筆記錄, 2 個角色
✅ pytest 實際通過                    全部通過
✅ 測試覆蓋率達標                        85%

============================================================
總分：95% - ✅ 可能真實
============================================================

【需要 Johnny 手動確認】
1. [03-implementation/src/]
   → 隨機選 1 處，確認內容不是空洞的 template
```

---

### stage-pass

```bash
# 生成 STAGE_PASS.md
python cli.py stage-pass --phase 3

# 指定專案目錄
python cli.py stage-pass --phase 3 --project /path/to/project

# 跳過 Git 推送
python cli.py stage-pass --phase 3 --no-git
```

---

## 2. Framework 檢查指令

### enforce (FrameworkEnforcer BLOCK)

```bash
# 執行 BLOCK 等級檢查
python cli.py enforce --level BLOCK

# 執行 WARN 等級檢查
python cli.py enforce --level WARN

# 執行 ALL 等級檢查
python cli.py enforce --level ALL

# 查看詳細輸出
python cli.py enforce --level BLOCK --verbose
```

**BLOCK 檢查項目**：
| 檢查 | 門檻 |
|------|------|
| SPEC_TRACKING | ≥90% |
| CONSTITUTION_SCORE | ≥60 |
| ASPICE_PHASE_TRACE | 完整 |
| ASPICE_COMPLETE | 100% |
| COVERAGE_THRESHOLD | ≥70% |
| TRACEABILITY_COMPLETE | 完整 |

---

## 3. Constitution 檢查

```bash
# 檢查所有 Constitution
python quality_gate/constitution/runner.py

# 檢查特定類型
python quality_gate/constitution/runner.py --type srs
python quality_gate/constitution/runner.py --type sad
python quality_gate/constitution/runner.py --type test_plan

# 查看幫助
python quality_gate/constitution/runner.py --help
```

---

## 4. Claims 驗證

```bash
# 驗證所有 Claims
python -c "from quality_gate.claims_verifier import ClaimsVerifier; \
  print(ClaimsVerifier('.').verify_all())"

# 驗證 sessions_spawn.log
python -c "from quality_gate.claims_verifier import ClaimsVerifier; \
  print(ClaimsVerifier('.').verify_sessions_spawn_log())"

# 驗證 sub-agent 使用
python -c "from quality_gate.claims_verifier import ClaimsVerifier; \
  print(ClaimsVerifier('.').verify_subagent_usage())"
```

---

## 5. A/B Enforcer

```bash
# 執行 A/B 分離檢查
python -c "from quality_gate.ab_enforcer import ABEnforcer; \
  print(ABEnforcer('.').verify_ab_separation())"

# 執行 A/B 對話檢查
python -c "from quality_gate.ab_enforcer import ABEnforcer; \
  print(ABEnforcer('.').verify_dialogue())"

# 執行 QA ≠ Developer 檢查
python -c "from quality_gate.ab_enforcer import ABEnforcer; \
  print(ABEnforcer('.').verify_roles())"
```

---

## 6. Integrity Tracker

```bash
# 查看 Integrity Score
python -c "from quality_gate.integrity_tracker import IntegrityTracker; \
  tracker = IntegrityTracker('.'); \
  print(f'Score: {tracker.calculate_score()}')"

# 記錄作假行為
python -c "from quality_gate.integrity_tracker import IntegrityTracker; \
  tracker = IntegrityTracker('.'); \
  tracker.record_fake_qg(); \
  print(f'New Score: {tracker.calculate_score()}')"

# 記錄 skip phase
python -c "from quality_gate.integrity_tracker import IntegrityTracker; \
  tracker = IntegrityTracker('.'); \
  tracker.record_skip_phase(); \
  print(f'New Score: {tracker.calculate_score()}')"
```

---

## 7. Phase Artifact Enforcer

```bash
# 檢查 Phase N 的產出物
python quality_gate/phase_artifact_enforcer.py --phase 3

# 檢查所有 Phase
python quality_gate/phase_artifact_enforcer.py --all

# 嚴格模式
python quality_gate/phase_artifact_enforcer.py --phase 3 --strict
```

---

## 8. Spec Tracking

```bash
# 檢查規格追蹤
python cli.py spec-track check

# 初始化規格追蹤
python cli.py spec-track init

# 查看追蹤報告
python cli.py spec-track report
```

---

## 9. Ralph Mode

```bash
# 進入 Ralph Mode
python cli.py ralph --mode supervisor

# 查看可用模式
python cli.py ralph --list

# 執行特定命令
python cli.py ralph --execute "check quality"
```

---

## 10. 常用組合指令

### 每日驗證（Johnny）

```bash
# Phase N 完整驗證
python cli.py phase-verify --phase N

# 如果分數 < 70%，進一步檢查
python cli.py enforce --level BLOCK
```

### Agent 開發時

```bash
# 每次提交前執行
python cli.py enforce --level BLOCK
python cli.py phase-verify --phase CURRENT

# 如果 BLOCK 通過，生成 STAGE_PASS
python cli.py stage-pass --phase CURRENT
```

### 緊急情況

```bash
# 快速檢查所有關鍵指標
python cli.py enforce --level BLOCK

# 如果有問題，查看詳細
python -c "from enforcement.framework_enforcer import FrameworkEnforcer; \
  enforcer = FrameworkEnforcer('.'); \
  result = enforcer.run(level='BLOCK'); \
  for name, passed in result.block_checks.items(): \
    print(f'{name}: {passed}')"

# 查看 Integrity
python -c "from quality_gate.integrity_tracker import IntegrityTracker; \
  print(IntegrityTracker('.').generate_report())"
```

---

## 11. 指令速查表

| 指令 | 用途 | 使用者 |
|------|------|--------|
| `phase-verify --phase N` | 驗證 Phase N 真實性 | Johnny |
| `stage-pass --phase N` | 生成 Phase N STAGE_PASS | Agent |
| `enforce --level BLOCK` | 執行 BLOCK 檢查 | Agent |
| `constitution/runner.py` | Constitution 檢查 | Agent |
| `claims_verifier` | Claims 驗證 | Agent |
| `ab_enforcer` | A/B 分離驗證 | Agent |
| `integrity_tracker` | 誠信追蹤 | Johnny |
| `spec-track check` | 規格追蹤檢查 | Agent |
| `ralph --mode` | Ralph Mode | Agent |

---

## 12. 退出碼

| 退出碼 | 意義 |
|--------|------|
| 0 | 檢查通過 |
| 1 | 檢查失敗 |
| 2 | 錯誤（請查看錯誤訊息） |

---

## 13. 環境變數

```bash
# 指定專案路徑
export METHODOLOGY_PROJECT_ROOT=/path/to/project

# 指定日誌層級
export METHODOLOGY_LOG_LEVEL=DEBUG

# 跳過確認提示
export METHODOLOGY_NO_CONFIRM=1
```

---

---

## 14. Traceability 驗證（需求可追溯性）

### 使用 requirement_traceability.py

```bash
# 驗證完整性
python -m methodology-v2.requirement_traceability \
    --project-id my-project \
    --verify

# 匯出報告
python -m methodology-v2.requirement_traceability \
    --project-id my-project \
    --export traceability_report.json \
    --format aspice
```

### CLI 整合（透過 enforce）

```bash
# 執行 enforcement 並生成 ASPICE traceability 報告
python cli.py enforce --project . --aspice-report
```

### Phase 整合

| Phase | Traceability 驗證 |
|-------|-------------------|
| Phase 1 | FR→SRS 映射（TH-13）|
| Phase 2 | SAD↔Code 映射（TH-16）|
| Phase 3 | FR→Code 映射 |
| Phase 4 | FR↔Test 映射（TH-17）|
| Phase 5 | Quality→Test 連結 |
| Phase 6 | Quality→Audit 連結 |

### 驗證輸出範例

```json
{
  "project_id": "my-project",
  "total_requirements": 9,
  "frs_with_srs_mapping": 9,
  "frs_with_code_implementation": 9,
  "frs_with_test_coverage": 9,
  "srs_coverage": "100.0%",
  "code_coverage": "100.0%",
  "test_coverage": "100.0%",
  "verification_rate": "85.0%",
  "overall_completeness": "95.0%"
}
```

### ASPICE 合規報告

```bash
python -m methodology-v2.requirement_traceability \
    --project-id my-project \
    --verify \
    --format aspice \
    --export aspice_report.json
```

---

## 15. FR Quality 檢查腳本（v7.43-v7.56）

### check_fr_quality.py - FR 快速檢查

```bash
# 單次檢查
python scripts/check_fr_quality.py --fr FR-01 --project /path/to/project

# 迭代檢查
python scripts/check_fr_quality.py --fr FR-01 --project /path/to/project --loop
```

**用途**：每個 FR 完成後，快速檢查 Syntax + Import

---

### check_fr_full.py - FR 完整檢查

```bash
# 完整檢查（三層）
python scripts/check_fr_full.py --fr FR-01 --project /path/to/project --loop

# 只做 Layer 1
python scripts/check_fr_full.py --fr FR-01 --project /path --skip-constitution --skip-cqg
```

**三層檢查**：
| Layer | 檢查 | 時間 |
|-------|------|------|
| Layer 1 | Syntax + Import | ~30秒 |
| Layer 2 | Constitution (BVS + HR-09) | ~1分鐘 |
| Layer 3 | CQG (Linter + Complexity) | ~1分鐘 |

---

## 16. FR Mapping 腳本（v7.49-v7.51）

### generate_fr_mapping.py

```bash
python scripts/generate_fr_mapping.py --project /path/to/project
```

**產出**：`.methodology/fr_mapping.json`

**掃描策略**：FR Tag 解析 > Keyword 匹配

---

## 17. SAB 生成腳本（v7.47-v7.48）

### generate_sab.py

```bash
python scripts/generate_sab.py --project /path/to/project
```

**產出**：`.methodology/SAB.json`

---

## 18. Phase Prerequisite Checker（v7.57-v7.60）

### phase_prerequisite_checker.py

```bash
python -m quality_gate.constitution.runner --check-prerequisites --current-phase 3 --path /path -v
```

**用途**：Phase N 執行前，檢查 Phase (N-1) 產出是否 Ready

**前置產出表**：

| Phase | 前置產出 | 路徑 |
|-------|---------|------|
| 2 | SRS.md | `01-requirements/SRS.md` |
| 3 | SAD.md, fr_mapping.json | `02-architecture/SAD.md`, `.methodology/fr_mapping.json` |
| 4 | SAB.json | `.methodology/SAB.json` |
| 5 | TEST_PLAN.md | `04-testing/TEST_PLAN.md` |
| 6 | BASELINE.md | `05-baseline/BASELINE.md` |

---

*最後更新: 2026-04-12*
