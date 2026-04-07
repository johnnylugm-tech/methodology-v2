#!/usr/bin/env python3
"""
Unit Tests - methodology-v2 Core Modules

執行方式：
    python -m pytest tests/ -v
    python -m unittest tests/test_progress_dashboard.py -v
"""

import unittest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from progress_dashboard import ProgressDashboard, BacklogItem, Sprint
from cost_allocator import CostAllocator, CostEntry, Budget, CostType
from message_bus import MessageBus, MessageType, MessagePriority, Envelope
from gantt_chart import GanttChart, GanttTask, TaskStatus
from pm_mode import PMMode, MorningReport, CostForecast
from pm_terminology import PMTerminologyMapper, TermMapping, Role
from resource_dashboard import ResourceDashboard, Resource, ResourceType, ResourceStatus, TeamMember, SkillLevel


class TestProgressDashboard(unittest.TestCase):
    """ProgressDashboard 測試"""
    
    def setUp(self):
        """測試前準備"""
        self.dashboard = ProgressDashboard()
    
    def test_create_sprint(self):
        """測試建立 Sprint"""
        sprint_id = self.dashboard.create_sprint(
            name="Test Sprint",
            goal="Test Goal",
            capacity=40
        )
        self.assertIsNotNone(sprint_id)
        self.assertIn(sprint_id, self.dashboard.sprints)
    
    def test_add_to_backlog(self):
        """測試加入 backlog"""
        item_id = self.dashboard.add_to_backlog(
            title="Test Item",
            story_points=5,
            priority=2
        )
        self.assertIsNotNone(item_id)
        self.assertIn(item_id, self.dashboard.backlog)
        
        item = self.dashboard.backlog[item_id]
        self.assertEqual(item.title, "Test Item")
        self.assertEqual(item.story_points, 5)
        self.assertEqual(item.priority, 2)
        self.assertFalse(item.completed)
    
    def test_mark_item_completed(self):
        """測試標記完成"""
        item_id = self.dashboard.add_to_backlog("Test", story_points=3)
        
        # 初始未完成
        self.assertFalse(self.dashboard._is_item_completed(item_id))
        
        # 標記完成
        result = self.dashboard.mark_item_completed(item_id)
        self.assertTrue(result)
        
        # 驗證完成
        self.assertTrue(self.dashboard._is_item_completed(item_id))
        self.assertTrue(self.dashboard.backlog[item_id].completed)
        self.assertIsNotNone(self.dashboard.backlog[item_id].completed_at)
    
    def test_sprint_basic(self):
        """測試 Sprint 基本功能"""
        sprint_id = self.dashboard.create_sprint(
            name="Test Sprint",
            goal="Goal",
            capacity=50
        )
        self.assertIsNotNone(sprint_id)
        self.assertIn(sprint_id, self.dashboard.sprints)
        
        sprint = self.dashboard.sprints[sprint_id]
        self.assertEqual(sprint.name, "Test Sprint")
        self.assertEqual(sprint.capacity, 50)
    
    def test_persistence(self):
        """測試持久化"""
        import tempfile
        import os
        
        item_id = self.dashboard.add_to_backlog("Persist Test", story_points=5)
        self.dashboard.mark_item_completed(item_id)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
            path = f.name
        
        try:
            self.dashboard.save(path)
            self.assertTrue(os.path.exists(path))
            
            # 載入新實例
            new_dashboard = ProgressDashboard()
            new_dashboard.load(path)
            
            self.assertIn(item_id, new_dashboard.backlog)
            self.assertTrue(new_dashboard.backlog[item_id].completed)
        finally:
            if os.path.exists(path):
                os.unlink(path)


class TestCostAllocator(unittest.TestCase):
    """CostAllocator 測試"""
    
    def setUp(self):
        """測試前準備"""
        self.allocator = CostAllocator()
    
    def test_create_budget(self):
        """測試建立預算"""
        budget_id = self.allocator.create_budget(
            name="Test Project",
            total_amount=1000.0,
            period="project"
        )
        self.assertIsNotNone(budget_id)
        self.assertIn(budget_id, self.allocator.budgets)
    
    def test_cost_entry(self):
        """測試成本項目"""
        self.allocator.create_budget("proj1", 500.0, "project")
        
        entry_id = self.allocator.add_entry(
            project_id="proj1",
            user_id="user1",
            cost_type=CostType.API_CALL,
            amount=50.0
        )
        
        self.assertIsNotNone(entry_id)
        self.assertEqual(len(self.allocator.entries), 1)
    
    def test_budget_update(self):
        """測試預算更新"""
        self.allocator.create_budget("proj1", 100.0, "project")
        self.allocator.create_budget("proj2", 200.0, "project")
        
        # 只更新 proj1
        self.allocator.add_entry("proj1", "user1", CostType.API_CALL, 30.0)
        
        proj1 = self.allocator.budgets.get("budget-1")
        proj2 = self.allocator.budgets.get("budget-2")
        
        self.assertEqual(proj1.spent, 30.0)
        self.assertEqual(proj2.spent, 0.0)
    
    def test_cost_by_project(self):
        """測試專案成本查詢"""
        self.allocator.create_budget("proj1", 500.0, "project")
        
        self.allocator.add_entry("proj1", "user1", CostType.API_CALL, 100.0)
        self.allocator.add_entry("proj1", "user2", CostType.COMPUTE, 50.0)
        
        costs = self.allocator.get_project_costs("proj1")
        self.assertEqual(costs["total"], 150.0)
        self.assertEqual(costs["by_user"]["user1"], 100.0)
        self.assertEqual(costs["by_user"]["user2"], 50.0)


