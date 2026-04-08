# P3 系列深度整合報告：Change Management × TCO Calculator × Onboarding Checklist

整理：Musk Agent | 日期：2026-04-08
適用版本：methodology-v2 v6.74

---

## Executive Summary：三個提案的核心診斷

| 提案 | 真正問題 | 核心方向 | 優先級 |
|------|---------|----------|--------|
| P3-1 Change Management | 對錯了受眾（高管而非工程師）| 重寫為「技術價值主張」| 🟡 P2 |
| P3-2 TCO Calculator | 數字全為幻覺，會害人做錯誤決策 | 改為「情境模擬器」，接入真實數據 | 🔴 P1（不做會害人）|
| P3-3 Onboarding Checklist | 引用不存在的資源，Certification 多餘 | 重寫為「互動式自助嚮導」| 🟢 P0（最值得做）|

---

## P3-1｜重寫：Technical Value Proposition Kit（技術價值主張工具包）

### 現有方案的問題

- 受眾錯誤：Engineer 不需要 Change Management，需要「這個東西能幫我解決什麼問題」
- 語言錯誤：「變革管理」「阻力識別」是 HR 語言，不是工程師語言
- 數字空洞：「採用率 +40%」無從驗證

### 重寫方向：Adoption Playbook for Engineers

**核心命題重構**：
```
不是「如何推動組織接受 methodology-v2」
而是「一個工程師，在忙碌的日常中，為什麼要多學這套東西？」

答案不是「品質會提升」
答案是「你今天浪費的時間會變少」
```

### 落地架構

```
adoption/
├── VALUE_PROPOSITION.md      # 30-second pitch for engineers
├── QUICK_WINS.md             # 3 things you can do today
├── CASE_STUDIES/
│   └── real_cases.json       # 來自 FeedbackStore 的真實數據
├── ROI_CALCULATOR/
│   └── scenario_model.py     # 接 FeedbackStore 的情境模擬
└── INTEGRATION_GUIDE.md     # 如何在現有工具鏈中嵌入
```

### VALUE_PROPOSITION.md 核心內容

```markdown
# 30秒版本

**你的問題**：
→ Code review 發現問題時，已經太晚了
→ 等到 QA 測出 Bug，已經來不及了
→ Architecture drift 了三個月才發現

**methodology-v2 解決什麼**：
→ Quality Gate 在你寫 Code 的當下就告訴你問題在哪裡
→ Drift Monitor 在 Phase-Gate 就發現偏離
→ Feedback Loop 讓每一個問題都有追蹤、不會遺漏

**代價**：
→ 每個 Sprint 多花 15 分鐘執行 Quality Gate check
→ 第一個月多投入 2 小時設定 Threshold

**回報**：
→ 你自己告訴我：過去三個月你浪費了多少時間在「後期才發現的問題」上？
```

### 整合點

| 現有模組 | 接入方式 |
|----------|----------|
| FeedbackStore | 讀取真實 defect-reduction 案例 |
| Quality Gate | 展示「早期發現」vs「晚期發現」的成本差異 |
| Drift Monitor | 展示「及時發現」vs「慢性 drift」的維修成本 |

### 量化基準建立方法

```python
# 測量當前狀態（第一件事）
def measure_current_state(project_path):
    """從 Git history + issue tracker 計算："""
    # 1. 從 PR review comment 計算「後期發現」的比例
    # 2. 從 bug assignee 計算「上線後才發現」的比率
    # 3. 從 commit message 計算 drift 是否被及時發現
    
    return {
        "late_detection_rate": 0.42,  # 42% 的問題在 code review 後才發現
        "production_bug_rate": 0.15,  # 15% 的問題上線後才爆
        "drift_detection_time": "3 months average",
    }
```

### 執行步驟

1. **Week 1**：建立 `measure_current_state()` 函式，從 Johnny 自己的專案取數據
2. **Week 2**：撰寫 `VALUE_PROPOSITION.md` + `QUICK_WINS.md`
3. **Week 3**：建立 `CASE_STUDIES/real_cases.json`，從 FeedbackStore 結構化輸出
4. **Week 4**：寫 `INTEGRATION_GUIDE.md`，對接 GitHub Actions / Slack

---

## P3-2｜重寫：Scenario Model（情境模擬器，非 ROI 計算機）

### 現有方案的問題

- **所有數字都是假設**：做出來會害人拿假的數字去做 business case
- **會被用來說服管理層**：最危險的場景——用虛構數字換取真實資源
- **迴避了核心問題**：沒有回答「這些數字從哪裡來」

### 重寫方向：Scenario Model

**核心重構**：
```
不是「讓我告訴你 ROI 是多少」
而是「讓我幫你估算在不同假設下可能發生的成本與收益」

每一個數字都必須有「你的輸入是什麼」和「這個數字來自哪裡」兩個標記
```

