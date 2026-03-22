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


class MethodologyCLI:
    """統一 CLI 入口"""
    
    VERSION = "5.10.0"
    
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
        else:
            print(f"Unknown command: {command}")
            return 1
        
        return 0
    
    # ==================== Commands ====================
    
    def cmd_init(self, args):
        """初始化專案"""
        project_name = args.name or "my-project"
        
        print(f"Initializing project: {project_name}")
        
        # Create project structure
        dirs = [".methodology", ".methodology/tasks", ".methodology/sprints"]
        for d in dirs:
            os.makedirs(d, exist_ok=True)
        
        # Save initial state
        self.progress.save()
        
        print(f"✅ Project '{project_name}' initialized")
        print(f"\nNext steps:")
        print(f"  python cli.py task add \"Your first task\"")
        print(f"  python cli.py sprint create")
        print(f"  python cli.py board")
        
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
            print(f"✅ Task added: {item_id}")
            print(f"   Title: {args.title or 'New Task'}")
            print(f"   Points: {args.points or 1}")
            
        elif action == "list":
            self.progress.load()
            items = list(self.progress.backlog.values())
            if not items:
                print("No tasks found")
                return 0
            
            print(f"\n{'ID':<10} {'Title':<30} {'Points':<8} {'Status':<12}")
            print("-" * 60)
            for item in items:
                print(f"{item.id:<10} {item.title[:28]:<30} {item.story_points:<8} {item.sprint_id or 'backlog':<12}")
            
        elif action == "complete":
            if self.progress.mark_item_completed(args.task_id):
                print(f"✅ Task {args.task_id} marked as completed")
            else:
                print(f"❌ Task {args.task_id} not found")
        
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
            print(f"✅ Sprint created: {sprint.name}")
            print(f"   Duration: {sprint.duration_days} days")
            print(f"   Capacity: {sprint.capacity_points} points")
            
        elif action == "list":
            sprints = list(self.sprint_planner.sprints.values())
            if not sprints:
                print("No sprints found")
                return 0
            
            print(f"\n{'ID':<15} {'Name':<20} {'Status':<12} {'Capacity':<10}")
            print("-" * 60)
            for s in sprints:
                status = "active" if s.is_active else ("completed" if s.is_completed else "planning")
                print(f"{s.id:<15} {s.name[:18]:<20} {status:<12} {s.capacity_points:<10}")
        
        elif action == "start":
            if self.sprint_planner.start_sprint(args.sprint_id):
                print(f"✅ Sprint {args.sprint_id} started")
            else:
                print(f"❌ Sprint {args.sprint_id} not found")
        
        return 0
    
    def cmd_board(self, args):
        """開啟視覺化儀表板"""
        print("╔" + "═" * 60 + "╗")
        print("║" + " PROJECT BOARD ".center(60) + "║")
        print("╚" + "═" * 60 + "╝")
        print()
        
        # Progress
        summary = {"total_items": len(self.progress.backlog), "completed_items": sum(1 for i in self.progress.backlog.values() if i.completed)}
        
        print("📊 Progress:")
        if summary:
            print(f"   Total Items: {summary.get("total_items", 0)}")
            print(f"   Completed: {summary.get('completed_items', 0)}")
            print(f"   In Progress: {summary.get('in_progress_items', 0)}")
            print(f"   Completion: {summary.get('completion_rate', 0):.1f}%")
        else:
            print("   No data")
        
        print()
        
        # Gantt
        if self.gantt.tasks:
            print("📅 Gantt Chart:")
            print(self.gantt.to_rich_ascii())
        else:
            print("📅 Gantt: No tasks")
        
        print()
        
        # Message Bus
        print("📬 Message Bus:")
        print(self.bus.to_cli())
        
        return 0
    
    def cmd_report(self, args):
        """生成報告"""
        report_type = args.type or "weekly"
        
        print("╔" + "═" * 60 + "╗")
        print("║" + f" {report_type.upper()} REPORT ".center(60) + "║")
        print("╚" + "═" * 60 + "╝")
        print()
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print()
        
        # Progress
        print("## 📊 Progress")
        summary = {"total_items": len(self.progress.backlog), "completed_items": sum(1 for i in self.progress.backlog.values() if i.completed)}
        if summary:
            for key, value in summary.items():
                print(f"   {key}: {value}")
        print()
        
        # Data sources
        print("## 📈 Data Sources")
        connections = self.data_manager.list_connections()
        if connections:
            for conn in connections:
                status = "✅" if conn['connected'] else "❌"
                print(f"   {status} {conn['name']} ({conn['type']})")
        else:
            print("   No data sources connected")
        print()
        
        # Save report
        if args.output:
            with open(args.output, 'w') as f:
                f.write(f"# {report_type.upper()} Report\n\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n\n")
                f.write(json.dumps(summary, indent=2, default=str))
            print(f"✅ Report saved to {args.output}")
        
        return 0
    
    def cmd_status(self, args):
        """顯示狀態"""
        self.progress.load()
        print("╔" + "═" * 60 + "╗")
        print("║" + " METHODOLOGY STATUS ".center(60) + "║")
        print("╚" + "═" * 60 + "╝")
        print()
        print(f"Version: {self.VERSION}")
        print()
        
        # Tasks
        items = list(self.progress.backlog.values())
        print(f"📋 Tasks: {len(items)} total")
        
        # Sprints
        sprints = list(self.sprint_planner.sprints.values())
        active = sum(1 for s in sprints if s.is_active)
        print(f"🏃 Sprints: {len(sprints)} total, {active} active")
        
        # Message Bus
        bus_status = self.bus.get_queue_status()
        print(f"📬 Message Bus: {bus_status['queue_size']} queued")
        
        # Data Sources
        connections = self.data_manager.list_connections()
        connected = sum(1 for c in connections if c['connected'])
        print(f"🔗 Data Sources: {connected}/{len(connections)} connected")
        
        return 0
    
    def cmd_resources(self, args):
        """資源管理"""
        action = args.action
        
        if action == "list":
            print("📦 Resources:")
            print("   (Use DataSourceManager to connect resources)")
            print()
            print("   Connect to data sources:")
            print("   - Prometheus (metrics)")
            print("   - Jira (tasks)")
            print("   - OpenTelemetry (traces)")
            print()
            print("   Example:")
            print("   ```python")
            print("   from methodology import DataSourceManager, PrometheusConnector")
            print("   dm = DataSourceManager()")
            print("   dm.connect('prom', PrometheusConnector, url='http://localhost:9090')")
            print("   ```")
        
        return 0
    
    def cmd_bus(self, args):
        """Message Bus 管理"""
        action = args.action
        
        if action == "status":
            print(self.bus.to_cli())
        
        elif action == "tree":
            print(self.bus.to_tree())
        
        elif action == "watch":
            seconds = args.seconds or 10
            print(f"Watching Message Bus for {seconds} seconds...")
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
            print(f"✅ Created evaluation suite: {suite.id}")
            print(f"   Name: {suite.name}")
            return 0
        
        elif action == "list":
            suites = list(self.evaluator.suites.values())
            if not suites:
                print("No evaluation suites found")
                return 0
            
            print(f"\n{'ID':<12} {'Name':<30} {'Status':<12} {'Tests'}")
            print("-" * 70)
            for s in suites:
                print(f"{s.id:<12} {s.name[:28]:<30} {s.status.value:<12} {len(s.test_cases)}")
            return 0
        
        elif action == "report":
            if not args.suite_id:
                print("Error: --suite-id required")
                return 1
            
            if args.suite_id not in self.evaluator.suites:
                print(f"Suite '{args.suite_id}' not found")
                return 1
            
            print(self.evaluator.generate_report(args.suite_id))
            return 0
        
        elif action == "run":
            if not args.suite_id:
                print("Error: --suite-id required")
                return 1
            
            if args.suite_id not in self.evaluator.suites:
                print(f"Suite '{args.suite_id}' not found")
                return 1
            
            # 定義簡單的 mock agent
            import time
            def mock_agent(prompt, context=None, timeout=30):
                time.sleep(0.1)
                return f"Response to: {prompt[:50]}..."
            
            print(f"Running evaluation suite: {args.suite_id}...")
            self.evaluator.run_suite(args.suite_id, mock_agent)
            print("✅ Evaluation completed")
            return 0
        
        elif action == "add":
            if not args.suite_id:
                print("Error: --suite-id required")
                return 1
            
            if not args.name:
                print("Error: --name (test case name) required")
                return 1
            
            test = self.evaluator.add_test_case(
                suite_id=args.suite_id,
                name=args.name,
                input_prompt=args.prompt or "Test prompt",
                expected_output=args.expected
            )
            print(f"✅ Added test case: {test.id} - {test.name}")
            return 0
        
        elif action == "hitl":
            pending = self.hitl.get_pending_count()
            print(f"\n📋 Human-in-the-Loop")
            print(f"   Pending reviews: {pending}")
            return 0
        
        print(f"Unknown action: {action}")
        return 1
    
    def cmd_quality(self, args):
        """Data Quality Checker"""
        action = args.action
        
        if action == "check":
            print("📊 Data Quality Checker")
            print("=" * 50)
            # Generate sample data
            sample_data = [
                {"id": 1, "name": "Alice", "email": "alice@test.com", "age": 30},
                {"id": 2, "name": "Bob", "email": "bob@test.com", "age": 25},
                {"id": 3, "name": "", "email": "invalid", "age": None},
            ]
            report = self.data_quality.analyze(sample_data)
            print(self.data_quality.generate_report_markdown(report))
        elif action == "report":
            print(self.data_quality.generate_report())
        return 0
    
    def cmd_enterprise(self, args):
        """Enterprise Integration Hub"""
        action = args.action
        
        if action == "status":
            print("🏢 Enterprise Integration Hub")
            print("=" * 50)
            status = self.enterprise.get_status()
            for k, v in status.items():
                print(f"  {k}: {v}")
        elif action == "audit":
            print(self.enterprise.audit.generate_report())
        return 0
    
    def cmd_wizard(self, args):
        """Setup Wizard"""
        print("🧙‍♂️ Setup Wizard")
        print("=" * 50)
        wizard = SetupWizard()
        
        # Interactive setup
        project_name = input("Project name: ") or "my-agent-project"
        use_case = input("Use case (customer_service/coding/research/data_analysis/custom): ") or "customer_service"
        
        config = wizard.create_project(
            name=project_name,
            use_case=use_case
        )
        
        print(f"\n✅ Project created: {config.name}")
        print(f"   Use case: {config.use_case.value}")
        print(f"   Workflow: {config.workflow}")
        print(f"   Agents: {len(config.agents)}")
        return 0
    
    def cmd_guardrails(self, args):
        """Security Guardrails"""
        action = args.action
        
        if action == "check":
            text = args.text or "Sample text to check"
            try:
                result = self.guardrails.check(text)
                print("🛡️ Security Check Results")
                print("=" * 50)
                print(f"Text: {text[:50]}...")
                print(f"\nSafe: {'✅' if result.safe else '❌'}")
                if result.threats:
                    print("\nThreats detected:")
                    for threat in result.threats:
                        print(f"  - {threat}")
            except Exception as e:
                print(f"🛡️ Guardrails Active (method: check)")
                print(f"   Error during check: {e}")
        return 0
    
    def cmd_scale(self, args):
        """AutoScaler"""
        action = args.action
        
        if action == "status":
            status = self.autoscaler.get_status()
            print("⚖️ AutoScaler Status")
            print("=" * 50)
            for k, v in status.items():
                print(f"  {k}: {v}")
        elif action == "scale":
            current = int(args.current or 1)
            target = self.autoscaler.calculate_target_instances(current)
            print(f"\n⚖️ Scaling Recommendation")
            print(f"  Current: {current}")
            print(f"  Target: {target}")
        return 0
    
    def cmd_migrate(self, args):
        """LangGraph / CrewAI Migration Tool"""
        if not args.file:
            print("Usage: python cli.py migrate [--from crewai|langgraph] [--to crewai|langgraph] <file.py>")
            return 1

        from_framework = getattr(args, 'from', None)
        to_framework = getattr(args, 'to', None)

        # Cross-framework migration
        if from_framework and to_framework:
            if from_framework == to_framework:
                print(f"⚠️ Source and target are the same: {from_framework}")
                return 1

            print(f"🔄 Migrating {from_framework.upper()} → {to_framework.upper()}...")
            print(f"   File: {args.file}")
            print()

            report = bridge_quick_convert(args.file, from_framework, to_framework)

            if report.success:
                print(f"✅ Migration successful!")
                print(f"   Output: {report.output_file}")
                print(f"   Nodes migrated: {report.nodes_migrated}")
                print()

                # Validate
                success, messages = self.bridge.validate_migration(
                    args.file, report.output_file,
                    f"{from_framework}_to_{to_framework}"
                )
                for msg in messages:
                    print(f"   {msg}")
            else:
                print(f"❌ Migration failed:")
                for err in report.errors:
                    print(f"   - {err}")

            return 0

        # Default: LangGraph migration (backward compatible)
        print(f"🔄 Analyzing {args.file}...")
        result = self.migrator.analyze_file(args.file)
        print(self.migrator.generate_report(result))
        return 0
    
    def cmd_parse(self, args):
        """Structured Output Engine"""
        print("📝 Structured Output Engine")
        print("=" * 50)
        print(self.structured.generate_report())
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
            print(report.to_markdown())
        elif action == "forecast":
            forecast = self.pm_mode.predict_cost(
                project_name="AI Assistant",
                current_cost=500.0,
                budget=2000.0,
                daily_burn_rate=85.0,
                days_remaining=18
            )
            print(forecast.to_markdown())
        elif action == "health":
            health = self.pm_mode.get_sprint_health(velocity=35, planned=50, completed=30)
            print(f"\n## Sprint Health")
            print(f"Status: {health['health']}")
            print(f"Score: {health['health_score']}/10")
            print(f"Completion: {health['completion_rate']:.1f}%")
        return 0
    
    def cmd_term(self, args):
        """術語查詢"""
        query = args.query
        if query:
            results = self.terminology.search(query)
            if results:
                print(f"\n# Search: {query}\n")
                for r in results[:5]:
                    print(f"## {r.pm_term}")
                    print(f"- **Dev**: {r.dev_term}")
                    print(f"- **Scrum**: {r.scrum_term}")
                    print(f"- **定義**: {r.definition}")
                    print()
            else:
                print(f"No results for '{query}'")
        else:
            print(self.terminology.to_markdown_table())
        return 0
    
    def cmd_resources(self, args):
        """資源儀表板"""
        action = args.action
        
        if action == "list":
            print(self.resources.to_table())
        elif action == "stats":
            summary = self.resources.get_resource_summary()
            print("\n📊 Resource Summary:")
            print(f"  Total: {summary['total']}")
            print(f"  Team Size: {summary['team_size']}")
            print(f"  Monthly Cost: ${summary['total_monthly_cost']:.2f}")
            print(f"  By Type: {summary['by_type']}")
        elif action == "skills":
            matrix = self.resources.get_team_skills_matrix()
            print("\n👥 Team Skills:")
            for skill, members in matrix.items():
                print(f"  {skill}: {', '.join(members)}")
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
                    print(f"   {k}: {v}")
            else:
                print(self.debugger.get_stats())
        
        elif action == "list":
            agent_id = args.agent_id
            if not agent_id:
                print("Error: --agent-id required")
                return 1
            events = self.debugger.get_trace(agent_id, limit=args.limit or 20)
            if not events:
                print(f"No trace events found for agent: {agent_id}")
                return 0
            print(f"\n📋 Trace Events for: {agent_id}")
            print("-" * 70)
            for event in events:
                print(f"  [{event['timestamp']}] {event['event_type']} - {event.get('id', 'N/A')}")
                if event.get('data'):
                    for k, v in event['data'].items():
                        print(f"     {k}: {str(v)[:50]}")
        
        elif action == "clear":
            if args.agent_id:
                self.debugger.clear(args.agent_id)
                print(f"✅ Cleared traces for agent: {args.agent_id}")
            else:
                self.debugger.clear()
                print("✅ Cleared all traces")
        
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
            print("Error: --agent-id required")
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
                print("Error: --correlation required for correlation view")
                return 1
        
        elif args.action == "export":
            # 導出 JSON
            json_data = self.debugger.export(agent_id)
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(json_data)
                print(f"✅ Trace exported to {args.output}")
            else:
                print(json_data)
        
        return 0
    
    def cmd_approval(self, args):
        """人類審批管理"""
        action = args.action
        
        if action == "list":
            pending = self.approval_flow.get_pending()
            if not pending:
                print("✅ No pending approvals")
                return 0
            print(f"\n{'ID':<15} {'Name':<30} {'Type':<15} {'Requester':<15}")
            print("-" * 80)
            for p in pending:
                print(f"{p['id']:<15} {p['name'][:28]:<30} {p['approval_type']:<15} {p.get('requester_name', p.get('requester','')):<15}")
            return 0
        
        elif action == "create":
            req_id = self.approval_flow.create_request(
                name=args.name or "New Approval Request",
                description=args.description or "",
                requester=args.requester or "user",
                requester_name=args.requester_name or "",
                approval_type=args.approval_type or "general",
            )
            print(f"✅ Created approval request: {req_id}")
            return 0
        
        elif action == "approve":
            if not args.request_id:
                print("Error: --request-id required")
                return 1
            level = None
            if args.level:
                try:
                    level = ApprovalLevel(args.level)
                except ValueError:
                    print(f"Error: Invalid level '{args.level}'. Use: l1, l2, l3, l4, final")
                    return 1
            result = self.approval_flow.approve(args.request_id, args.approver or "user",
                                               comment=args.comment or "", level=level)
            if result:
                print(f"✅ Approved: {args.request_id}")
            else:
                print(f"❌ Failed to approve: {args.request_id}")
            return 0
        
        elif action == "reject":
            if not args.request_id:
                print("Error: --request-id required")
                return 1
            level = None
            if args.level:
                try:
                    level = ApprovalLevel(args.level)
                except ValueError:
                    print(f"Error: Invalid level '{args.level}'. Use: l1, l2, l3, l4, final")
                    return 1
            result = self.approval_flow.reject(args.request_id, args.approver or "user",
                                              comment=args.comment or "", level=level)
            if result:
                print(f"✅ Rejected: {args.request_id}")
            else:
                print(f"❌ Failed to reject: {args.request_id}")
            return 0
        
        elif action == "show":
            if not args.request_id:
                print("Error: --request-id required")
                return 1
            request = self.approval_flow.get_request(args.request_id)
            if not request:
                print(f"❌ Request not found: {args.request_id}")
                return 1
            print(f"\n{'='*60}")
            print(f"Approval Request: {request.name}")
            print(f"{'='*60}")
            print(f"ID: {request.id}")
            print(f"Type: {request.approval_type}")
            print(f"Status: {request.status.value}")
            print(f"Requester: {request.requester_name or request.requester}")
            print(f"Created: {request.created_at}")
            print(f"\nDescription:")
            print(f"  {request.description}")
            print(f"\nSteps:")
            for i, step in enumerate(request.steps):
                marker = "→" if i == request.current_step_index else ("✓" if step.status != ApprovalStatus.PENDING else " ")
                print(f"  {marker} [{step.level.value.upper()}] {step.approver} - {step.status.value}")
                for approval in step.approvals:
                    print(f"      - {approval['approver']}: {approval['status'].value} ({approval.get('comment','')})")
            print(f"\n{'='*60}")
            return 0
        
        elif action == "report":
            print(self.approval_flow.generate_report())
            return 0
        
        elif action == "stats":
            stats = self.approval_flow.get_statistics()
            print("\n📊 Approval Statistics")
            print("=" * 40)
            for k, v in stats.items():
                print(f"  {k}: {v}")
            return 0
        
        print(f"Unknown action: {action}")
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
            print(f"✅ Risk added: {risk.id}")
            print(f"   Title: {risk.title}")
            print(f"   Level: {risk.level.value}")
            print(f"   Owner: {risk.owner}")
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
                print("No risks found")
                return 0

            print(f"\n{'ID':<10} {'Level':<10} {'Status':<12} {'Title':<30} {'Owner':<15}")
            print("-" * 80)
            for r in risks:
                print(f"{r.id:<10} {r.level.value:<10} {r.status.value:<12} {r.title[:28]:<30} {r.owner:<15}")
            return 0

        elif action == "show":
            risk = self.registry.get_risk(args.risk_id)
            if not risk:
                print(f"❌ Risk not found: {args.risk_id}")
                return 1
            print(f"\n{'='*60}")
            print(f"Risk: {risk.title}")
            print(f"{'='*60}")
            print(f"ID: {risk.id}")
            print(f"Level: {risk.level.value}")
            print(f"Status: {risk.status.value}")
            print(f"Owner: {risk.owner}")
            print(f"Probability: {risk.probability:.0%}")
            print(f"Impact: {risk.impact}")
            print(f"Created: {risk.created_at.strftime('%Y-%m-%d %H:%M')}")
            if risk.mitigated_at:
                print(f"Mitigated: {risk.mitigated_at.strftime('%Y-%m-%d %H:%M')}")
            if risk.closed_at:
                print(f"Closed: {risk.closed_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"\nDescription:\n  {risk.description}")
            print(f"\nMitigation:\n  {risk.mitigation}")
            print(f"{'='*60}")
            return 0

        elif action == "close":
            if self.registry.update_risk_status(args.risk_id, RiskStatus.CLOSED):
                print(f"✅ Risk closed: {args.risk_id}")
            else:
                print(f"❌ Risk not found: {args.risk_id}")
            return 0

        elif action == "mitigate":
            if self.registry.update_risk_status(args.risk_id, RiskStatus.MITIGATED):
                print(f"✅ Risk mitigated: {args.risk_id}")
            else:
                print(f"❌ Risk not found: {args.risk_id}")
            return 0

        elif action == "report":
            print(self.registry.generate_report())
            return 0

        elif action == "stats":
            summary = self.registry.get_summary()
            print("\n📊 Risk Summary")
            print("=" * 40)
            print(f"Total Risks: {summary['total']}")
            print("\nBy Status:")
            for k, v in summary['by_status'].items():
                print(f"  {k}: {v}")
            print("\nBy Level:")
            for k, v in summary['by_level'].items():
                print(f"  {k}: {v}")
            return 0

        elif action == "delete":
            if self.registry.delete_risk(args.risk_id):
                print(f"✅ Risk deleted: {args.risk_id}")
            else:
                print(f"❌ Risk not found: {args.risk_id}")
            return 0

        print(f"Unknown action: {action}")
        return 1

    def cmd_p2p(self, args):
        """P2P 團隊配置管理"""
        action = args.p2p_action
        cache_path = ".p2p_team_cache.json"

        if action == "init":
            try:
                self.p2p_config = P2PTeamConfig.from_json(args.config_path)
            except FileNotFoundError as e:
                print(f"❌ {e}")
                return 1
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON: {e}")
                return 1

            if not self.p2p_config.validate():
                print("❌ Config validation failed")
                return 1

            # Persist to cache for stateless access
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(self.p2p_config.to_dict(), f, indent=2, ensure_ascii=False)

            summary = self.p2p_config.summary()
            print(f"✅ Team loaded: {summary['teamId']}")
            print(f"   Mode: {summary['mode']}")
            print(f"   Members: {summary['memberCount']}")
            print(f"   Max Spawn Depth: {summary['maxSpawnDepth']}")
            return 0

        # Reload from cache for status/list
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    self.p2p_config = P2PTeamConfig.from_dict(json.load(f))
            except Exception:
                self.p2p_config = None

        if self.p2p_config is None:
            print("❌ No team loaded. Run: python cli.py p2p init <config.json>")
            return 1

        if action == "status":
            summary = self.p2p_config.summary()
            print(f"\n📡 P2P Team Status")
            print("=" * 40)
            print(f"Team ID: {summary['teamId']}")
            print(f"Mode: {summary['mode']}")
            print(f"Members: {summary['memberCount']}")
            print(f"Roles: {', '.join(summary['roles'])}")
            print(f"Max Spawn Depth: {summary['maxSpawnDepth']}")
            print(f"Agent-to-Agent: {'✅' if summary['allowAgentToAgent'] else '❌'}")
            return 0

        if action == "list":
            members = self.p2p_config.list_agents()
            if not members:
                print("No members in team")
                return 0
            print(f"\n👥 Team Members ({len(members)})")
            print("-" * 60)
            print(f"{'Agent ID':<25} {'Role':<18} {'Spawn':<8} {'Memory'}")
            print("-" * 60)
            for m in members:
                spawn = "✅" if m["canSpawnSubagent"] else "❌"
                memory = "✅" if m["peerMemoryEnabled"] else "❌"
                print(f"{m['agentId']:<25} {m['role']:<18} {spawn:<8} {memory}")
            return 0

        print(f"Unknown action: {action}")
        return 1

    def cmd_version(self, args):
        """顯示版本"""
        print(f"Methodology v{self.VERSION}")
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