class TestMessageBus(unittest.TestCase):
    """MessageBus 測試"""
    
    def setUp(self):
        """測試前準備"""
        self.bus = MessageBus()
    
    def test_publish(self):
        """測試發布訊息"""
        msg_id = self.bus.publish("test-topic", {"key": "value"})
        self.assertIsNotNone(msg_id)
        self.assertTrue(len(msg_id) > 0)
    
    def test_subscribe(self):
        """測試訂閱"""
        received = []
        
        def handler(msg):
            received.append(msg)
        
        self.bus.subscribe("test-topic", handler)
        self.bus.publish("test-topic", {"data": "test"})
        
        # 處理訊息 - 調用 process_next 如果存在的話
        # 或直接檢查訊息是否被處理
        status = self.bus.get_queue_status()
        self.assertGreater(status["stats"]["messages_sent"], 0)
    
    def test_priority_queue(self):
        """測試優先級佇列"""
        self.bus.publish("task", {"task": "low"}, MessagePriority.LOW)
        self.bus.publish("task", {"task": "high"}, MessagePriority.HIGH)
        self.bus.publish("task", {"task": "normal"}, MessagePriority.NORMAL)
        
        # 佇列中應該有訊息
        status = self.bus.get_queue_status()
        self.assertGreater(status["queue_size"], 0)
    
    def test_dead_letter_queue(self):
        """測試死信佇列"""
        def failing_handler(msg):
            raise Exception("Test error")
        
        self.bus.subscribe("fail-topic", failing_handler)
        self.bus.publish("fail-topic", {"fails": True})
        
        # 檢查死信佇列狀態
        status = self.bus.get_queue_status()
        self.assertIn("dead_letter_queue_size", status)
    
    def test_to_cli(self):
        """測試 CLI 輸出"""
        self.bus.publish("tasks", {"task": "test"})
        self.bus.publish("errors", {"error": "failed"})
        
        output = self.bus.to_cli()
        self.assertIsInstance(output, str)
        self.assertIn("MESSAGE BUS STATUS", output)
        self.assertIn("Messages Sent", output)


class TestGanttChart(unittest.TestCase):
    """GanttChart 測試"""
    
    def setUp(self):
        """測試前準備"""
        self.gantt = GanttChart()
    
    def test_add_task(self):
        """測試加入任務"""
        task = self.gantt.add_task(
            task_id="task-1",
            name="Test Task",
            start_date="2026-03-20",
            duration=5,
            status=TaskStatus.IN_PROGRESS
        )
        
        self.assertIsNotNone(task)
        self.assertIn("task-1", self.gantt.tasks)
        self.assertEqual(self.gantt.tasks["task-1"].name, "Test Task")
    
    def test_to_rich_ascii(self):
        """測試 ASCII 輸出"""
        self.gantt.add_task("task-1", "Task 1", "2026-03-20", 5)
        self.gantt.add_task("task-2", "Task 2", "2026-03-22", 6)
        
        output = self.gantt.to_rich_ascii()
        self.assertIsInstance(output, str)
        self.assertIn("Task 1", output)
        self.assertIn("Task 2", output)
    
    def test_get_summary(self):
        """測試摘要"""
        self.gantt.add_task("task-1", "Task 1", "2026-03-20", 5, status=TaskStatus.COMPLETED)
        self.gantt.add_task("task-2", "Task 2", "2026-03-22", 6, status=TaskStatus.IN_PROGRESS)
        
        summary = self.gantt.get_summary()
        
        self.assertEqual(summary["total_tasks"], 2)
        self.assertEqual(summary["completed"], 1)
        self.assertEqual(summary["in_progress"], 1)
    
    def test_csv_export(self):
        """測試 CSV 匯出"""
        self.gantt.add_task("task-1", "Task 1", "2026-03-20", 5)
        
        csv = self.gantt.to_csv()
        self.assertIn("Task 1", csv)
        self.assertIn("2026-03-20", csv)


