#!/usr/bin/env python3
"""
Methodology CLI - 統一命令列介面

使用方法：
    python cli.py init "專案名"
    python cli.py task add "任務" --points 5
    python cli.py sprint create
    python cli.py board
    python cli.py report
    python cli.py status
"""

import sys
import os
import argparse
import json
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from progress_dashboard import ProgressDashboard
from gantt_chart import GanttChart, ResourceGanttChart
from message_bus import MessageBus
from sprint_planner import SprintPlanner
from pm_terminology import PMTerminologyMapper
from resource_dashboard import ResourceDashboard
from pm_mode import PMMode
from agent_evaluator import AgentEvaluator, HumanEvaluator, TestCase, EvaluationSuite
from structured_output import StructuredOutputEngine
from data_quality import DataQualityChecker
from enterprise_hub import EnterpriseHub
from langgraph_migrator import LangGraphMigrationTool
from crewai_bridge import FrameworkBridge, bridge_quick_convert
from wizard.wizard import SetupWizard, TEMPLATES
from guardrails.guardrails import Guard
from autoscaler.autoscaler import AutoScaler
from data_connector import DataSourceManager
from agent_debugger import AgentDebugger, EventType
from approval_flow import ApprovalFlow, ApprovalLevel, ApprovalStatus
from risk_registry import RiskRegistry, RiskLevel, RiskStatus
from p2p_team_config import P2PTeamConfig
from hitl_controller import HITLController, AgentOwner, OutputStatus


