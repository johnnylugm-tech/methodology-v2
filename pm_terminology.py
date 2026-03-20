"""
PM Terminology Mapping - 專業術語對照表

統一不同角色對同一概念的不同稱呼：
- PM (Product Manager) / TPM (Technical PM) / 開發者
- 顧問視角：商業價值 vs 技術實現
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class Role(Enum):
    """角色"""
    PM = "product_manager"
    TPM = "technical_pm"
    DEV = "developer"
    DESIGN = "designer"
    QA = "qa"
    SCRUM_MASTER = "scrum_master"


@dataclass
class TermMapping:
    """術語對照"""
    # 基本資訊
    term_id: str
    category: str
    
    # 各角色稱呼
    pm_term: str          # PM 常用術語
    dev_term: str         # 開發者常用術語
    scrum_term: str        # Scrum 術語
    
    # 說明
    definition: str        # 定義
    example: str          # 範例
    
    # 元資料
    aliases: List[str] = field(default_factory=list)  # 別名
    related_terms: List[str] = field(default_factory=list)  # 相關術語


class PMTerminologyMapper:
    """PM 術語對照器"""
    
    # 類別
    CATEGORIES = [
        "backlog",        # 待辦事項
        "sprint",         # 迭代
        "estimation",     # 估算
        "prioritization", # 優先級
        "workflow",       # 工作流
        "metrics",        # 指標
        "quality",        # 品質
        "communication",  # 溝通
        "planning",       # 規劃
        "review",         # 審查
    ]
    
    def __init__(self):
        self.mappings: Dict[str, TermMapping] = {}
        self._build_default_mappings()
    
    def _build_default_mappings(self):
        """建立預設術語庫"""
        
        mappings = [
            # ========== Backlog ==========
            TermMapping(
                term_id="backlog",
                category="backlog",
                pm_term="待辦清單 / Backlog",
                dev_term="Task List / Issue Queue",
                scrum_term="Product Backlog / Sprint Backlog",
                definition="所有待完成工作的清單",
                example="產品待辦清單包含所有功能、改进和修復",
                aliases=["task_list", "todo_list", "issue_queue", "ticket_queue"],
                related_terms=["user_story", "epic", "task", "bug"]
            ),
            TermMapping(
                term_id="user_story",
                category="backlog",
                pm_term="使用者故事",
                dev_term="Feature Ticket / User Story",
                scrum_term="User Story",
                definition="以使用者視角描述的功能需求",
                example="身為用戶，我希望能夠登入，這樣我可以查看我的個人資料",
                aliases=["feature", "requirement", "use_case"],
                related_terms=["acceptance_criteria", "backlog", "story_points"]
            ),
            TermMapping(
                term_id="epic",
                category="backlog",
                pm_term="大型功能 / Epic",
                dev_term="Large Feature / Epic",
                scrum_term="Epic",
                definition="過大的使用者故事，需要拆分",
                example="「電子商務系統」是一個 epic，可以拆成數十個 user story",
                aliases=["large_feature", "initiative", "theme"],
                related_terms=["user_story", "backlog", "sprint"]
            ),
            TermMapping(
                term_id="bug",
                category="backlog",
                pm_term="Bug / 缺陷",
                dev_term="Bug / Defect",
                scrum_term="Defect",
                definition="程式碼中的錯誤導致功能不正常",
                example="用戶無法登入，因為驗證 API 返回錯誤",
                aliases=["defect", "issue", "problem"],
                related_terms=["task", "hotfix", "regression"]
            ),
            TermMapping(
                term_id="spike",
                category="backlog",
                pm_term="研究任務 / Spike",
                dev_term="Research Task / Tech Spike",
                scrum_term="Spike",
                definition="用於研究或原型開發的時間boxed任務",
                example="需要一個 spike 來評估新的資料庫方案",
                aliases=["research", "proof_of_concept", "poc"],
                related_terms=["task", "estimation", "story_points"]
            ),
            
            # ========== Sprint ==========
            TermMapping(
                term_id="sprint",
                category="sprint",
                pm_term="衝刺 / 迭代",
                dev_term="Sprint / Iteration / Cycle",
                scrum_term="Sprint",
                definition="固定時長的工作區間，通常 1-4 週",
                example="團隊正在完成 Sprint 5，目標是發布支付功能",
                aliases=["iteration", "cycle", "milestone"],
                related_terms=["sprint_planning", "sprint_review", "sprint_retrospective"]
            ),
            TermMapping(
                term_id="sprint_goal",
                category="sprint",
                pm_term="衝刺目標",
                dev_term="Sprint Goal / Iteration Objective",
                scrum_term="Sprint Goal",
                definition="本次衝刺要達成的核心目標",
                example="Sprint 5 的目標是完成用戶認證功能",
                aliases=["objective", "target", "aim"],
                related_terms=["sprint", "commitment", "velocity"]
            ),
            TermMapping(
                term_id="sprint_velocity",
                category="metrics",
                pm_term="團隊速度",
                dev_term="Velocity",
                scrum_term="Sprint Velocity",
                definition="團隊每個 sprint 完成的平均故事點",
                example="團隊的平均速度是 42 點/ sprint",
                aliases=["speed", "throughput"],
                related_terms=["sprint", "story_points", "capacity"]
            ),
            
            # ========== Estimation ==========
            TermMapping(
                term_id="story_points",
                category="estimation",
                pm_term="故事點",
                dev_term="Story Points / SP",
                scrum_term="Story Points",
                definition="表示任務複雜度的相對單位",
                example="這個任務估計是 5 個故事點",
                aliases=["sp", "points", "effort_points"],
                related_terms=["estimation", "planning_poker", "velocity"]
            ),
            TermMapping(
                term_id="estimation",
                category="estimation",
                pm_term="估算",
                dev_term="Estimation / Sizing",
                scrum_term="Planning Poker / Sizing",
                definition="預測任務所需工作量的過程",
                example="團隊在 sprint planning 時估算每個任務的點數",
                aliases=["sizing", "planning", "guessing"],
                related_terms=["story_points", "planning_poker", "t-shirt_sizes"]
            ),
            TermMapping(
                term_id="capacity",
                category="estimation",
                pm_term="團隊容量",
                dev_term="Team Capacity",
                scrum_term="Sprint Capacity",
                definition="團隊在 sprint 期間可用的總工作量",
                example="考慮請假和會議，團隊容量是 35 點",
                aliases=["availability", " bandwidth", "resources"],
                related_terms=["velocity", "sprint", "team_availability"]
            ),
            
            # ========== Prioritization ==========
            TermMapping(
                term_id="priority",
                category="prioritization",
                pm_term="優先級",
                dev_term="Priority / P-level",
                scrum_term="Priority / Order",
                definition="任務執行的順序重要性",
                example="P0 = 最高優先，必須這週完成",
                aliases=["urgency", "importance", "criticality"],
                related_terms=["moscow", "kano", "value_vs_effort"]
            ),
            TermMapping(
                term_id="moascow",
                category="prioritization",
                pm_term="MoSCoW 優先級",
                dev_term="Must/Should/Could/Won't",
                scrum_term="MoSCoW",
                definition="四級優先級分類法",
                example="Must have = 登入功能，Should have = 社交登入",
                aliases=["must_have", "should_have", "could_have", "wont_have"],
                related_terms=["priority", "kpi", "mvp"]
            ),
            TermMapping(
                term_id="roi",
                category="prioritization",
                pm_term="投資回報率",
                dev_term="Return on Investment",
                scrum_term="Business Value / ROI",
                definition="預期收益與成本的比值",
                example="A 功能 ROI 高，應該優先開發",
                aliases=["business_value", "value", "impact"],
                related_terms=["priority", "effort", "value_vs_effort"]
            ),
            
            # ========== Workflow ==========
            TermMapping(
                term_id="workflow",
                category="workflow",
                pm_term="工作流程",
                dev_term="Workflow / Pipeline",
                scrum_term="Workflow",
                definition="任務從建立到完成的流轉過程",
                example="我们的 workflow 是: Backlog → To Do → In Progress → Review → Done",
                aliases=["pipeline", "process", "stage"],
                related_terms=["kanban", "state_machine", "automation"]
            ),
            TermMapping(
                term_id="kanban",
                category="workflow",
                pm_term="看板",
                dev_term="Kanban Board / Task Board",
                scrum_term="Kanban",
                definition="視覺化工作流程的板子",
                example="團隊用看板追蹤所有任務的狀態",
                aliases=["board", "task_board", "trello"],
                related_terms=["workflow", "wip_limit", "cycle_time"]
            ),
            TermMapping(
                term_id="wip_limit",
                category="workflow",
                pm_term="在製品限制",
                dev_term="Work In Progress Limit / WIP",
                scrum_term="WIP Limit",
                definition="限制每個階段同時進行的任務數",
                example="In Progress 階段 WIP 限制是 3",
                aliases=["wip", "concurrent_tasks", "limit"],
                related_terms=["kanban", "flow", "bottleneck"]
            ),
            TermMapping(
                term_id="cycle_time",
                category="metrics",
                pm_term="循環時間",
                dev_term="Cycle Time",
                scrum_term="Cycle Time",
                definition="任務從開始到完成的時間",
                example="平均 cycle time 是 2.5 天",
                aliases=["lead_time", "flow_time", "turnaround_time"],
                related_terms=["lead_time", "throughput", "efficiency"]
            ),
            
            # ========== Quality ==========
            TermMapping(
                term_id="quality",
                category="quality",
                pm_term="品質",
                dev_term="Code Quality / Quality",
                scrum_term="Quality",
                definition="產品滿足需求的程度",
                example="高品質的代碼 = 可讀、可維護、可擴展",
                aliases=["code_quality", "standard", "excellence"],
                related_terms=["best_practices", "review", "testing"]
            ),
            TermMapping(
                term_id="technical_debt",
                category="quality",
                pm_term="技術債務",
                dev_term="Technical Debt / Tech Debt",
                scrum_term="Technical Debt",
                definition="為加速交付而做的短期取捨，長期需要償還",
                example="我們有技術債務：沒有單元測試、重複代碼過多",
                aliases=["tech_debt", "design_debt", "debt"],
                related_terms=["quality", "refactor", "maintainability"]
            ),
            TermMapping(
                term_id="definition_of_done",
                category="quality",
                pm_term="完成定義",
                dev_term="Definition of Done / DoD",
                scrum_term="Definition of Done",
                definition="任務被認為完成的標準清單",
                example="DoD = code + test + review + documentation",
                aliases=["dod", "done_criteria", "completion_criteria"],
                related_terms=["acceptance_criteria", "quality", "review"]
            ),
            TermMapping(
                term_id="acceptance_criteria",
                category="quality",
                pm_term="驗收標準",
                dev_term="Acceptance Criteria / AC",
                scrum_term="Acceptance Criteria",
                definition="用戶故事被接受必須滿足的條件",
                example="AC: 登入成功後顯示用戶名，失敗顯示錯誤訊息",
                aliases=["ac", "success_criteria", "验收标准"],
                related_terms=["user_story", "definition_of_done", "testing"]
            ),
            
            # ========== Metrics ==========
            TermMapping(
                term_id="kpi",
                category="metrics",
                pm_term="關鍵績效指標",
                dev_term="Key Performance Indicator",
                scrum_term="Sprint KPI",
                definition="衡量成功的關鍵指標",
                example="KPI: 交付速度、缺陷率、客戶滿意度",
                aliases=["metric", "goal", "target"],
                related_terms=["okr", "sprint_velocity", "quality"]
            ),
            TermMapping(
                term_id="burndown",
                category="metrics",
                pm_term="燃盡圖",
                dev_term="Burndown Chart",
                scrum_term="Sprint Burndown",
                definition="顯示剩餘工作隨時間變化的圖表",
                example="Sprint 結束時剛好燃盡 = 完美",
                aliases=["burndown_chart", "progress_chart"],
                related_terms=["velocity", "sprint", "capacity"]
            ),
            TermMapping(
                term_id="throughput",
                category="metrics",
                pm_term="吞吐量",
                dev_term="Throughput",
                scrum_term="Throughput",
                definition="單位時間內完成的任務數",
                example="團隊每週 throughput 是 15 個任務",
                aliases=["velocity", "completion_rate", "output"],
                related_terms=["cycle_time", "velocity", "wip"]
            ),
            
            # ========== Communication ==========
            TermMapping(
                term_id="standup",
                category="communication",
                pm_term="每日站會",
                dev_term="Daily Standup / Daily Scrum",
                scrum_term="Daily Standup",
                definition="每天短的同步會議",
                example="昨天做了什麼 / 今天要做什麼 / 有什麼阻礙",
                aliases=["daily", "scrum", "sync"],
                related_terms=["sprint", "blocker", "planning"]
            ),
            TermMapping(
                term_id="retrospective",
                category="communication",
                pm_term="回顧會議",
                dev_term="Retro / Retrospective",
                scrum_term="Sprint Retrospective",
                definition="Sprint 結束後的反思會議",
                example="什麼做得好 / 什麼可以改進 / 下次要做什麼",
                aliases=["retro", "lessons_learned", "review"],
                related_terms=["sprint", "improvement", "action_item"]
            ),
            TermMapping(
                term_id="blocker",
                category="communication",
                pm_term="阻礙 /  blocker",
                dev_term="Blocker / Blocking Issue",
                scrum_term="Impediment / Blocker",
                definition="阻止任務或團隊前進的問題",
                example="Blocker: 等不及 API 文件",
                aliases=["impediment", "blocking", "obstacle"],
                related_terms=["standup", "escalation", "risk"]
            ),
            
            # ========== Planning ==========
            TermMapping(
                term_id="planning",
                category="planning",
                pm_term="規劃",
                dev_term="Planning / Estimation Session",
                scrum_term="Sprint Planning",
                definition="決定下一個 sprint 要做什麼的會議",
                example="Sprint Planning 決定了 12 個 user story，共 45 點",
                aliases=["sprint_planning", "estimation_meeting"],
                related_terms=["sprint", "backlog", "capacity"]
            ),
            TermMapping(
                term_id="roadmap",
                category="planning",
                pm_term="產品路線圖",
                dev_term="Product Roadmap",
                scrum_term="Product Roadmap",
                definition="產品長期發展規劃的視覺化",
                example="Q2 路線圖：認證 → 支付 → 通知",
                aliases=["product_plan", "timeline", "strategy"],
                related_terms=["epic", "milestone", "planning"]
            ),
            TermMapping(
                term_id="mvp",
                category="planning",
                pm_term="最小可行產品",
                dev_term="Minimum Viable Product",
                scrum_term="MVP",
                definition="具有核心功能的最簡產品版本",
                example="MVP 版本只有登入和基本資料檢視",
                aliases=["minimum", "basic", "core_product"],
                related_terms=["launch", "feature", "priority"]
            ),
        ]
        
        for m in mappings:
            self.mappings[m.term_id] = m
    
    def get(self, term_id: str) -> Optional[TermMapping]:
        """取得術語對照"""
        return self.mappings.get(term_id)
    
    def search(self, query: str, role: Role = None) -> List[TermMapping]:
        """
        搜尋術語
        
        Args:
            query: 搜尋關鍵字
            role: 角色偏好（影響排名）
        
        Returns:
            符合的術語列表
        """
        query = query.lower()
        results = []
        
        for mapping in self.mappings.values():
            score = 0
            
            # 精確匹配 term_id
            if query == mapping.term_id:
                score += 100
            
            # 在術語中搜尋
            if query in mapping.pm_term.lower():
                score += 50
            if query in mapping.dev_term.lower():
                score += 50
            if query in mapping.scrum_term.lower():
                score += 50
            
            # 在別名中搜尋
            for alias in mapping.aliases:
                if query in alias.lower():
                    score += 30
            
            # 在定義中搜尋
            if query in mapping.definition.lower():
                score += 10
            
            if score > 0:
                results.append((score, mapping))
        
        # 排序
        results.sort(key=lambda x: -x[0])
        return [r[1] for r in results]
    
    def get_by_category(self, category: str) -> List[TermMapping]:
        """取得某類別的所有術語"""
        return [m for m in self.mappings.values() if m.category == category]
    
    def translate(self, term: str, from_role: Role, to_role: Role) -> Optional[str]:
        """
        翻譯術語（從某角色視角到另一角色）
        
        Args:
            term: 原始術語
            from_role: 來源角色
            to_role: 目標角色
        
        Returns:
            翻譯後的術語
        """
        # 嘗試找到這個術語
        for mapping in self.mappings.values():
            # 檢查是否匹配任何術語形式
            if (term.lower() == mapping.term_id or 
                term.lower() in mapping.aliases or
                term.lower() in mapping.pm_term.lower() or
                term.lower() in mapping.dev_term.lower() or
                term.lower() in mapping.scrum_term.lower()):
                
                # 根據目標角色返回對應術語
                if to_role == Role.PM:
                    return mapping.pm_term
                elif to_role == Role.DEV:
                    return mapping.dev_term
                elif to_role == Role.SCRUM_MASTER:
                    return mapping.scrum_term
        
        return None
    
    def generate_report(self) -> str:
        """產生術語對照報告"""
        lines = []
        lines.append("# PM 術語對照表")
        lines.append("")
        
        for category in self.CATEGORIES:
            terms = self.get_by_category(category)
            if not terms:
                continue
            
            lines.append(f"## {category.upper()}")
            lines.append("")
            
            for term in terms:
                lines.append(f"### {term.pm_term}")
                lines.append("")
                lines.append(f"- **PM**: {term.pm_term}")
                lines.append(f"- **Developer**: {term.dev_term}")
                lines.append(f"- **Scrum**: {term.scrum_term}")
                lines.append("")
                lines.append(f"**定義**: {term.definition}")
                lines.append(f"**範例**: {term.example}")
                if term.aliases:
                    lines.append(f"**別名**: {', '.join(term.aliases)}")
                lines.append("")
                lines.append("---")
                lines.append("")
        
        return "\n".join(lines)
    
    def to_markdown_table(self) -> str:
        """產生 Markdown 格式的表格"""
        lines = []
        lines.append("| 術語 | PM 稱呼 | Developer 稱呼 | Scrum 稱呼 |")
        lines.append("|------|---------|----------------|------------|")
        
        for mapping in sorted(self.mappings.values(), key=lambda x: x.category):
            lines.append(
                f"| {mapping.term_id} | {mapping.pm_term} | {mapping.dev_term} | {mapping.scrum_term} |"
            )
        
        return "\n".join(lines)


# ==================== CLI Interface ====================

if __name__ == "__main__":
    import sys
    
    mapper = PMTerminologyMapper()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "search" and len(sys.argv) > 2:
            query = sys.argv[2]
            results = mapper.search(query)
            print(f"\n# Search Results for '{query}':\n")
            for result in results[:5]:
                print(f"## {result.pm_term}")
                print(f"- **Definition**: {result.definition}")
                print(f"- **Dev Term**: {result.dev_term}")
                print(f"- **Scrum Term**: {result.scrum_term}")
                print()
        
        elif command == "category" and len(sys.argv) > 2:
            category = sys.argv[2]
            terms = mapper.get_by_category(category)
            print(f"\n# {category.upper()} Terms:\n")
            for term in terms:
                print(f"- {term.pm_term} ({term.term_id})")
        
        elif command == "report":
            print(mapper.generate_report())
        
        elif command == "table":
            print(mapper.to_markdown_table())
        
        elif command == "translate":
            # translate <term> <from_role> <to_role>
            if len(sys.argv) > 4:
                term, from_r, to_r = sys.argv[2], sys.argv[3], sys.argv[4]
                from_role = Role(from_r)
                to_role = Role(to_r)
                result = mapper.translate(term, from_role, to_role)
                print(f"{from_role.value} → {to_role.value}: {result}")
        
        elif command == "list":
            print("\n# Categories:")
            for cat in mapper.CATEGORIES:
                print(f"  - {cat}")
            print("\n# All Terms:")
            for m in sorted(mapper.mappings.values(), key=lambda x: x.term_id):
                print(f"  - {m.term_id}: {m.pm_term}")
        
        else:
            print("Usage:")
            print("  python pm_terminology.py search <query>")
            print("  python pm_terminology.py category <category>")
            print("  python pm_terminology.py translate <term> <from_role> <to_role>")
            print("  python pm_terminology.py report")
            print("  python pm_terminology.py table")
            print("  python pm_terminology.py list")
    else:
        # 互動模式
        print("PM Terminology Mapper")
        print("=" * 50)
        print("Commands:")
        print("  search <query> - Search for a term")
        print("  category <name> - List terms in category")
        print("  list - List all categories and terms")
        print("  report - Generate full report")
        print("  table - Generate markdown table")
        print()
        
        # 互動搜尋
        while True:
            try:
                cmd = input("> ").strip()
                if not cmd:
                    continue
                
                parts = cmd.split()
                if parts[0] == "search" and len(parts) > 1:
                    results = mapper.search(parts[1])
                    for r in results[:3]:
                        print(f"  {r.pm_term} ({r.term_id})")
                elif parts[0] == "list":
                    for m in sorted(mapper.mappings.values(), key=lambda x: x.term_id):
                        print(f"  {m.term_id}: {m.pm_term}")
                elif parts[0] == "exit":
                    break
            except (EOFError, KeyboardInterrupt):
                break