### 落地架構

```
tools/
├── scenario_model.py          # 情境模擬引擎
├── data_sources.py            # 從哪裡取真實數據
├── templates/
│   └── scenario_report.md      # 輸出格式
└── validators/
    └── claim_validator.py     # 檢查每個假設是否有依據
```

### 核心程式碼（修復版）

```python
# tools/scenario_model.py
class ScenarioModel:
    """
    情境模擬器：給定不同假設，計算範圍區間。
    每個數字都必須標記來源：user_input / historical_data / assumption。
    """
    
    def __init__(self, project_path: str, feedback_store=None):
        self.project_path = project_path
        self.feedback_store = feedback_store
        self._validate_data_sources()
    
    def _validate_data_sources(self):
        """檢查有多少數字來自真實數據"""
        self.data_availability = {
            "historical_defects": self._get_from_feedback("defect_count") is not None,
            "historical_efficiency": self._get_from_history() is not None,
            "team_size": True,  # 用戶一定知道團隊人數
            "hourly_rate": "user_input",  # 用戶輸入
        }
    
    def calculate(self, user_inputs: dict, scenarios: dict) -> dict:
        """
        user_inputs: 用戶已知的數字（團隊人數、時薪、目前問題數量）
        scenarios: 不同情境（conservative / moderate / optimistic）
        
        返回包含 source_tag 的結果：每個數字都標明來源
        """
        results = {}
        for name, params in scenarios.items():
            calc = self._calc_scenario(user_inputs, params)
            calc["_source_tags"] = self._tag_sources(params)
            results[name] = calc
        
        return results
    
    def _tag_sources(self, params: dict) -> dict:
        """為每個參數標記來源"""
        tags = {}
        for key, value in params.items():
            if key in self.data_availability and self.data_availability[key]:
                tags[key] = "historical_data"
            elif key in ["hourly_rate", "team_size"]:
                tags[key] = "user_input"
            else:
                tags[key] = "assumption"  # ← 必須是 assumption，不能是 fact
        return tags
    
    def generate_report(self, results: dict) -> str:
        """輸出帶有 source tag 的報告"""
        report = []
        for scenario, data in results.items():
            report.append(f"\n## {scenario.upper()} Scenario")
            report.append(f"(confidence: {self._calc_confidence(data['_source_tags'])})")
            
            for key, value in data.items():
                if key.startswith("_"):
                    continue
                source = data["_source_tags"].get(key, "unknown")
                report.append(f"- {key}: {value} [source: {source}]")
        
        report.append("\n⚠️ 這個報告包含假設，請自行驗證每個 [source: assumption] 的數字")
        return "\n".join(report)
    
    def _calc_confidence(self, source_tags: dict) -> str:
        assumptions = sum(1 for v in source_tags.values() if v == "assumption")
        if assumptions == 0:
            return "HIGH (all data from historical)"
        elif assumptions <= 2:
            return "MEDIUM (few assumptions)"
        else:
            return "LOW (mostly assumptions — validate before use)"
```

### 關鍵設計原則

1. **移除「計算確定值」的能力**：不給你一個數字，只給你範圍區間
2. **每個數字都有 source tag**：historical_data / user_input / assumption，絕不混淆
3. **輸出自帶警告**：每份報告都有「請驗證assumption」的 disclaimer
4. **Confidence Score**：自動計算這份報告的可信度

### 接入現有系統

```python
# 從 FeedbackStore 取真實數據
def _get_defect_reduction(self) -> float | None:
    """從 FeedbackStore 讀取實際的 defect 減少數據"""
    if self.feedback_store is None:
        return None
    
    # 讀取 Closed feedback 中 source=quality_gate 的記錄
    closed = self.feedback_store.get_by_status("verified")
    quality_feedback = [f for f in closed if f.source == "quality_gate"]
    
    if len(quality_feedback) >= 3:  # 至少3個數據點才有統計意義
        # 計算平均解決時間
        return sum(f.resolution_time_hours for f in quality_feedback) / len(quality_feedback)
    return None  # 數據不足
```

### 執行步驟

1. **Week 1**：建立 `scenario_model.py`，移除虛構數字，加入 source tagging
2. **Week 2**：建立 `data_sources.py`，對接 FeedbackStore
3. **Week 3**：建立 `templates/scenario_report.md`，設計輸出格式
4. **Week 4**：建立 `validators/claim_validator.py`，檢查假設是否被驗證

---

## P3-3｜重寫：Interactive Onboarding Wizard（互動式入職嚮導）

### 現有方案的問題

