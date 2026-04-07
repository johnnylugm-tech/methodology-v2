# Verify_Agent Guide

## 什麼是 Verify_Agent

在 A/B 審查之後、主代理接受結果前，執行一個獨立的驗證 Agent。目的是確保產物的正確性。

## 觸發條件

| 條件 | 動作 |
|------|------|
| Phase 3+ 代碼交付 | 自動觸發 |
| Agent B 分數 < 80 | 自動觸發 |
| Agent A 自評分數差異 > 20 | 自動觸發 |

## Verify_Agent Prompt

```
你是 Verify_Agent，負責驗證產物的正確性。

任務：{task_description}
產物：{artifact_content}
聲稱的正確性：{Agent_A_claims}

驗證步驟：
1. 列出產物中的每個事實聲稱
2. 對每個聲稱，找出對應的驗證依據（代碼/文件/測試）
3. 評估聲稱是否被充分證實

輸出格式：
{
  "verified_claims": [...],
  "unverified_claims": [...],
  "confidence": 1-10,
  "verdict": "APPROVED" | "REJECTED"
}
```

## 第三審計代理（Phase 3+ SOP 新增）

在 Phase 3/4 的 SOP 中，Quality Gate 之後新增：

```bash
// Phase 3 新增
7. 第三審計代理審查（如滿足觸發條件）
   python cli.py verify-artifact --phase 3 --repo .
8. 根據 Verify_Agent 結果決定：
   - APPROVED → 進入 Phase 4
   - REJECTED → 回歸 Agent A 修復
```

## CLI 命令

```bash
# 執行 Verify_Agent
python cli.py verify-artifact --phase 3 --repo .
```
