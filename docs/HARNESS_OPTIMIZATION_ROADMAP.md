# Harness Engineering Framework — Optimization Roadmap

> 來源：Harness Engineering Framework vs methodology-v2 深度對比分析
> 日期：2026-04-16
> 狀態：規劃中

---

## 背景

Harness Engineering Framework 是一個企業級 AI 軟體交付框架（2026-04-09），其設計理念與 methodology-v2 有高度重疊，但多了幾個重要的模組。

以下是從 Harness 移植到 methodology-v2 的具體優化方案。

---

## 深度對比：Harness vs methodology-v2

### 核心架構對照

| 維度 | Harness Engineering | methodology-v2 | 差距 |
|------|---------------------|-----------------|------|
| **生命週期** | 8 Phase（含可選 Phase 0） | 8 Phase（P0 缺失） | Harness +1 可選研究階段 |
| **Quality Gate** | 三級制（70/85/90） | 固定閾值（無分級） | **重大差距** |
| **Phase 0 研究** | ✅ 完整 4 階段（2-5天） | ❌ 完全缺失 | **重大差距** |
| **獨立 Auditor** | 4 角色 Auditor，含 binding veto | Phase 6 有 Auditor，無 veto 機制 | **中等差距** |
| **三方簽署** | Phase 7 三方 sign-off（Auditor/TL/PM） | ❌ 無明確定義 | **重大差距** |
| **Quality 維度** | 9 維度加權評分（結構化） | 9 維度但未加權 | **輕微差距** |
| **Traceability** | 完整雙向追溯矩陣 | ✅ Phase 4 專門處理 | 相當 |
| **A/B 協作** | Spec/Code A/B | ✅ Phase 1-2 雙軌 | 相當 |
| **迭代控制** | 5輪自動改進循环 | HR-12/13（未落地） | **重大差距** |
| **輕量化** | 需完整團隊 | ✅ 適合個人/小團隊 | methodology-v2 勝 |
| **自動化程度** | Phase 0-7 全腳本化 | 部分 CLI 自動化 | Harness 勝 |

---

## 9 維度 Quality 評分（已部分實現）

Harness 的 9 維度加權評分是目前最完整的程式碼品質框架。methodology-v2 的 `phase_3_dimensions.py` 已實現基礎版本：

```python
QUALITY_DIMENSIONS = {
    "linting":           {"weight": 0.10, "threshold": 80},
    "type_safety":       {"weight": 0.15, "threshold": 80},
    "test_coverage":     {"weight": 0.20, "threshold": 80},
    "security":          {"weight": 0.15, "threshold": 85},
    "performance":       {"weight": 0.10, "threshold": 75},
    "architecture":      {"weight": 0.10, "threshold": 75},
    "readability":       {"weight": 0.10, "threshold": 75},
    "error_handling":    {"weight": 0.05, "threshold": 80},
    "documentation":     {"weight": 0.05, "threshold": 70},
}

def calculate_weighted_score(scores: dict) -> float:
    """加權平均計算 Overall Score"""
    total = sum(
        scores[dim] * QUALITY_DIMENSIONS[dim]["weight"]
        for dim in QUALITY_DIMENSIONS
    )
    return round(total, 2)
```

**現狀：** 基礎結構已有，但與 Harness 的 9 維度完整度仍有差距。TH-05/06 已提升至 >90% 門檻。

---

## 實施路線圖

| 優先級 | 優化項 | 工作量 | 對應 Harness 模組 | 狀態 |
|--------|--------|--------|------------------|------|
| **P0** | Phase 0 研究機制 | 中 | Harness Phase 0 | 規劃中 |
| **P0** | Quality Level 三級制 | 小 | Harness Phase 2.5 | 規劃中 |
| **P0** | 落地 HR-12/13 追蹤 | 中 | —（純内部改進）| 規劃中 |
| **P1** | Phase 6 Auditor Veto | 小 | Harness Phase 6 | 規劃中 |
| **P1** | Phase 7 三方 Sign-Off | 小 | Harness Phase 7 | 規劃中 |
| **P1** | 9 維度加權評分 | 小 | Harness Phase 3 | 規劃中 |
| **P2** | State.json 重構 | 中 | —（純内部改進）| 規劃中 |

---

## P0: Phase 0 研究機制

### 目標
補上「知識缺口評估」階段，針對新技術或領域知識缺口做系統性調研。

### 觸發條件
- 團隊缺乏領域專業知識
- 涉及新興技術（高不確定性）
- 商業影響高，需可行性分析

### 規格