class MethodologyCLI:
    """統一 CLI 入口"""
    
    VERSION = "5.12.0"
    
    def __init__(self):
        self.progress = ProgressDashboard()
        self.gantt = GanttChart()
        self.bus = MessageBus()
        self.sprint_planner = SprintPlanner()
        self.terminology = PMTerminologyMapper()
        self.pm_mode = PMMode()
        self.evaluator = AgentEvaluator()
        self.hitl = HumanEvaluator()
        self.structured = StructuredOutputEngine()
        self.data_quality = DataQualityChecker()
        self.enterprise = EnterpriseHub()
        self.migrator = LangGraphMigrationTool()
        self.bridge = FrameworkBridge()
        self.wizard = SetupWizard()
        self.guardrails = Guard()
        self.autoscaler = AutoScaler()
        self.resources = ResourceDashboard()
        self.data_manager = DataSourceManager()
        self.debugger = AgentDebugger()
        self.approval_flow = ApprovalFlow()
        self.registry = RiskRegistry()
        self.p2p_config: P2PTeamConfig = None
        self.hitl_controller = HITLController()
    
    def run(self, args):
        """執行命令"""
        command = args.command
        
        if command == "init":
            return self.cmd_init(args)
        elif command == "task":
            return self.cmd_task(args)
        elif command == "sprint":
            return self.cmd_sprint(args)
        elif command == "board":
            return self.cmd_board(args)
        elif command == "gantt-resource":
            return self.cmd_gantt_resource(args)
        elif command == "report":
            return self.cmd_report(args)
        elif command == "status":
            return self.cmd_status(args)
        elif command == "resources":
            return self.cmd_resources(args)
        elif command == "bus":
            return self.cmd_bus(args)
        elif command == "version":
            return self.cmd_version(args)
        elif command == "term":
            return self.cmd_term(args)
        elif command == "pm":
            return self.cmd_pm(args)
        elif command == "eval":
            return self.cmd_eval(args)
        elif command == "quality":
            return self.cmd_quality(args)
        elif command == "enterprise":
            return self.cmd_enterprise(args)
        elif command == "migrate":
            return self.cmd_migrate(args)
        elif command == "wizard":
            return self.cmd_wizard(args)
        elif command == "guardrails":
            return self.cmd_guardrails(args)
        elif command == "scale":
            return self.cmd_scale(args)
        elif command == "parse":
            return self.cmd_parse(args)
        elif command == "resources":
            return self.cmd_resources(args)
        elif command == "debug":
            return self.cmd_debug(args)
        elif command == "trace":
            return self.cmd_trace(args)
        elif command == "approval":
            return self.cmd_approval(args)
        elif command == "risk":
            return self.cmd_risk(args)
        elif command == "p2p":
            return self.cmd_p2p(args)
        elif command == "hitl":
            return self.cmd_hitl(args)
        else:
            pass # Removed print-debug
            return 1
        
        return 0
    
    # ==================== Commands ====================
    
    def cmd_init(self, args):
        """初始化專案"""
        project_name = args.name or "my-project"
        
        pass # Removed print-debug
        
        # Create project structure
        dirs = [".methodology", ".methodology/tasks", ".methodology/sprints"]
        for d in dirs:
            os.makedirs(d, exist_ok=True)
        
        # Save initial state
        self.progress.save()
        
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
        
        return 0
    
    def cmd_task(self, args):
        """任務管理"""
        action = args.action
        
        if action == "add":
            item_id = self.progress.add_to_backlog(
                args.title or "New Task",
                story_points=args.points or 1,
                priority=args.priority or 3
            )
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            
        elif action == "list":
            self.progress.load()
            items = list(self.progress.backlog.values())
            if not items:
                pass # Removed print-debug
                return 0
            
            pass # Removed print-debug
            pass # Removed print-debug
            for item in items:
                pass # Removed print-debug
            
        elif action == "complete":
            if self.progress.mark_item_completed(args.task_id):
                pass # Removed print-debug
            else:
                pass # Removed print-debug
        
        return 0
    
    def cmd_sprint(self, args):
        """Sprint 管理"""
        action = args.action
        
        if action == "create":
            sprint = self.sprint_planner.create_sprint(
                name=args.name or "Sprint 1",
                start_date=args.start or datetime.now().strftime("%Y-%m-%d"),
                end_date=args.end or (datetime.now().replace(day=14)).strftime("%Y-%m-%d"),
                capacity=args.capacity or 40
            )
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            
        elif action == "list":
            sprints = list(self.sprint_planner.sprints.values())
            if not sprints:
                pass # Removed print-debug
                return 0
            
            pass # Removed print-debug
            pass # Removed print-debug
            for s in sprints:
                status = "active" if s.is_active else ("completed" if s.is_completed else "planning")
                pass # Removed print-debug
        
        elif action == "start":
            if self.sprint_planner.start_sprint(args.sprint_id):
                pass # Removed print-debug
            else:
                pass # Removed print-debug
        
        return 0
    
    def cmd_board(self, args):
        """開啟視覺化儀表板"""
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
        
        # Progress
        summary = {"total_items": len(self.progress.backlog), "completed_items": sum(1 for i in self.progress.backlog.values() if i.completed)}
        
        pass # Removed print-debug
        if summary:
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
        else:
            pass # Removed print-debug
        
        pass # Removed print-debug
        
        # Gantt
        if self.gantt.tasks:
            pass # Removed print-debug
            pass # Removed print-debug
        else:
            pass # Removed print-debug
        
        pass # Removed print-debug
        
        # Message Bus
        pass # Removed print-debug
        pass # Removed print-debug
        
        return 0
    
    def cmd_report(self, args):
        """生成報告"""
        report_type = args.type or "weekly"
        
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
        
        # Progress
        pass # Removed print-debug
        summary = {"total_items": len(self.progress.backlog), "completed_items": sum(1 for i in self.progress.backlog.values() if i.completed)}
        if summary:
            for key, value in summary.items():
                pass # Removed print-debug
        pass # Removed print-debug
        
        # Data sources
        pass # Removed print-debug
        connections = self.data_manager.list_connections()
        if connections:
            for conn in connections:
                status = "✅" if conn['connected'] else "❌"
                pass # Removed print-debug
        else:
            pass # Removed print-debug
        pass # Removed print-debug
        
        # Save report
        if args.output:
            with open(args.output, 'w') as f:
                f.write(f"# {report_type.upper()} Report\n\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n\n")
                f.write(json.dumps(summary, indent=2, default=str))
            pass # Removed print-debug
        
        return 0
    
    def cmd_status(self, args):
        """顯示狀態"""
        self.progress.load()
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
        
        # Tasks
        items = list(self.progress.backlog.values())
        pass # Removed print-debug
        
        # Sprints
        sprints = list(self.sprint_planner.sprints.values())
        active = sum(1 for s in sprints if s.is_active)
        pass # Removed print-debug
        
        # Message Bus
        bus_status = self.bus.get_queue_status()
        pass # Removed print-debug
        
        # Data Sources
        connections = self.data_manager.list_connections()
        connected = sum(1 for c in connections if c['connected'])
        pass # Removed print-debug
        
        return 0
    
    def cmd_resources(self, args):
        """資源管理"""
        action = args.action
        
        if action == "list":
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
        
        return 0
    
    def cmd_bus(self, args):
        """Message Bus 管理"""
        action = args.action
        
        if action == "status":
            pass # Removed print-debug
        
        elif action == "tree":
            pass # Removed print-debug
        
        elif action == "watch":
            seconds = args.seconds or 10
            pass # Removed print-debug
            self.bus.watch(seconds)
        
        return 0
    
    def cmd_eval(self, args):
        """Agent Evaluation"""
        action = args.eval_action
        
        if action == "create":
            suite = self.evaluator.create_suite(
                name=args.name or "Test Suite",
                description=args.description or "",
                iterations=args.iterations or 1
            )
            pass # Removed print-debug
            pass # Removed print-debug
            return 0
        
        elif action == "list":
            suites = list(self.evaluator.suites.values())
            if not suites:
                pass # Removed print-debug
                return 0
            
            pass # Removed print-debug
            pass # Removed print-debug
            for s in suites:
                pass # Removed print-debug
            return 0
        
        elif action == "report":
            if not args.suite_id:
                pass # Removed print-debug
                return 1
            
            if args.suite_id not in self.evaluator.suites:
                pass # Removed print-debug
                return 1
            
            pass # Removed print-debug
            return 0
        
        elif action == "run":
            if not args.suite_id:
                pass # Removed print-debug
                return 1
            
            if args.suite_id not in self.evaluator.suites:
                pass # Removed print-debug
                return 1
            
            # 定義簡單的 mock agent
            import time
            def mock_agent(prompt, context=None, timeout=30):
                time.sleep(0.1)
                return f"Response to: {prompt[:50]}..."
            
            pass # Removed print-debug
            self.evaluator.run_suite(args.suite_id, mock_agent)
            pass # Removed print-debug
            return 0
        
        elif action == "add":
            if not args.suite_id:
                pass # Removed print-debug
                return 1
            
            if not args.name:
                pass # Removed print-debug
                return 1
            
            test = self.evaluator.add_test_case(
                suite_id=args.suite_id,
                name=args.name,
                input_prompt=args.prompt or "Test prompt",
                expected_output=args.expected
            )
            pass # Removed print-debug
            return 0
        
        elif action == "hitl":
            pending = self.hitl.get_pending_count()
            pass # Removed print-debug
            pass # Removed print-debug
            return 0
        
        pass # Removed print-debug
        return 1
    
    def cmd_quality(self, args):
        """Data Quality Checker"""
        action = args.action
        
        if action == "check":
            pass # Removed print-debug
            pass # Removed print-debug
            # Generate sample data
            sample_data = [
                {"id": 1, "name": "Alice", "email": "alice@test.com", "age": 30},
                {"id": 2, "name": "Bob", "email": "bob@test.com", "age": 25},
                {"id": 3, "name": "", "email": "invalid", "age": None},
            ]
            report = self.data_quality.analyze(sample_data)
            pass # Removed print-debug
        elif action == "report":
            pass # Removed print-debug
        return 0
    
    def cmd_enterprise(self, args):
        """Enterprise Integration Hub"""
        action = args.action
        
        if action == "status":
            pass # Removed print-debug
            pass # Removed print-debug
            status = self.enterprise.get_status()
            for k, v in status.items():
                pass # Removed print-debug
        elif action == "audit":
            pass # Removed print-debug
        return 0
    
    def cmd_wizard(self, args):
        """Setup Wizard"""
        pass # Removed print-debug
        pass # Removed print-debug
        wizard = SetupWizard()
        
        # Interactive setup
        project_name = input("Project name: ") or "my-agent-project"
        use_case = input("Use case (customer_service/coding/research/data_analysis/custom): ") or "customer_service"
        
        config = wizard.create_project(
            name=project_name,
            use_case=use_case
        )
        
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
        return 0
    
    def cmd_guardrails(self, args):
        """Security Guardrails"""
        action = args.action
        
        if action == "check":
            text = args.text or "Sample text to check"
            try:
                result = self.guardrails.check(text)
                pass # Removed print-debug
                pass # Removed print-debug
                pass # Removed print-debug
                pass # Removed print-debug
                if result.threats:
                    pass # Removed print-debug
                    for threat in result.threats:
                        pass # Removed print-debug
            except Exception as e:
                pass # Removed print-debug
                pass # Removed print-debug
        return 0
    
    def cmd_scale(self, args):
        """AutoScaler"""
        action = args.action
        
        if action == "status":
            status = self.autoscaler.get_status()
            pass # Removed print-debug
            pass # Removed print-debug
            for k, v in status.items():
                pass # Removed print-debug
        elif action == "scale":
            current = int(args.current or 1)
            target = self.autoscaler.calculate_target_instances(current)
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
        return 0
    
    def cmd_migrate(self, args):
        """LangGraph / CrewAI Migration Tool"""
        if not args.file:
            pass # Removed print-debug
            return 1

        from_framework = getattr(args, 'from', None)
        to_framework = getattr(args, 'to', None)

        # Cross-framework migration
        if from_framework and to_framework:
            if from_framework == to_framework:
                pass # Removed print-debug
                return 1

            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug

            report = bridge_quick_convert(args.file, from_framework, to_framework)

            if report.success:
                pass # Removed print-debug
                pass # Removed print-debug
                pass # Removed print-debug
                pass # Removed print-debug

                # Validate
                success, messages = self.bridge.validate_migration(
                    args.file, report.output_file,
                    f"{from_framework}_to_{to_framework}"
                )
                for msg in messages:
                    pass # Removed print-debug
            else:
                pass # Removed print-debug
                for err in report.errors:
                    pass # Removed print-debug

            return 0

        # Default: LangGraph migration (backward compatible)
        pass # Removed print-debug
        result = self.migrator.analyze_file(args.file)
        pass # Removed print-debug
        return 0
    
    def cmd_parse(self, args):
        """Structured Output Engine"""
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
        return 0
    
    def cmd_pm(self, args):
        """PM Mode"""
        action = args.action
        
        if action == "report":
            report = self.pm_mode.generate_morning_report(
                sprint_name="Sprint 5",
                sprint_progress=65.0,
                completed_yesterday=["完成登入功能", "修復認證 Bug"],
                planned_today=["開發儀表板", "API 文件"],
                blockers=["等不及第三方 API 文件"],
                velocity=42.0
            )
            pass # Removed print-debug
        elif action == "forecast":
            forecast = self.pm_mode.predict_cost(
                project_name="AI Assistant",
                current_cost=500.0,
                budget=2000.0,
                daily_burn_rate=85.0,
                days_remaining=18
            )
            pass # Removed print-debug
        elif action == "health":
            health = self.pm_mode.get_sprint_health(velocity=35, planned=50, completed=30)
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
        return 0
    
    def cmd_term(self, args):
        """術語查詢"""
        query = args.query
        if query:
            results = self.terminology.search(query)
            if results:
                pass # Removed print-debug
                for r in results[:5]:
                    pass # Removed print-debug
                    pass # Removed print-debug
                    pass # Removed print-debug
                    pass # Removed print-debug
                    pass # Removed print-debug
            else:
                pass # Removed print-debug
        else:
            pass # Removed print-debug
        return 0
    
    def cmd_resources(self, args):
        """資源儀表板"""
        action = args.action
        
        if action == "list":
            pass # Removed print-debug
        elif action == "stats":
            summary = self.resources.get_resource_summary()
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
        elif action == "skills":
            matrix = self.resources.get_team_skills_matrix()
            pass # Removed print-debug
            for skill, members in matrix.items():
                pass # Removed print-debug
        return 0
    
    def cmd_debug(self, args):
        """Agent Debug - 查看追蹤"""
        action = args.action
        
        if action == "status":
            print(self.debugger.to_table())
        
        elif action == "stats":
            agent_id = args.agent_id
            if agent_id:
                stats = self.debugger.get_stats(agent_id)
                print(f"\n📊 Debug Stats for: {agent_id}")
                for k, v in stats.items():
                    pass # Removed print-debug
            else:
                print(self.debugger.get_stats())
        
        elif action == "list":
            agent_id = args.agent_id
            if not agent_id:
                pass # Removed print-debug
                return 1
            events = self.debugger.get_trace(agent_id, limit=args.limit or 20)
            if not events:
                pass # Removed print-debug
                return 0
            pass # Removed print-debug
            pass # Removed print-debug
            for event in events:
                pass # Removed print-debug
                if event.get('data'):
                    for k, v in event['data'].items():
                        pass # Removed print-debug
        
        elif action == "clear":
            if args.agent_id:
                self.debugger.clear(args.agent_id)
                pass # Removed print-debug
            else:
                self.debugger.clear()
                pass # Removed print-debug
        
        elif action == "enable":
            self.debugger.enable_debug()
            self.bus.enable_debug()
            print("✅ Debug mode enabled")
        
        elif action == "disable":
            self.debugger.disable_debug()
            self.bus.disable_debug()
            print("✅ Debug mode disabled")
        
        return 0
    
    def cmd_trace(self, args):
        """Agent Trace - 視覺化追蹤"""
        agent_id = args.agent_id
        
        if not agent_id:
            pass # Removed print-debug
            return 1
        
        if args.action == "view":
            # 視覺化 trace
            print(self.debugger.visualize(agent_id, max_events=args.limit or 50))
        
        elif args.action == "correlation":
            # 視覺化 correlation
            correlation_id = args.correlation
            if correlation_id:
                print(self.debugger.visualize_correlation(correlation_id))
            else:
                pass # Removed print-debug
                return 1
        
        elif args.action == "export":
            # 導出 JSON
            json_data = self.debugger.export(agent_id)
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(json_data)
                pass # Removed print-debug
            else:
                pass # Removed print-debug
        
        return 0
    
    def cmd_approval(self, args):
        """人類審批管理"""
        action = args.action
        
        if action == "list":
            pending = self.approval_flow.get_pending()
            if not pending:
                pass # Removed print-debug
                return 0
            pass # Removed print-debug
            pass # Removed print-debug
            for p in pending:
                pass # Removed print-debug
            return 0
        
        elif action == "create":
            req_id = self.approval_flow.create_request(
                name=args.name or "New Approval Request",
                description=args.description or "",
                requester=args.requester or "user",
                requester_name=args.requester_name or "",
                approval_type=args.approval_type or "general",
            )
            pass # Removed print-debug
            return 0
        
        elif action == "approve":
            if not args.request_id:
                pass # Removed print-debug
                return 1
            level = None
            if args.level:
                try:
                    level = ApprovalLevel(args.level)
                except ValueError:
                    pass # Removed print-debug
                    return 1
            result = self.approval_flow.approve(args.request_id, args.approver or "user",
                                               comment=args.comment or "", level=level)
            if result:
                pass # Removed print-debug
            else:
                pass # Removed print-debug
            return 0
        
        elif action == "reject":
            if not args.request_id:
                pass # Removed print-debug
                return 1
            level = None
            if args.level:
                try:
                    level = ApprovalLevel(args.level)
                except ValueError:
                    pass # Removed print-debug
                    return 1
            result = self.approval_flow.reject(args.request_id, args.approver or "user",
                                              comment=args.comment or "", level=level)
            if result:
                pass # Removed print-debug
            else:
                pass # Removed print-debug
            return 0
        
        elif action == "show":
            if not args.request_id:
                pass # Removed print-debug
                return 1
            request = self.approval_flow.get_request(args.request_id)
            if not request:
                pass # Removed print-debug
                return 1
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            for i, step in enumerate(request.steps):
                marker = "→" if i == request.current_step_index else ("✓" if step.status != ApprovalStatus.PENDING else " ")
                pass # Removed print-debug
                for approval in step.approvals:
                    pass # Removed print-debug
            pass # Removed print-debug
            return 0
        
        elif action == "report":
            pass # Removed print-debug
            return 0
        
        elif action == "stats":
            stats = self.approval_flow.get_statistics()
            pass # Removed print-debug
            pass # Removed print-debug
            for k, v in stats.items():
                pass # Removed print-debug
            return 0
        
        pass # Removed print-debug
        return 1

    def cmd_risk(self, args):
        """風險登記表管理"""
        action = args.action

        if action == "add":
            risk = self.registry.add_risk(
                title=args.title,
                description=args.desc or "",
                level=RiskLevel.from_string(args.level) if args.level else RiskLevel.MEDIUM,
                owner=args.owner or "unassigned",
                impact=args.impact or "",
                probability=args.probability or 0.5,
                mitigation=args.mitigation or "",
            )
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            return 0

        elif action == "list":
            level_filter = args.level
            status_filter = args.status

            if level_filter:
                risks = self.registry.get_risks_by_level(RiskLevel.from_string(level_filter))
            elif status_filter:
                risks = self.registry.get_risks_by_status(RiskStatus.from_string(status_filter))
            else:
                risks = self.registry.get_all_risks()

            if not risks:
                pass # Removed print-debug
                return 0

            pass # Removed print-debug
            pass # Removed print-debug
            for r in risks:
                pass # Removed print-debug
            return 0

        elif action == "show":
            risk = self.registry.get_risk(args.risk_id)
            if not risk:
                pass # Removed print-debug
                return 1
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            if risk.mitigated_at:
                pass # Removed print-debug
            if risk.closed_at:
                pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            return 0

        elif action == "close":
            if self.registry.update_risk_status(args.risk_id, RiskStatus.CLOSED):
                pass # Removed print-debug
            else:
                pass # Removed print-debug
            return 0

        elif action == "mitigate":
            if self.registry.update_risk_status(args.risk_id, RiskStatus.MITIGATED):
                pass # Removed print-debug
            else:
                pass # Removed print-debug
            return 0

        elif action == "report":
            pass # Removed print-debug
            return 0

        elif action == "stats":
            summary = self.registry.get_summary()
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            for k, v in summary['by_status'].items():
                pass # Removed print-debug
            pass # Removed print-debug
            for k, v in summary['by_level'].items():
                pass # Removed print-debug
            return 0

        elif action == "delete":
            if self.registry.delete_risk(args.risk_id):
                pass # Removed print-debug
            else:
                pass # Removed print-debug
            return 0

        pass # Removed print-debug
        return 1

    def cmd_p2p(self, args):
        """P2P 團隊配置管理"""
        action = args.p2p_action
        cache_path = ".p2p_team_cache.json"

        if action == "init":
            try:
                self.p2p_config = P2PTeamConfig.from_json(args.config_path)
            except FileNotFoundError as e:
                pass # Removed print-debug
                return 1
            except json.JSONDecodeError as e:
                pass # Removed print-debug
                return 1

            if not self.p2p_config.validate():
                pass # Removed print-debug
                return 1

            # Persist to cache for stateless access
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(self.p2p_config.to_dict(), f, indent=2, ensure_ascii=False)

            summary = self.p2p_config.summary()
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            return 0

        # Reload from cache for status/list
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    self.p2p_config = P2PTeamConfig.from_dict(json.load(f))
            except Exception:
                self.p2p_config = None

        if self.p2p_config is None:
            pass # Removed print-debug
            return 1

        if action == "status":
            summary = self.p2p_config.summary()
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            return 0

        if action == "list":
            members = self.p2p_config.list_agents()
            if not members:
                pass # Removed print-debug
                return 0
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            for m in members:
                spawn = "✅" if m["canSpawnSubagent"] else "❌"
                memory = "✅" if m["peerMemoryEnabled"] else "❌"
                pass # Removed print-debug
            return 0

        pass # Removed print-debug
        return 1

    def cmd_hitl(self, args):
        """HITL 人類介入管理"""
        action = args.action
        
        if action == "register":
            # 註冊負責人
            owner = AgentOwner(
                owner_id=args.owner_id,
                name=args.name or "",
                email=args.email or "",
                role=args.role or "Owner",
            )
            if self.hitl_controller.register_owner(owner):
                pass # Removed print-debug
            else:
                pass # Removed print-debug
            return 0
        
        elif action == "list":
            # 列出負責人或產出
            if args.list_type == "owners":
                owners = self.hitl_controller.list_owners()
                if not owners:
                    pass # Removed print-debug
                    return 0
                pass # Removed print-debug
                pass # Removed print-debug
                for o in owners:
                    pass # Removed print-debug
                return 0
            elif args.list_type == "outputs":
                outputs = self.hitl_controller.get_outputs_by_status(OutputStatus(args.status_filter)) if args.status_filter else list(self.hitl_controller.outputs.values())
                if not outputs:
                    pass # Removed print-debug
                    return 0
                pass # Removed print-debug
                pass # Removed print-debug
                for o in outputs:
                    pass # Removed print-debug
                return 0
            elif args.list_type == "pending":
                pending = self.hitl_controller.get_pending_reviews(args.owner_filter)
                if not pending:
                    pass # Removed print-debug
                    return 0
                pass # Removed print-debug
                pass # Removed print-debug
                for o in pending:
                    pass # Removed print-debug
                return 0
        
        elif action == "assign":
            # 指派 Agent 給負責人
            if self.hitl_controller.assign_agent_to_owner(args.agent_id, args.owner_id):
                owner = self.hitl_controller.get_owner(args.owner_id)
                pass # Removed print-debug
            else:
                pass # Removed print-debug
            return 0
        
        elif action == "approve":
            # 批准產出
            if self.hitl_controller.approve_output(args.output_id, args.approver or "user"):
                pass # Removed print-debug
            else:
                pass # Removed print-debug
            return 0
        
        elif action == "reject":
            # 要求修改
            feedback = args.feedback or "Revision requested"
            if self.hitl_controller.request_revision(args.output_id, args.approver or "user", feedback):
                pass # Removed print-debug
                pass # Removed print-debug
            else:
                pass # Removed print-debug
            return 0
        
        elif action == "show":
            # 顯示產出詳情
            output = self.hitl_controller.get_output(args.output_id)
            if not output:
                pass # Removed print-debug
                return 1
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            if output.submitted_at:
                pass # Removed print-debug
            if output.approved_at:
                pass # Removed print-debug
            if output.feedback:
                pass # Removed print-debug
            if output.revision_count > 0:
                pass # Removed print-debug
            pass # Removed print-debug
            return 0
        
        elif action == "stats":
            # 顯示統計
            stats = self.hitl_controller.get_statistics()
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            for status, count in stats['by_status'].items():
                pass # Removed print-debug
            return 0
        
        elif action == "report":
            # 生成報告
            pass # Removed print-debug
            return 0
        
        elif action == "escalate":
            # 升級產出
            from hitl_controller import EscalationLevel
            level = EscalationLevel(args.level) if args.level else EscalationLevel.OWNER
            if self.hitl_controller.escalate_output(args.output_id, args.reason, level):
                pass # Removed print-debug
                pass # Removed print-debug
                pass # Removed print-debug
            else:
                pass # Removed print-debug
            return 0
        
        pass # Removed print-debug
        return 1

    def cmd_version(self, args):
        """顯示版本"""
        pass # Removed print-debug
        return 0


