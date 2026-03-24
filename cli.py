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
from anti_shortcut.blacklist import CommandBlacklist, ViolationSeverity
from anti_shortcut.audit_logger import AIAuditLogger, ActionType
from anti_shortcut.double_confirm import DoubleConfirmation, ConfirmationLevel
from anti_shortcut.impact_analysis import ImpactAnalyzer
from security_defense import (
    InputValidator,
    ExecutionSandbox,
    OutputFilter,
    HumanInTheLoop,
    SandboxConfig,
    SandboxLevel,
    ApprovalLevel,
)
from code_metrics import MetricsTracker


class MethodologyCLI:
    """統一 CLI 入口"""
    
    VERSION = "5.42.0"
    
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
        self.blacklist = CommandBlacklist()  # 危險操作黑名單
        self.ai_audit = AIAuditLogger()  # AI 操作審計日誌
        # Deep Security Defense
        self.input_validator = InputValidator()
        self.execution_sandbox = ExecutionSandbox(SandboxConfig(level=SandboxLevel.STRICT))
        self.output_filter = OutputFilter()
        self.hitl_security = HumanInTheLoop()
    
    def _check_command(self, command: str) -> bool:
        """檢查命令是否危險"""
        blocked = self.blacklist.check(command)
        if blocked:
            pass # Removed print-debug
            return False
        return True
    
    def run(self, args):
        """執行命令"""
        command = args.command
        
        if command == "init":
            return self.cmd_init(args)
        elif command == "finish":
            return self.cmd_finish(args)
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
        elif command == "constitution":
            return self.cmd_constitution(args)
        elif command == "constitution-sync":
            return self.cmd_constitution_sync(args)
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
        elif command == "audit":
            return self.cmd_audit(args)
        elif command == "migrate":
            return self.cmd_migrate(args)
        elif command == "wizard":
            return self.cmd_wizard(args)
        elif command == "guardrails":
            return self.cmd_guardrails(args)
        elif command == "security":
            return self.cmd_security(args)
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
        elif command == "gatekeeper":
            return self.cmd_gatekeeper(args)
        elif command == "confirmations":
            return self.cmd_confirmations(args)
        elif command == "release":
            return self.cmd_release(args)
        elif command == "policy":
            return self.cmd_policy(args)
        elif command == "install-hook":
            return self.cmd_install_hook(args)
        elif command == "enforcement-config":
            return self.cmd_enforcement_config(args)
        elif command == "enforcement":
            return self.cmd_enforcement(args)
        elif command == "quality-gate" or command == "qg":
            return self.cmd_quality_gate(args)
        elif command == "decision" or command == "dec":
            return self.cmd_decision_gate(args)
        elif command == "agent-proof-hook":
            return self.cmd_agent_proof_hook(args)
        elif command == "memory":
            return self.cmd_memory(args)
        elif command == "roi":
            return self.cmd_roi(args)
        elif command == "m27":
            return self.cmd_m27(args)
        elif command == "metrics":
            return self.cmd_metrics(args)
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
        
        # 啟動 quality_watch daemon
        import subprocess
        project_path = Path.cwd()
        subprocess.Popen(
            [sys.executable, "quality_watch.py", "start", "--project", str(project_path)],
            cwd=str(project_path)
        )
        
        print(f"✅ Initialized: {project_name}")
        print(f"🚀 Quality Watch started")
        
        return 0
    
    def cmd_finish(self, args):
        """Finish project and stop quality watch"""
        project_path = Path.cwd()
        
        # 停止 quality_watch
        result = subprocess.run(
            [sys.executable, "quality_watch.py", "stop", "--project", str(project_path)],
            capture_output=True,
            text=True
        )
        
        print(f"✅ Project finished")
        print(f"🛑 Quality Watch stopped")
        
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
    
    def cmd_audit(self, args):
        """AI Audit Logger - AI 操作審計"""
        action = args.action
        
        if action == "status":
            pass # Removed print-debug
            pass # Removed print-debug
            report = self.ai_audit.get_audit_report()
            pass # Removed print-debug
            pass # Removed print-debug
            for op_type, count in report['by_type'].items():
                pass # Removed print-debug
            pass # Removed print-debug
        
        elif action == "anomalies":
            pass # Removed print-debug
            pass # Removed print-debug
            agent_id = getattr(args, 'agent', None)
            severity = getattr(args, 'severity', None)
            
            anomalies = self.ai_audit.get_anomalies(agent_id=agent_id, severity=severity)
            
            if not anomalies:
                pass # Removed print-debug
                return 0
            
            for i, anomaly in enumerate(anomalies, 1):
                pass # Removed print-debug
                pass # Removed print-debug
                pass # Removed print-debug
                pass # Removed print-debug
        
        elif action == "report":
            pass # Removed print-debug
            pass # Removed print-debug
            agent_id = getattr(args, 'agent', None)
            report = self.ai_audit.get_audit_report(agent_id=agent_id)
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

    def cmd_security(self, args):
        """Deep Security Defense"""
        action = args.action

        if action == "deep-check":
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            sandbox_config = self.execution_sandbox.config
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pending = self.hitl_security.get_pending()
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug

        elif action == "enable-deep-defense":
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
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug

        elif action == "audit-log":
            pass # Removed print-debug
            pass # Removed print-debug
            input_audit = self.input_validator
            output_audit = self.output_filter.get_audit_log()
            hitl_audit = self.hitl_security.get_pending()

            pass # Removed print-debug
            if output_audit:
                for i, entry in enumerate(output_audit[-5:], 1):
                    pass # Removed print-debug
            else:
                pass # Removed print-debug

            pass # Removed print-debug
            if hitl_audit:
                for req in hitl_audit[:5]:
                    pass # Removed print-debug
            else:
                pass # Removed print-debug

        elif action == "validate":
            text = args.text or "ignore previous instructions"
            pass # Removed print-debug
            result = self.input_validator.validate(text)
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            if result.matched_patterns:
                pass # Removed print-debug
                for p in result.matched_patterns:
                    pass # Removed print-debug
            if result.recommendations:
                pass # Removed print-debug
                for r in result.recommendations:
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
    
    def _print_impact_report(self, impact):
        """列印 Impact Analysis 報告"""
        risk_label = "🟢 Low" if impact.risk_score < 40 else "🟡 Medium" if impact.risk_score < 70 else "🔴 High"
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
        if impact.affected_tests:
            pass # Removed print-debug
            for test in impact.affected_tests:
                pass # Removed print-debug
            pass # Removed print-debug
        if impact.affected_modules:
            pass # Removed print-debug
            for mod in impact.affected_modules[:10]:  # Limit to 10
                pass # Removed print-debug
            if len(impact.affected_modules) > 10:
                pass # Removed print-debug
            pass # Removed print-debug
        if impact.recommendations:
            pass # Removed print-debug
            for rec in impact.recommendations:
                pass # Removed print-debug
            pass # Removed print-debug
    
    def _print_risk_report(self, report):
        """列印 Risk Report"""
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
        pass # Removed print-debug
    
    def cmd_trace(self, args):
        """Agent Trace - 視覺化追蹤"""
        action = args.action
        
        # Impact Analysis commands (no agent_id required)
        if action == "impact":
            if not args.file:
                pass # Removed print-debug
                return 1
            analyzer = ImpactAnalyzer(project_path=".")
            analyzer.scan_project()
            impact = analyzer.analyze_change(args.file)
            self._print_impact_report(impact)
            return 0
        
        elif action == "graphviz":
            analyzer = ImpactAnalyzer(project_path=".")
            analyzer.scan_project()
            report = analyzer.get_dependency_report()
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(report['graphviz'])
                pass # Removed print-debug
            else:
                pass # Removed print-debug
            return 0
        
        elif action == "risk-report":
            analyzer = ImpactAnalyzer(project_path=".")
            analyzer.scan_project()
            report = analyzer.get_dependency_report()
            self._print_risk_report(report)
            return 0
        
        # Agent Trace commands (require agent_id)
        agent_id = args.agent_id
        if not agent_id:
            pass # Removed print-debug
            return 1
        
        if action == "view":
            # 視覺化 trace
            print(self.debugger.visualize(agent_id, max_events=args.limit or 50))
        
        elif action == "correlation":
            # 視覺化 correlation
            correlation_id = args.correlation
            if correlation_id:
                print(self.debugger.visualize_correlation(correlation_id))
            else:
                pass # Removed print-debug
                return 1
        
        elif action == "export":
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

    def cmd_roi(self, args):
        """ROI Dashboard"""
        from roi_tracker import ROICalculator

        calculator = ROICalculator()

        if args.subcommand == "dashboard":
            data = calculator.get_dashboard_data()
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            for period, report in data.items():
                pass # Removed print-debug
                pass # Removed print-debug
                pass # Removed print-debug
                pass # Removed print-debug
                pass # Removed print-debug
                if hasattr(report, 'recommendation') and report.recommendation:
                    pass # Removed print-debug
            pass # Removed print-debug
            return 0

        elif args.subcommand == "report":
            report = calculator.calculate(args.period)
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            return 0

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

    def cmd_constitution(self, args):
        """Constitution management"""
        subcmd = args.subcommand

        if subcmd == "view":
            from constitution import load_constitution
            pass # Removed print-debug
        elif subcmd == "thresholds":
            from constitution import get_quality_thresholds
            thresholds = get_quality_thresholds()
            pass # Removed print-debug
            for k, v in thresholds.items():
                pass # Removed print-debug
        elif subcmd == "errors":
            from constitution import get_error_levels
            levels = get_error_levels()
            pass # Removed print-debug
            for k, v in levels.items():
                pass # Removed print-debug
        elif subcmd == "check":
            pass # Removed print-debug
            # TODO: 檢查專案是否符合憲章
            pass # Removed print-debug
        elif subcmd == "edit":
            pass # Removed print-debug
            import subprocess
            subprocess.run(["open", "constitution/CONSTITUTION.md"])
        elif subcmd == "compile":
            from constitution import compile_constitution
            compiled = compile_constitution()
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
        elif subcmd == "verify":
            if not args.output:
                pass # Removed print-debug
                pass # Removed print-debug
                return 1
            from constitution import compile_constitution, verify_agent_output
            compiled = compile_constitution()
            result = verify_agent_output(compiled, args.output)
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            if result['violations']:
                pass # Removed print-debug
                for v in result['violations']:
                    pass # Removed print-debug
        else:
            pass # Removed print-debug
            pass # Removed print-debug
        return 0

    def cmd_constitution_sync(self, args):
        """Sync Constitution to Policy Engine"""
        from enforcement.constitution_policy_sync import ConstitutionPolicyGenerator
        
        generator = ConstitutionPolicyGenerator()
        policies = generator.sync()
        
        pass # Removed print-debug
        return 0

    def cmd_version(self, args):
        """顯示版本"""
        pass # Removed print-debug
        return 0

    def cmd_gatekeeper(self, args):
        """Workflow Gatekeeper"""
        from anti_shortcut.gatekeeper import Gatekeeper, Phase
        
        gk = Gatekeeper()
        action = args.action
        
        if action == "status":
            gk.print_status()
        elif action == "check":
            pass # Removed print-debug
            all_passed = gk.check_all_gates()
            gk.print_status()
            if all_passed:
                pass # Removed print-debug
                return 0
            else:
                pass # Removed print-debug
                return 1
        elif action == "enforce":
            pass # Removed print-debug
            gk.start_phase(Phase.CONSTITUTION)
            # 執行 Constitution gates
            for gate in gk.phase_records[Phase.CONSTITUTION].gates:
                gk.check_gate(gate.gate_id)
            gk.print_status()
            if gk.can_proceed_to_next_phase():
                pass # Removed print-debug
                return 0
            else:
                pass # Removed print-debug
                return 1
        return 0

    def cmd_confirmations(self, args):
        """Double Confirmation Management"""
        dc = DoubleConfirmation(timeout_minutes=30)
        action = args.action
        
        if action == "list":
            pending = dc.get_pending(operation=args.operation)
            if not pending:
                pass # Removed print-debug
                return 0
            pass # Removed print-debug
            for p in pending:
                required = 1 if p.level == ConfirmationLevel.SINGLE else 2
                pass # Removed print-debug
                pass # Removed print-debug
                pass # Removed print-debug
                pass # Removed print-debug
                pass # Removed print-debug
            return 0
        
        elif action == "confirm":
            if not args.confirmation_id or not args.confirmed_by:
                pass # Removed print-debug
                return 1
            success = dc.confirm(args.confirmation_id, args.confirmed_by)
            if success:
                status = dc.get_status(args.confirmation_id)
                if status and status.get("status") == "approved":
                    pass # Removed print-debug
                else:
                    pass # Removed print-debug
                return 0
            else:
                pass # Removed print-debug
                return 1
        
        elif action == "reject":
            if not args.confirmation_id or not args.confirmed_by:
                pass # Removed print-debug
                return 1
            success = dc.reject(args.confirmation_id, args.confirmed_by, args.reason or "")
            if success:
                pass # Removed print-debug
                return 0
            else:
                pass # Removed print-debug
                return 1
        
        elif action == "status":
            if not args.confirmation_id:
                pass # Removed print-debug
                return 1
            status = dc.get_status(args.confirmation_id)
            if status:
                pass # Removed print-debug
                pass # Removed print-debug
                pass # Removed print-debug
                pass # Removed print-debug
                pass # Removed print-debug
                pass # Removed print-debug
                pass # Removed print-debug
                if 'required' in status:
                    pass # Removed print-debug
                return 0
            else:
                pass # Removed print-debug
                return 1
        
        elif action == "check":
            if not args.operation:
                pass # Removed print-debug
                return 1
            level = dc.requires_confirmation(args.operation)
            pass # Removed print-debug
            if level == ConfirmationLevel.BLOCKED:
                pass # Removed print-debug
            elif level == ConfirmationLevel.APPROVAL:
                pass # Removed print-debug
            elif level == ConfirmationLevel.DOUBLE:
                pass # Removed print-debug
            elif level == ConfirmationLevel.SINGLE:
                pass # Removed print-debug
            return 0
        
        return 0

    def cmd_release(self, args):
        """Release Management with Double Confirmation"""
        if not args.version:
            pass # Removed print-debug
            return 1
        
        dc = DoubleConfirmation(timeout_minutes=30)
        operation = "release"
        description = f"發布版本 {args.version} 到 GitHub"
        metadata = {"version": args.version, "repo": args.repo or "main"}
        
        level = dc.requires_confirmation(operation)
        
        if level == ConfirmationLevel.BLOCKED:
            pass # Removed print-debug
            return 1
        
        if level == ConfirmationLevel.NONE:
            pass # Removed print-debug
            return 0
        
        if not args.confirm:
            pass # Removed print-debug
            pass # Removed print-debug
            conf_id = dc.create_pending(operation, description, metadata)
            if conf_id:
                pass # Removed print-debug
            return 1
        
        # 創建待確認
        conf_id = dc.create_pending(operation, description, metadata)
        
        if conf_id == "__BLOCKED__":
            pass # Removed print-debug
            return 1
        
        # Agent 確認 (第一次)
        pass # Removed print-debug
        dc.confirm(conf_id, confirmed_by="agent-cli")
        
        pending = dc._find_pending(conf_id)
        if pending:
            required = 1 if pending.level == ConfirmationLevel.SINGLE else 2
            current = len(pending.confirmations)
            pass # Removed print-debug
            
            if current < required:
                pass # Removed print-debug
                pass # Removed print-debug
                pass # Removed print-debug
                pass # Removed print-debug
                pass # Removed print-debug
                return 1
        else:
            status = dc.get_status(conf_id)
            if status and status.get("status") == "approved":
                pass # Removed print-debug
                return 0
            else:
                pass # Removed print-debug
                return 1
        
        return 0

    def cmd_policy(self, args):
        """Run Policy Engine checks"""
        from enforcement.policy_engine import create_hard_block_engine
        try:
            engine = create_hard_block_engine()
            results = engine.enforce_all()
            summary = engine.get_summary()
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            if summary['all_passed']:
                pass # Removed print-debug
                return 0
            else:
                pass # Removed print-debug
                return 1
        except Exception as e:
            pass # Removed print-debug
            return 1

    def cmd_install_hook(self, args):
        """Install pre-commit hook"""
        import shutil
        import os
        
        hook_source = os.path.join(os.path.dirname(__file__), "pre-commit.template")
        hook_dest = os.path.join(os.path.dirname(__file__), ".git", "hooks", "pre-commit")
        
        if os.path.exists(hook_dest):
            response = input(f"Overwrite existing hook at {hook_dest}? [y/N] ")
            if response.lower() != 'y':
                pass # Removed print-debug
                return 0
        
        shutil.copy(hook_source, hook_dest)
        os.chmod(hook_dest, 0o755)
        pass # Removed print-debug
        return 0

    def cmd_enforcement_config(self, args):
        """Unified Enforcement Configuration"""
        from enforcement_config import EnforcementConfig, ConfigGenerator, EnforcementMode
        
        action = args.action
        
        if not action or action == "show":
            config = EnforcementConfig.load()
            pass # Removed print-debug
        elif action == "init":
            config = ConfigGenerator.local_only()
            config.save()
            pass # Removed print-debug
            pass # Removed print-debug
        elif action == "set":
            mode = args.mode or "local"
            if mode == "github":
                config = ConfigGenerator.github_actions()
            elif mode == "gitlab":
                config = ConfigGenerator.gitlab_ci()
            elif mode == "jenkins":
                config = ConfigGenerator.jenkins()
            elif mode == "azure":
                config = ConfigGenerator.azure_pipelines()
            else:
                config = ConfigGenerator.local_only()
            config.save()
            pass # Removed print-debug
            pass # Removed print-debug
        elif action == "detect":
            config = ConfigGenerator.auto_detect()
            pass # Removed print-debug
            pass # Removed print-debug
        else:
            pass # Removed print-debug
            return 1
        return 0

    def cmd_enforcement(self, args):
        """
        Enforcement 統一 CLI

        子命令：
        - run: 執行所有 enforcement 檢查
        - check: 檢查 enforcement 狀態
        - status: 顯示摘要
        - install: 安裝 hook
        - config: 顯示/設定 enforcement 設定
        """
        from enforcement_config import EnforcementConfig, ConfigGenerator
        from enforcement import PolicyEngine, ConstitutionAsCode, EnforcementLevel
        from enforcement.execution_registry import ExecutionRegistry

        sub = args.subcommand

        if sub == "run":
            # 執行所有 enforcement 檢查
            pass # Removed print-debug
            pass # Removed print-debug

            passed = 0
            failed = 0

            # 1. Policy Engine
            pass # Removed print-debug
            try:
                engine = PolicyEngine()
                results = engine.enforce_all()
                summary = engine.get_summary()
                pass # Removed print-debug
                if summary['all_passed']:
                    passed += 1
                    pass # Removed print-debug
                else:
                    failed += 1
                    pass # Removed print-debug
            except Exception as e:
                failed += 1
                pass # Removed print-debug

            # 2. Constitution Check
            pass # Removed print-debug
            try:
                constitution = ConstitutionAsCode()
                # 嘗試從環境變數讀取 commit message
                import os
                commit_msg = os.environ.get('COMMIT_MSG', os.environ.get('GIT_COMMITMSG', ''))
                if commit_msg:
                    constitution.enforce({"commit_message": commit_msg})
                pass # Removed print-debug
                passed += 1
            except Exception as e:
                failed += 1
                pass # Removed print-debug

            # 3. 記錄到 Registry
            pass # Removed print-debug
            try:
                registry = ExecutionRegistry()
                registry.record("enforcement-run", {
                    "policy_passed": passed > 0,
                    "constitution_passed": True,
                })
                pass # Removed print-debug
            except Exception as e:
                pass # Removed print-debug

            # 總結
            pass # Removed print-debug
            if failed == 0:
                pass # Removed print-debug
                return 0
            else:
                pass # Removed print-debug
                return 1

        elif sub == "check":
            # 檢查 enforcement 狀態
            config = EnforcementConfig.load()
            pass # Removed print-debug
            return 0

        elif sub == "status":
            # 顯示摘要
            config = EnforcementConfig.load()
            pass # Removed print-debug

            # 顯示 Policy Engine 狀態
            pass # Removed print-debug
            try:
                engine = PolicyEngine()
                summary = engine.get_summary()
                pass # Removed print-debug
                pass # Removed print-debug
                pass # Removed print-debug
            except Exception as e:
                pass # Removed print-debug
            return 0

        elif sub == "install":
            # 安裝 hook
            from pathlib import Path
            import shutil

            hook_source = Path(__file__).parent / "pre-commit.template"
            hook_dest = Path(__file__).parent / ".git" / "hooks" / "pre-commit"

            if not hook_source.exists():
                pass # Removed print-debug
                return 1

            hook_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(hook_source, hook_dest)
            hook_dest.chmod(0o755)

            pass # Removed print-debug
            return 0

        elif sub == "config":
            # 顯示/設定 enforcement 設定
            if args.mode:
                mode = args.mode
                if mode == "local":
                    config = ConfigGenerator.local_only()
                elif mode == "github":
                    config = ConfigGenerator.github_actions()
                elif mode == "gitlab":
                    config = ConfigGenerator.gitlab_ci()
                elif mode == "jenkins":
                    config = ConfigGenerator.jenkins()
                elif mode == "azure":
                    config = ConfigGenerator.azure_pipelines()
                else:
                    pass # Removed print-debug
                    pass # Removed print-debug
                    return 1

                config.save()
                pass # Removed print-debug

            pass # Removed print-debug
            return 0

        else:
            pass # Removed print-debug
            pass # Removed print-debug
            return 1

    def cmd_quality_gate(self, args):
        """Quality Gate - 統一品質閘道檢查"""
        from quality_gate import UnifiedGate

        sub = args.subcommand

        if sub == "check" or sub == "all":
            print("=" * 50)
            print("Quality Gate - Unified Check")
            print("=" * 50)

            gate = UnifiedGate()
            result = gate.check_all()

            print(f"\nOverall Score: {result.overall_score}%")
            print(f"Status: {'✅ PASSED' if result.passed else '❌ FAILED'}")

            print("\nChecks:")
            for check in result.checks:
                status = "✅" if check.passed else "❌"
                print(f"  {status} {check.name}: {check.score}%")
                if check.violations:
                    for v in check.violations[:3]:
                        print(f"      - {v}")

            sys.exit(0 if result.passed else 1)

        elif sub == "doc" or sub == "docs":
            gate = UnifiedGate()
            result = gate.check_documents_only()
            print(f"Document Existence: {'✅' if result.passed else '❌'}")
            if result.violations:
                for v in result.violations:
                    print(f"  - {v}")
            sys.exit(0 if result.passed else 1)

        elif sub == "constitution":
            gate = UnifiedGate()
            result = gate.check_constitution_only()
            print(f"Constitution Compliance: {'✅' if result.passed else '❌'}")
            if result.violations:
                for v in result.violations[:5]:
                    print(f"  - {v}")
            sys.exit(0 if result.passed else 1)

        elif sub == "phase":
            gate = UnifiedGate()
            result = gate.check_phase_only()
            print(f"Phase References: {'✅' if result.passed else '❌'}")
            if result.violations:
                for v in result.violations:
                    print(f"  - {v}")
            sys.exit(0 if result.passed else 1)

        elif sub == "aspice":
            # ASPICE 合規檢查（使用 Document Existence）
            gate = UnifiedGate()
            result = gate.check_documents_only()
            print(json.dumps(result.to_dict() if hasattr(result, 'to_dict') else result, indent=2))
            sys.exit(0 if result.passed else 1)

        else:
            print(f"Unknown subcommand: {sub}")
            print("Available: check, doc, constitution, phase, aspice")
            return 1

        return 0

    def cmd_decision_gate(self, args):
        """Decision Gate - 決策分類閘道"""
        from decision_gate import DecisionRecorder

        sub = args.subcommand
        cmd_args = args.args or []

        recorder = DecisionRecorder()

        if sub == "classify" or sub == "add":
            # 新增並分類決策
            if len(cmd_args) < 2:
                print("Usage: decision classify <item> <description> [spec_ref]")
                sys.exit(1)

            item = cmd_args[0]
            description = cmd_args[1]
            spec_ref = cmd_args[2] if len(cmd_args) > 2 else None

            result = recorder.classify_and_record(item, description, spec_ref)

            print(f"✅ Decision classified:")
            print(f"   ID: {result.decision_id}")
            print(f"   Risk: {result.risk_level.value}")
            print(f"   Type: {result.decision_type.value}")
            if result.requires_confirmation:
                print(f"   ⚠️  Requires user confirmation!")
            if result.options:
                print(f"   Options: {', '.join(result.options)}")
            if result.recommendation:
                print(f"   Recommendation: {result.recommendation}")

        elif sub == "list" or sub == "ls":
            decisions = recorder.get_all()
            if not decisions:
                print("No decisions recorded yet.")
            else:
                print(f"{'ID':<10} {'Item':<20} {'Risk':<15} {'Decision':<15} {'Status':<10}")
                print("-" * 70)
                for d in decisions:
                    print(f"{d['id']:<10} {d['item']:<20} {d['risk']:<15} {d['decision']:<15} {d['status']:<10}")

        elif sub == "pending" or sub == "p":
            pending = recorder.get_pending()
            print(f"Pending decisions: {len(pending)}")
            for d in pending:
                print(f"  {d['id']}: {d['item']} ({d['risk']})")

        elif sub == "confirm":
            if len(cmd_args) < 2:
                print("Usage: decision confirm <id> <value>")
                sys.exit(1)

            decision_id = cmd_args[0]
            value = cmd_args[1]
            recorder.confirm(decision_id, value)
            print(f"✅ Decision {decision_id} confirmed: {value}")

        elif sub == "report":
            print(recorder.generate_report())

        else:
            print("Usage:")
            print("  decision classify <item> <description> [spec_ref]")
            print("  decision list")
            print("  decision pending")
            print("  decision confirm <id> <value>")
            print("  decision report")

        return 0

    def cmd_agent_proof_hook(self, args):
        """Agent-Proof Hook Management"""
        from enforcement.agent_proof_hook import AgentProofHook

        hook = AgentProofHook()

        if args.action == "install":
            hook.install(force=True)
        elif args.action == "verify":
            if not hook.verify():
                sys.exit(1)
        elif args.action == "uninstall":
            hook.uninstall()
        else:
            hook.install()

        return 0

    def cmd_memory(self, args):
        """Memory Governance CLI"""
        from memory_governance import (
            MemoryValidator,
            StateCoordinator,
            ConflictResolver,
            MemoryAudit,
            ResolutionStrategy
        )

        sub = args.subcommand

        if sub == "validate":
            # 驗證記憶
            validator = MemoryValidator()
            pass # Removed print-debug
            return 0

        elif sub == "status":
            # 顯示協調狀態
            coordinator = StateCoordinator()
            summary = coordinator.get_global_state_summary()
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            return 0

        elif sub == "audit":
            # 顯示審計日誌
            audit = MemoryAudit()
            records = audit.get_records(limit=10)
            pass # Removed print-debug
            for r in records:
                pass # Removed print-debug
            return 0

        elif sub == "resolve":
            # 解決衝突
            pass # Removed print-debug
            return 0

        return 0

    def cmd_m27(self, args):
        """M2.7 Self-Evolving Integration"""
        from m27_integration import (
            HybridAttention,
            SelfIteration,
            FailureAnalyzer,
            HarnessOptimizer,
            AttentionConfig
        )

        sub = args.sub

        if sub == "status":
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            return 0

        elif sub == "analyze":
            log = args.failure_log or "No failure log provided"
            analyzer = FailureAnalyzer()
            path = analyzer.analyze(log)
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            for r in path.recommendations:
                pass # Removed print-debug
            return 0

        elif sub == "iterate":
            pass # Removed print-debug
            pass # Removed print-debug
            return 0

        elif sub == "optimize":
            pass # Removed print-debug
            pass # Removed print-debug
            return 0

        return 0

    def cmd_metrics(self, args):
        """Code Metrics - 代碼品質指標"""
        from code_metrics import MetricsTracker

        sub = args.subcommand if hasattr(args, 'subcommand') else "report"

        tracker = MetricsTracker()

        if sub == "report" or sub == "check":
            pass # Removed print-debug
            report = tracker.generate_report()

            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug
            pass # Removed print-debug

            if report['complexity_violations']:
                pass # Removed print-debug
                for v in report['complexity_violations'][:10]:
                    pass # Removed print-debug

            if report.get('coupling'):
                pass # Removed print-debug
                pass # Removed print-debug
                pass # Removed print-debug

            pass # Removed print-debug
            return 0

        elif sub == "history":
            latest = tracker.get_latest()
            if latest:
                pass # Removed print-debug
            else:
                pass # Removed print-debug
            return 0

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
    
    # finish
    subparsers.add_parser("finish", help="Finish project and stop quality watch")
    
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

    # constitution
    constitution_parser = subparsers.add_parser("constitution", help="Constitution")
    constitution_parser.add_argument("subcommand", nargs="?", default="view",
                                   choices=["view", "thresholds", "errors", "check", "edit", "compile", "verify"],
                                   help="Constitution subcommand")
    constitution_parser.add_argument("output", nargs="?", help="Output text to verify (for verify subcommand)")

    # constitution-sync
    subparsers.add_parser("constitution-sync", help="Sync Constitution to Policy Engine")

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
    
    # audit
    audit_parser = subparsers.add_parser("audit", help="AI Audit Logger")
    audit_parser.add_argument("action", choices=["status", "anomalies", "report"], default="status")
    audit_parser.add_argument("--agent", help="Filter by agent ID")
    audit_parser.add_argument("--severity", choices=["low", "medium", "high", "critical"],
                              help="Filter by severity")
    
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

    # security - Deep Security Defense
    security_parser = subparsers.add_parser("security", help="Deep Security Defense Architecture")
    security_parser.add_argument(
        "action",
        choices=["deep-check", "enable-deep-defense", "audit-log", "validate"],
        default="deep-check"
    )
    security_parser.add_argument("--text", help="Text to validate (for validate action)")

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
    trace_parser.add_argument("action", choices=["view", "correlation", "export", "impact", "graphviz", "risk-report"],
                            help="Trace action")
    trace_parser.add_argument("--agent-id", help="Agent ID")
    trace_parser.add_argument("--correlation", help="Correlation ID")
    trace_parser.add_argument("--limit", type=int, help="Limit events")
    trace_parser.add_argument("--output", "-o", help="Output file")
    trace_parser.add_argument("--file", "-f", help="File path for impact analysis")
    
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

    # roi (ROI Dashboard)
    roi_parser = subparsers.add_parser("roi", help="ROI Tracking Dashboard")
    roi_parser.add_argument("subcommand", nargs="?", default="dashboard",
                           choices=["dashboard", "report"],
                           help="ROI subcommand")
    roi_parser.add_argument("period", nargs="?", choices=["day", "week", "month"], default="month",
                           help="Time period for report")

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
    
    # gatekeeper
    gatekeeper_parser = subparsers.add_parser("gatekeeper", help="Workflow Gatekeeper")
    gatekeeper_parser.add_argument("action", choices=["status", "check", "enforce"],
                                   help="Gatekeeper action")
    
    # confirmations (double confirmation)
    confirmations_parser = subparsers.add_parser("confirmations", help="Double Confirmation Management")
    confirmations_parser.add_argument("action", choices=["list", "confirm", "reject", "status", "check"],
                                      help="Confirmation action")
    confirmations_parser.add_argument("--id", dest="confirmation_id", help="Confirmation ID")
    confirmations_parser.add_argument("--by", dest="confirmed_by", help="Confirmed by (agent or human)")
    confirmations_parser.add_argument("--reason", help="Rejection reason")
    confirmations_parser.add_argument("--operation", help="Filter by operation type")
    
    # release (with double confirmation)
    release_parser = subparsers.add_parser("release", help="Release Management (requires confirmation)")
    release_parser.add_argument("--version", help="Version to release")
    release_parser.add_argument("--repo", help="Repository name")
    release_parser.add_argument("--confirm", action="store_true", help="Request confirmation before release")
    
    # policy (policy engine)
    subparsers.add_parser("policy", help="Run Policy Engine checks")
    
    # install-hook (pre-commit hook installer)
    subparsers.add_parser("install-hook", help="Install pre-commit hook")
    
    # enforcement-config (Unified Enforcement Configuration)
    enforcement_config_parser = subparsers.add_parser("enforcement-config", help="Unified Enforcement Configuration")
    enforcement_config_parser.add_argument("action", nargs="?", choices=["init", "set", "show", "detect"],
                                          help="Action: init, set, show, detect")
    enforcement_config_parser.add_argument("mode", nargs="?", choices=["local", "github", "gitlab", "jenkins", "azure"],
                                          help="Mode for 'set' action")

    # enforcement (Unified Enforcement CLI)
    enforcement_parser = subparsers.add_parser("enforcement", help="Unified Enforcement CLI")
    enforcement_parser.add_argument("subcommand", nargs="?", default="run",
                                   choices=["run", "check", "status", "install", "config"],
                                   help="Enforcement subcommand")
    enforcement_parser.add_argument("mode", nargs="?", choices=["local", "github", "gitlab", "jenkins", "azure"],
                                   help="Mode for 'config' subcommand")

    # quality-gate (Quality Gate - 品質閘道)
    quality_gate_parser = subparsers.add_parser("quality-gate", aliases=["qg"], help="Quality Gate - 品質閘道檢查")
    quality_gate_parser.add_argument("subcommand", nargs="?", default="check",
                                     choices=["check", "all", "doc", "docs", "phase", "aspice"],
                                     help="Quality gate subcommand")

    # decision (Decision Gate - 決策分類閘道)
    decision_parser = subparsers.add_parser("decision", aliases=["dec"], help="Decision Gate - 決策分類閘道")
    decision_parser.add_argument("subcommand", nargs="?", default="list",
                                choices=["classify", "add", "list", "ls", "pending", "p", "confirm", "report"],
                                help="Decision gate subcommand")
    decision_parser.add_argument("args", nargs="*", help="Arguments for subcommand")

    # agent-proof-hook (Agent-Proof Hook Management)
    agent_proof_hook_parser = subparsers.add_parser("agent-proof-hook", help="Agent-Proof Hook Management")
    agent_proof_hook_parser.add_argument("action", nargs="?", choices=["install", "verify", "uninstall"],
                                         help="Action: install, verify, uninstall")

    # memory (Memory Governance Framework)
    memory_parser = subparsers.add_parser("memory", help="Memory Governance Framework")
    memory_parser.add_argument("subcommand", nargs="?", default="status",
                              choices=["validate", "status", "audit", "resolve"],
                              help="Memory governance subcommand")

    # m27 (M2.7 Self-Evolving Integration)
    m27_parser = subparsers.add_parser("m27", help="M2.7 Self-Evolving Integration")
    m27_parser.add_argument("sub", nargs="?", default="status",
                           choices=["status", "analyze", "iterate", "optimize"],
                           help="M2.7 action")
    m27_parser.add_argument("--log", dest="failure_log", help="Failure log for analysis")

    # metrics (Code Metrics)
    metrics_parser = subparsers.add_parser("metrics", help="Code Metrics - 代碼品質指標")
    metrics_parser.add_argument("subcommand", nargs="?", default="report",
                              choices=["report", "check", "history"],
                              help="Metrics subcommand")

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    cli = MethodologyCLI()
    return cli.run(args)


if __name__ == "__main__":
    sys.exit(main())
