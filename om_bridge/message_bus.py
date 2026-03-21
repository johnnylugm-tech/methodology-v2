"""
Message Bus - 事件驅動匯流排
"""

import asyncio
from typing import Callable, Dict, List, Any
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, field
import logging

from .events import Event

logger = logging.getLogger(__name__)


@dataclass
class Subscription:
    """訂閱者"""
    callback: Callable
    filter_fn: Callable = None


class MessageBus:
    """事件匯流排 - Pub/Sub 模式"""
    
    def __init__(self, history_size: int = 1000):
        self._subscribers: Dict[str, List[Subscription]] = defaultdict(list)
        self._history: List[Event] = []
        self._history_size = history_size
        self._lock = asyncio.Lock()
    
    def subscribe(self, event_type: str, callback: Callable, filter_fn: Callable = None):
        """
        訂閱事件
        
        Args:
            event_type: 事件類型 (如 "om.task.completed")
            callback: 回調函數 (event: Event)
            filter_fn: 可選的過濾函數 (data: dict) -> bool
        """
        sub = Subscription(callback=callback, filter_fn=filter_fn)
        self._subscribers[event_type].append(sub)
        logger.debug(f"Subscribed to {event_type}: {callback.__name__}")
    
    def unsubscribe(self, event_type: str, callback: Callable):
        """取消訂閱"""
        self._subscribers[event_type] = [
            s for s in self._subscribers[event_type] 
            if s.callback != callback
        ]
    
    async def publish(self, event_type: str, data: dict, source: str = None):
        """
        發布事件
        
        Args:
            event_type: 事件類型
            data: 事件資料
            source: 事件來源 (如 "om", "v2")
        """
        event = Event(
            event_type=event_type,
            data=data,
            source=source,
            timestamp=datetime.now()
        )
        
        # 存入歷史
        async with self._lock:
            self._history.append(event)
            if len(self._history) > self._history_size:
                self._history = self._history[-self._history_size:]
        
        # 通知訂閱者
        subscribers = self._subscribers.get(event_type, [])
        if not subscribers:
            logger.debug(f"No subscribers for {event_type}")
            return
        
        tasks = []
        for sub in subscribers:
            # 執行過濾函數
            if sub.filter_fn and not sub.filter_fn(event.data):
                continue
            
            # 異步執行回調
            try:
                if asyncio.iscoroutinefunction(sub.callback):
                    tasks.append(asyncio.create_task(sub.callback(event)))
                else:
                    # 同步回調在執行緒池執行
                    loop = asyncio.get_event_loop()
                    tasks.append(loop.run_in_executor(None, sub.callback, event))
            except Exception as e:
                logger.error(f"Error in subscriber {sub.callback.__name__}: {e}")
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info(f"Published {event_type} to {len(subscribers)} subscribers")
    
    def get_history(self, event_type: str = None, limit: int = 100) -> List[Event]:
        """獲取事件歷史"""
        if event_type:
            return [e for e in self._history if e.event_type == event_type][-limit:]
        return self._history[-limit:]
    
    def get_stats(self) -> dict:
        """獲取匯流排統計"""
        return {
            "total_events": len(self._history),
            "event_types": {
                et: len(subs) 
                for et, subs in self._subscribers.items()
            },
            "subscriber_counts": {
                et: len(subs) 
                for et, subs in self._subscribers.items()
            }
        }


# 全域實例
_default_bus: MessageBus = None


def get_bus() -> MessageBus:
    """獲取預設匯流排實例"""
    global _default_bus
    if _default_bus is None:
        _default_bus = MessageBus()
    return _default_bus


def set_bus(bus: MessageBus):
    """設定預設匯流排實例"""
    global _default_bus
    _default_bus = bus


__all__ = ["MessageBus", "Subscription", "get_bus", "set_bus"]