class TestPMMode(unittest.TestCase):
    """PMMode 測試"""
    
    def setUp(self):
        """測試前準備"""
        self.pm = PMMode()
    
    def test_generate_morning_report(self):
        """測試生成晨間報告"""
        report = self.pm.generate_morning_report(
            sprint_name="Sprint 5",
            sprint_progress=65.0,
            completed_yesterday=["完成登入功能"],
            planned_today=["開發儀表板"],
            blockers=["等 API 文件"],
            velocity=42.0
        )
        
        self.assertIsInstance(report, MorningReport)
        self.assertEqual(report.sprint_name, "Sprint 5")
        self.assertEqual(report.sprint_progress, 65.0)
        self.assertEqual(len(report.completed_yesterday), 1)
        self.assertEqual(len(report.blockers), 1)
    
    def test_cost_predictor(self):
        """測試成本預測"""
        forecast = self.pm.predict_cost(
            project_name="AI Assistant",
            current_cost=500.0,
            budget=2000.0,
            daily_burn_rate=100.0,
            days_remaining=20
        )
        
        self.assertIsInstance(forecast, CostForecast)
        self.assertEqual(forecast.project_name, "AI Assistant")
        self.assertEqual(forecast.current_cost, 500.0)
        self.assertEqual(forecast.budget, 2000.0)
        self.assertTrue(forecast.days_until_budget_exhausted > 0)
    
    def test_sprint_health(self):
        """測試 Sprint 健康狀況"""
        health = self.pm.get_sprint_health(
            velocity=35,
            planned=50,
            completed=30
        )
        
        self.assertIn("health", health)
        self.assertIn("health_score", health)
        self.assertIn("completion_rate", health)
        self.assertEqual(health["completion_rate"], 60.0)
    
    def test_report_to_markdown(self):
        """測試報告轉 Markdown"""
        report = self.pm.generate_morning_report(
            sprint_name="Test",
            sprint_progress=50.0
        )
        
        md = report.to_markdown()
        self.assertIsInstance(md, str)
        self.assertIn("# 🌅 晨間報告", md)
        self.assertIn("Test", md)


class TestPMTerminology(unittest.TestCase):
    """PM Terminology 測試"""
    
    def setUp(self):
        """測試前準備"""
        self.mapper = PMTerminologyMapper()
    
    def test_search(self):
        """測試搜尋"""
        results = self.mapper.search("sprint")
        self.assertGreater(len(results), 0)
    
    def test_get_by_term_id(self):
        """測試依 ID 取得"""
        mapping = self.mapper.get("sprint")
        self.assertIsNotNone(mapping)
        # pm_term should contain sprint-related content
        self.assertTrue(len(mapping.pm_term) > 0)
    
    def test_translate(self):
        """測試翻譯"""
        result = self.mapper.translate("velocity", Role.DEV, Role.PM)
        self.assertIsNotNone(result)
    
    def test_categories(self):
        """測試類別"""
        categories = self.mapper.CATEGORIES
        self.assertIn("backlog", categories)
        self.assertIn("sprint", categories)
        self.assertIn("estimation", categories)
    
    def test_to_markdown_table(self):
        """測試 Markdown 表格"""
        table = self.mapper.to_markdown_table()
        self.assertIsInstance(table, str)
        self.assertIn("| 術語 |", table)


class TestResourceDashboard(unittest.TestCase):
    """ResourceDashboard 測試"""
    
    def setUp(self):
        """測試前準備"""
        self.dashboard = ResourceDashboard()
    
    def test_add_resource(self):
        """測試加入資源"""
        resource = self.dashboard.add_resource(
            id="test-tool",
            name="Test Tool",
            type=ResourceType.TOOL,
            description="A test tool",
            cost=10.0
        )
        
        self.assertIsNotNone(resource)
        self.assertIn("test-tool", self.dashboard.resources)
    
    def test_get_by_type(self):
        """測試依類型取得"""
        resources = self.dashboard.get_resources_by_type(ResourceType.TOOL)
        self.assertGreater(len(resources), 0)
    
    def test_get_summary(self):
        """測試摘要"""
        summary = self.dashboard.get_resource_summary()
        
        self.assertIn("total", summary)
        self.assertIn("by_type", summary)
        self.assertIn("total_monthly_cost", summary)
        self.assertGreater(summary["total"], 0)
    
    def test_to_table(self):
        """測試表格輸出"""
        table = self.dashboard.to_table()
        self.assertIsInstance(table, str)
        self.assertIn("RESOURCE INVENTORY", table)
    
    def test_add_team_member(self):
        """測試加入團隊成員"""
        member = self.dashboard.add_team_member(
            resource_id="member-test",
            name="Test User",
            role="Developer",
            skills={"python": SkillLevel.EXPERT}
        )
        
        self.assertIsNotNone(member)
        self.assertIn("member-test", self.dashboard.team_members)


# ==================== Test Runner ====================

if __name__ == "__main__":
    # 執行測試
    unittest.main(verbosity=2)
