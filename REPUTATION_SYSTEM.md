# Agent 信譽評分系統

**版本**: v1.0  
**生效日期**: 2026-03-27  
**目的**: 實現 Sub-agent 匿名舉報機制的評分支撐

---

## 評分架構

```
┌─────────────────────────────────────────────────────────────────┐
│                     信譽評分系統架構                             │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐     ┌──────────────────┐
│   主代理評分      │     │  Sub-agent 評分  │
│   (被審查者)      │     │   (舉報者)       │
├──────────────────┤     ├──────────────────┤
│ 品質分數         │     │ 舉報信譽分       │
│ 審查通過率       │     │ 舉報準確率       │
│ 審查時間         │     │ 舉報採納率       │
│ 異常行為         │     │ 假舉報次數       │
└────────┬─────────┘     └────────┬─────────┘
         │                         │
         └───────────┬─────────────┘
                     │
                     ▼
         ┌─────────────────────┐
         │    綜合信譽分        │
         │    (0-100)          │
         └─────────────────────┘
```

---

## 評分維度

### 主代理評分（被審查者）

| 維度 | 分數範圍 | 計算方式 |
|------|----------|----------|
| **品質分數** | 0-30 | Quality Gate 分數 |
| **通過率** | 0-20 | 首次通過率 × 20 |
| **審查品質** | 0-25 | 引用原文數 × 5，問題數 × 5 |
| **異常行為** | -30~0 | 每次異常扣分 |
| **總分** | 0-100 | 上述加總 |

### Sub-agent 評分（舉報者）

| 維度 | 分數範圍 | 計算方式 |
|------|----------|----------|
| **基礎分** | 50 | 初始分數 |
| **準確率** | -20~+20 | 被採納舉報加分，未採納扣分 |
| **品質** | -10~+10 | 證據完整性加分 |
| **頻率** | -10~0 | 短時間多舉報扣分 |
| **總分** | 0-100 | 上述加總 |

---

## 評分計算

### 主代理評分公式

```python
class MainAgentScorer:
    """主代理評分器"""
    
    def calculate_score(self, agent_id: str, phase_history: List[Dict]) -> int:
        """計算主代理信譽分"""
        
        # 1. 品質分數（0-30）
        quality_score = sum([p.get("qg_score", 0) for p in phase_history]) / len(phase_history)
        quality_score = min(30, quality_score * 0.3)
        
        # 2. 通過率（0-20）
        first_pass_rate = sum([1 for p in phase_history if p.get("first_pass", False)]) / len(phase_history)
        pass_score = first_pass_rate * 20
        
        # 3. 審查品質（0-25）
        review_quality = 0
        for p in phase_history:
            review = p.get("review", {})
            quoted = len(review.get("quoted_lines", []))
            questions = len(review.get("questions", []))
            review_quality += min(quoted * 2, 10) + min(questions * 5, 15)
        review_quality = min(25, review_quality / len(phase_history))
        
        # 4. 異常行為（-30~0）
        anomaly_penalty = 0
        for p in phase_history:
            if p.get("anomaly_detected"):
                anomaly_penalty -= 10
        anomaly_penalty = max(-30, anomaly_penalty)
        
        # 總分
        total = quality_score + pass_score + review_quality + anomaly_penalty
        return max(0, min(100, int(total)))
```

### Sub-agent 評分公式

```python
class SubAgentScorer:
    """Sub-agent 評分器"""
    
    def calculate_score(self, agent_id: str, report_history: List[Dict]) -> int:
        """計算 Sub-agent 信譽分"""
        
        # 1. 基礎分
        base_score = 50
        
        # 2. 準確率（-20~+20）
        total_reports = len(report_history)
        if total_reports > 0:
            accepted = sum([1 for r in report_history if r.get("status") == "accepted"])
            accuracy = (accepted / total_reports - 0.5) * 40  # -20~+20
        else:
            accuracy = 0
        
        # 3. 品質（-10~+10）
        evidence_quality = 0
        for r in report_history:
            if r.get("has_evidence"):
                evidence_quality += 2
            if r.get("has_description"):
                evidence_quality += 1
        evidence_quality = min(10, evidence_quality)
        
        # 4. 頻率（-10~0）
        # 短時間多舉報會扣分
        recent_reports = [r for r in report_history 
                         if r.get("timestamp") > (now() - timedelta(hours=1))]
        if len(recent_reports) > 3:
            frequency_penalty = -10
        elif len(recent_reports) > 1:
            frequency_penalty = -5
        else:
            frequency_penalty = 0
        
        # 總分
        total = base_score + accuracy + evidence_quality + frequency_penalty
        return max(0, min(100, int(total)))
```

