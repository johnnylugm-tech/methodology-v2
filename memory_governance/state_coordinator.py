#!/usr/bin/env python3
"""
State Coordinator
=================
協調多 Agent 的記憶狀態

功能：
- 維護全局記憶狀態
- 檢測記憶衝突
- 提供狀態同步
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import datetime
from enum import Enum
import threading


class ConflictType(Enum):
    """衝突類型"""
    CONTENT_MISMATCH = "content_mismatch"
    TIMESTAMP_CONFLICT = "timestamp_conflict"
    VERSION_CONFLICT = "version_conflict"
    DELETED_CONFLICT = "deleted_conflict"


@dataclass
class MemoryConflict:
    """記憶衝突"""
    conflict_id: str
    conflict_type: ConflictType
    agent_ids: List[str]
    memory_keys: List[str]
    detected_at: datetime
    description: str
    resolved: bool = False
    resolution: str = ""


class StateCoordinator:
    """
    狀態協調器
    
    使用方式：
    
    ```python
    coordinator = StateCoordinator()
    
    # 註冊 Agent 記憶
    coordinator.register("agent-1", {"preference": "dark"})
    coordinator.register("agent-2", {"preference": "light"})
    
    # 檢測衝突
    conflicts = coordinator.detect_conflicts()
    
    # 解決衝突
    for conflict in conflicts:
        coordinator.resolve(conflict.conflict_id, "agent-1")
    ```
    """
    
    def __init__(self):
        self.agent_states: Dict[str, Dict[str, any]] = {}
        self.global_state: Dict[str, any] = {}
        self.conflicts: List[MemoryConflict] = []
        self.lock = threading.Lock()
        self._conflict_counter = 0
    
    def register(self, agent_id: str, state: Dict[str, any]):
        """註冊 Agent 狀態"""
        with self.lock:
            self.agent_states[agent_id] = {
                "state": state,
                "registered_at": datetime.now(),
                "version": 1
            }
            self._update_global_state(agent_id, state)
    
    def _update_global_state(self, agent_id: str, state: Dict[str, any]):
        """更新全局狀態"""
        for key, value in state.items():
            full_key = f"{agent_id}:{key}"
            if full_key not in self.global_state:
                self.global_state[full_key] = []
            self.global_state[full_key].append({
                "value": value,
                "agent_id": agent_id,
                "timestamp": datetime.now()
            })
    
    def detect_conflicts(self) -> List[MemoryConflict]:
        """檢測衝突"""
        conflicts = []
        
        # 檢查同一鍵的不同值
        for key, values in self.global_state.items():
            if len(values) > 1:
                # 多個 Agent 對同一鍵有不同的值
                unique_values = set(v["value"] for v in values)
                if len(unique_values) > 1:
                    agent_ids = [v["agent_id"] for v in values]
                    conflict = MemoryConflict(
                        conflict_id=f"conflict-{self._conflict_counter}",
                        conflict_type=ConflictType.CONTENT_MISMATCH,
                        agent_ids=list(set(agent_ids)),
                        memory_keys=[key],
                        detected_at=datetime.now(),
                        description=f"Agents {agent_ids} have different values for {key}"
                    )
                    conflicts.append(conflict)
                    self._conflict_counter += 1
        
        self.conflicts.extend(conflicts)
        return conflicts
    
    def resolve(self, conflict_id: str, winner_agent_id: str):
        """解決衝突"""
        for conflict in self.conflicts:
            if conflict.conflict_id == conflict_id:
                conflict.resolved = True
                conflict.resolution = f"Winner: {winner_agent_id}"
                break
    
    def get_active_conflicts(self) -> List[MemoryConflict]:
        """取得未解決的衝突"""
        return [c for c in self.conflicts if not c.resolved]
    
    def get_state(self, agent_id: str) -> Optional[Dict[str, any]]:
        """取得 Agent 狀態"""
        return self.agent_states.get(agent_id, {}).get("state")
    
    def get_global_state_summary(self) -> Dict:
        """取得全局狀態摘要"""
        return {
            "total_agents": len(self.agent_states),
            "total_keys": len(self.global_state),
            "active_conflicts": len(self.get_active_conflicts()),
            "agents": list(self.agent_states.keys())
        }