- 引用大量不存在的文件（Video、IMPROVEMENT_OVERVIEW.md）
- Certification 多餘且不受工程師歡迎
- Role-based sign-off 適合大企業，不適合開源工具
- 沒有互動性，只是靜態 checklist

### 重寫方向：CLI-based Interactive Wizard

**核心重構**：
```
不是「閱讀這個文件並打勾」
而是「執行這個命令，我帶你走過第一個 Phase」

目標：30分鐘內，工程師可以完成第一個真实的 Phase-gate workflow
```

### 落地架構

```
onboarding/
├── wizard.py                  # 互動式 CLI 向導
├── checkpoints/
│   ├── phase1.yaml           # Phase 1 的檢查點
│   ├── phase2.yaml
│   └── phase3.yaml
├── resources/
│   ├── QUICK_START.md         # 真正的快速入門（存在！）
│   └── TOOL_REFERENCE.md      # CLI 工具索引
└── progress/
    └── state.json             # 追蹤用戶進度
```

### 核心程式碼

```python
# onboarding/wizard.py
import sys
import click
from pathlib import Path

@click.command()
@click.option("--project", "-p", default=".", help="專案路徑")
@click.option("--phase", default=1, help="從哪個 Phase 開始")
def onboarding_wizard(project: str, phase: int):
    """互動式 Onboarding 向導：帶你走過第一個 Phase"""
    
    project_path = Path(project).resolve()
    
    # 讀取進度（如果有的話）
    progress_file = project_path / ".methodology" / "onboarding_progress.json"
    progress = _load_progress(progress_file)
    
    # 顯示當前狀態
    click.echo(f"\n🔄 methodology-v2 Onboarding Wizard")
    click.echo(f"   Project: {project_path.name}")
    click.echo(f"   Current phase: {phase}")
    click.echo(f"   Progress: {_render_progress(progress)}")
    
    # Phase 1 檢查點
    if phase <= 1:
        _run_phase1_checkpoints(project_path, progress)
    
    # Phase 2 檢查點
    if phase <= 2:
        _run_phase2_checkpoints(project_path, progress)
    
    # 完成
    _save_progress(progress_file, progress)
    _render_completion_message(progress)


def _run_phase1_checkpoints(project_path: Path, progress: dict):
    """Phase 1 檢查點"""
    
    checkpoints = [
        ("初始化專案結構", _check_project_structure),
        ("執行 Quality Gate check", _check_quality_gate),
        ("建立第一個 artifact (SRS.md)", _check_srs_generated),
        ("執行 Constitution check", _check_constitution),
    ]
    
    click.echo("\n📋 Phase 1 Checkpoints:")
    
    for i, (name, check_fn) in enumerate(checkpoints, 1):
        status = check_fn(project_path)
        progress[f"phase1_{i}"] = status
        
        icon = "✅" if status else "❌"
        click.echo(f"  {icon} {i}. {name}")
        
        if not status:
            click.echo(f"     提示：{_get_hint(name)}")


def _run_phase2_checkpoints(project_path: Path, progress: dict):
    """Phase 2 檢查點"""
    # ... 類似結構
```

### 與現有工具鏈的整合

```python
# 實際呼叫現有的 CLI 工具
def _check_quality_gate(project_path: Path) -> bool:
    """執行真實的 Quality Gate check"""
    import subprocess
    result = subprocess.run(
        ["python", "cli.py", "quality-gate", "check", "--project", str(project_path)],
        capture_output=True, text=True, cwd=project_path.parent
    )
    return result.returncode == 0


def _check_srs_generated(project_path: Path) -> bool:
    """確認 SRS.md 存在"""
    srs_path = project_path / "docs" / "01-requirements" / "SRS.md"
    return srs_path.exists()


def _get_hint(checkpoint_name: str) -> str:
    hints = {
        "初始化專案結構": "執行: python cli.py init --project .",
        "執行 Quality Gate check": "執行: python cli.py qg check -p .",
        "建立第一個 artifact (SRS.md)": "執行: python cli.py phase --init --phase 1",
        "執行 Constitution check": "執行: python cli.py constitution check --phase 1",
    }
    return hints.get(checkpoint_name, "請查閱 Quick Start Guide")
```

### 刪除的內容

| 原始內容 | 刪除原因 | 替代方案 |
|----------|----------|----------|
| Certification | 工程師不需要考試 | 「完成第一個真實 Phase」作為交付 |
| Role-based Sign-off | 不適合開源/中小團隊 | 自我核查 + GitHub PR merge 作為確認 |
| Architecture Video | 不存在 | 改為「15分鐘語音Pitch」或移除 |
| IMPROVEMENT_OVERVIEW.md | 不存在 | 改為連結到已有文件 |
| Slack/Email support | 不會有人維護 | 改為「GitHub Issues」 |

