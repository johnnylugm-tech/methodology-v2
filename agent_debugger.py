#!/usr/bin/env python3
"""
Agent Debugger - Agent 追蹤和除錯系統

提供 Agent 可觀測性增強：
1. 記錄每次 LLM 呼叫
2. 追蹤狀態變化
3. 時間軸視覺化
"""

import json
import uuid
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import threading
import time


class EventType(Enum):
    """事件類型"""
    LLM_CALL = "llm_call"
    LLM_RESPONSE = "llm_response"
    STATE_CHANGE = "state_change"
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    TOOL_CALL = "tool_call"
    TOOL_RESPONSE = "tool_response"
    ERROR = "error"
    SPAWN = "spawn"
    TERMINATE = "terminate"
    HEARTBEAT = "heartbeat"


@dataclass
class TraceEvent:
    """追蹤事件"""
    id: str
    agent_id: str
    event_type: EventType
    timestamp: datetime
    
    # 事件資料
    data: Dict = field(default_factory=dict)
    
    # 關聯
    parent_event_id: str = None
    correlation_id: str = None
    
    # 效能
    duration_ms: float = None
    
    # 額外上下文
    tags: List[str] = field(default_factory=list)
    
    @classmethod
    def create(cls, agent_id: str, event_type: EventType, data: Dict = None,
               parent_event_id: str = None, correlation_id: str = None,
               duration_ms: float = None, tags: List[str] = None) -> 'TraceEvent':
        return cls(
            id=str(uuid.uuid4())[:12],
            agent_id=agent_id,
            event_type=event_type,
            timestamp=datetime.now(),
            data=data or {},
            parent_event_id=parent_event_id,
            correlation_id=correlation_id,
            duration_ms=duration_ms,
            tags=tags or [],
        )
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "parent_event_id": self.parent_event_id,
            "correlation_id": self.correlation_id,
            "duration_ms": self.duration_ms,
            "tags": self.tags,
        }


