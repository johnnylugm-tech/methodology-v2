# TODO: Use environment variable - # TODO: Use environment variable - # TODO: Use environment variable - # TODO: Use environment variable - # TODO: Use environment variable - # TODO: Use environment variable - #!/usr/bin/env python3
"""
Agent Evaluation Framework

提供：
- 自動化 Agent 行為評估
- A/B 測試框架
- 效能指標收集
- 人類評估整合 (HITL)
"""

import time
import json
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod
import statistics


class MetricType(Enum):
    """指標類型"""
    LATENCY = "latency"           # 回應延遲 (ms)
    ACCURACY = "accuracy"         # 準確率 (0-100%)
    COST = "cost"                 # 成本 ($)
    TOKEN_USAGE = "token_usage"   # Token 消耗
    SUCCESS_RATE = "success_rate" # 成功率 (0-100%)
    ERROR_RATE = "error_rate"     # 錯誤率 (0-100%)
    CUSTOM = "custom"             # 自訂指標


class EvaluationStatus(Enum):
    """評估狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentVersion(Enum):
    """Agent 版本"""
    A = "agent_a"
    B = "agent_b"
    CONTROL = "control"
    TREATMENT = "treatment"


@dataclass
class TestCase:
    """測試用例"""
    id: str
    name: str
    description: str = ""
    
    # 輸入
    input_prompt: str = ""
    input_context: Dict[str, Any] = None
    
    # 預期輸出
    expected_output: Any = None
    evaluation_criteria: Dict[str, float] = None  # e.g., {"accuracy": 0.9}
    
    # 標籤
    tags: List[str] = field(default_factory=list)
    
    # 版本
    agent_version: AgentVersion = AgentVersion.A
    
    # 元資料
    created_at: datetime = field(default_factory=datetime.now)
    timeout: int = 30  # seconds
    
    def __post_init__(self):
        if self.input_context is None:
            self.input_context = {}
        if self.evaluation_criteria is None:
            self.evaluation_criteria = {}
        if not self.id:
            self.id = hashlib.md5(f"{self.name}{time.time()}".encode()).hexdigest()[:8]


@dataclass
class EvaluationResult:
    """評估結果"""
    test_case_id: str
    test_case_name: str
    
    # 實際輸出
    actual_output: Any = None
    raw_response: Any = None
    
    # 指標
    metrics: Dict[str, float] = field(default_factory=dict)
    
    # 評估
    passed: bool = False
    score: float = 0.0  # 0-100
    feedback: str = ""
    
    # 錯誤
    error: str = None
    error_type: str = None
    
    # 時間戳
    started_at: datetime = None
    completed_at: datetime = None
    duration_ms: float = 0.0
    
    def __post_init__(self):
        if self.started_at is None:
            self.started_at = datetime.now()
    
    @property
    def latency_ms(self) -> float:
        return self.metrics.get("latency_ms", self.duration_ms)
    
    @property
    def success(self) -> bool:
        return self.passed and self.error is None


@dataclass
class EvaluationSuite:
    """評估套件"""
    id: str
    name: str
    description: str = ""
    
    # 測試用例
    test_cases: List[TestCase] = field(default_factory=list)
    
    # 配置
    iterations: int = 1  # 每個測試執行次數
    parallel: bool = False
    delay_between_tests: float = 0  # seconds
    
    # 版本
    version_a_name: str = "Agent A"
    version_b_name: str = "Agent B"
    
    # 門檻
    pass_threshold: float = 80.0  # 80% 通過率
    latency_threshold_ms: float = 5000  # 5s
    
    # 狀態
    status: EvaluationStatus = EvaluationStatus.PENDING
    started_at: datetime = None
    completed_at: datetime = None
    
    # 結果
    results_a: List[EvaluationResult] = field(default_factory=list)
    results_b: List[EvaluationResult] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.id:
            self.id = hashlib.md5(f"{self.name}{time.time()}".encode()).hexdigest()[:8]


class AgentEvaluator:
    """Agent 評估器"""
    
    def __init__(self):
        self.suites: Dict[str, EvaluationSuite] = {}
        self.history: List[EvaluationSuite] = []
    
    def create_suite(
        self,
        name: str,
        description: str = "",
        iterations: int = 1,
        **kwargs
    ) -> EvaluationSuite:
        """建立評估套件"""
        suite = EvaluationSuite(
            id=hashlib.md5(f"{name}{time.time()}".encode()).hexdigest()[:8],
            name=name,
            description=description,
            iterations=iterations,
            **kwargs
        )
        self.suites[suite.id] = suite
        return suite
    
    def add_test_case(
        self,
        suite_id: str,
        name: str,
        input_prompt: str,
        expected_output: Any = None,
        **kwargs
    ) -> TestCase:
        """加入測試用例"""
        if suite_id not in self.suites:
            raise ValueError(f"Suite '{suite_id}' not found")
        
        test_case = TestCase(
            id=hashlib.md5(f"{name}{time.time()}".encode()).hexdigest()[:8],
            name=name,
            input_prompt=input_prompt,
            expected_output=expected_output,
            **kwargs
        )
        
        self.suites[suite_id].test_cases.append(test_case)
        return test_case
    
    def run_suite(
        self,
        suite_id: str,
        agent_a_fn: Callable,
        agent_b_fn: Callable = None,
        progress_callback: Callable = None
    ) -> EvaluationSuite:
        """執行評估套件"""
        if suite_id not in self.suites:
            raise ValueError(f"Suite '{suite_id}' not found")
        
        suite = self.suites[suite_id]
        suite.status = EvaluationStatus.RUNNING
        suite.started_at = datetime.now()
        
        total_tests = len(suite.test_cases) * suite.iterations * (2 if agent_b_fn else 1)
        completed = 0
        
        for iteration in range(suite.iterations):
            for test_case in suite.test_cases:
                # Version A
                result_a = self._run_single_test(test_case, agent_a_fn)
                result_a.agent_version = AgentVersion.A
                suite.results_a.append(result_a)
                
                completed += 1
                if progress_callback:
                    progress_callback(completed, total_tests)
                
                # Version B (A/B Testing)
                if agent_b_fn:
                    result_b = self._run_single_test(test_case, agent_b_fn)
                    result_b.agent_version = AgentVersion.B
                    suite.results_b.append(result_b)
                    
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, total_tests)
                
                # Delay between tests
                if suite.delay_between_tests > 0:
                    time.sleep(suite.delay_between_tests)
        
        suite.status = EvaluationStatus.COMPLETED
        suite.completed_at = datetime.now()
        self.history.append(suite)
        
        return suite
    
    def _run_single_test(
        self,
        test_case: TestCase,
        agent_fn: Callable
    ) -> EvaluationResult:
        """執行單一測試"""
        result = EvaluationResult(
            test_case_id=test_case.id,
            test_case_name=test_case.name,
            started_at=datetime.now()
        )
        
        try:
            # 執行 Agent (帶超時)
            start_time = time.time()
            response = agent_fn(
                prompt=test_case.input_prompt,
                context=test_case.input_context,
                timeout=test_case.timeout
            )
            end_time = time.time()
            
            result.duration_ms = (end_time - start_time) * 1000
            result.raw_response = response
            result.actual_output = response
            
            # 計算指標
            result.metrics["latency_ms"] = result.duration_ms
            result.metrics["timestamp"] = datetime.now().timestamp()
            
            # 評估結果
            result = self._evaluate_result(result, test_case)
            
        except Exception as e:
            result.error = str(e)
            result.error_type = type(e).__name__
            result.metrics["error"] = 1
        
        result.completed_at = datetime.now()
        return result
    
    def _evaluate_result(
        self,
        result: EvaluationResult,
        test_case: TestCase
    ) -> EvaluationResult:
        """評估結果"""
        score = 100.0
        passed_criteria = []
        failed_criteria = []
        
        # Latency check
        if result.duration_ms > 5000:
            score -= 20
            failed_criteria.append("latency")
        else:
            passed_criteria.append("latency")
        
        # Error check
        if result.error:
            score -= 50
            failed_criteria.append("error")
        else:
            passed_criteria.append("error")
        
        # Expected output check (if provided)
        if test_case.expected_output is not None:
            if result.actual_output == test_case.expected_output:
                passed_criteria.append("accuracy")
            else:
                # 簡單的字串相似度檢查
                similarity = self._calculate_similarity(
                    str(result.actual_output),
                    str(test_case.expected_output)
                )
                if similarity > 0.8:
                    score += 0
                    passed_criteria.append("accuracy")
                else:
                    score -= 30
                    failed_criteria.append("accuracy")
        
        # Evaluation criteria
        for criterion, threshold in test_case.evaluation_criteria.items():
            if criterion in result.metrics:
                if result.metrics[criterion] >= threshold:
                    passed_criteria.append(criterion)
                else:
                    score -= 20
                    failed_criteria.append(criterion)
        
        result.score = max(0, min(100, score))
        result.passed = result.score >= 80.0 and len(failed_criteria) == 0
        
        # Feedback
        if passed_criteria:
            result.feedback = f"✅ Passed: {', '.join(passed_criteria)}"
        if failed_criteria:
            result.feedback += f"\n❌ Failed: {', '.join(failed_criteria)}"
        
        return result
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """計算字串相似度 (簡單 Jaccard)"""
        set1 = set(str1.lower().split())
        set2 = set(str2.lower().split())
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def compare_versions(self, suite_id: str) -> Dict[str, Any]:
        """比較 A/B 版本"""
        if suite_id not in self.suites:
            raise ValueError(f"Suite '{suite_id}' not found")
        
        suite = self.suites[suite_id]
        
        stats_a = self._calculate_stats(suite.results_a)
        stats_b = self._calculate_stats(suite.results_b) if suite.results_b else None
        
        comparison = {
            "suite_id": suite_id,
            "suite_name": suite.name,
            "version_a": suite.version_a_name,
            "version_b": suite.version_b_name,
            "total_tests_a": len(suite.results_a),
            "total_tests_b": len(suite.results_b),
            "stats_a": stats_a,
            "stats_b": stats_b,
            "winner": None,
            "improvement": None
        }
        
        # 決定贏家
        if stats_b:
            if stats_a["avg_score"] > stats_b["avg_score"]:
                comparison["winner"] = "A"
                comparison["improvement"] = (
                    (stats_a["avg_score"] - stats_b["avg_score"]) 
                    / stats_b["avg_score"] * 100
                )
            elif stats_b["avg_score"] > stats_a["avg_score"]:
                comparison["winner"] = "B"
                comparison["improvement"] = (
                    (stats_b["avg_score"] - stats_a["avg_score"]) 
                    / stats_a["avg_score"] * 100
                )
            else:
                comparison["winner"] = "TIE"
        
        return comparison
    
    def _calculate_stats(self, results: List[EvaluationResult]) -> Dict[str, float]:
        """計算統計數據"""
        if not results:
            return {}
        
        scores = [r.score for r in results]
        latencies = [r.duration_ms for r in results]
        passed = sum(1 for r in results if r.passed)
        
        return {
            "avg_score": statistics.mean(scores),
            "median_score": statistics.median(scores),
            "min_score": min(scores),
            "max_score": max(scores),
            "std_dev": statistics.stdev(scores) if len(scores) > 1 else 0,
            "pass_rate": (passed / len(results)) * 100,
            "avg_latency_ms": statistics.mean(latencies),
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed
        }
    
    def generate_report(self, suite_id: str) -> str:
        """產生評估報告"""
        if suite_id not in self.suites:
            raise ValueError(f"Suite '{suite_id}' not found")
        
        suite = self.suites[suite_id]
        comparison = self.compare_versions(suite_id)
        
        lines = []
        lines.append("╔" + "═" * 70 + "╗")
        lines.append("║" + f" 📊 EVALUATION REPORT: {suite.name} ".center(70) + "║")
        lines.append("╚" + "═" * 70 + "╝")
        lines.append("")
        
        # 基本資訊
        lines.append(f"**Suite ID**: {suite.id}")
        lines.append(f"**Status**: {suite.status.value}")
        lines.append(f"**Test Cases**: {len(suite.test_cases)}")
        lines.append(f"**Iterations**: {suite.iterations}")
        lines.append("")
        
        # Version A 統計
        lines.append(f"## 📌 Version A: {suite.version_a_name}")
        stats_a = comparison["stats_a"]
        lines.append(f"- **Tests**: {stats_a['total']}")
        lines.append(f"- **Pass Rate**: {stats_a['pass_rate']:.1f}%")
        lines.append(f"- **Avg Score**: {stats_a['avg_score']:.1f}/100")
        lines.append(f"- **Avg Latency**: {stats_a['avg_latency_ms']:.0f}ms")
        lines.append("")
        
        # Version B 統計
        if stats_b := comparison["stats_b"]:
            lines.append(f"## 📌 Version B: {suite.version_b_name}")
            lines.append(f"- **Tests**: {stats_b['total']}")
            lines.append(f"- **Pass Rate**: {stats_b['pass_rate']:.1f}%")
            lines.append(f"- **Avg Score**: {stats_b['avg_score']:.1f}/100")
            lines.append(f"- **Avg Latency**: {stats_b['avg_latency_ms']:.0f}ms")
            lines.append("")
        
        # 贏家
        if winner := comparison["winner"]:
            lines.append("## 🏆 Winner")
            if winner == "A":
                lines.append(f"**Version A** ({suite.version_a_name}) wins!")
                if improvement := comparison["improvement"]:
                    lines.append(f"Improvement: +{improvement:.1f}%")
            elif winner == "B":
                lines.append(f"**Version B** ({suite.version_b_name}) wins!")
                if improvement := comparison["improvement"]:
                    lines.append(f"Improvement: +{improvement:.1f}%")
            else:
                lines.append("**TIE** - No significant difference")
            lines.append("")
        
        # 個別結果
        if suite.results_a:
            lines.append("## 📋 Individual Results (Version A)")
            for r in suite.results_a[:5]:  # 只顯示前 5 個
                status = "✅" if r.passed else "❌"
                lines.append(
                    f"{status} {r.test_case_name}: "
                    f"Score={r.score:.0f} | Latency={r.duration_ms:.0f}ms"
                )
            if len(suite.results_a) > 5:
                lines.append(f"... and {len(suite.results_a) - 5} more")
            lines.append("")
        
        # 失敗的測試
        failed_a = [r for r in suite.results_a if not r.passed]
        if failed_a:
            lines.append("## 🔴 Failed Tests (Version A)")
            for r in failed_a:
                lines.append(f"- {r.test_case_name}: {r.feedback}")
            lines.append("")
        
        return "\n".join(lines)


# ==================== Human-in-the-Loop ====================

class HumanEvaluator:
    """人類評估器 (HITL)"""
    
    def __init__(self):
        self.pending_reviews: List[EvaluationResult] = []
        self.completed_reviews: List[Dict] = []
    
    def submit_for_review(self, result: EvaluationResult) -> str:
        """提交結果供人工審查"""
        review_id = hashlib.md5(
            f"{result.test_case_id}{time.time()}".encode()
        ).hexdigest()[:8]
        
        self.pending_reviews.append(result)
        
        return review_id
    
    def approve(
        self,
        review_id: str,
        score: float,
        feedback: str = ""
    ) -> bool:
        """批准結果"""
        if not self.pending_reviews:
            return False
        
        result = self.pending_reviews.pop(0)
        
        self.completed_reviews.append({
            "review_id": review_id,
            "test_case_id": result.test_case_id,
            "test_case_name": result.test_case_name,
            "original_score": result.score,
            "human_score": score,
            "feedback": feedback,
            "approved_at": datetime.now()
        })
        
        return True
    
    def reject(
        self,
        review_id: str,
        reason: str
    ) -> bool:
        """拒絕結果"""
        if not self.pending_reviews:
            return False
        
        result = self.pending_reviews.pop(0)
        
        self.completed_reviews.append({
            "review_id": review_id,
            "test_case_id": result.test_case_id,
            "test_case_name": result.test_case_name,
            "original_score": result.score,
            "human_score": None,
            "feedback": reason,
            "rejected_at": datetime.now()
        })
        
        return True
    
    def get_pending_count(self) -> int:
        """取得待審查數量"""
        return len(self.pending_reviews)


# ==================== Main ====================

if __name__ == "__main__":
    pass # Removed print-debug
    pass # Removed print-debug
    pass # Removed print-debug
    
    # 建立評估器
    evaluator = AgentEvaluator()
    
    # 建立測試套件
    suite = evaluator.create_suite(
        name="Login Flow Evaluation",
        description="測試登入流程的 Agent 行為",
        iterations=1,
        version_a_name="GPT-4",
        version_b_name="Claude-3"
    )
    
    # 加入測試用例
    evaluator.add_test_case(
        suite_id=suite.id,
        name="Valid Login",
        input_prompt="User tries to login with correct credentials",
        expected_output="Login successful",
        tags=["happy_path"]
    )
    
    evaluator.add_test_case(
        suite_id=suite.id,
        name="Invalid Password",
        input_prompt="User enters wrong password",
        expected_output="Authentication failed",
        tags=["error_case"]
    )
    
    evaluator.add_test_case(
        suite_id=suite.id,
        name="Empty Username",
        input_prompt="User submits empty username field",
        expected_output="Validation error",
        tags=["validation"]
    )
    
    pass # Removed print-debug
    pass # Removed print-debug
    pass # Removed print-debug
    
    # 定義 Mock Agent 函數
    def mock_agent_a(prompt: str, context: Dict = None, timeout: int = 30):
        """Mock Agent A"""
        time.sleep(0.1)  # 模擬延遲
        return f"[GPT-4] Response to: {prompt[:50]}..."
    
    def mock_agent_b(prompt: str, context: Dict = None, timeout: int = 30):
        """Mock Agent B"""
        time.sleep(0.15)  # 模擬延遲
        return f"[Claude-3] Response to: {prompt[:50]}..."
    
    # 執行評估
    pass # Removed print-debug
    def progress(current, total):
        pass # Removed print-debug
    
    results = evaluator.run_suite(suite.id, mock_agent_a, mock_agent_b, progress)
    pass # Removed print-debug
    pass # Removed print-debug
    
    # 產生報告
    pass # Removed print-debug
    
    # Human Evaluator
    pass # Removed print-debug
    pass # Removed print-debug
    pass # Removed print-debug
    
    hitl = HumanEvaluator()
    
    # 模擬提交審查
    if suite.results_a:
        review_id = hitl.submit_for_review(suite.results_a[0])
        pass # Removed print-debug
        pass # Removed print-debug
        
        # 批准
        hitl.approve(review_id, score=95.0, feedback="Good response")
        pass # Removed print-debug
