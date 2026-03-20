#!/usr/bin/env python3
"""
GanttChart - 甘特圖生成器

為工作流任務生成甘特圖視圖
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class TaskStatus(Enum):
    """任務狀態"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"
    BLOCKED = "blocked"


@dataclass
class GanttTask:
    """甘特圖任務"""
    id: str
    name: str
    start_date: datetime
    duration_days: int  # 持續天數
    end_date: datetime = None
    
    # 依賴
    dependencies: List[str] = field(default_factory=list)
    
    # 狀態
    status: TaskStatus = TaskStatus.PLANNED
    
    # 元數據
    assignee: str = ""
    color: str = "#3B82F6"  # 藍色預設
    progress: float = 0.0  # 0-100%
    
    def __post_init__(self):
        if self.end_date is None:
            self.end_date = self.start_date + timedelta(days=self.duration_days)
    
    @property
    def days(self) -> int:
        return self.duration_days
    
    def get_bar_length(self, scale: int = 3) -> int:
        """根據比例計算柱狀長度"""
        return self.duration_days * scale


class GanttChart:
    """
    甘特圖生成器
    
    使用方式：
    
    ```python
    from methodology import GanttChart
    
    gantt = GanttChart()
    
    # 加入任務
    gantt.add_task("Design", start="2026-03-20", duration=2, assignee="John")
    gantt.add_task("Implement", start="2026-03-22", duration=3, depends_on=["Design"])
    gantt.add_task("Test", start="2026-03-25", duration=2, depends_on=["Implement"])
    
    # 產生圖表
    print(gantt.to_ascii())
    print(gantt.to_mermaid())
    print(gantt.to_json())
    ```
    """
    
    def __init__(self, start_date: str = None, scale: int = 3):
        """
        初始化甘特圖
        
        Args:
            start_date: 開始日期 (YYYY-MM-DD)，預設今天
            scale: 比例 (每個單位代表的天數)
        """
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d") if start_date else datetime.now()
        self.start_date = self.start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        self.scale = scale
        self.tasks: Dict[str, GanttTask] = {}
        self.task_order: List[str] = []
    
    def add_task(self, task_id: str, name: str, start_date: str = None,
                duration: int = 1, depends_on: List[str] = None,
                status: TaskStatus = TaskStatus.PLANNED,
                assignee: str = "", color: str = "#3B82F6") -> GanttTask:
        """
        加入任務
        
        Args:
            task_id: 任務 ID
            name: 任務名稱
            start_date: 開始日期 (YYYY-MM-DD 或 datetime)
            duration: 持續天數
            depends_on: 依賴的任務 ID 列表
            status: 任務狀態
            assignee: 負責人
            color: 顏色 (hex)
            
        Returns:
            GanttTask 實例
        """
        # 解析開始日期
        if isinstance(start_date, str):
            start = datetime.strptime(start_date, "%Y-%m-%d")
        elif isinstance(start_date, datetime):
            start = start_date
        else:
            start = self.start_date
        
        task = GanttTask(
            id=task_id,
            name=name,
            start_date=start,
            duration_days=duration,
            dependencies=depends_on or [],
            status=status,
            assignee=assignee,
            color=color
        )
        
        self.tasks[task_id] = task
        self.task_order.append(task_id)
        
        # 更新結束日期
        task.end_date = start + timedelta(days=duration)
        
        return task
    
    def add_milestone(self, milestone_id: str, name: str, date: str, depends_on: List[str] = None):
        """加入里程碑"""
        return self.add_task(
            task_id=milestone_id,
            name=f"🎯 {name}",
            start_date=date,
            duration=0,  # 里程碑持續 0 天
            depends_on=depends_on,
            status=TaskStatus.PLANNED,
            color="#10B981"  # 綠色
        )
    
    def get_timeline(self) -> List[datetime]:
        """取得時間線"""
        if not self.tasks:
            return [self.start_date]
        
        # 找最早和最晚
        all_dates = []
        for task in self.tasks.values():
            all_dates.extend([task.start_date, task.end_date])
        
        start = min(all_dates)
        end = max(all_dates)
        
        # 生成每天的日期
        dates = []
        current = start
        while current <= end:
            dates.append(current)
            current += timedelta(days=1)
        
        return dates
    
    def get_width(self) -> int:
        """取得圖表寬度"""
        if not self.tasks:
            return 30
        
        dates = self.get_timeline()
        return len(dates) * self.scale + 30
    
    def to_ascii(self) -> str:
        """
        產生 ASCII 甘特圖
        
        Returns:
            ASCII 藝術甘特圖
        """
        if not self.tasks:
            return "No tasks"
        
        lines = []
        dates = self.get_timeline()
        width = self.get_width()
        
        # 標題
        lines.append("=" * width)
        lines.append("GANTT CHART")
        lines.append("=" * width)
        lines.append("")
        
        # 日期軸
        date_header = "Task".ljust(20) + " | "
        for d in dates:
            if d.day % 5 == 0 or d.day == 1:
                date_header += d.strftime("%m/%d")
            else:
                date_header += " "
        lines.append(date_header)
        
        # 分隔線
        lines.append("-" * width)
        
        # 任務列
        for task_id in self.task_order:
            task = self.tasks[task_id]
            
            # 任務名稱
            name = task.name[:18].ljust(20)
            row = name + " | "
            
            # 繪製任務條
            for d in dates:
                if task.start_date <= d < task.end_date:
                    if task.duration_days == 0:
                        row += "◆"  # 里程碑
                    else:
                        row += "█"
                elif d < task.start_date or d >= task.end_date:
                    row += " "
                else:
                    row += "█"
            
            # 狀態標記
            status_markers = {
                TaskStatus.PLANNED: " ○",
                TaskStatus.IN_PROGRESS: " ◔",
                TaskStatus.COMPLETED: " ●",
                TaskStatus.DELAYED: " ⚠",
                TaskStatus.BLOCKED: " ⛔",
            }
            row += status_markers.get(task.status, "")
            
            # 進度
            if task.progress > 0:
                row += f" {task.progress:.0f}%"
            
            lines.append(row)
        
        # 圖例
        lines.append("")
        lines.append("-" * width)
        lines.append("Legend:")
        lines.append("  █ Block (in progress)")
        lines.append("  ○ Planned  ◔ In Progress  ● Completed")
        lines.append("  ⚠ Delayed  ⛔ Blocked")
        lines.append("  ◆ Milestone")
        
        return "\n".join(lines)
    
    def to_mermaid(self) -> str:
        """
        產生 Mermaid Gantt 圖
        
        Returns:
            Mermaid 格式代碼
        """
        lines = ["gantt"]
        lines.append("    title Project Timeline")
        lines.append("    dateFormat YYYY-MM-DD")
        
        # 解析日期格式
        for task_id in self.task_order:
            task = self.tasks[task_id]
            start = task.start_date.strftime("%Y-%m-%d")
            end = task.end_date.strftime("%Y-%m-%d")
            
            # 任務名稱
            name = task.name.replace('🎯 ', '')
            
            # 依賴
            deps = ""
            if task.dependencies:
                deps = f", after: {', '.join(task.dependencies)}"
            
            # 繪製方式：里程碑用 milestone，否則用 section
            if task.duration_days == 0:
                lines.append(f"    milestone {name} {start}{deps}")
            else:
                lines.append(f"    section {name}")
                lines.append(f"    {name} :{start}, {end}{deps}")
        
        return "\n".join(lines)
    
    def to_json(self) -> str:
        """
        產生 JSON 格式
        
        Returns:
            JSON 字串
        """
        import json
        
        data = {
            "start_date": self.start_date.strftime("%Y-%m-%d"),
            "tasks": [
                {
                    "id": task.id,
                    "name": task.name,
                    "start": task.start_date.strftime("%Y-%m-%d"),
                    "end": task.end_date.strftime("%Y-%m-%d"),
                    "duration_days": task.duration_days,
                    "status": task.status.value,
                    "progress": task.progress,
                    "assignee": task.assignee,
                    "dependencies": task.dependencies,
                    "color": task.color
                }
                for task in self.tasks.values()
            ],
            "timeline": [
                d.strftime("%Y-%m-%d")
                for d in self.get_timeline()
            ]
        }
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def to_html(self) -> str:
        """
        產生 HTML 甘特圖
        
        Returns:
            HTML 代碼
        """
        dates = self.get_timeline()
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Gantt Chart</title>
    <style>
        .gantt {{
            font-family: Arial, sans-serif;
            border-collapse: collapse;
            width: 100%;
        }}
        .gantt th, .gantt td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        .gantt th {{
            background-color: #4CAF50;
            color: white;
        }}
        .task-bar {{
            background-color: #3B82F6;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
        }}
        .milestone {{
            background-color: #10B981;
            color: white;
            padding: 4px 8px;
            border-radius: 50%;
        }}
    </style>