---

## 評分觸發時機

| 事件 | 觸發評分 |
|------|----------|
| Phase 完成 | 主代理 +5 分（正常）|
| Phase 失敗 | Sub-agent -10 分 |
| 舉報被採納 | Sub-agent +15 分 |
| 舉報被駁回 | Sub-agent -10 分 |
| 異常行為 | 主代理 -10 分 |
| 假舉報 | Sub-agent -20 分 |

---

## 評分等級

### 主代理等級

| 等級 | 分數 | 權限 |
|------|------|------|
| 🟢 優秀 | 90-100 | 正常權限，可帶多個 Sub-agent |
| 🟡 良好 | 70-89 | 正常權限 |
| 🟠 警告 | 50-69 | 需加強審查 |
| 🔴 停權 | 0-49 | 禁止擔任主代理 |

### Sub-agent 等級

| 等級 | 分數 | 權限 |
|------|------|------|
| 🟢 可信 | 80-100 | 舉報優先處理 |
| 🟡 普通 | 50-79 | 正常舉報 |
| 🟠 懷疑 | 30-49 | 舉報需審核 |
| 🔴 停權 | 0-29 | 禁止舉報 |

---

## 評分公開性

```
┌─────────────────────────────────────────────────────┐
│                   評分公開原則                       │
├─────────────────────────────────────────────────────┤
│ 主代理評分    │ 公開（所有人可見）                   │
│ Sub-agent ID │ 隱藏（只顯示 Hash）                  │
│ Sub-agent 等級│ 公開（可見可信度）                  │
│ 舉報詳情     │ 保密（只有審計團隊可看）             │
│ 評分明細     │ 當事人可看                           │
└─────────────────────────────────────────────────────┘
```

---

## 評分API

```python
from reputation_system import (
    MainAgentScorer,
    SubAgentScorer,
    ReputationLevel,
    get_agent_score,
    update_score
)

# 取得主代理評分
score = get_agent_score("main-agent-001")
print(f"主代理評分: {score.score} - {score.level.value}")

# 取得 Sub-agent 等級（匿名）
level = get_agent_level("sub-agent-hash-xxx")
print(f"Sub-agent 等級: {level.value}")

# 更新評分（系統自動觸發）
update_score(
    agent_id="main-agent-001",
    event="phase_complete",
    details={"qg_score": 90}
)

# Sub-agent 舉報時檢查信譽
if get_agent_level("sub-agent-xxx") == ReputationLevel.SUSPICIOUS:
    print("警告：此 Sub-agent 舉報需額外審核")
```

---

## 防作弊機制

| 機制 | 說明 |
|------|------|
| **時序檢查** | 評分更新有冷卻時間，不能快速刷分 |
| **多維度驗證** | 單一維度異常會觸發審計 |
| **歷史比對** | 與同類型 Agent 比對，異常會警告 |
| **第三方審計** | 每月由外部團隊審計評分合理性 |

---

## 評分示例

### 主代理評分變化

```
Phase 1 完成 → +5 分（首次通過）
Phase 2 完成 → +5 分（首次通過）
異常行為 → -10 分
Phase 3 完成 → +5 分（首次通過）
...
```

### Sub-agent 舉報評分變化

```
舉報 #1（被採納）→ +15 分
舉報 #2（被駁回）→ -10 分
舉報 #3（被採納）→ +15 分
...
```

---

## 評分查詢命令

```bash
# 查詢主代理評分
python -c "from reputation_system import get_agent_score; print(get_agent_score('main-001'))"

# 查詢 Sub-agent 等級
python -c "from reputation_system import get_agent_level; print(get_agent_level('sub-hash'))"

# 評分明細
python -c "from reputation_system import get_score_history; print(get_score_history('main-001'))"
```

---

*版本: v1.0 | 生效: 2026-03-27*