# Human-Agent 互動流程

> **版本**: v6.09.0  
> **目標**: 確保 100% 落實 SKILL.md 規範  
> **核心原則**: Human-in-the-Loop (HITL) + AI 防作假機制

---

## 1. 總體流程架構

```
┌─────────────────────────────────────────────────────────────────┐
│                    8 Phase 開發流程                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──►              │
│   需求      架構      代碼      測試                            │
│     │        │        │        │                               │
│     ▼        ▼        ▼        ▼                               │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                         │
│  │BLOCK │ │BLOCK │ │BLOCK │ │BLOCK │                         │
│  │check │ │check │ │check │ │check │                         │
│  └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘                         │
│     │        │        │        │                               │
│     ▼        ▼        ▼        ▼                               │
│  ┌─────────────────────────────────┐                           │
│  │     Johnny HITL 審核介入        │                           │
│  │  (phase-verify --phase N)       │                           │
│  └─────────────────────────────────┘                           │
│              │                                                 │
│     ┌────────┴────────┐                                        │
│     ▼                 ▼                                        │
│  ✅ CONFIRM      ❌ REJECT                                    │
│     │                 │                                         │
│     ▼                 ▼                                         │
│  下一 Phase    Agent 重新執行                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 每 Phase 標準互動流程

### Phase N 開始時

```
1. Agent: 接收 Phase N 任務
2. Agent: 使用對應 Prompt Template 執行工作
3. Agent: 呼叫 sessions_spawn 啟動 A/B 協作
4. Agent: 執行 FrameworkEnforcer BLOCK 檢查
5. Agent: 生成 STAGE_PASS.md
6. Agent: 推送到 GitHub
7. 【HITL 介入】Johnny: 執行 phase-verify --phase N
8. Johnny: 根據清單確認內容
9. Johnny: 給出 CONFIRM / QUERY / REJECT
```

---

## 3. HITL 介入點說明

### Johnny 的三種回應

| 回應 | 意義 | 動作 |
|------|------|------|
| `CONFIRM` | 通過 | 進入下一 Phase |
| `QUERY` | 有疑問 | Agent 必須回答問題 |
| `REJECT` | 不通過 | Agent 回到 Phase 重新執行 |

### Johnny 審核責任

Johnny 不需要懂技術細節，只需要：

1. **執行驗證指令**：`python cli.py phase-verify --phase N`
2. **查看自動檢查結果**：分數 ≥70% 即可能真實
3. **抽查關鍵產出**：根據清單選 1-2 項確認
4. **問「為什麼」**：對可疑內容追問

---

## 4. 每 Phase Johnny 必檢清單

### Phase 1: 需求規格

| # | 檢查項目 | 操作 |
|---|----------|------|
| 1 | SRS.md 存在 | 確認 `01-requirements/SRS.md` 存在 |
| 2 | FR 追蹤 | 隨機抽 3 條 FR，確認有邏輯驗證方法 |
| 3 | SPEC_TRACKING | 確認 `SPEC_TRACKING.md` 有實際內容 |
| 4 | sessions_spawn.log | 確認有 A/B 兩個角色的記錄 |

### Phase 2: 架構設計

| # | 檢查項目 | 操作 |
|---|----------|------|
| 1 | SAD.md 存在 | 確認 `02-architecture/SAD.md` 存在 |
| 2 | 模組邊界 | 查看模組圖，確認邊界合理 |
| 3 | 衝突記錄 | 確認有 `CONFLICT_LOG.md` 或衝突已解決 |
| 4 | sessions_spawn.log | 確認有 A/B 審查記錄 |

### Phase 3: 代碼實現

| # | 檢查項目 | 操作 |
|---|----------|------|
| 1 | 代碼存在 | 確認 `03-implementation/src/` 有實際代碼 |
| 2 | 測試存在 | 確認 `03-implementation/tests/` 有測試 |
| 3 | pytest 通過 | 執行 `pytest` 確認全部通過 |
| 4 | 覆蓋率 | 執行 `pytest --cov` 確認 ≥70% |

### Phase 4: 測試

| # | 檢查項目 | 操作 |
|---|----------|------|
| 1 | TEST_PLAN.md | 確認有測試策略和 TC 清單 |
| 2 | TEST_RESULTS.md | 確認有 pytest 實際輸出（非截圖） |
| 3 | 失敗案例 | 確認失敗案例有根本原因分析 |
| 4 | sessions_spawn.log | 確認 QA ≠ Developer |

### Phase 5: 驗收與交付

| # | 檢查項目 | 操作 |
|---|----------|------|
| 1 | BASELINE.md | 確認功能對照表完整 |
| 2 | 驗收通過 | 確認所有 P0 功能 ✅ |
| 3 | MONITORING_PLAN | 確認有監控計畫 |
| 4 | sessions_spawn.log | 確認 DevOps + Architect 參與 |

### Phase 6: 品質保證

| # | 檢查項目 | 操作 |
|---|----------|------|
| 1 | QUALITY_REPORT.md | 確認有 7 章節 |
| 2 | 根源分析 | 確認問題根源到 Layer 3 |
| 3 | 改進建議 | 確認有 P0/P1/P2 建議 |
| 4 | sessions_spawn.log | 確認 QA + Architect 參與 |

### Phase 7: 風險評估

| # | 檢查項目 | 操作 |
|---|----------|------|
| 1 | RISK_REGISTER.md | 確認有 HIGH/MEDIUM 風險 |
| 2 | 演練記錄 | 確認至少 1 個演練 |
| 3 | 緩解措施 | 確認每個風險有 4 層緩解 |
| 4 | sessions_spawn.log | 確認有悲觀視角的 Agent A |

### Phase 8: 配置管理

| # | 檢查項目 | 操作 |
|---|----------|------|
| 1 | CONFIG_RECORDS.md | 確認有 8 章節 |
| 2 | pip freeze | 確認有實際依賴清單 |
| 3 | Git Tag | 確認有 `v[version]` tag |
| 4 | 回滾 SOP | 確認有回滾步驟 |

---

## 5. 防作假機制

### 技術防線

| 機制 | 作用 |
|------|------|
| FrameworkEnforcer BLOCK | 結構性檢查，沒有通過不能繼續 |
| sessions_spawn.log | 記錄 A/B 協作事實 |
| Claims Verifier | 驗證聲稱的 A/B 使用是否屬實 |
| Phase Truth Verifier | 計算真實性分數 |

### Human 防線

| 機制 | 作用 |
|------|------|
| Johnny 審核 | 外部視角，Agent 無法控制 |
| 隨機抽查 | 不可預測，Agent 無法針對 |
| 追問「為什麼」 | 深入理解，發現表面下的問題 |

---

## 6. CLI 指令速查

```bash
# Phase 真相驗證（Johnny 必執行）
python cli.py phase-verify --phase N

# Framework BLOCK 檢查
python cli.py enforce --level BLOCK

# STAGE_PASS 生成
python cli.py stage-pass --phase N

# Constitution 檢查
python quality_gate/constitution/runner.py --type srs

# Claims 驗證
python -c "from quality_gate.claims_verifier import ClaimsVerifier; \
  print(ClaimsVerifier('.').verify_all())"
```

---

## 7. 緊急情況處理

### 發現作假

```
1. Johnny 執行 phase-verify --phase N
2. 分數 < 50%，高度可疑
3. Johnny 詢問：「這個測試失敗是什麼原因？」
4. 如果 Agent 回答模糊或矛盾
5. Johnny: REJECT
6. 記錄到 MEMORY.md
7. 累計 3 次，停止該 Agent 接任務
```

### Agent 跳過 Phase

```
1. 如果 Agent 聲稱完成 Phase N 但：
   - phase-verify 分數極低
   - 缺少必要的產出物
2. Johnny: REJECT
3. Agent: 回到 Phase N-1 重新開始
```

---

*最後更新: 2026-03-31*
