"""Observability Agent - 完整套用 methodology-v2 框架"""
import sys
sys.path.insert(0, '/workspace/methodology-v2')

from methodology_base import QualityGate, Monitor

try:
    from smart_router import SmartRouter
    ROUTER = True
except ImportError:
    ROUTER = False

class ObservabilityAgent:
    """可觀測性 Agent"""
    
    def __init__(self, agent_id: str, name: str = "ObsBot"):
        self.id = agent_id
        self.name = name
        self.status = "idle"
        
        # Framework 整合
        if ROUTER:
            self.router = SmartRouter(auto_route=True)
        else:
            self.router = None
        
        self.quality_gate = QualityGate()
        self.monitor = Monitor()
        self._traces = []
    
    def run(self, task: str):
        self.status = "running"
        
        # 自動路由
        model = "default"
        if self.router:
            route = self.router.route(task)
            model = route.model
        
        # 執行
        result = self._execute(task)
        
        # 品質把關
        self.quality_gate.check_default(result)
        
        self.status = "completed"
        return {"model": model, "result": result}
    
    def _execute(self, task: str):
        self._traces.append({"task": task, "status": "completed"})
        return {"task": task, "status": "completed"}

if __name__ == "__main__":
    agent = ObservabilityAgent("obs-001")
    result = agent.run("collect metrics")
