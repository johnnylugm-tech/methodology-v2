#!/usr/bin/env python3
"""
Knowledge Base - 知識傳遞庫

範例庫、最佳實踐庫、模式庫
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict


@dataclass
class Pattern:
    """模式/範例"""
    id: str
    name: str
    category: str
    problem: str = ""
    solution: str = ""
    
    # 內容
    description: str = ""
    code_example: str = ""
    
    # 元數據
    tags: List[str] = field(default_factory=list)
    language: str = "python"
    
    # 評估
    usage_count: int = 0
    success_rate: float = 0.0
    rating: float = 0.0
    
    # 時間
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "problem": self.problem,
            "solution": self.solution,
            "code_example": self.code_example[:100] + "..." if len(self.code_example) > 100 else self.code_example,
            "tags": self.tags,
            "language": self.language,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "rating": self.rating,
        }


@dataclass
class BestPractice:
    """最佳實踐"""
    id: str
    title: str
    category: str
    
    # 內容
    description: str
    steps: List[str] = field(default_factory=list)
    do_list: List[str] = field(default_factory=list)
    dont_list: List[str] = field(default_factory=list)
    
    # 適用場景
    use_cases: List[str] = field(default_factory=list)
    
    # 評估
    effectiveness: float = 0.0  # 0-1
    
    # 時間
    created_at: datetime = field(default_factory=datetime.now)


class KnowledgeBase:
    """知識庫管理器"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or "~/.methodology/knowledge_base.json"
        self.db_path = os.path.expanduser(self.db_path)
        
        self.patterns: Dict[str, Pattern] = {}
        self.best_practices: Dict[str, BestPractice] = {}
        
        # 載入預設模式
        self._load_defaults()
    
    def _load_defaults(self):
        """載入預設模式庫"""
        
        # Agent 協調模式
        self.add_pattern(Pattern(
            id="pattern-001",
            name="Sequential Agent Flow",
            category="agent-coordination",
            problem="需要多個 Agent 順序執行任務",
            solution="使用 Sequential Workflow，確保每個步驟完成後再執行下一個",
            code_example="""wf = WorkflowGraph()
wf.add_node("research", "研究")
wf.add_node("design", "設計", depends_on=["research"])
wf.add_node("implement", "實現", depends_on=["design"])
wf.execute()""",
            tags=["workflow", "sequential", "agents"],
            language="python",
            rating=4.5
        ))
        
        self.add_pattern(Pattern(
            id="pattern-002",
            name="Parallel Agent Tasks",
            category="agent-coordination",
            problem="多個獨立的任務需要同時處理",
            solution="使用 ParallelExecutor，設定 max_workers 控制並發數",
            code_example="""executor = ParallelExecutor(max_workers=3)
executor.add_task("task1", func1)
executor.add_task("task2", func2)
executor.add_task("task3", func3)
result = executor.execute_all()""",
            tags=["parallel", "executor", "concurrent"],
            language="python",
            rating=4.3
        ))
        
        self.add_pattern(Pattern(
            id="pattern-003",
            name="Router with Cost Optimization",
            category="cost-optimization",
            problem="需要在多個模型間選擇最便宜的",
            solution="使用 SmartRouter.select_cost_efficient_model() 自動選擇",
            code_example="""router = SmartRouter()
router.set_budget("low")  # 限制成本
result = router.route(task)
# 或直接選擇最便宜的
model = router.select_cost_efficient_model(task, "medium")""",
            tags=["cost", "router", "optimization"],
            language="python",
            rating=4.7
        ))
        
        # 安全模式
        self.add_pattern(Pattern(
            id="pattern-004",
            name="API Key Rotation",
            category="security",
            problem="需要定期輪換 API Key",
            solution="使用 FailoverManager 設定多個 Key，自動切換",
            code_example="""manager = FailoverManager()
manager.register_model("gpt-4o", "OpenAI", api_key="key1")
manager.set_fallback("gpt-4o", "claude")
result = manager.execute_with_failover(task_func)""",
            tags=["security", "api-key", "failover"],
            language="python",
            rating=4.2
        ))
        
        # 最佳實踐
        self.add_best_practice(BestPractice(
            id="bp-001",
            title="PM Daily Workflow",
            category="project-management",
            description="PM 一天的標準工作流程",
            steps=[
                "09:00 - 檢查 Dashboard 健康狀態",
                "10:00 - 分配新任務",
                "12:00 - 品質審視",
                "15:00 - 成本檢視",
                "17:00 - 進度彙報"
            ],
            do_list=[
                "使用 Dashboard 追蹤進度",
                "使用 CostOptimizer 控制成本",
                "使用 ApprovalFlow 審批重要決策"
            ],
            dont_list=[
                "不要忽略 PredictiveMonitor 預警",
                "不要超過月度預算"
            ],
            use_cases=["日常管理", "例會準備"],
            effectiveness=0.9
        ))
        
        self.add_best_practice(BestPractice(
            id="bp-002",
            title="Multi-Agent Debugging",
            category="debugging",
            description="當 Agent 系統出錯時的調查流程",
            steps=[
                "1. 檢查 AgentRegistry 狀態",
                "2. 查看 MessageBus 佇列",
                "3. 檢查 WorkflowGraph 執行日誌",
                "4. 驗證 AuditLogger 軌跡"
            ],
            do_list=[
                "先查日誌再下結論",
                "檢查資源是否足夠"
            ],
            dont_list=[
                "不要重啟所有服務",
                "不要忽略錯誤訊息"
            ],
            use_cases=["系統故障", "任務卡住"],
            effectiveness=0.85
        ))
        
        # ========== 企業級模式 (v2) ==========
        
        # DevOps 模式
        self.add_pattern(Pattern(
            id="pattern-010",
            name="Zero-Downtime Deployment",
            category="devops",
            problem="部署時服務中斷",
            solution="使用藍綠部署或滾動更新",
            code_example="""spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0""",
            tags=["devops", "deployment", "zero-downtime"],
            language="yaml",
            rating=4.6
        ))
        
        # 監控模式
        self.add_pattern(Pattern(
            id="pattern-011",
            name="Three Pillars of Observability",
            category="monitoring",
            problem="無法快速定位問題",
            solution="實現 Metrics + Logs + Traces 三合一可觀測性",
            code_example="""# Prometheus Metrics
prometheus_clientCounter('requests_total')
# Structured Logging
logger.info("Request processed", extra={"request_id": req_id})
# OpenTelemetry Trace
with tracer.start_as_current_span("process") as span:""",
            tags=["monitoring", "observability", "tracing"],
            language="python",
            rating=4.4
        ))
        
        # 安全模式
        self.add_pattern(Pattern(
            id="pattern-012",
            name="Defense in Depth",
            category="security",
            problem="單一安全措施不足",
            solution="多層安全：網路隔離 → 認證授權 → 輸入驗證 → 加密 → 審計",
            code_example="""# 1. 網路層
firewall.allow(internal_only)
# 2. 認證層
auth.require_mfa()
# 3. 授權層
rbac.check_permission(user, resource)
# 4. 審計日誌
audit.log(action, user, resource)""",
            tags=["security", "defense", "multi-layer"],
            language="python",
            rating=4.8
        ))
        
        # 架構模式
        self.add_pattern(Pattern(
            id="pattern-013",
            name="Event-Driven Architecture",
            category="architecture",
            problem="服務間耦合過高",
            solution="使用事件匯流排解耦，生產者只知道事件，不知消費者",
            code_example="""# 生產者
event_bus.publish("order.created", {"order_id": "123"})
# 消費者
@event_bus.subscribe("order.created")
def send_confirmation(event):
    email.send(event.customer)""",
            tags=["architecture", "event-driven", "decoupling"],
            language="python",
            rating=4.5
        ))
        
        # API 設計模式
        self.add_pattern(Pattern(
            id="pattern-014",
            name="API Versioning Strategy",
            category="api-design",
            problem="API 更新影響現有用戶",
            solution="URL versioning + 向前相容",
            code_example="""@app.route("/api/v1/users")
@app.route("/api/v2/users")
def users():
    version = request.api_version
    if version == "v1":
        return legacy_user_service.get_users()
    return current_user_service.get_users()""",
            tags=["api", "versioning", "rest"],
            language="python",
            rating=4.2
        ))
        
        # 企業實踐 - Incident Response
        self.add_best_practice(BestPractice(
            id="bp-003",
            title="Incident Response Playbook",
            category="operations",
            description="生產環境事故應變標準流程",
            steps=[
                "1. 檢測 → 警報觸發或用戶回報",
                "2. 評估 → 確認影響範圍和嚴重性",
                "3. 遏制 → 隔離問題防止擴大",
                "4. 消除 → 移除根本原因",
                "5. 恢復 → 驗證服務正常運行",
                "6. 復原 → 確認所有功能正常",
                "7. 會議 → 事故後檢討 (Post-mortem)"
            ],
            do_list=[
                "立即通知相關團隊",
                "保留現場日誌和錯誤訊息",
                "記錄每個處置步驟的時間點",
                "在解決後 24 小時內完成 Post-mortem"
            ],
            dont_list=[
                "不要在未了解範圍前急於修復",
                "不要假設問題會自動消失",
                "不要隱瞞或淡化問題"
            ],
            use_cases=["生產環境故障", "安全事件", "效能問題"],
            effectiveness=0.95
        ))
        
        # 企業實踐 - Code Review
        self.add_best_practice(BestPractice(
            id="bp-004",
            title="Code Review Best Practices",
            category="development",
            description="程式碼審查的標準流程和檢查清單",
            steps=[
                "1. 作者準備 → 確保程式碼通過本地測試",
                "2. 描述變更 → 說明目的和影響範圍",
                "3. 審查者檢視 → 依檢查清單逐項確認",
                "4. 討論 → 在 PR 中留下評論",
                "5. 核准/請求修改 → 依據評論決定",
                "6. 合併 → 由作者或維護者合併"
            ],
            do_list=[
                "每次審查不超過 400 行",
                "24 小時內回應評論",
                "使用自動化工具先檢查 (lint, test)",
                "表揚好的程式碼設計"
            ],
            dont_list=[
                "不要進行人身攻擊",
                "不要忽視小型 PR 的審查",
                "不要在未理解前就批准"
            ],
            use_cases=["Pull Request 審查", "代碼品質把關", "知識傳遞"],
            effectiveness=0.88
        ))
        
        # 企業實踐 - Database Migration
        self.add_best_practice(BestPractice(
            id="bp-005",
            title="Database Migration Strategy",
            category="data",
            description="安全執行資料庫遷移的最佳實踐",
            steps=[
                "1. 備份 → 完整資料庫備份",
                "2. 測試 → 在 staging 環境演練",
                "3. 向前 → 創建新結構和新欄位",
                "4. 資料遷移 → 批次遷移舊資料",
                "5. 驗證 → 確認資料完整性",
                "6. 向後 → 舊程式相容性 (如有)",
                "7. 監控 → 觀察效能和錯誤"
            ],
            do_list=[
                "永遠先備份",
                "使用 transaction 包裝",
                "分批次遷移大量資料",
                "保留回滾計畫"
            ],
            dont_list=[
                "不要在高峰時段執行遷移",
                "不要刪除欄位，只rename",
                "不要忽略預估的執行時間"
            ],
            use_cases=["Schema 變更", "索引創建", "資料清理"],
            effectiveness=0.91
        ))
    
    def add_pattern(self, pattern: Pattern):
        """新增模式"""
        self.patterns[pattern.id] = pattern
    
    def add_best_practice(self, practice: BestPractice):
        """新增最佳實踐"""
        self.best_practices[practice.id] = practice
    
    def search_patterns(self, query: str, 
                      category: str = None,
                      tags: List[str] = None) -> List[Pattern]:
        """
        搜尋模式
        
        Args:
            query: 搜尋關鍵詞
            category: 分類過濾
            tags: 標籤過濾
            
        Returns:
            符合的 Pattern 列表
        """
        results = []
        
        for pattern in self.patterns.values():
            # 檢查關鍵詞
            query_lower = query.lower()
            matches_query = (
                query_lower in pattern.name.lower() or
                query_lower in pattern.description.lower() or
                query_lower in pattern.problem.lower() or
                query_lower in pattern.solution.lower()
            )
            
            if not matches_query:
                continue
            
            # 檢查分類
            if category and pattern.category != category:
                continue
            
            # 檢查標籤
            if tags:
                if not any(tag in pattern.tags for tag in tags):
                    continue
            
            results.append(pattern)
        
        # 按評分排序
        results.sort(key=lambda p: -p.rating)
        
        return results
    
    def search_best_practices(self, query: str,
                             category: str = None) -> List[BestPractice]:
        """搜尋最佳實踐"""
        results = []
        query_lower = query.lower()
        
        for practice in self.best_practices.values():
            matches = (
                query_lower in practice.title.lower() or
                query_lower in practice.description.lower()
            )
            
            if not matches:
                continue
            
            if category and practice.category != category:
                continue
            
            results.append(practice)
        
        return results
    
    def find_similar_scenario(self, scenario: str) -> Optional[Pattern]:
        """
        根據場景找到類似的解決方案
        
        Args:
            scenario: 場景描述
            
        Returns:
            最相似的 Pattern 或 None
        """
        patterns = self.search_patterns(scenario)
        
        if patterns:
            # 更新使用次數
            best = patterns[0]
            best.usage_count += 1
            return best
        
        return None
    
    def get_recommendations(self, context: str, limit: int = 5) -> List[Dict]:
        """
        根據上下文取得推薦
        
        Args:
            context: 當前上下文
            limit: 返回數量
            
        Returns:
            推薦的模式和實踐
        """
        recommendations = []
        
        # 搜尋相關模式
        patterns = self.search_patterns(context)[:limit]
        for p in patterns:
            recommendations.append({
                "type": "pattern",
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "rating": p.rating,
                "usage_count": p.usage_count,
            })
        
        # 搜尋相關實踐
        practices = self.search_best_practices(context)[:limit // 2]
        for bp in practices:
            recommendations.append({
                "type": "best_practice",
                "id": bp.id,
                "name": bp.title,
                "description": bp.description,
                "effectiveness": bp.effectiveness,
            })
        
        return recommendations
    
    def generate_report(self) -> str:
        """生成知識庫報告"""
        categories = defaultdict(list)
        for pattern in self.patterns.values():
            categories[pattern.category].append(pattern)
        
        report = f"""
# 📚 知識庫報告

## 統計

| 指標 | 數值 |
|------|------|
| 總模式數 | {len(self.patterns)} |
| 總實踐數 | {len(self.best_practices)} |
| 分類數 | {len(categories)} |

---

## 分類

"""
        
        for category, patterns in sorted(categories.items()):
            avg_rating = sum(p.rating for p in patterns) / len(patterns)
            report += f"\n### {category.title()}\n\n"
            report += f"| 模式 | 評分 | 使用次數 |\n"
            report += f"|------|------|------|\n"
            
            for p in patterns:
                report += f"| {p.name} | {p.rating:.1f} | {p.usage_count} |\n"
        
        report += "\n\n## 熱門模式\n\n"
        
        top_patterns = sorted(
            self.patterns.values(),
            key=lambda p: -p.usage_count
        )[:5]
        
        for p in top_patterns:
            report += f"- {p.name} (使用 {p.usage_count} 次)\n"
        
        return report
    
    def save(self):
        """保存知識庫"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        data = {
            "patterns": {
                k: v.__dict__ for k, v in self.patterns.items()
            },
            "best_practices": {
                k: v.__dict__ for k, v in self.best_practices.items()
            }
        }
        
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def load(self):
        """載入知識庫"""
        if not os.path.exists(self.db_path):
            return
        
        with open(self.db_path, 'r') as f:
            data = json.load(f)
        
        # 恢復模式
        for k, v in data.get("patterns", {}).items():
            pattern = Pattern(**v)
            self.patterns[k] = pattern
        
        # 恢復實踐
        for k, v in data.get("best_practices", {}).items():
            practice = BestPractice(**v)
            self.best_practices[k] = practice


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    kb = KnowledgeBase()
    
    print("=== Search Patterns ===")
    results = kb.search_patterns("cost optimization")
    for p in results:
        print(f"- {p.name} ({p.rating}★)")
    
    print("\n=== Find Similar ===")
    pattern = kb.find_similar_scenario("I need to route tasks to multiple agents")
    if pattern:
        print(f"Found: {pattern.name}")
        print(f"Problem: {pattern.problem}")
    
    print("\n=== Recommendations ===")
    recs = kb.get_recommendations("multi-agent coordination", limit=3)
    for r in recs:
        print(f"- [{r['type']}] {r['name']}")
    
    print("\n=== Report ===")
    print(kb.generate_report())
