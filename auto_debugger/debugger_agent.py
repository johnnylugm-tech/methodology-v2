"""AutoDebugger Agent - 完整套用 methodology-v2 框架"""
import sys
sys.path.insert(0, '/workspace/methodology-v2')

from methodology_base import QualityGate, Monitor

try:
    from smart_router import SmartRouter
    ROUTER = True
except ImportError:
    ROUTER = False

class AutoDebuggerAgent:
    """自動調試 Agent"""
    
    def __init__(self, agent_id: str, name: str = "DebugBot"):
        self.id = agent_id
        self.name = name
        self.status = "idle"
        
        if ROUTER:
            self.router = SmartRouter(auto_route=True)
        else:
            self.router = None
        
        self.quality_gate = QualityGate()
        self.monitor = Monitor()
        self.errors = []
    
    def run(self, task: str):
        self.status = "running"
        
        model = "default"
        if self.router:
            route = self.router.route(task)
            model = route.model
        
        result = self._analyze(task)
        self.quality_gate.check_default(result)
        
        self.status = "completed"
        return {"model": model, "result": result}
    
    def _analyze(self, task: str):
        return {"task": task, "analyzed": True}

if __name__ == "__main__":
    agent = AutoDebuggerAgent("debug-001")
    result = agent.run("analyze timeout error")
