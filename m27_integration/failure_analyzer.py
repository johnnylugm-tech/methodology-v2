#!/usr/bin/env python3
"""
Failure Analyzer
==============
M2.7 的失敗路徑分析

功能：
- 分析 Agent 執行失敗的路徑
- 識別失敗模式
- 提供改進建議

使用方式：

```python
analyzer = FailureAnalyzer()

path = analyzer.analyze(failure_log)
print(f"Failure type: {path.failure_type}")
print(f"Root cause: {path.root_cause}")
print(f"Recommendations: {path.recommendations}")
```
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

class FailureType(Enum):
    """失敗類型"""
    TIMEOUT = "timeout"
    MEMORY_OVERFLOW = "memory_overflow"
    INVALID_TOOL_CALL = "invalid_tool_call"
    LOOPS = "loops"
    HALLUCINATION = "hallucination"
    CONTEXT_OVERFLOW = "context_overflow"
    UNKNOWN = "unknown"

@dataclass
class FailurePath:
    """失敗路徑"""
    path_id: str
    failure_type: FailureType
    root_cause: str
    steps: List[str]  # 導致失敗的步驟序列
    recommendations: List[str]
    confidence: float  # 0-1

class FailureAnalyzer:
    """
    失敗分析器
    
    分析失敗路徑，識別根本原因
    """
    
    # 失敗模式特徵
    PATTERNS = {
        FailureType.TIMEOUT: ["timeout", "deadline", "took too long"],
        FailureType.MEMORY_OVERFLOW: ["memory", "out of memory", "OOM"],
        FailureType.INVALID_TOOL_CALL: ["tool not found", "invalid tool", "function not found"],
        FailureType.LOOPS: ["loop", "repeating", "stuck", "circular"],
        FailureType.HALLUCINATION: ["invalid", "nonsense", "doesn't exist"],
        FailureType.CONTEXT_OVERFLOW: ["context length", "too long", "exceeds limit"],
    }
    
    def analyze(self, failure_log: str) -> FailurePath:
        """
        分析失敗日誌
        
        Args:
            failure_log: 失敗日誌文字
        
        Returns:
            FailurePath: 失敗路徑分析結果
        """
        import uuid
        
        # 識別失敗類型
        failure_type = self._identify_type(failure_log)
        
        # 識別根本原因
        root_cause = self._identify_root_cause(failure_type, failure_log)
        
        # 生成建議
        recommendations = self._generate_recommendations(failure_type)
        
        return FailurePath(
            path_id=f"path-{uuid.uuid4().hex[:8]}",
            failure_type=failure_type,
            root_cause=root_cause,
            steps=self._extract_steps(failure_log),
            recommendations=recommendations,
            confidence=0.8  # 預設置信度
        )
    
    def _identify_type(self, log: str) -> FailureType:
        """識別失敗類型"""
        log_lower = log.lower()
        
        for failure_type, keywords in self.PATTERNS.items():
            if any(kw in log_lower for kw in keywords):
                return failure_type
        
        return FailureType.UNKNOWN
    
    def _identify_root_cause(self, failure_type: FailureType, log: str) -> str:
        """識別根本原因"""
        causes = {
            FailureType.TIMEOUT: "任務執行時間過長，超過設定的逾時限制",
            FailureType.MEMORY_OVERFLOW: "記憶體使用超過限制",
            FailureType.INVALID_TOOL_CALL: "嘗試呼叫不存在的工具",
            FailureType.LOOPS: "Agent 陷入重複循環",
            FailureType.HALLUCINATION: "Agent 產生了與事實不符的輸出",
            FailureType.CONTEXT_OVERFLOW: "上下文長度超出模型限制",
            FailureType.UNKNOWN: "無法確定失敗原因"
        }
        return causes.get(failure_type, causes[FailureType.UNKNOWN])
    
    def _extract_steps(self, log: str) -> List[str]:
        """提取導致失敗的步驟"""
        steps = []
        lines = log.split('\n')
        for line in lines:
            if line.strip().startswith('Step') or line.strip().startswith('>'):
                steps.append(line.strip())
        return steps[:10]  # 最多取 10 步
    
    def _generate_recommendations(self, failure_type: FailureType) -> List[str]:
        """生成改進建議"""
        recommendations = {
            FailureType.TIMEOUT: [
                "將任務拆分為更小的子任務",
                "增加逾時限制",
                "使用更快的模型"
            ],
            FailureType.MEMORY_OVERFLOW: [
                "減少上下文長度",
                "使用記憶體優化的模型"
            ],
            FailureType.INVALID_TOOL_CALL: [
                "檢查工具名稱是否正確",
                "更新工具列表"
            ],
            FailureType.LOOPS: [
                "添加迴圈檢測",
                "增加最大迭代次數限制"
            ],
            FailureType.HALLUCINATION: [
                "提供更多上下文",
                "使用更可靠的模型"
            ],
            FailureType.CONTEXT_OVERFLOW: [
                "壓縮上下文",
                "分段處理長文本"
            ],
            FailureType.UNKNOWN: [
                "查看完整日誌",
                "聯繫支持團隊"
            ]
        }
        return recommendations.get(failure_type, recommendations[FailureType.UNKNOWN])