</head>
<body>
    <h1>Gantt Chart</h1>
    <table class="gantt">
        <tr>
            <th>Task</th>
            <th>Start</th>
            <th>End</th>
            <th>Duration</th>
            <th>Progress</th>
            <th>Timeline</th>
        </tr>
"""
        
        for task in self.tasks.values():
            # 生成時間軸
            timeline = ""
            for d in dates:
                if task.start_date <= d < task.end_date:
                    if task.duration_days == 0:
                        timeline += "◆"
                    else:
                        timeline += "█"
                else:
                    timeline += " "
            
            task_class = "milestone" if task.duration_days == 0 else "task-bar"
            html += f"""
        <tr>
            <td>{task.name}</td>
            <td>{task.start_date.strftime('%Y-%m-%d')}</td>
            <td>{task.end_date.strftime('%Y-%m-%d')}</td>
            <td>{task.duration_days} days</td>
            <td>{task.progress}%</td>
            <td><span class="{task_class}">{timeline}</span></td>
        </tr>
"""
        
        html += """
    </table>
</body>
</html>
"""
        
        return html
    
    def export_svg(self, filename: str = "gantt.svg"):
        """
        匯出 SVG 檔案
        
        Args:
            filename: 檔案名稱
        """
        svg = self._generate_svg()
        
        with open(filename, 'w') as f:
            f.write(svg)
        
        return filename
    
    def _generate_svg(self) -> str:
        """生成 SVG"""
        dates = self.get_timeline()
        row_height = 30
        date_width = 20 * self.scale
        name_width = 150
        
        width = name_width + len(dates) * date_width + 50
        height = len(self.tasks) * row_height + 80
        
        svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
    <style>
        .task-name {{ font-size: 12px; fill: #333; }}
        .date-label {{ font-size: 10px; fill: #666; }}
        .task-bar {{ fill: #3B82F6; }}
        .milestone {{ fill: #10B981; }}
    </style>
"""
        
        # 標題
        svg += f'    <text x="10" y="30" font-size="16" font-weight="bold">Project Gantt</text>\n'
        
        # 日期軸
        y = 50
        svg += f'    <text x="10" y="{y + 15}" class="task-name">Task</text>\n'
        
        for i, d in enumerate(dates):
            x = name_width + i * date_width
            svg += f'    <text x="{x}" y="{y + 15}" class="date-label">{d.day}</text>\n'
            svg += f'    <line x1="{x}" y1="{y}" x2="{x}" y2="{height}" stroke="#eee" />\n'
        
        # 任務
        for j, task_id in enumerate(self.task_order):
            task = self.tasks[task_id]
            y = 60 + j * row_height
            
            # 任務名稱
            svg += f'    <text x="10" y="{y + 20}" class="task-name">{task.name}</text>\n'
            
            # 任務條
            if task.duration_days == 0:
                # 里程碑
                start_idx = (task.start_date - dates[0]).days
                x = name_width + start_idx * date_width
                svg += f'    <circle cx="{x + 5}" cy="{y + 15}" r="8" class="milestone" />\n'
            else:
                # 普通任務
                start_idx = (task.start_date - dates[0]).days
                width = task.duration_days * date_width
                x = name_width + start_idx * date_width
                svg += f'    <rect x="{x}" y="{y + 5}" width="{width}" height="20" rx="4" class="task-bar" />\n'
                
                # 進度
                if task.progress > 0:
                    progress_width = width * (task.progress / 100)
                    svg += f'    <rect x="{x}" y="{y + 5}" width="{progress_width}" height="20" rx="4" fill="#2563EB" />\n'
        
    
    # ==================== 增強視覺化 ====================
    
    def to_rich_ascii(self) -> str:
        """產生豐富的 ASCII 甘特圖"""
        if not self.tasks:
            return "No tasks"
        
        dates = self.get_timeline()
        lines = []
        
        lines.append("╔" + "═" * 70 + "╗")
        lines.append("║" + " GANTT CHART ".center(70) + "║")
        lines.append("╚" + "═" * 70 + "╝")
        lines.append("")
        
        # Date header
        date_str = "│" + "Task".ljust(18)
        for d in dates:
            date_str += d.strftime(" %m/%d")
        lines.append(date_str + " │")
        lines.append("├" + "─" * 19 + "┼" + "─" * (len(dates) * 6) + "┤")
        
        for task_id in self.task_order:
            task = self.tasks[task_id]
            status_icons = {
                TaskStatus.PLANNED: "○",
                TaskStatus.IN_PROGRESS: "◔",
                TaskStatus.COMPLETED: "●",
                TaskStatus.DELAYED: "◐",
                TaskStatus.BLOCKED: "⛔",
            }
            icon = status_icons.get(task.status, "?")
            name = task.name[:16].ljust(16)
            row = f"│ {icon} {name} │"
            
            for d in dates:
                if task.duration_days == 0:
                    row += "  ◆  " if d.date() == task.start_date.date() else "     "
                elif task.start_date.date() <= d.date() < task.end_date.date():
                    row += " █ "
                else:
                    row += "  .  "
            lines.append(row)
            
            if task.duration_days > 0 and task.progress > 0:
                prog = "█" * int(task.progress / 10)
                empty = " " * (10 - len(prog))
                lines.append(f"│   └[{prog}{empty}] {task.progress:3.0f}% │")
        
        lines.append("")
        lines.append("○ Planned  ◔ In Progress  ● Completed  ◐ Delayed  ⛔ Blocked  ◆ Milestone")
        return "\n".join(lines)
    
    def to_csv(self) -> str:
        """產生 CSV 格式"""
        lines = ["id,name,start_date,end_date,duration,status,progress,assignee"]
        for task_id in self.task_order:
            task = self.tasks[task_id]
            deps = ",".join(task.dependencies) if task.dependencies else ""
            lines.append(f"{task.id},{task.name},{task.start_date.strftime('%Y-%m-%d')},{task.end_date.strftime('%Y-%m-%d')},{task.duration_days},{task.status.value},{task.progress},{task.assignee},{deps}")
        return "\n".join(lines)
    
    def export_csv(self, filename: str = "gantt.csv"):
        """匯出 CSV"""
        with open(filename, 'w') as f:
            f.write(self.to_csv())
        return filename
    
    def to_interactive_html(self) -> str:
        """產生互動式 HTML (Plotly.js)"""
        task_names = [t.name for t in self.tasks.values()]
        durations = [t.duration_days for t in self.tasks.values()]
        progress = [t.progress for t in self.tasks.values()]
        colors = ["#10B981" if t.status == TaskStatus.COMPLETED else "#3B82F6" for t in self.tasks.values()]
        
        return f"""<!DOCTYPE html>
<html><head><title>Gantt Chart</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>body{{font-family:Arial;margin:20px}}#chart{{width:100%;height:500px}}</style>
</head><body>
<h1>📊 Gantt Chart</h1>
<div id="chart"></div>
<script>
var data=[{{type:'bar',x:{durations},y:{task_names},orientation:'h',marker:{{color:'{colors}'}},text:{progress},textposition:'outside'}}];
Plotly.newPlot('chart',data,{{title:'Project Timeline',xaxis:{{title:'Days'}},yaxis:{{title:'',automargin:true}},height:500,margin:{{l:150}}}});
</script></body></html>"""
    
    def export_interactive_html(self, filename: str = "gantt_interactive.html"):
        """匯出互動式 HTML"""
        with open(filename, 'w') as f:
            f.write(self.to_interactive_html())
        return filename
    
    def get_summary(self) -> Dict:
        """取得甘特圖摘要"""
        if not self.tasks:
            return {}
        dates = self.get_timeline()
        return {
            "total_tasks": len(self.tasks),
            "total_days": len(dates),
            "start_date": dates[0].strftime('%Y-%m-%d') if dates else None,
            "end_date": dates[-1].strftime('%Y-%m-%d') if dates else None,
            "completed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED),
            "in_progress": sum(1 for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS),
            "total_progress": sum(t.progress for t in self.tasks.values()) / len(self.tasks) if self.tasks else 0,
        }


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    gantt = GanttChart()
    gantt.add_task('design', 'System Design', start_date='2026-03-20', duration=2, assignee='Alice')
    gantt.add_task('backend', 'Backend Dev', start_date='2026-03-22', duration=3, depends_on=['design'], assignee='Bob')
    gantt.tasks['design'].status = TaskStatus.COMPLETED
    gantt.tasks['design'].progress = 100
    gantt.tasks['backend'].status = TaskStatus.IN_PROGRESS
    gantt.tasks['backend'].progress = 50
    
    print("=== Rich ASCII ===")
    print(gantt.to_rich_ascii())
    print("\n=== Summary ===")
    import json
    print(json.dumps(gantt.get_summary(), indent=2))
