#!/usr/bin/env python3
"""
Integrity Tracker - 誠信追蹤系統

功能：
1. 記錄每次「聲稱 vs 實際」不符
2. 計算誠信分數（100 開始，每次不符扣分）
3. 自動降低後續決策權限
4. 輸出誠信報告

使用方式：
    from quality_gate.integrity_tracker import IntegrityTracker
    
    tracker = IntegrityTracker("/path/to/project")
    tracker.record_violation({"type": "qg_not_executed", "details": "..."})
    print(tracker.get_trust_level())
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class IntegrityTracker:
    """
    誠信追蹤系統
    
    用於記錄和追蹤 Agent 的誠信行為。
    每次「聲稱 vs 實際」不符都會被記錄並扣分。
    """
    
    # 扣分規則
    VIOLATION_SCORES = {
        "subagent_claim": 20,        # 聲稱使用 sub-agent 但未使用
        "code_lines_claim": 15,      # 代碼行數聲稱與實際不符 > 5%
        "qg_not_executed": 10,       # 聲稱執行 Quality Gate 但未執行
        "qa_equals_developer": 25,   # QA = Developer（角色衝突）
        "missing_dialogue": 15,      # 缺少 Developer 回應 Reviewer 的記錄
        "fake_qg_result": 20,        # 虛假 Quality Gate 結果
        "skip_phase": 30,            # 跳過 Phase
        "revision_zero": 15,         # 聲稱 Revision = 0 但有修改
    }
    
    # 信任等級閾值
    TRUST_LEVELS = {
        "FULL_TRUST": 80,
        "PARTIAL_TRUST": 50,
        "LOW_TRUST": 0,
    }
    
    def __init__(self, project_path: str):
        """
        Initialize IntegrityTracker
        
        Args:
            project_path: 專案根目錄路徑
        """
        self.project_path = Path(project_path)
        self.integrity_file = self.project_path / ".integrity_tracker.json"
        self._load_or_initialize()
    
    def _load_or_initialize(self):
        """載入或初始化誠信記錄"""
        if self.integrity_file.exists():
            with open(self.integrity_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.integrity_score = data.get("integrity_score", 100)
                self.violations = data.get("violations", [])
                self.history = data.get("history", [])
        else:
            self.integrity_score = 100
            self.violations = []
            self.history = []
    
    def _save(self):
        """保存誠信記錄到檔案"""
        data = {
            "integrity_score": self.integrity_score,
            "violations": self.violations,
            "history": self.history,
            "last_updated": datetime.now().isoformat()
        }
        with open(self.integrity_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def record_violation(self, violation: Dict) -> Dict:
        """
        記錄違規
        
        Args:
            violation: 違規記錄，格式：
                {
                    "type": "qg_not_executed",  # 違規類型
                    "phase": "phase_3",        # 發生 Phase
                    "details": "...",          # 詳細說明
                    "claimed": "...",          # 聲稱的值
                    "actual": "...",           # 實際的值
                    "evidence": ["..."]        # 證據檔案列表
                }
        
        Returns:
            Dict: 更新後的誠信分數和信任等級
        """
        # 計算扣分
        violation_type = violation.get("type", "unknown")
        deduction = self.VIOLATION_SCORES.get(violation_type, 10)
        
        # 建立違規記錄
        record = {
            "id": len(self.violations) + 1,
            "timestamp": datetime.now().isoformat(),
            "type": violation_type,
            "phase": violation.get("phase", "unknown"),
            "details": violation.get("details", ""),
            "claimed": violation.get("claimed", ""),
            "actual": violation.get("actual", ""),
            "deduction": deduction,
            "evidence": violation.get("evidence", [])
        }
        
        self.violations.append(record)
        
        # 更新誠信分數
        self.integrity_score = max(0, self.integrity_score - deduction)
        
        # 記錄歷史
        self.history.append({
            "action": "violation_recorded",
            "violation_id": record["id"],
            "type": violation_type,
            "score_before": self.integrity_score + deduction,
            "score_after": self.integrity_score,
            "timestamp": datetime.now().isoformat()
        })
        
        self._save()
        
        return {
            "violation_id": record["id"],
            "deduction": deduction,
            "new_score": self.integrity_score,
            "trust_level": self.get_trust_level(),
            "restrictions": self.get_restrictions()
        }
    
    def get_trust_level(self) -> str:
        """
        取得信任等級
        
        Returns:
            str: FULL_TRUST / PARTIAL_TRUST / LOW_TRUST
        """
        if self.integrity_score >= self.TRUST_LEVELS["FULL_TRUST"]:
            return "FULL_TRUST"
        elif self.integrity_score >= self.TRUST_LEVELS["PARTIAL_TRUST"]:
            return "PARTIAL_TRUST"
        else:
            return "LOW_TRUST"
    
    def get_restrictions(self) -> List[str]:
        """
        取得基於當前信任等級的權限限制
        
        Returns:
            List[str]: 限制列表
        """
        if self.integrity_score >= 80:
            return []
        elif self.integrity_score >= 50:
            return [
                "建議二次驗證重要產出",
                "建議執行完整 Quality Gate"
            ]
        elif self.integrity_score >= 25:
            return [
                "禁止直接進入下一 Phase",
                "所有產出需二次驗證",
                "禁止跳过 Quality Gate",
                "每次 Phase 結束需人工確認"
            ]
        else:
            return [
                "禁止直接進入下一 Phase",
                "所有產出需二次驗證",
                "禁止跳过 Quality Gate",
                "每次 Phase 結束需人工確認",
                "限制自動決策權限",
                "需全程人工監督"
            ]
    
    def can_proceed_to_next_phase(self) -> Dict:
        """
        檢查是否可以進入下一個 Phase
        
        Returns:
            Dict: {
                "allowed": bool,
                "reason": str,
                "restrictions": List[str]
            }
        """
        trust = self.get_trust_level()
        
        if trust == "FULL_TRUST":
            return {
                "allowed": True,
                "reason": "誠信分數充足",
                "restrictions": []
            }
        elif trust == "PARTIAL_TRUST":
            return {
                "allowed": True,
                "reason": "需注意：誠信分數低於標準，建議二次驗證",
                "restrictions": self.get_restrictions()
            }
        else:
            return {
                "allowed": False,
                "reason": "誠信分數過低，禁止直接進入下一 Phase",
                "restrictions": self.get_restrictions()
            }
    
    def get_integrity_report(self) -> Dict:
        """
        取得完整的誠信報告
        
        Returns:
            Dict: 完整的誠信狀態報告
        """
        return {
            "integrity_score": self.integrity_score,
            "trust_level": self.get_trust_level(),
            "violations_count": len(self.violations),
            "violations": self.violations,
            "restrictions": self.get_restrictions(),
            "can_proceed": self.can_proceed_to_next_phase(),
            "history_count": len(self.history)
        }
    
    def reset_score(self, new_score: int = 100):
        """
        重置誠信分數（管理員操作）
        
        Args:
            new_score: 新的分數（預設 100）
        """
        self.integrity_score = new_score
        self.history.append({
            "action": "score_reset",
            "old_score": 100,
            "new_score": new_score,
            "timestamp": datetime.now().isoformat()
        })
        self._save()
    
    @staticmethod
    def from_claims_verifier(project_path: str, claims_result: Dict) -> "IntegrityTracker":
        """
        從 Claims Verifier 結果自動記錄違規
        
        Args:
            project_path: 專案路徑
            claims_result: Claims Verifier 的驗證結果
        
        Returns:
            IntegrityTracker: 實例（已記錄違規）
        """
        tracker = IntegrityTracker(project_path)
        
        # 檢查 Sub-agent 使用
        if not claims_result.get("subagent_usage", {}).get("match", True):
            tracker.record_violation({
                "type": "subagent_claim",
                "phase": "phase_3",
                "details": "聲稱使用 sub-agent 但驗證失敗",
                "claimed": claims_result.get("subagent_usage", {}).get("claimed", "unknown"),
                "actual": claims_result.get("subagent_usage", {}).get("actual", "unknown")
            })
        
        # 檢查代碼行數
        code_lines = claims_result.get("code_lines", {})
        if not code_lines.get("match", True):
            tracker.record_violation({
                "type": "code_lines_claim",
                "phase": "phase_3",
                "details": "代碼行數聲稱與實際不符",
                "claimed": code_lines.get("claimed", "unknown"),
                "actual": code_lines.get("actual", "unknown")
            })
        
        # 檢查 Quality Gate 執行
        qg = claims_result.get("quality_gate", {})
        if not qg.get("executed", False):
            tracker.record_violation({
                "type": "qg_not_executed",
                "phase": "phase_3",
                "details": "聲稱執行 Quality Gate 但未執行",
                "claimed": qg.get("claimed", "unknown"),
                "actual": qg.get("actual", "not executed")
            })
        
        return tracker
    
    @staticmethod
    def from_ab_enforcer(project_path: str, ab_result: Dict) -> "IntegrityTracker":
        """
        從 A/B Enforcer 結果自動記錄違規
        
        Args:
            project_path: 專案路徑
            ab_result: A/B Enforcer 的驗證結果
        
        Returns:
            IntegrityTracker: 實例（已記錄違規）
        """
        tracker = IntegrityTracker(project_path)
        
        # 檢查 QA = Developer
        if not ab_result.get("qa_not_developer", {}).get("passed", True):
            tracker.record_violation({
                "type": "qa_equals_developer",
                "phase": "phase_4",
                "details": "Phase 4 Tester = Phase 3 Developer（角色衝突）",
                "claimed": "不同人",
                "actual": "同一人"
            })
        
        # 檢查對話記錄
        if not ab_result.get("dialogue_exists", {}).get("passed", True):
            tracker.record_violation({
                "type": "missing_dialogue",
                "phase": "phase_4",
                "details": "缺少 Developer 回應 Reviewer 意見的記錄",
                "claimed": "有對話",
                "actual": "無對話"
            })
        
        return tracker


def main():
    """CLI 入口"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: integrity_tracker.py <project_path> [report|reset]")
        sys.exit(1)
    
    project_path = sys.argv[1]
    tracker = IntegrityTracker(project_path)
    
    if len(sys.argv) > 2:
        command = sys.argv[2]
        if command == "report":
            report = tracker.get_integrity_report()
            print(json.dumps(report, indent=2, ensure_ascii=False))
        elif command == "reset":
            tracker.reset_score()
            print(f"重置完成，當前分數: {tracker.integrity_score}")
        else:
            print(f"未知命令: {command}")
    else:
        # 預設輸出信任等級
        print(f"信任等級: {tracker.get_trust_level()}")
        print(f"誠信分數: {tracker.integrity_score}")
        print(f"限制: {tracker.get_restrictions()}")


if __name__ == "__main__":
    main()