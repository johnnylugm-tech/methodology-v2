"""
OmO + Methodology-v2 Bridge (Mode C)

事件驅動的 decoupled 整合方案

支援：
- Mode A: OmO → Methodology-v2 (品質把關)
- Mode B: Methodology-v2 → OmO (多模型執行)

使用方式：

    from om_bridge import EventBridge
    
    bridge = EventBridge()
    await bridge.start()

"""

from .events import (
    OMEvents,
    V2Events,
    Event,
    OMTaskData,
    OMTaskCompletedData,
    V2TaskPlannedData,
    V2QualityCheckData,
    V2ErrorClassifiedData,
    ALL_EVENTS
)

from .message_bus import MessageBus, Subscription, get_bus, set_bus

from .om_adapter import OmOAdapter, OmOConfig

from .v2_adapter import V2Adapter, V2Config

from .bridge import EventBridge

__version__ = "1.0.0"

__all__ = [
    # Events
    "OMEvents",
    "V2Events", 
    "Event",
    "OMTaskData",
    "OMTaskCompletedData",
    "V2TaskPlannedData",
    "V2QualityCheckData",
    "V2ErrorClassifiedData",
    "ALL_EVENTS",
    # Message Bus
    "MessageBus",
    "Subscription",
    "get_bus",
    "set_bus",
    # Adapters
    "OmOAdapter",
    "OmOConfig",
    "V2Adapter",
    "V2Config",
    # Bridge
    "EventBridge",
    # Version
    "__version__"
]