### 新增的內容

| 新增內容 | 理由 |
|----------|------|
| 互動式進度追蹤 | state.json 持久化，關掉後可恢復 |
| 自動 CLI 執行 | 不是「讀了沒」而是「做了沒」 |
| 真實 Error 回饋 | 如果 check 失敗，顯示錯誤訊息 + 建議修正方式 |
| 快速跳過 | 已熟悉的工程師可以跳過 Foundation 直達 Phase 2 |

### 執行步驟

1. **Week 1**：建立 `wizard.py` 框架 + Phase 1 checkpoints
2. **Week 2**：建立 Phase 2/3 checkpoints + `QUICK_START.md`
3. **Week 3**：建立 progress tracking + `--resume` 功能
4. **Week 4**：整合進 `cli.py` 成為 `python cli.py onboarding` 指令

---

## 三個提案的橫向整合

### 共同的數據來源

```
所有三個工具都應該從同一個數據源取得真實數據：

FeedbackStore
    ├── defect_reduction  ← TCO Calculator (historical_data)
    │   └── 來自 quality_gate feedback
    ├── adoption_metrics  ← Change Management (real_cases)
    │   └── 來自 BVS violations / Constitution passes
    └── team_velocity    ← Onboarding Wizard
        └── 來自 Phase completion time
```

### 檔案位置規劃

```
methodology-v2/
├── adoption/                      # P3-1 重寫
│   ├── VALUE_PROPOSITION.md
│   ├── QUICK_WINS.md
│   ├── CASE_STUDIES/
│   │   └── real_cases.json
│   └── INTEGRATION_GUIDE.md
│
├── tools/
│   └── scenario_model.py          # P3-2 重寫（從 tools/ 而非原本提議的位置）
│       ├── data_sources.py
│       ├── templates/
│       └── validators/
│
└── onboarding/
    ├── wizard.py                  # P3-3 重寫（CLI 向導）
    ├── checkpoints/
    │   ├── phase1.yaml
    │   ├── phase2.yaml
    │   └── phase3.yaml
    ├── resources/
    │   ├── QUICK_START.md         # 必須存在，不能假設
    │   └── TOOL_REFERENCE.md
    └── progress/
        └── state.json
```

---

## 執行優先順序

| 優先級 | 提案 | 理由 | 預估工時 |
|--------|------|------|----------|
| P0 | P3-3 Onboarding Wizard | 最實用、工程師接受度最高 | 3-4 weeks |
| P1 | P3-2 Scenario Model | 不做會害人，數字可信度問題嚴重 | 2-3 weeks |
| P2 | P3-1 Adoption Kit | 可以晚一點，但遲早需要 | 2 weeks |

---

## 數字基準建立流程（所有三個提案的前置工作）

在開始做任何一個提案之前，必須先建立測量基準：

```python
# tools/baseline_measurement.py
def establish_baseline(project_path: str) -> dict:
    """
    建立測量基準。這是所有 P3 提案的共同前置工作。
    在做任何改善之前，先測量「現在是什麼狀態」。
    """
    
    return {
        # 來自 Git history
        "defect_detection_stage": {
            "coding": count_commits_tagged("defect_coding"),
            "review": count_commits_tagged("defect_review"), 
            "qa": count_commits_tagged("defect_qa"),
            "production": count_commits_tagged("defect_production"),
        },
        
        # 來自 FeedbackStore
        "quality_gate_coverage": {
            "total_artifacts": count_artifact_files(),
            "checked_by_gate": count_quality_gate_checked(),
        },
        
        # 來自 onboarding session
        "time_to_first_phase": {
            "average": calculate_average_phase1_time(),  # 如果有歷史數據
            "sample_size": get_sample_size(),
        },
        
        # 來自團隊
        "team_context": {
            "size": "user_input",  # 這個一定是用戶輸入
            "hourly_rate": "user_input",
            "current_methodology": "user_input",
        }
    }
```

**沒有這個測量基準，所有「改善XX%」的數字都是假的。**

---

## 結論與建議

### 三個提案的最終命運

| 提案 | 決定 | 理由 |
|------|------|------|
| P3-1 Change Management | ✅ 可做，但需重寫受眾 | 需求存在，但必須是 Engineer-first 不是 HR-first |
| P3-2 TCO Calculator | ⚠️ 必須重寫 | 不改就是幻覺產生器，會害人 |
| P3-3 Onboarding Checklist | ✅ 強烈建議做 | 三個裡面最靠譜，CLI wizard 形式工程師接受度高 |

### 第一步

在開始任何一個提案之前，先執行 `baseline_measurement.py`，建立真正的測量基準。**所有後續的數字都必須基於這個基準。**

---

*最後更新：2026-04-08 | Musk Agent*
