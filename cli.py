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
from gantt_chart import GanttChart
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
from wizard.wizard import SetupWizard, TEMPLATES
from guardrails.guardrails import Guard
from autoscaler.autoscaler import AutoScaler
from data_connector import DataSourceManager


class MethodologyCLI:
    """統一 CLI 入口"""
    
    VERSION = "5.4.0"
    
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
        self.wizard = SetupWizard()
        self.guardrails = Guard()
        self.autoscaler = AutoScaler()
        self.resources = ResourceDashboard()
        self.data_manager = DataSourceManager()
    
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
        """LangGraph Migration Tool"""
        if not args.file:
            pass # Removed print-debug
            return 1
        
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
    migrate_parser = subparsers.add_parser("migrate", help="LangGraph Migration")
    migrate_parser.add_argument("file", help="File to migrate")
    
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