@dataclass
class LLMCallEvent(TraceEvent):
    """LLM 呼叫事件"""
    def __init__(self, agent_id: str, prompt: str, model: str = None,
                 temperature: float = None, max_tokens: int = None,
                 parent_event_id: str = None, correlation_id: str = None, **kwargs):
        super().__init__(
            id=str(uuid.uuid4())[:12],
            agent_id=agent_id,
            event_type=EventType.LLM_CALL,
            timestamp=datetime.now(),
            data={
                "prompt": prompt[:500] if prompt else "",  # 截斷過長的 prompt
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            parent_event_id=parent_event_id,
            correlation_id=correlation_id,
        )


class AgentDebugger:
    """Agent 可觀測性增強"""
    
    def __init__(self, max_events: int = 10000):
        # Agent ID -> 事件列表
        self.traces: Dict[str, List[TraceEvent]] = defaultdict(list)
        
        # 全域事件索引 (correlation_id -> events)
        self.correlation_index: Dict[str, List[str]] = defaultdict(list)
        
        # 事件計數器
        self.event_count = 0
        
        # 設定
        self.max_events = max_events
        
        # 鎖
        self.lock = threading.RLock()
        
        # 是否啟用
        self.enabled = True
        
        # 訂閱者回呼
        self._subscribers: List[Callable[[TraceEvent], None]] = []
        
        # 統計
        self.stats = {
            "total_events": 0,
            "llm_calls": 0,
            "errors": 0,
            "active_agents": set(),
        }
    
    def trace(self, agent_id: str, event_type: EventType, data: Dict = None,
             parent_event_id: str = None, correlation_id: str = None,
             duration_ms: float = None, tags: List[str] = None) -> str:
        """
        記錄一個追蹤事件
        
        Args:
            agent_id: Agent 標識
            event_type: 事件類型
            data: 事件資料
            parent_event_id: 父事件 ID (用於建立時間軸關聯)
            correlation_id: 關聯 ID (用於跨 Agent 追蹤)
            duration_ms: 持續時間 (毫秒)
            tags: 標籤列表
        
        Returns:
            事件 ID
        """
        if not self.enabled:
            return None
        
        with self.lock:
            event = TraceEvent.create(
                agent_id=agent_id,
                event_type=event_type,
                data=data,
                parent_event_id=parent_event_id,
                correlation_id=correlation_id,
                duration_ms=duration_ms,
                tags=tags,
            )
            
            # 添加到 traces
            self.traces[agent_id].append(event)
            
            # 如果事件過多，刪除最舊的
            if len(self.traces[agent_id]) > self.max_events:
                self.traces[agent_id] = self.traces[agent_id][-self.max_events:]
            
            # 索引 correlation_id
            if correlation_id:
                self.correlation_index[correlation_id].append(event.id)
            
            # 更新統計
            self.event_count += 1
            self.stats["total_events"] += 1
            self.stats["active_agents"].add(agent_id)
            
            if event_type == EventType.LLM_CALL:
                self.stats["llm_calls"] += 1
            elif event_type == EventType.ERROR:
                self.stats["errors"] += 1
            
            # 通知訂閱者
            for callback in self._subscribers:
                try:
                    callback(event)
                except Exception:
                    pass
            
            return event.id
    
    def trace_llm_call(self, agent_id: str, prompt: str, model: str = None,
                       parent_event_id: str = None, correlation_id: str = None,
                       **llm_kwargs) -> str:
        """專門記錄 LLM 呼叫"""
        event = LLMCallEvent(
            agent_id=agent_id,
            prompt=prompt,
            model=model,
            parent_event_id=parent_event_id,
            correlation_id=correlation_id,
            **llm_kwargs
        )
        
        with self.lock:
            self.traces[agent_id].append(event)
            if correlation_id:
                self.correlation_index[correlation_id].append(event.id)
            self.event_count += 1
            self.stats["total_events"] += 1
            self.stats["llm_calls"] += 1
            self.stats["active_agents"].add(agent_id)
            
            for callback in self._subscribers:
                try:
                    callback(event)
                except Exception:
                    pass
            
            return event.id
    
    def trace_llm_response(self, agent_id: str, response: str,
                          parent_event_id: str = None, correlation_id: str = None,
                          duration_ms: float = None):
        """記錄 LLM 回應"""
        return self.trace(
            agent_id=agent_id,
            event_type=EventType.LLM_RESPONSE,
            data={"response": response[:500] if response else ""},
            parent_event_id=parent_event_id,
            correlation_id=correlation_id,
            duration_ms=duration_ms,
        )
    
    def trace_state_change(self, agent_id: str, from_state: str, to_state: str,
                          reason: str = None):
        """記錄狀態變化"""
        return self.trace(
            agent_id=agent_id,
            event_type=EventType.STATE_CHANGE,
            data={
                "from_state": from_state,
                "to_state": to_state,
                "reason": reason,
            },
            tags=[f"state:{to_state}"]
        )
    
    def trace_message(self, agent_id: str, direction: str, topic: str,
                     payload: Any, correlation_id: str = None):
        """記錄訊息"""
        event_type = EventType.MESSAGE_SENT if direction == "out" else EventType.MESSAGE_RECEIVED
        return self.trace(
            agent_id=agent_id,
            event_type=event_type,
            data={
                "direction": direction,
                "topic": topic,
                "payload": str(payload)[:200],
            },
            correlation_id=correlation_id,
        )
    
    def trace_error(self, agent_id: str, error: str, context: Dict = None):
        """記錄錯誤"""
        return self.trace(
            agent_id=agent_id,
            event_type=EventType.ERROR,
            data={
                "error": error,
                "context": context or {},
            },
            tags=["error"]
        )
    
    def get_trace(self, agent_id: str, time_range: tuple = None,
                  event_types: List[EventType] = None,
                  limit: int = 100) -> List[Dict]:
        """
        取得 trace 歷史
        
        Args:
            agent_id: Agent 標識
            time_range: 時間範圍 (start, end) datetime tuples
            event_types: 過濾的事件類型列表
            limit: 返回上限
        
        Returns:
            事件列表
        """
        with self.lock:
            events = self.traces.get(agent_id, [])
            
            # 時間過濾
            if time_range:
                start, end = time_range
                events = [e for e in events if start <= e.timestamp <= end]
            
            # 類型過濾
            if event_types:
                type_values = [et.value for et in event_types]
                events = [e for e in events if e.event_type.value in type_values]
            
            # 限制
            events = events[-limit:]
            
            return [e.to_dict() for e in events]
    
    def get_timeline(self, agent_id: str, time_range: tuple = None) -> List[Dict]:
        """
        取得時間軸格式的事件 (包含父子關係)
        
        Returns:
            時間軸列表
        """
        events = self.get_trace(agent_id, time_range)
        
        # 建立樹狀結構
        event_map = {e["id"]: {**e, "children": []} for e in events}
        root_events = []
        
        for event in events:
            if event["parent_event_id"] and event["parent_event_id"] in event_map:
                event_map[event["parent_event_id"]]["children"].append(event_map[event["id"]])
            else:
                root_events.append(event_map[event["id"]])
        
        return root_events
    
    def visualize(self, agent_id: str, time_range: tuple = None,
                  max_events: int = 50) -> str:
        """
        視覺化 trace (文字模式)
        
        Args:
            agent_id: Agent 標識
            time_range: 時間範圍
            max_events: 最大顯示事件數
        
        Returns:
            ASCII 格式的視覺化輸出
        """
        events = self.get_trace(agent_id, time_range, limit=max_events)
        
        if not events:
            return f"No trace events found for agent: {agent_id}"
        
        lines = []
        lines.append("╔" + "═" * 70 + "╗")
        lines.append("║" + f" AGENT TRACE: {agent_id} ".center(70) + "║")
        lines.append("╚" + "═" * 70 + "╝")
        
        # 統計
        llm_calls = sum(1 for e in events if e["event_type"] == "llm_call")
        errors = sum(1 for e in events if e["event_type"] == "error")
        total_duration = sum(e.get("duration_ms", 0) or 0 for e in events)
        
        lines.append("")
        lines.append(f"  📊 Statistics:")
        lines.append(f"     Total Events: {len(events)}")
        lines.append(f"     LLM Calls: {llm_calls}")
        lines.append(f"     Errors: {errors}")
        lines.append(f"     Total Duration: {total_duration:.2f}ms")
        lines.append("")
        
        # 時間軸
        lines.append("  📅 Timeline:")
        lines.append("  " + "─" * 66)
        
        for i, event in enumerate(events):
            ts = event["timestamp"]
            event_type = event["event_type"]
            eid = event["id"]
            
            # 事件圖標
            icon_map = {
                "llm_call": "🤖",
                "llm_response": "💬",
                "state_change": "🔄",
                "message_sent": "📤",
                "message_received": "📥",
                "tool_call": "🔧",
                "tool_response": "✅",
                "error": "❌",
                "spawn": "🆕",
                "terminate": "🔚",
                "heartbeat": "💓",
            }
            icon = icon_map.get(event_type, "•")
            
            # 時間
            time_str = ts.split("T")[1][:12] if "T" in ts else ts
            
            # 持續時間
            duration_str = ""
            if event.get("duration_ms"):
                duration_str = f" ({event['duration_ms']:.1f}ms)"
            
            # 顯示資料摘要
            data_preview = ""
            data = event.get("data", {})
            if "prompt" in data:
                data_preview = f" - {data['prompt'][:30]}..."
            elif "to_state" in data:
                data_preview = f" - {data['from_state']} → {data['to_state']}"
            elif "error" in data:
                data_preview = f" - {data['error'][:40]}"
            elif "topic" in data:
                data_preview = f" - {data['topic']}"
            
            lines.append(f"  {icon} [{time_str}] {event_type}{duration_str}{data_preview}")
            
            # 錯誤高亮
            if event_type == "error":
                lines.append(f"     └─ ❌ {event.get('data', {}).get('error', 'Unknown error')}")
        
        lines.append("")
        
        return "\n".join(lines)
    
    def visualize_correlation(self, correlation_id: str) -> str:
        """
        視覺化跨 Agent 追蹤 (同一 correlation_id 的事件)
        
        Returns:
            ASCII 格式輸出
        """
        with self.lock:
            event_ids = self.correlation_index.get(correlation_id, [])
            
            # 收集所有相關事件
            all_events = []
            for eid in event_ids:
                for agent_id, events in self.traces.items():
                    for event in events:
                        if event.id == eid:
                            all_events.append(event)
                            break
            
            if not all_events:
                return f"No events found for correlation_id: {correlation_id}"
            
            # 按時間排序
            all_events.sort(key=lambda e: e.timestamp)
            
            lines = []
            lines.append("╔" + "═" * 70 + "╗")
            lines.append("║" + f" CORRELATION TRACE: {correlation_id[:12]} ".center(70) + "║")
            lines.append("╚" + "═" * 70 + "╝")
            lines.append("")
            
            for event in all_events:
                icon_map = {
                    "llm_call": "🤖",
                    "llm_response": "💬",
                    "state_change": "🔄",
                    "message_sent": "📤",
                    "message_received": "📥",
                    "tool_call": "🔧",
                    "tool_response": "✅",
                    "error": "❌",
                    "spawn": "🆕",
                    "terminate": "🔚",
                    "heartbeat": "💓",
                }
                icon = icon_map.get(event.event_type.value, "•")
                ts = event.timestamp.strftime("%H:%M:%S.%f")[:-3]
                
                lines.append(f"  {icon} [{ts}] {event.agent_id}: {event.event_type.value}")
                if event.parent_event_id:
                    lines.append(f"       └─ parent: {event.parent_event_id}")
            
            lines.append("")
            
            return "\n".join(lines)
    
    def get_stats(self, agent_id: str = None) -> Dict:
        """取得統計資訊"""
        with self.lock:
            if agent_id:
                events = self.traces.get(agent_id, [])
                return {
                    "agent_id": agent_id,
                    "total_events": len(events),
                    "llm_calls": sum(1 for e in events if e.event_type == EventType.LLM_CALL),
                    "errors": sum(1 for e in events if e.event_type == EventType.ERROR),
                    "first_event": events[0].timestamp.isoformat() if events else None,
                    "last_event": events[-1].timestamp.isoformat() if events else None,
                }
            else:
                return {
                    "total_events": self.event_count,
                    "llm_calls": self.stats["llm_calls"],
                    "errors": self.stats["errors"],
                    "active_agents": len(self.stats["active_agents"]),
                    "agents": list(self.stats["active_agents"]),
                }
    
    def enable_debug(self):
        """啟用除錯追蹤"""
        self.enabled = True
    
    def disable_debug(self):
        """停用除錯追蹤"""
        self.enabled = False
    
    def subscribe(self, callback: Callable[[TraceEvent], None]):
        """訂閱追蹤事件"""
        self._subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable[[TraceEvent], None]):
        """取消訂閱"""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
    
    def clear(self, agent_id: str = None):
        """清除追蹤資料"""
        with self.lock:
            if agent_id:
                self.traces.pop(agent_id, None)
            else:
                self.traces.clear()
                self.correlation_index.clear()
                self.event_count = 0
                self.stats = {
                    "total_events": 0,
                    "llm_calls": 0,
                    "errors": 0,
                    "active_agents": set(),
                }
    
    def export(self, agent_id: str = None, time_range: tuple = None) -> str:
        """導出追蹤資料為 JSON"""
        if agent_id:
            events = self.get_trace(agent_id, time_range)
        else:
            with self.lock:
                events = [e.to_dict() for events in self.traces.values() for e in events]
        
        return json.dumps({
            "exported_at": datetime.now().isoformat(),
            "agent_id": agent_id,
            "events": events,
        }, indent=2, default=str)
    
    def to_table(self) -> str:
        """表格格式輸出"""
        with self.lock:
            stats = self.get_stats()
            
            lines = []
            lines.append("╔" + "═" * 50 + "╗")
            lines.append("║" + " AGENT DEBUGGER STATUS ".center(50) + "║")
            lines.append("╚" + "═" * 50 + "╝")
            lines.append("")
            lines.append(f"  Enabled:       {'Yes' if self.enabled else 'No'}")
            lines.append(f"  Total Events: {stats['total_events']}")
            lines.append(f"  LLM Calls:    {stats['llm_calls']}")
            lines.append(f"  Errors:       {stats['errors']}")
            lines.append(f"  Active Agents:{stats['active_agents']}")
            lines.append("")
            lines.append("  Agents:")
            
            for agent_id in sorted(stats.get("agents", [])):
                agent_stats = self.get_stats(agent_id)
                lines.append(f"    - {agent_id}: {agent_stats['total_events']} events")
            
            lines.append("")
            
            return "\n".join(lines)


