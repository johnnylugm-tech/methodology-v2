"""
AutoScaler for methodology-v2

Automatic agent scaling based on load, time, and cost.
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, time as dt_time
from enum import Enum
import threading


class ScalingAction(Enum):
    NONE = "none"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"


@dataclass
class AgentMetrics:
    """Current agent metrics"""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    queue_length: int = 0
    response_time: float = 0.0
    error_rate: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class TimeSchedule:
    """Time-based scaling schedule"""
    start_time: dt_time
    end_time: dt_time
    min_agents: int
    max_agents: int


class AutoScaler:
    """
    Automatic agent scaling for methodology-v2.
    
    Usage:
        scaler = AutoScaler(min_agents=2, max_agents=10)
        scaler.check_and_scale()
    """
    
    def __init__(
        self,
        min_agents: int = 1,
        max_agents: int = 10,
        scale_up_threshold: float = 0.8,
        scale_down_threshold: float = 0.2,
        cooldown_seconds: int = 300,
        budget: Optional[float] = None,
        cost_per_agent: Optional[float] = None
    ):
        self.min_agents = min_agents
        self.max_agents = max_agents
        self.scale_up_threshold = scale_up_threshold
        self.scale_down_threshold = scale_down_threshold
        self.cooldown_seconds = cooldown_seconds
        self.budget = budget
        self.cost_per_agent = cost_per_agent
        
        self.current_agents = min_agents
        self.last_scale_time = 0
        self.schedules: List[TimeSchedule] = []
        
        self.metrics = AgentMetrics()
        self.scaling_history: List[Dict] = []
    
    def update_metrics(self, metrics: AgentMetrics):
        """Update current metrics"""
        self.metrics = metrics
    
    def add_schedule(self, start: str, end: str, min_agents: int, max_agents: int):
        """Add time-based schedule"""
        start_time = dt_time(*map(int, start.split(":")))
        end_time = dt_time(*map(int, end.split(":")))
        
        self.schedules.append(TimeSchedule(
            start_time=start_time,
            end_time=end_time,
            min_agents=min_agents,
            max_agents=max_agents
        ))
    
    def get_desired_replicas(self) -> int:
        """Calculate desired agent count"""
        now = datetime.now().time()
        
        # Check time-based schedules first
        for schedule in self.schedules:
            if schedule.start_time <= now <= schedule.end_time:
                return self._calculate_scale(schedule.min_agents, schedule.max_agents)
        
        # Use load-based scaling
        return self._calculate_scale(self.min_agents, self.max_agents)
    
    def _calculate_scale(self, min_val: int, max_val: int) -> int:
        """Calculate scale based on metrics"""
        # Scale up triggers
        if (self.metrics.queue_length > 100 or 
            self.metrics.cpu_usage > self.scale_up_threshold or
            self.metrics.error_rate > 0.1):
            return min(self.current_agents + 1, max_val)
        
        # Scale down triggers (all metrics must be low)
        if (self.metrics.queue_length < 10 and 
            self.metrics.cpu_usage < self.scale_down_threshold and
            self.metrics.error_rate < 0.01):
            return max(self.current_agents - 1, min_val)
        
        return self.current_agents
    
    def check_and_scale(self) -> ScalingAction:
        """Check metrics and scale if needed"""
        # Check cooldown
        if time.time() - self.last_scale_time < self.cooldown_seconds:
            return ScalingAction.NONE
        
        desired = self.get_desired_replicas()
        
        if desired > self.current_agents:
            self.current_agents = desired
            self.last_scale_time = time.time()
            self._record_scaling(ScalingAction.SCALE_UP, desired)
            return ScalingAction.SCALE_UP
        
        elif desired < self.current_agents:
            self.current_agents = desired
            self.last_scale_time = time.time()
            self._record_scaling(ScalingAction.SCALE_DOWN, desired)
            return ScalingAction.SCALE_DOWN
        
        return ScalingAction.NONE
    
    def _record_scaling(self, action: ScalingAction, replicas: int):
        """Record scaling event"""
        self.scaling_history.append({
            "action": action.value,
            "replicas": replicas,
            "timestamp": time.time(),
            "metrics": {
                "cpu": self.metrics.cpu_usage,
                "queue": self.metrics.queue_length,
                "error_rate": self.metrics.error_rate
            }
        })
    
    def get_status(self) -> Dict:
        """Get current scaling status"""
        return {
            "current_agents": self.current_agents,
            "min_agents": self.min_agents,
            "max_agents": self.max_agents,
            "metrics": {
                "cpu_usage": self.metrics.cpu_usage,
                "memory_usage": self.metrics.memory_usage,
                "queue_length": self.metrics.queue_length,
                "response_time": self.metrics.response_time,
                "error_rate": self.metrics.error_rate
            },
            "last_scale": self.last_scale_time,
            "scaling_count": len(self.scaling_history)
        }
    
    def scale_to(self, replicas: int):
        """Manually scale to specified replicas"""
        self.current_agents = max(self.min_agents, min(replicas, self.max_agents))
        self.last_scale_time = time.time()
        self._record_scaling(ScalingAction.NONE, self.current_agents)


class K8sAutoscaler:
    """
    Kubernetes HPA integration for methodology-v2.
    
    Usage:
        k8s = K8sAutoscaler(deployment_name="agents")
        k8s.create_hpa(min_replicas=2, max_replicas=20)
    """
    
    def __init__(
        self,
        deployment_name: str = "methodology-agents",
        namespace: str = "default"
    ):
        self.deployment_name = deployment_name
        self.namespace = namespace
    
    def create_hpa(
        self,
        min_replicas: int = 2,
        max_replicas: int = 20,
        target_cpu_percent: int = 80
    ) -> Dict:
        """Create Kubernetes HPA"""
        hpa_config = {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {
                "name": self.deployment_name,
                "namespace": self.namespace
            },
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": self.deployment_name
                },
                "minReplicas": min_replicas,
                "maxReplicas": max_replicas,
                "metrics": [
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "cpu",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": target_cpu_percent
                            }
                        }
                    }
                ]
            }
        }
        
        return hpa_config
    
    def get_hpa_manifest(self) -> str:
        """Get HPA YAML manifest"""
        import yaml
        config = self.create_hpa()
        return yaml.dump(config)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AutoScaler CLI")
    parser.add_argument("command", choices=["start", "status", "scale"])
    parser.add_argument("--min", type=int, default=2)
    parser.add_argument("--max", type=int, default=10)
    parser.add_argument("--to", type=int, help="Scale to N agents")
    
    args = parser.parse_args()
    
    scaler = AutoScaler(min_agents=args.min, max_agents=args.max)
    
    if args.command == "start":
        print(f"Starting AutoScaler (min={args.min}, max={args.max})")
        while True:
            action = scaler.check_and_scale()
            if action != ScalingAction.NONE:
                print(f"Scaling: {action.value} -> {scaler.current_agents}")
            time.sleep(30)
    
    elif args.command == "status":
        status = scaler.get_status()
        print(f"Current Agents: {status['current_agents']}")
        print(f"Metrics: {status['metrics']}")
    
    elif args.command == "scale":
        if args.to:
            scaler.scale_to(args.to)
            print(f"Scaled to {args.to} agents")
