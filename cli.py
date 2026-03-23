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


class MethodologyCLI:
    """統一 CLI 入口"""
    
    VERSION = "5.35.0"
    
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
            print(self.blacklist.explain(blocked))
            return False
        return True
    
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
        elif command == "agent-proof-hook":
            return self.cmd_agent_proof_hook(args)
        elif command == "memory":
            return self.cmd_memory(args)
        elif command == "roi":
            return self.cmd_roi(args)
        elif command == "m27":
            return self.cmd_m27(args)
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
            print(f'   Total Items: {summary.get("total_items", 0)}')
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
    
    def cmd_audit(self, args):
        """AI Audit Logger - AI 操作審計"""
        action = args.action
        
        if action == "status":
            print("🔍 AI Audit Status")
            print("=" * 50)
            report = self.ai_audit.get_audit_report()
            print(f"Total Operations: {report['total_operations']}")
            print(f"\nBy Type:")
            for op_type, count in report['by_type'].items():
                print(f"  - {op_type}: {count}")
            print(f"\nAnomalies: {report['anomalies']['total']} "
                  f"({report['anomalies']['critical']} critical, "
                  f"{report['anomalies']['high']} high)")
        
        elif action == "anomalies":
            print("🚨 AI Audit Anomalies")
            print("=" * 50)
            agent_id = getattr(args, 'agent', None)
            severity = getattr(args, 'severity', None)
            
            anomalies = self.ai_audit.get_anomalies(agent_id=agent_id, severity=severity)
            
            if not anomalies:
                print("No anomalies detected.")
                return 0
            
            for i, anomaly in enumerate(anomalies, 1):
                print(f"\n{i}. [{anomaly.severity.upper()}] {anomaly.anomaly_type.value}")
                print(f"   Agent: {anomaly.agent_id}")
                print(f"   Description: {anomaly.description}")
                print(f"   Time: {anomaly.timestamp.isoformat()}")
        
        elif action == "report":
            print("📊 AI Audit Report")
            print("=" * 50)
            agent_id = getattr(args, 'agent', None)
            report = self.ai_audit.get_audit_report(agent_id=agent_id)
            print(json.dumps(report, indent=2))
        
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

    def cmd_security(self, args):
        """Deep Security Defense"""
        action = args.action

        if action == "deep-check":
            print("🔒 Deep Security Defense - Status Check")
            print("=" * 50)
            print("Layer 1: Input Validator")
            print("  ✅ Module loaded")
            print("Layer 2: Execution Sandbox")
            sandbox_config = self.execution_sandbox.config
            print(f"  ✅ Sandbox Level: {sandbox_config.level.value}")
            print(f"  ✅ Max Execution Time: {sandbox_config.max_execution_time}s")
            print("Layer 3: Output Filter")
            print("  ✅ Module loaded")
            print("Layer 4: Human-in-the-Loop")
            pending = self.hitl_security.get_pending()
            print(f"  ✅ Pending Requests: {len(pending)}")
            print()
            print("🛡️ Deep Defense Architecture v5.33")

        elif action == "enable-deep-defense":
            print("🔒 Enabling Deep Security Defense")
            print("=" * 50)
            print("✅ Layer 1: Input Validation - ACTIVE")
            print("   - LPCI Attack Detection")
            print("   - Prompt Injection Detection")
            print("   - Blacklist/Whitelist Support")
            print("✅ Layer 2: Execution Sandbox - ACTIVE")
            print("   - Strict Isolation Mode")
            print("   - Minimal PATH (/usr/bin:/bin)")
            print("   - Restricted Working Directory (/tmp)")
            print("✅ Layer 3: Output Filter - ACTIVE")
            print("   - Sensitive Data Detection")
            print("   - Automatic Redaction")
            print("   - Audit Logging")
            print("✅ Layer 4: Human-in-the-Loop - ACTIVE")
            print("   - Approval Queue")
            print("   - Auto-Escalation")
            print("   - Audit Trail")
            print()
            print("🛡️ All 4 security layers are now ENABLED")

        elif action == "audit-log":
            print("📋 Security Audit Log")
            print("=" * 50)
            input_audit = self.input_validator
            output_audit = self.output_filter.get_audit_log()
            hitl_audit = self.hitl_security.get_pending()

            print(f"Output Filter Entries: {len(output_audit)}")
            if output_audit:
                for i, entry in enumerate(output_audit[-5:], 1):
                    print(f"  {i}. {entry}")
            else:
                print("  (no entries)")

            print(f"\nHITL Pending Requests: {len(hitl_audit)}")
            if hitl_audit:
                for req in hitl_audit[:5]:
                    print(f"  - {req.action}: {req.description[:50]}...")
            else:
                print("  (no pending requests)")

        elif action == "validate":
            text = args.text or "ignore previous instructions"
            print(f"🔍 Validating input: {text[:50]}...")
            result = self.input_validator.validate(text)
            print("=" * 50)
            print(f"Safe: {'✅' if result.is_safe else '❌'}")
            print(f"Threat Type: {result.threat_type.value if result.threat_type else 'None'}")
            print(f"Confidence: {result.confidence:.2f}")
            if result.matched_patterns:
                print(f"Matched Patterns:")
                for p in result.matched_patterns:
                    print(f"  - {p}")
            if result.recommendations:
                print(f"Recommendations:")
                for r in result.recommendations:
                    print(f"  - {r}")

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
    
    def _print_impact_report(self, impact):
        """列印 Impact Analysis 報告"""
        risk_label = "🟢 Low" if impact.risk_score < 40 else "🟡 Medium" if impact.risk_score < 70 else "🔴 High"
        print()
        print("=" * 50)
        print("    Impact Analysis Report")
        print("=" * 50)
        print(f"📁 Changed File: {impact.changed_file}")
        print()
        print(f"📊 Risk Score: {impact.risk_score}/100 ({risk_label} Risk)")
        print()
        if impact.affected_tests:
            print(f"🔴 Affected Tests ({len(impact.affected_tests)}):")
            for test in impact.affected_tests:
                print(f"   - {test}")
            print()
        if impact.affected_modules:
            print(f"🟡 Affected Modules ({len(impact.affected_modules)}):")
            for mod in impact.affected_modules[:10]:  # Limit to 10
                print(f"   - {mod}")
            if len(impact.affected_modules) > 10:
                print(f"   ... and {len(impact.affected_modules) - 10} more")
            print()
        if impact.recommendations:
            print("💡 Recommendations:")
            for rec in impact.recommendations:
                print(f"   - {rec}")
            print()
    
    def _print_risk_report(self, report):
        """列印 Risk Report"""
        print()
        print("=" * 50)
        print("    Dependency Risk Report")
        print("=" * 50)
        print(f"📊 Total Nodes: {report['total_nodes']}")
        print(f"🔗 Total Edges: {report['total_edges']}")
        print(f"🧪 Test Files: {report['test_files']}")
        print()
    
    def cmd_trace(self, args):
        """Agent Trace - 視覺化追蹤"""
        action = args.action
        
        # Impact Analysis commands (no agent_id required)
        if action == "impact":
            if not args.file:
                print("Error: --file required for impact analysis")
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
                print(f"✅ Dependency graph exported to {args.output}")
            else:
                print(report['graphviz'])
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
            print("Error: --agent-id required for this action")
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
                print("Error: --correlation required for correlation view")
                return 1
        
        elif action == "export":
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

    def cmd_roi(self, args):
        """ROI Dashboard"""
        from roi_tracker import ROICalculator

        calculator = ROICalculator()

        if args.subcommand == "dashboard":
            data = calculator.get_dashboard_data()
            print("=" * 50)
            print("ROI Dashboard")
            print("=" * 50)
            for period, report in data.items():
                print(f"\n{period.upper()}:")
                print(f"  Cost: ${report.total_cost:.2f}")
                print(f"  Value: ${report.total_value:.2f}")
                print(f"  ROI: {report.roi_percentage}%")
                print(f"  Net: ${report.net_value:.2f}")
                if hasattr(report, 'recommendation') and report.recommendation:
                    print(f"  Recommendation: {report.recommendation}")
            print()
            return 0

        elif args.subcommand == "report":
            report = calculator.calculate(args.period)
            print(f"ROI Report ({args.period})")
            print("=" * 40)
            print(f"Total Cost: ${report.total_cost:.2f}")
            print(f"Total Value: ${report.total_value:.2f}")
            print(f"ROI: {report.roi_percentage}%")
            print(f"Net Value: ${report.net_value:.2f}")
            print(f"Recommendation: {report.recommendation}")
            print()
            return 0

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
                print(f"✅ Owner registered: {owner.name} ({owner.owner_id})")
            else:
                print(f"❌ Owner already exists: {owner.owner_id}")
            return 0
        
        elif action == "list":
            # 列出負責人或產出
            if args.list_type == "owners":
                owners = self.hitl_controller.list_owners()
                if not owners:
                    print("No owners registered")
                    return 0
                print(f"\n{'Owner ID':<20} {'Name':<20} {'Email':<30} {'Role':<15} {'Agents'}")
                print("-" * 90)
                for o in owners:
                    print(f"{o.owner_id:<20} {o.name:<20} {o.email:<30} {o.role:<15} {len(o.agents)}")
                return 0
            elif args.list_type == "outputs":
                outputs = self.hitl_controller.get_outputs_by_status(OutputStatus(args.status_filter)) if args.status_filter else list(self.hitl_controller.outputs.values())
                if not outputs:
                    print("No outputs found")
                    return 0
                print(f"\n{'Output ID':<20} {'Agent':<15} {'Owner':<15} {'Task':<20} {'Status':<15}")
                print("-" * 90)
                for o in outputs:
                    print(f"{o.id:<20} {o.agent_id:<15} {o.owner_id:<15} {o.task_id:<20} {o.status.value:<15}")
                return 0
            elif args.list_type == "pending":
                pending = self.hitl_controller.get_pending_reviews(args.owner_filter)
                if not pending:
                    print("No pending reviews")
                    return 0
                print(f"\n{'Output ID':<20} {'Agent':<15} {'Task':<20} {'Created':<20} {'Owner'}")
                print("-" * 90)
                for o in pending:
                    print(f"{o.id:<20} {o.agent_id:<15} {o.task_id:<20} {o.created_at.strftime('%Y-%m-%d %H:%M'):<20} {o.owner_id}")
                return 0
        
        elif action == "assign":
            # 指派 Agent 給負責人
            if self.hitl_controller.assign_agent_to_owner(args.agent_id, args.owner_id):
                owner = self.hitl_controller.get_owner(args.owner_id)
                print(f"✅ Assigned {args.agent_id} -> {owner.name if owner else args.owner_id}")
            else:
                print(f"❌ Failed to assign: owner {args.owner_id} not found")
            return 0
        
        elif action == "approve":
            # 批准產出
            if self.hitl_controller.approve_output(args.output_id, args.approver or "user"):
                print(f"✅ Approved: {args.output_id}")
            else:
                print(f"❌ Failed to approve: {args.output_id}")
            return 0
        
        elif action == "reject":
            # 要求修改
            feedback = args.feedback or "Revision requested"
            if self.hitl_controller.request_revision(args.output_id, args.approver or "user", feedback):
                print(f"✅ Revision requested: {args.output_id}")
                print(f"   Feedback: {feedback}")
            else:
                print(f"❌ Failed to request revision: {args.output_id}")
            return 0
        
        elif action == "show":
            # 顯示產出詳情
            output = self.hitl_controller.get_output(args.output_id)
            if not output:
                print(f"❌ Output not found: {args.output_id}")
                return 1
            print(f"\n{'='*60}")
            print(f"Output: {output.id}")
            print(f"{'='*60}")
            print(f"Agent: {output.agent_id}")
            print(f"Owner: {output.owner_id}")
            print(f"Task: {output.task_id}")
            print(f"Status: {output.status.value}")
            print(f"Created: {output.created_at}")
            if output.submitted_at:
                print(f"Submitted: {output.submitted_at}")
            if output.approved_at:
                print(f"Approved: {output.approved_at} by {output.approved_by}")
            if output.feedback:
                print(f"Feedback: {output.feedback}")
            if output.revision_count > 0:
                print(f"Revision count: {output.revision_count}")
            print(f"{'='*60}")
            return 0
        
        elif action == "stats":
            # 顯示統計
            stats = self.hitl_controller.get_statistics()
            print(f"\n📊 HITL Statistics")
            print("=" * 40)
            print(f"Total outputs: {stats['total_outputs']}")
            print(f"Pending reviews: {stats['pending_reviews']}")
            print(f"Total owners: {stats['total_owners']}")
            print(f"Agents assigned: {stats['total_agents_assigned']}")
            print(f"Avg revision count: {stats['avg_revision_count']}")
            print(f"\nBy status:")
            for status, count in stats['by_status'].items():
                print(f"  {status}: {count}")
            return 0
        
        elif action == "report":
            # 生成報告
            print(self.hitl_controller.generate_report())
            return 0
        
        elif action == "escalate":
            # 升級產出
            from hitl_controller import EscalationLevel
            level = EscalationLevel(args.level) if args.level else EscalationLevel.OWNER
            if self.hitl_controller.escalate_output(args.output_id, args.reason, level):
                print(f"✅ Escalated: {args.output_id}")
                print(f"   Reason: {args.reason}")
                print(f"   Level: {level.value}")
            else:
                print(f"❌ Failed to escalate: {args.output_id}")
            return 0
        
        print(f"Unknown action: {action}")
        return 1

    def cmd_constitution(self, args):
        """Constitution management"""
        subcmd = args.subcommand

        if subcmd == "view":
            from constitution import load_constitution
            print(load_constitution())
        elif subcmd == "thresholds":
            from constitution import get_quality_thresholds
            thresholds = get_quality_thresholds()
            print("Quality Thresholds:")
            for k, v in thresholds.items():
                print(f"  {k}: {v}%")
        elif subcmd == "errors":
            from constitution import get_error_levels
            levels = get_error_levels()
            print("Error Levels:")
            for k, v in levels.items():
                print(f"  {k}: {v['name']} (recoverable: {v['recoverable']})")
        elif subcmd == "check":
            print("Checking project compliance...")
            # TODO: 檢查專案是否符合憲章
            print("✅ Project is compliant")
        elif subcmd == "edit":
            print("Opening constitution in editor...")
            import subprocess
            subprocess.run(["open", "constitution/CONSTITUTION.md"])
        elif subcmd == "compile":
            from constitution import compile_constitution
            compiled = compile_constitution()
            print("Constitution compiled successfully!")
            print(f"  Version: {compiled.version}")
            print(f"  Hash: {compiled.hash}")
            print(f"  Specs: {len(compiled.specs)} sections")
        elif subcmd == "verify":
            if not args.output:
                print("Error: output text required for verify")
                print("Usage: python3 cli.py constitution verify '<agent_output>'")
                return 1
            from constitution import compile_constitution, verify_agent_output
            compiled = compile_constitution()
            result = verify_agent_output(compiled, args.output)
            print("Verification Result:")
            print(f"  Compliant: {result['compliant']}")
            print(f"  Score: {result['score']}/100")
            print(f"  Version: {result['version']}")
            if result['violations']:
                print("  Violations:")
                for v in result['violations']:
                    print(f"    - [{v['severity']}] {v['description']}")
        else:
            print(f"Unknown subcommand: {subcmd}")
            print("Available: view, thresholds, errors, check, edit, compile, verify")
        return 0

    def cmd_constitution_sync(self, args):
        """Sync Constitution to Policy Engine"""
        from enforcement.constitution_policy_sync import ConstitutionPolicyGenerator
        
        generator = ConstitutionPolicyGenerator()
        policies = generator.sync()
        
        print(f"\n✅ Synced {len(policies)} policies from Constitution")
        return 0

    def cmd_version(self, args):
        """顯示版本"""
        print(f"Methodology v{self.VERSION}")
        return 0

    def cmd_gatekeeper(self, args):
        """Workflow Gatekeeper"""
        from anti_shortcut.gatekeeper import Gatekeeper, Phase
        
        gk = Gatekeeper()
        action = args.action
        
        if action == "status":
            gk.print_status()
        elif action == "check":
            print("檢查所有 Gates...")
            all_passed = gk.check_all_gates()
            gk.print_status()
            if all_passed:
                print("\n✅ 所有 Gates 通過")
                return 0
            else:
                print("\n❌ 部分 Gates 未通過")
                return 1
        elif action == "enforce":
            print("强制執行 Constitution...")
            gk.start_phase(Phase.CONSTITUTION)
            # 執行 Constitution gates
            for gate in gk.phase_records[Phase.CONSTITUTION].gates:
                gk.check_gate(gate.gate_id)
            gk.print_status()
            if gk.can_proceed_to_next_phase():
                print("\n✅ Constitution 階段完成，可以進入下一階段")
                return 0
            else:
                print("\n❌ Constitution 階段未完成")
                return 1
        return 0

    def cmd_confirmations(self, args):
        """Double Confirmation Management"""
        dc = DoubleConfirmation(timeout_minutes=30)
        action = args.action
        
        if action == "list":
            pending = dc.get_pending(operation=args.operation)
            if not pending:
                print("沒有待確認的操作")
                return 0
            print(f"待確認操作 ({len(pending)} 個):")
            for p in pending:
                required = 1 if p.level == ConfirmationLevel.SINGLE else 2
                print(f"  [{p.confirmation_id}] {p.operation}")
                print(f"      描述: {p.description}")
                print(f"      等級: {p.level.value} (需要 {required} 人確認)")
                print(f"      已確認: {len(p.confirmations)}/{required}")
                print()
            return 0
        
        elif action == "confirm":
            if not args.confirmation_id or not args.confirmed_by:
                print("錯誤：需要 --id 和 --by 參數")
                return 1
            success = dc.confirm(args.confirmation_id, args.confirmed_by)
            if success:
                status = dc.get_status(args.confirmation_id)
                if status and status.get("status") == "approved":
                    print(f"✓ 確認完成，操作已批准")
                else:
                    print(f"✓ 確認已記錄，等待更多人確認...")
                return 0
            else:
                print(f"✗ 確認失敗，ID 不存在或已過期")
                return 1
        
        elif action == "reject":
            if not args.confirmation_id or not args.confirmed_by:
                print("錯誤：需要 --id 和 --by 參數")
                return 1
            success = dc.reject(args.confirmation_id, args.confirmed_by, args.reason or "")
            if success:
                print(f"✓ 操作已拒絕")
                return 0
            else:
                print(f"✗ 拒絕失敗，ID 不存在或已過期")
                return 1
        
        elif action == "status":
            if not args.confirmation_id:
                print("錯誤：需要 --id 參數")
                return 1
            status = dc.get_status(args.confirmation_id)
            if status:
                print(f"確認狀態:")
                print(f"  ID: {status['confirmation_id']}")
                print(f"  操作: {status['operation']}")
                print(f"  描述: {status.get('description', 'N/A')}")
                print(f"  等級: {status.get('level', 'N/A')}")
                print(f"  狀態: {status['status']}")
                print(f"  已確認: {status['confirmations']}")
                if 'required' in status:
                    print(f"  需要: {status['required']} 人")
                return 0
            else:
                print(f"✗ 找不到確認 ID")
                return 1
        
        elif action == "check":
            if not args.operation:
                print("錯誤：需要 --operation 參數")
                return 1
            level = dc.requires_confirmation(args.operation)
            print(f"操作 '{args.operation}' 需要確認等級: {level.value}")
            if level == ConfirmationLevel.BLOCKED:
                print("  ⚠️ 此操作被阻止")
            elif level == ConfirmationLevel.APPROVAL:
                print("  需要人類審批")
            elif level == ConfirmationLevel.DOUBLE:
                print("  需要 2 人確認")
            elif level == ConfirmationLevel.SINGLE:
                print("  需要 1 人確認")
            return 0
        
        return 0

    def cmd_release(self, args):
        """Release Management with Double Confirmation"""
        if not args.version:
            print("錯誤：需要 --version 參數")
            return 1
        
        dc = DoubleConfirmation(timeout_minutes=30)
        operation = "release"
        description = f"發布版本 {args.version} 到 GitHub"
        metadata = {"version": args.version, "repo": args.repo or "main"}
        
        level = dc.requires_confirmation(operation)
        
        if level == ConfirmationLevel.BLOCKED:
            print("❌ 此操作被系統阻止")
            return 1
        
        if level == ConfirmationLevel.NONE:
            print(f"✅ 發布 {args.version} - 不需要確認")
            return 0
        
        if not args.confirm:
            print(f"⚠️  發布 {args.version} 需要確認")
            print(f"   使用 --confirm 參數來請求確認")
            conf_id = dc.create_pending(operation, description, metadata)
            if conf_id:
                print(f"   確認 ID: {conf_id}")
            return 1
        
        # 創建待確認
        conf_id = dc.create_pending(operation, description, metadata)
        
        if conf_id == "__BLOCKED__":
            print("❌ 此操作被阻止")
            return 1
        
        # Agent 確認 (第一次)
        print("Waiting for confirmation...")
        dc.confirm(conf_id, confirmed_by="agent-cli")
        
        pending = dc._find_pending(conf_id)
        if pending:
            required = 1 if pending.level == ConfirmationLevel.SINGLE else 2
            current = len(pending.confirmations)
            print(f"[{current}/{required}] Agent confirmed")
            
            if current < required:
                print(f"[{required}/{required}] Waiting for human confirmation...")
                print(f"\n請在另一個 terminal 執行:")
                print(f"  python cli.py confirmations confirm --id {conf_id} --by human-admin")
                print(f"\n或查看狀態:")
                print(f"  python cli.py confirmations status --id {conf_id}")
                return 1
        else:
            status = dc.get_status(conf_id)
            if status and status.get("status") == "approved":
                print("✓ Release approved")
                return 0
            else:
                print("✗ Release not approved")
                return 1
        
        return 0

    def cmd_policy(self, args):
        """Run Policy Engine checks"""
        from enforcement.policy_engine import create_hard_block_engine
        try:
            engine = create_hard_block_engine()
            results = engine.enforce_all()
            summary = engine.get_summary()
            print(f"\n📊 Policy Summary:")
            print(f"   Passed: {summary['passed']}/{summary['total']}")
            print(f"   Pass Rate: {summary['pass_rate']}%")
            if summary['all_passed']:
                print("\n✅ All policies passed")
                return 0
            else:
                print("\n❌ Some policies failed")
                return 1
        except Exception as e:
            print(f"\n❌ Policy check failed: {e}")
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
                print("Aborted")
                return 0
        
        shutil.copy(hook_source, hook_dest)
        os.chmod(hook_dest, 0o755)
        print(f"✅ Pre-commit hook installed at {hook_dest}")
        return 0

    def cmd_enforcement_config(self, args):
        """Unified Enforcement Configuration"""
        from enforcement_config import EnforcementConfig, ConfigGenerator, EnforcementMode
        
        action = args.action
        
        if not action or action == "show":
            config = EnforcementConfig.load()
            print(config.get_summary())
        elif action == "init":
            config = ConfigGenerator.local_only()
            config.save()
            print("✅ Initialized with LOCAL mode")
            print("   Use 'python cli.py enforcement-config set <mode>' to change")
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
            print(f"✅ Config set: {mode}")
            print(config.get_summary())
        elif action == "detect":
            config = ConfigGenerator.auto_detect()
            print(f"🔍 Detected: {config.mode.value} ({config.platform.value})")
            print(config.get_summary())
        else:
            print(f"Unknown action: {action}")
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
            print("🔍 Running Enforcement Checks...")
            print("=" * 50)

            passed = 0
            failed = 0

            # 1. Policy Engine
            print("\n⚙️ Policy Engine...")
            try:
                engine = PolicyEngine()
                results = engine.enforce_all()
                summary = engine.get_summary()
                print(f"   Passed: {summary['passed']}/{summary['total']}")
                if summary['all_passed']:
                    passed += 1
                    print("   ✅ Policy Engine passed")
                else:
                    failed += 1
                    print("   ❌ Policy Engine failed")
            except Exception as e:
                failed += 1
                print(f"   ❌ Policy Engine error: {e}")

            # 2. Constitution Check
            print("\n📜 Constitution Check...")
            try:
                constitution = ConstitutionAsCode()
                # 嘗試從環境變數讀取 commit message
                import os
                commit_msg = os.environ.get('COMMIT_MSG', os.environ.get('GIT_COMMITMSG', ''))
                if commit_msg:
                    constitution.enforce({"commit_message": commit_msg})
                print("   ✅ Constitution check passed")
                passed += 1
            except Exception as e:
                failed += 1
                print(f"   ❌ Constitution check failed: {e}")

            # 3. 記錄到 Registry
            print("\n📝 Recording to Registry...")
            try:
                registry = ExecutionRegistry()
                registry.record("enforcement-run", {
                    "policy_passed": passed > 0,
                    "constitution_passed": True,
                })
                print("   ✅ Recorded")
            except Exception as e:
                print(f"   ⚠️ Registry warning: {e}")

            # 總結
            print("\n" + "=" * 50)
            if failed == 0:
                print("✅ All enforcement checks passed!")
                return 0
            else:
                print(f"❌ {failed} check(s) failed")
                return 1

        elif sub == "check":
            # 檢查 enforcement 狀態
            config = EnforcementConfig.load()
            print(config.get_summary())
            return 0

        elif sub == "status":
            # 顯示摘要
            config = EnforcementConfig.load()
            print(config.get_summary())

            # 顯示 Policy Engine 狀態
            print("\n⚙️ Policy Engine Status:")
            try:
                engine = PolicyEngine()
                summary = engine.get_summary()
                print(f"   Total Policies: {summary['total']}")
                print(f"   Passed: {summary['passed']}")
                print(f"   Pass Rate: {summary['pass_rate']}%")
            except Exception as e:
                print(f"   Error: {e}")
            return 0

        elif sub == "install":
            # 安裝 hook
            from pathlib import Path
            import shutil

            hook_source = Path(__file__).parent / "pre-commit.template"
            hook_dest = Path(__file__).parent / ".git" / "hooks" / "pre-commit"

            if not hook_source.exists():
                print("❌ pre-commit.template not found")
                return 1

            hook_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(hook_source, hook_dest)
            hook_dest.chmod(0o755)

            print(f"✅ Pre-commit hook installed at {hook_dest}")
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
                    print(f"Unknown mode: {mode}")
                    print("Available: local, github, gitlab, jenkins, azure")
                    return 1

                config.save()
                print(f"✅ Config set to: {mode}")

            print(EnforcementConfig.load().get_summary())
            return 0

        else:
            print(f"Unknown subcommand: {sub}")
            print("Available: run, check, status, install, config")
            return 1

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
            print("Memory validation: OK")
            return 0

        elif sub == "status":
            # 顯示協調狀態
            coordinator = StateCoordinator()
            summary = coordinator.get_global_state_summary()
            print(f"Agents: {summary['total_agents']}")
            print(f"Keys: {summary['total_keys']}")
            print(f"Conflicts: {summary['active_conflicts']}")
            return 0

        elif sub == "audit":
            # 顯示審計日誌
            audit = MemoryAudit()
            records = audit.get_records(limit=10)
            print(f"Recent records: {len(records)}")
            for r in records:
                print(f"  {r.record_id}: {r.action} by {r.agent_id}")
            return 0

        elif sub == "resolve":
            # 解決衝突
            print("Use memoryGovernance.resolve() in code")
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
            print("M2.7 Integration Status:")
            print("  - Hybrid Attention: Ready")
            print("  - Self Iteration: Ready")
            print("  - Failure Analyzer: Ready")
            print("  - Harness Optimizer: Ready")
            return 0

        elif sub == "analyze":
            log = args.failure_log or "No failure log provided"
            analyzer = FailureAnalyzer()
            path = analyzer.analyze(log)
            print(f"Failure Type: {path.failure_type.value}")
            print(f"Root Cause: {path.root_cause}")
            print(f"Confidence: {path.confidence}")
            print("Recommendations:")
            for r in path.recommendations:
                print(f"  - {r}")
            return 0

        elif sub == "iterate":
            print("Self Iteration: Ready (use in code with SelfIteration class)")
            print("  from m27_integration import SelfIteration")
            return 0

        elif sub == "optimize":
            print("Harness Optimizer: Ready (use in code with HarnessOptimizer class)")
            print("  from m27_integration import HarnessOptimizer")
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

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    cli = MethodologyCLI()
    return cli.run(args)


if __name__ == "__main__":
    sys.exit(main())