# ==================== Main ====================

def main():
    parser = argparse.ArgumentParser(
        description="Methodology - AI Agent Development Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # init
    init_parser = subparsers.add_parser("init", help="Initialize project")
    init_parser.add_argument("name", nargs="?", help="Project name")
    
    # task
    task_parser = subparsers.add_parser("task", help="Task management")
    task_parser.add_argument("action", choices=["add", "list", "complete", "sprint"],
                           help="Task action")
    task_parser.add_argument("title", nargs="?", help="Task title")
    task_parser.add_argument("--points", type=int, help="Story points")
    task_parser.add_argument("--priority", type=int, help="Priority (1-5)")
    task_parser.add_argument("--task-id", help="Task ID")
    task_parser.add_argument("--sprint-id", help="Sprint ID")
    
    # sprint
    sprint_parser = subparsers.add_parser("sprint", help="Sprint management")
    sprint_parser.add_argument("action", choices=["create", "list", "start"],
                             help="Sprint action")
    sprint_parser.add_argument("name", nargs="?", help="Sprint name")
    sprint_parser.add_argument("--start", help="Start date (YYYY-MM-DD)")
    sprint_parser.add_argument("--end", help="End date (YYYY-MM-DD)")
    sprint_parser.add_argument("--capacity", type=int, help="Capacity (points)")
    sprint_parser.add_argument("--sprint-id", help="Sprint ID")
    
    # board
    board_parser = subparsers.add_parser("board", help="Open project board")
    board_parser.add_argument("--sprint-id", help="Sprint ID")
    
    # report
    report_parser = subparsers.add_parser("report", help="Generate report")
    report_parser.add_argument("--type", choices=["daily", "weekly", "monthly"],
                             help="Report type")
    report_parser.add_argument("--output", "-o", help="Output file")
    
    # status
    subparsers.add_parser("status", help="Show status")
    
    # bus
    bus_parser = subparsers.add_parser("bus", help="Message Bus")
    bus_parser.add_argument("action", choices=["status", "tree", "watch"],
                           help="Bus action")
    bus_parser.add_argument("--seconds", type=int, help="Watch duration")
    
    # resources
    resources_parser = subparsers.add_parser("resources", help="Resource dashboard")
    resources_parser.add_argument("action", choices=["list", "stats", "skills"],
                                 help="Resource action")
    
    # term
    term_parser = subparsers.add_parser("term", help="PM terminology")
    term_parser.add_argument("query", nargs="?", help="Search term")
    
    # pm
    pm_parser = subparsers.add_parser("pm", help="PM Mode")
    pm_parser.add_argument("action", choices=["report", "forecast", "health"],
                         help="PM action")
    
    # eval
    # eval subcommands
    eval_sp = subparsers.add_parser("eval", help="Agent Evaluation")
    eval_sub = eval_sp.add_subparsers(dest="eval_action", help="Evaluation actions")
    
    # eval create
    eval_create = eval_sub.add_parser("create", help="Create evaluation suite")
    eval_create.add_argument("name", help="Suite name")
    eval_create.add_argument("--description", help="Suite description")
    eval_create.add_argument("--iterations", type=int, default=1, help="Iterations")
    
    # eval list
    eval_sub.add_parser("list", help="List evaluation suites")
    
    # eval add
    eval_add = eval_sub.add_parser("add", help="Add test case")
    eval_add.add_argument("suite_id", help="Suite ID")
    eval_add.add_argument("name", nargs="?", help="Test case name")
    eval_add.add_argument("--prompt", help="Test prompt")
    eval_add.add_argument("--expected", help="Expected output")
    
    # eval run
    eval_run = eval_sub.add_parser("run", help="Run evaluation")
    eval_run.add_argument("suite_id", help="Suite ID")
    
    # eval report
    eval_report = eval_sub.add_parser("report", help="Show evaluation report")
    eval_report.add_argument("suite_id", help="Suite ID")
    
    # eval hitl
    eval_sub.add_parser("hitl", help="Human-in-the-Loop status")
    
    # quality
    quality_parser = subparsers.add_parser("quality", help="Data Quality Checker")
    quality_parser.add_argument("action", choices=["check", "report"], default="check")
    
    # enterprise
    enterprise_parser = subparsers.add_parser("enterprise", help="Enterprise Hub")
    enterprise_parser.add_argument("action", choices=["status", "audit"], default="status")
    
    # migrate
    migrate_parser = subparsers.add_parser("migrate", help="Framework Migration (CrewAI ↔ LangGraph)")
    migrate_parser.add_argument("file", help="File to migrate")
    migrate_parser.add_argument("--from", dest="from_", choices=["crewai", "langgraph"],
                                help="Source framework")
    migrate_parser.add_argument("--to", choices=["crewai", "langgraph"],
                                help="Target framework")

    # parse
    parse_parser = subparsers.add_parser("parse", help="Structured Output Engine")
    parse_parser.add_argument("--schema", help="Schema name")
    
    # wizard
    wizard_parser = subparsers.add_parser("wizard", help="Setup Wizard")
    
    # guardrails
    guardrails_parser = subparsers.add_parser("guardrails", help="Security Guardrails")
    guardrails_parser.add_argument("action", choices=["check"], default="check")
    guardrails_parser.add_argument("--text", help="Text to check")
    
    # scale
    scale_parser = subparsers.add_parser("scale", help="AutoScaler")
    scale_parser.add_argument("action", choices=["status", "scale"], default="status")
    scale_parser.add_argument("--current", help="Current instances")
    
    # debug
    debug_parser = subparsers.add_parser("debug", help="Agent Debugger")
    debug_parser.add_argument("action", choices=["status", "stats", "list", "clear", "enable", "disable"],
                            help="Debug action")
    debug_parser.add_argument("--agent-id", help="Agent ID")
    debug_parser.add_argument("--limit", type=int, help="Limit events")
    
    # trace
    trace_parser = subparsers.add_parser("trace", help="Agent Trace Visualization")
    trace_parser.add_argument("action", choices=["view", "correlation", "export"],
                            help="Trace action")
    trace_parser.add_argument("--agent-id", help="Agent ID")
    trace_parser.add_argument("--correlation", help="Correlation ID")
    trace_parser.add_argument("--limit", type=int, help="Limit events")
    trace_parser.add_argument("--output", "-o", help="Output file")
    
    # approval
    approval_parser = subparsers.add_parser("approval", help="Human Approval Management")
    approval_parser.add_argument("action", choices=["list", "create", "approve", "reject", "show", "report", "stats"],
                                help="Approval action")
    approval_parser.add_argument("--request-id", help="Request ID")
    approval_parser.add_argument("--name", help="Request name")
    approval_parser.add_argument("--description", help="Request description")
    approval_parser.add_argument("--requester", help="Requester ID")
    approval_parser.add_argument("--requester-name", help="Requester name")
    approval_parser.add_argument("--approval-type", help="Approval type (code_review, deployment, budget)")
    approval_parser.add_argument("--approver", help="Approver ID")
    approval_parser.add_argument("--level", help="Approval level (l1, l2, l3, l4, final)")
    approval_parser.add_argument("--comment", help="Comment")

    # risk
    risk_parser = subparsers.add_parser("risk", help="Risk Registry Management")
    risk_parser.add_argument("action", choices=["add", "list", "show", "close", "mitigate", "report", "stats", "delete"],
                             help="Risk action")
    risk_parser.add_argument("--title", help="Risk title")
    risk_parser.add_argument("--desc", help="Risk description")
    risk_parser.add_argument("--level", help="Risk level (low, medium, high, critical)")
    risk_parser.add_argument("--owner", help="Risk owner")
    risk_parser.add_argument("--impact", help="Impact description")
    risk_parser.add_argument("--probability", type=float, help="Probability (0-1)")
    risk_parser.add_argument("--mitigation", help="Mitigation strategy")
    risk_parser.add_argument("--risk-id", help="Risk ID")
    risk_parser.add_argument("--status", help="Filter by status (open, mitigated, accepted, closed)")

    # p2p
    p2p_parser = subparsers.add_parser("p2p", help="P2P Team Config")
    p2p_sub = p2p_parser.add_subparsers(dest="p2p_action", help="P2P actions")
    p2p_init = p2p_sub.add_parser("init", help="Initialize team from JSON")
    p2p_init.add_argument("config_path", help="Path to team config JSON file")
    p2p_sub.add_parser("status", help="Show team status")
    p2p_sub.add_parser("list", help="List team members")

    # hitl
    hitl_parser = subparsers.add_parser("hitl", help="HITL Human-in-the-Loop Management")
    hitl_parser.add_argument("action", choices=["register", "list", "assign", "approve", "reject", "show", "stats", "report", "escalate"],
                            help="HITL action")
    hitl_parser.add_argument("owner_id", nargs="?", help="Owner ID or Output ID depending on action")
    hitl_parser.add_argument("--name", help="Owner name")
    hitl_parser.add_argument("--email", help="Owner email")
    hitl_parser.add_argument("--role", help="Owner role")
    hitl_parser.add_argument("--agent-id", dest="agent_id", help="Agent ID for assignment")
    hitl_parser.add_argument("--output-id", dest="output_id", help="Output ID")
    hitl_parser.add_argument("--approver", help="Approver ID")
    hitl_parser.add_argument("--feedback", help="Feedback/reason")
    hitl_parser.add_argument("--reason", help="Escalation reason")
    hitl_parser.add_argument("--level", help="Escalation level (owner, manager, executive)")
    hitl_parser.add_argument("--list-type", dest="list_type", choices=["owners", "outputs", "pending"], default="owners",
                           help="List type (for 'list' action)")
    hitl_parser.add_argument("--status-filter", dest="status_filter", 
                           choices=["draft", "pending_review", "approved", "revision_requested", "completed", "escalated"],
                           help="Filter outputs by status")
    hitl_parser.add_argument("--owner-filter", dest="owner_filter", help="Filter by owner ID")

    # version
    subparsers.add_parser("version", help="Show version")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    cli = MethodologyCLI()
    return cli.run(args)


if __name__ == "__main__":
    sys.exit(main())
