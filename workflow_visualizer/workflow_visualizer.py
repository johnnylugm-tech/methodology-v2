"""
Workflow Visualizer for methodology-v2

Provides Mermaid diagram generation, execution tracing, and real-time monitoring.
"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AgentNode:
    """Agent node in workflow"""
    name: str
    role: str = ""
    description: str = ""
    color: str = ""


@dataclass
class TaskEvent:
    """Task execution event"""
    task_id: str
    agent: str
    action: str  # start, end, error
    timestamp: float = field(default_factory=time.time)
    data: Dict = field(default_factory=dict)
    duration: float = 0


class WorkflowVisualizer:
    """Generate workflow diagrams for methodology-v2"""
    
    THEMES = {
        "light": {"bg": "#ffffff", "text": "#333333"},
        "dark": {"bg": "#1e1e1e", "text": "#d4d4d4"}
    }
    
    AGENT_STYLES = {
        "research": {"color": "#97C1A9", "shape": "rounded"},
        "coder": {"color": "#82AAFF", "shape": "rectangle"},
        "reviewer": {"color": "#FFCB6B", "shape": "diamond"},
        "default": {"color": "#C792EA", "shape": "rounded"}
    }
    
    def __init__(self, theme: str = "light", layout: str = "TB"):
        self.theme = theme
        self.layout = layout
        self.custom_styles = {}
    
    def generate_diagram(
        self,
        agents: List[str] = None,
        process: str = "sequential",
        user_start: bool = True
    ) -> str:
        """Generate Mermaid workflow diagram"""
        if not agents:
            agents = ["Agent1", "Agent2", "Agent3"]
        
        if process == "sequential":
            return self._sequential_diagram(agents, user_start)
        elif process == "parallel":
            return self._parallel_diagram(agents, user_start)
        elif process == "hierarchical":
            return self._hierarchical_diagram(agents, user_start)
        else:
            return self._sequential_diagram(agents, user_start)
    
    def _sequential_diagram(self, agents: List[str], user_start: bool) -> str:
        """Generate sequential flow diagram"""
        lines = ["graph TB"]
        
        if user_start:
            lines.append("    Start([User])")
        
        prev = "Start" if user_start else None
        
        for i, agent in enumerate(agents):
            agent_id = f"A{i}"
            agent_name = agent if isinstance(agent, str) else agent.get("name", f"Agent{i}")
            role = agent.get("role", "") if isinstance(agent, dict) else ""
            
            node = f'{agent_id}["{agent_name}"]'
            if role:
                node = f'{agent_id}["{agent_name}\\n({role})"]'
            
            lines.append(f"    {node}")
            
            if prev:
                lines.append(f"    {prev} --> {agent_id}")
            
            prev = agent_id
        
        if user_start:
            lines.append(f"    {prev} --> End([User])")
        
        # Add styling
        lines.append("")
        lines.append("    classDef default fill:#f9f9f9,stroke:#333,stroke-width:1px")
        
        return "\n".join(lines)
    
    def _parallel_diagram(self, agents: List[str], user_start: bool) -> str:
        """Generate parallel flow diagram"""
        lines = ["graph TB"]
        
        if user_start:
            lines.append("    Start([User])")
            lines.append("    Start --> Split{Split}")
        else:
            lines.append("    Split{Split}")
        
        lines.append("    Split --> A0[Agent 1]")
        lines.append("    Split --> A1[Agent 2]")
        lines.append("    Split --> A2[Agent 3]")
        
        lines.append("    A0 --> Merge")
        lines.append("    A1 --> Merge")
        lines.append("    A2 --> Merge")
        
        if user_start:
            lines.append("    Merge --> End([User])")
        
        return "\n".join(lines)
    
    def _hierarchical_diagram(self, agents: List[str], user_start: bool) -> str:
        """Generate hierarchical flow diagram"""
        lines = ["graph TB"]
        
        if user_start:
            lines.append("    Start([User])")
            lines.append("    Start --> Coordinator[Coordinator]")
        else:
            lines.append("    Coordinator[Coordinator]")
        
        lines.append("    Coordinator --> Worker1[Worker 1]")
        lines.append("    Coordinator --> Worker2[Worker 2]")
        
        lines.append("    Worker1 --> Coordinator")
        lines.append("    Worker2 --> Coordinator")
        
        if user_start:
            lines.append("    Coordinator --> End([User])")
        
        return "\n".join(lines)
    
    def generate_diagram_from_crew(self, crew) -> str:
        """Generate diagram from methodology-v2 Crew"""
        agents = []
        if hasattr(crew, 'agents'):
            for agent in crew.agents:
                agents.append({
                    "name": getattr(agent, "name", "Agent"),
                    "role": getattr(agent, "role", "")
                })
        
        process = getattr(crew, "process", "sequential")
        return self.generate_diagram(agents, process)
    
    def set_agent_style(self, agent_name: str, color: str = None, shape: str = None):
        """Set custom style for agent"""
        self.custom_styles[agent_name] = {"color": color, "shape": shape}


class ExecutionTracer:
    """Trace and visualize agent execution"""
    
    def __init__(self):
        self.events: List[TaskEvent] = []
        self.tasks: Dict[str, Dict] = {}
    
    def start_task(self, agent: str, data: Dict = None) -> str:
        """Start tracking a task"""
        task_id = f"{agent}_{len(self.events)}"
        
        event = TaskEvent(
            task_id=task_id,
            agent=agent,
            action="start",
            data=data or {}
        )
        
        self.events.append(event)
        self.tasks[task_id] = {"agent": agent, "start_time": time.time(), "data": data}
        
        logger.info(f"Started task: {task_id}")
        return task_id
    
    def end_task(self, agent: str, data: Dict = None):
        """End tracking a task"""
        # Find matching start event
        for task_id, task in self.tasks.items():
            if task["agent"] == agent and "end_time" not in task:
                task["end_time"] = time.time()
                task["duration"] = task["end_time"] - task["start_time"]
                task["result"] = data
                
                event = TaskEvent(
                    task_id=task_id,
                    agent=agent,
                    action="end",
                    data=data or {},
                    duration=task["duration"]
                )
                self.events.append(event)
                
                logger.info(f"Ended task: {task_id} (duration: {task['duration']:.2f}s)")
                return
        
        logger.warning(f"No matching start event for: {agent}")
    
    def error(self, agent: str, error: str):
        """Record error"""
        for task_id, task in self.tasks.items():
            if task["agent"] == agent and "end_time" not in task:
                task["end_time"] = time.time()
                task["error"] = error
                
                event = TaskEvent(
                    task_id=task_id,
                    agent=agent,
                    action="error",
                    data={"error": error}
                )
                self.events.append(event)
                
                logger.error(f"Error in {agent}: {error}")
                return
    
    def visualize(self, format: str = "mermaid") -> str:
        """Visualize execution trace"""
        if format == "mermaid":
            return self._mermaid_trace()
        elif format == "json":
            return json.dumps(self.events, indent=2)
        else:
            return self._mermaid_trace()
    
    def _mermaid_trace(self) -> str:
        """Generate Mermaid timeline"""
        lines = ["sequenceDiagram"]
        
        for event in self.events:
            if event.action == "start":
                participant = event.agent
                lines.append(f"    participant {participant}")
                lines.append(f"    {participant}->>+{participant}: Start")
            elif event.action == "end":
                duration = f"({event.duration:.2f}s)" if event.duration else ""
                lines.append(f"    {event.agent}-->>-{event.agent}: End {duration}")
            elif event.action == "error":
                lines.append(f"    {event.agent}-->>-{event.agent}: Error")
        
        return "\n".join(lines)
    
    def get_timeline(self) -> List[Dict]:
        """Get execution timeline"""
        timeline = []
        
        for task_id, task in self.tasks.items():
            timeline.append({
                "agent": task["agent"],
                "start": task["start_time"],
                "end": task.get("end_time"),
                "duration": task.get("duration", 0),
                "error": task.get("error"),
                "result": task.get("result")
            })
        
        return sorted(timeline, key=lambda x: x["start"])
    
    def find_bottlenecks(self) -> List[Dict]:
        """Find execution bottlenecks"""
        bottlenecks = []
        
        for task_id, task in self.tasks.items():
            duration = task.get("duration", 0)
            
            if duration > 10:  # Threshold: 10 seconds
                bottlenecks.append({
                    "agent": task["agent"],
                    "avg_time": duration,
                    "issues": ["slow_execution"]
                })
        
        return bottlenecks


class WorkflowMonitor:
    """Real-time workflow monitoring"""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.tracer = ExecutionTracer()
        self.events = []
    
    def start_task(self, agent: str, data: Dict = None):
        """Record task start"""
        task_id = self.tracer.start_task(agent, data)
        self.events.append({
            "type": "task_start",
            "agent": agent,
            "task_id": task_id,
            "timestamp": datetime.now().isoformat()
        })
    
    def end_task(self, agent: str, data: Dict = None):
        """Record task end"""
        self.tracer.end_task(agent, data)
        self.events.append({
            "type": "task_end",
            "agent": agent,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_status(self) -> Dict:
        """Get current status"""
        return {
            "active_tasks": len([t for t in self.tracer.tasks.values() if "end_time" not in t]),
            "completed_tasks": len([t for t in self.tracer.tasks.values() if "end_time" in t]),
            "errors": len([t for t in self.tracer.tasks.values() if "error" in t]),
            "recent_events": self.events[-10:]
        }


# CLI entry point
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Workflow Visualizer")
    parser.add_argument("command", choices=["diagram", "trace", "monitor"])
    parser.add_argument("--agents", help="Comma-separated agent names")
    parser.add_argument("--process", choices=["sequential", "parallel", "hierarchical"])
    parser.add_argument("--port", type=int, default=8080)
    
    args = parser.parse_args()
    
    viz = WorkflowVisualizer()
    tracer = ExecutionTracer()
    
    if args.command == "diagram":
        agents = args.agents.split(",") if args.agents else ["A", "B", "C"]
        process = args.process or "sequential"
        print(viz.generate_diagram(agents, process))
    
    elif args.command == "trace":
        print("Use tracer.visualize() in code")
    
    elif args.command == "monitor":
        monitor = WorkflowMonitor(port=args.port)
        print(f"Monitor started on port {args.port}")