```
新增目錄：methodology-v2/phase_0_research/

phase_0_research/
├── research_directive.py      # 研究指令生成器
├── evaluation_scorer.py       # 4 維度評分（≥7.5 門檻）
├── insight_loop.py            # 3 輪迭代深化
├── dashboard_builder.py       # 研究儀表板輸出
└── README.md
```

### Stage 規格

| Stage | 輸入 | 輸出 | 閾值 |
|-------|------|------|------|
| Stage 1: Research Setup | 主題 + 商業 context | 3 bottleneck + 5 scenario | — |
| Stage 2: Evaluation | 研究產出 | 4 維度分數 | ≥7.5/10 |
| Stage 3: Insight Loop | 批評式自我檢視 | 深化 research | 3 輪 |
| Stage 4: Dashboard | 完整研究報告 | HTML 儀表板 | — |

---

## P0: Quality Level 三級制

### 目標
讓不同風險的專案有不同的品質成本

```python
QUALITY_LEVELS = {
    "STANDARD": {          # 70% 的專案
        "threshold": 70,
        "duration": "5 min",
        "checks": ["linting", "type_safety", "test_coverage", "security_baseline"],
        "auto_improve": False,
    },
    "HIGH": {              # 20% 的專案（推薦）
        "threshold": 85,
        "duration": "1-2 hrs",
        "dimensions": 9,
        "auto_improve": True,
        "max_iterations": 5,
    },
    "ENTERPRISE": {        # 10% 的專案
        "threshold": 90,
        "security_min": 95,
        "duration": "2-3 hrs",
        "dimensions": 9,
        "auto_improve": True,
        "enhanced_security": True,
    }
}
```

### CLI 新增
```bash
# 設定專案 quality level（once at initialization）
methodology project set-quality --level HIGH --reason "處理付款邏輯"

# 執行對應的 quality gate
methodology phase3 run --auto  # 根據 level 自動選擇流程
```

---

## P1: Phase 6 Auditor Veto

### 目標
新增 Auditor binding veto 機制

```python
AUDIT_ROLES = {
    "requirements_auditor": {
        "focus": "實作是否符合規格",
        "veto_authority": True,
        "checklist": ["functional_req", "acceptance_criteria", "scope_creep"]
    },
    "security_auditor": {
        "focus": "安全與合規",
        "veto_authority": True,
        "checklist": ["owasp_top10", "encryption", "hardcoded_secrets", "gdpr"]
    },
    "performance_auditor": {
        "focus": "效能與 UX",
        "veto_authority": True,
        "checklist": ["response_time", "load_test", "wcag"]
    },
    "business_value_auditor": {
        "focus": "商業價值與策略",
        "veto_authority": False,  # 商業 auditor 無 veto
        "checklist": ["roi", "stakeholder", "maintainability"]
    }
}
```

### 新增 Artifact（Phase 6 Audit Report）
```markdown
## Auditor Sign-Off Section（含否決權聲明）
### Requirements Auditor
**Authority:** BINDING VETO - Can block release unilaterally
**Sign:** _______________
**Decision:** [ APPROVED / REJECTED / CONDITIONAL ]
```

---

## P1: Phase 7 三方 Sign-Off

### 目標
建立正式的發布治理流程

```python
class ThreePartySignOff:
    REQUIRED_SIGNATURES = [
        {
            "role": "Independent Auditor",
            "authority": "VETO",  # binding - 可單方阻擋
            "can_override": False,
        },
        {
            "role": "Tech Lead",
            "authority": "QUALITY_OWNER",
            "can_override": False,
        },
        {
            "role": "Product Manager",
            "authority": "BUSINESS_OWNER",
            "can_override": False,
        }
    ]
```

### 新增 Artifact
```
RELEASE_SIGN_OFF.md
├── Auditor Sign-Off（VETO 權力）
├── Tech Lead Sign-Off
├── PM Sign-Off
├── Final Decision（APPROVED/REJECTED）
└── Deployment Record
```

---

## 核心差異總結

| 問題 | Harness 怎麼做 | methodology-v2 應該怎麼做 |
|------|---------------|------------------------|
| 知識缺口？ | Phase 0 專門研究 | 新增 phase_0_research/ |
| 品質成本不成比例？ | 三級制（70/85/90）| 新增 `--quality-level` flag |
| Auditor 太弱？ | Binding Veto | Phase 6 新增否決權欄位 |
| 發布缺乏治理？ | 三方 Sign-Off | Phase 7 新增 sign_off.md |
| HR-12/13 是空殼？ | 全腳本追蹤 | 落地 iterations/ 目錄 |
| Quality 維度太主觀？ | 9 維度加權計算 | 結構化 scoring 函數 |

---

*最後更新：2026-04-16*
