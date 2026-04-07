#!/usr/bin/env python3
"""
Conflict Resolver
=================
解決記憶衝突

策略：
- LATEST: 使用最新時間戳
- MAJORITY: 多數服從
- PRIORITY: 優先級
- MANUAL: 手動解決
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


class ResolutionStrategy(Enum):
    """解決策略"""
    LATEST = "latest"      # 最新優先
    MAJORITY = "majority"  # 多數服從
    PRIORITY = "priority"   # 優先級
    MANUAL = "manual"      # 手動解決


@dataclass
class ResolvedValue:
    """解決後的值"""
    value: Any
    strategy: ResolutionStrategy
    winning_agent_id: str
    timestamp: datetime


class ConflictResolver:
    """
    衝突解決器
    
    使用方式：
    
    ```python
    resolver = ConflictResolver()
    
    values = [
        {"agent_id": "agent-1", "value": "dark", "timestamp": ...},
        {"agent_id": "agent-2", "value": "light", "timestamp": ...},
    ]
    
    resolved = resolver.resolve(values, strategy=ResolutionStrategy.LATEST)
    print(resolved.value)  # "dark" or "light"
    ```
    """
    
    def __init__(self, agent_priorities: Dict[str, int] = None):
        """
        初始化
        
        Args:
            agent_priorities: Agent 優先級映射 {"agent_id": priority}
        """
        self.agent_priorities = agent_priorities or {}
    
    def resolve(
        self,
        values: List[Dict[str, Any]],
        strategy: ResolutionStrategy = ResolutionStrategy.LATEST
    ) -> Optional[ResolvedValue]:
        """
        解決衝突
        
        Args:
            values: 值列表 [{"agent_id": str, "value": any, "timestamp": datetime}]
            strategy: 解決策略
        
        Returns:
            ResolvedValue: 解決後的值
        """
        if not values:
            return None
        
        if len(values) == 1:
            return ResolvedValue(
                value=values[0]["value"],
                strategy=strategy,
                winning_agent_id=values[0]["agent_id"],
                timestamp=values[0].get("timestamp", datetime.now())
            )
        
        if strategy == ResolutionStrategy.LATEST:
            return self._resolve_latest(values)
        elif strategy == ResolutionStrategy.MAJORITY:
            return self._resolve_majority(values)
        elif strategy == ResolutionStrategy.PRIORITY:
            return self._resolve_priority(values)
        else:
            return None
    
    def _resolve_latest(self, values: List[Dict[str, Any]]) -> ResolvedValue:
        """使用最新時間戳"""
        latest = max(values, key=lambda v: v.get("timestamp", datetime.min))
        return ResolvedValue(
            value=latest["value"],
            strategy=ResolutionStrategy.LATEST,
            winning_agent_id=latest["agent_id"],
            timestamp=latest.get("timestamp", datetime.now())
        )
    
    def _resolve_majority(self, values: List[Dict[str, Any]]) -> ResolvedValue:
        """多數服從"""
        value_counts: Dict[Any, List[Dict]] = {}
        
        for v in values:
            val = v["value"]
            if val not in value_counts:
                value_counts[val] = []
            value_counts[val].append(v)
        
        # 找到最多數
        winner_value = max(value_counts.keys(), key=lambda k: len(value_counts[k]))
        winners = value_counts[winner_value]
        
        # 如果有平手，用最新時間打破
        if len(winners) > 1:
            latest = max(winners, key=lambda v: v.get("timestamp", datetime.min))
            winner_agent = latest["agent_id"]
        else:
            winner_agent = winners[0]["agent_id"]
        
        return ResolvedValue(
            value=winner_value,
            strategy=ResolutionStrategy.MAJORITY,
            winning_agent_id=winner_agent,
            timestamp=datetime.now()
        )
    
    def _resolve_priority(self, values: List[Dict[str, Any]]) -> ResolvedValue:
        """使用優先級"""
        if not self.agent_priorities:
            return self._resolve_latest(values)
        
        # 找到最高優先級
        def get_priority(v: Dict[str, Any]) -> int:
            agent_id = v["agent_id"]
            return self.agent_priorities.get(agent_id, 0)
        
        highest = max(values, key=get_priority)
        
        return ResolvedValue(
            value=highest["value"],
            strategy=ResolutionStrategy.PRIORITY,
            winning_agent_id=highest["agent_id"],
            timestamp=highest.get("timestamp", datetime.now())
        )