# ============================================================================
# Global debugger instance (for easy import)
# ============================================================================

_global_debugger: Optional[AgentDebugger] = None


def get_debugger() -> AgentDebugger:
    """取得全域除錯器實例"""
    global _global_debugger
    if _global_debugger is None:
        _global_debugger = AgentDebugger()
    return _global_debugger


def trace(agent_id: str, event_type: EventType, **kwargs) -> str:
    """全域 trace 捷徑"""
    return get_debugger().trace(agent_id, event_type, **kwargs)


# ============================================================================
# Main (standalone test)
# ============================================================================

if __name__ == "__main__":
    # 測試
    dbg = AgentDebugger()
    
    # 模擬追蹤
    dbg.trace("agent-001", EventType.SPAWN, {"config": "default"})
    
    call_id = dbg.trace_llm_call("agent-001", "Hello, how are you?", model="gpt-4")
    
    dbg.trace_llm_response(
        "agent-001",
        "I'm doing great! How can I help you today?",
        parent_event_id=call_id,
        duration_ms=150.5
    )
    
    dbg.trace_state_change("agent-001", "idle", "thinking", "User message received")
    dbg.trace_message("agent-001", "out", "command.worker", "process_task")
    
    dbg.trace_error("agent-001", "Connection timeout", {"retry": 3})
    
    # 可視化
    print(dbg.visualize("agent-001"))
    
    # 統計
    print(dbg.get_stats("agent-001"))
    
    # 清除
    dbg.clear("agent-001")
    print("\n✅ Agent Debugger test passed!")
