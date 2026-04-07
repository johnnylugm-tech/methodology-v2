"""
OmO + Methodology-v2 Bridge (Mode C)

事件驅動的 decoupled 整合方案

Bridge 同時支持：
- Mode A: OmO → Methodology-v2 (品質把關)
- Mode B: Methodology-v2 → OmO (多模型執行)
"""

import asyncio
import logging
from typing import Optional
import sys
import os

# 確保可以導入同目錄模組
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from .events import Event, OMEvents, V2Events
from .message_bus import MessageBus, get_bus, set_bus
from .om_adapter import OmOAdapter, OmOConfig
from .v2_adapter import V2Adapter, V2Config

logger = logging.getLogger(__name__)


class EventBridge:
    """
    OmO ↔ Methodology-v2 事件橋接器
    
    Mode C 的核心實現，支持：
    - Mode A: OmO 任務完成 → v2 品質把關
    - Mode B: v2 任務規劃 → OmO 多模型執行
    """
    
    def __init__(
        self,
        bus: MessageBus = None,
        om_config: OmOConfig = None,
        v2_config: V2Config = None,
        enable_mode_a: bool = True,
        enable_mode_b: bool = True
    ):
        """
        初始化橋接器
        
        Args:
            bus: 事件匯流排 (可選，預設使用全域實例)
            om_config: OmO 配置
            v2_config: Methodology-v2 配置
            enable_mode_a: 是否啟用 Mode A (OmO → v2)
            enable_mode_b: 是否啟用 Mode B (v2 → OmO)
        """
        self.bus = bus or get_bus()
        set_bus(self.bus)  # 設定為預設匯流排
        
        self.om = OmOAdapter(om_config, self.bus)
        self.v2 = V2Adapter(v2_config, self.bus)
        
        self.enable_mode_a = enable_mode_a
        self.enable_mode_b = enable_mode_b
        
        self._running = False
    
    async def start(self):
        """啟動橋接器"""
        if self._running:
            logger.warning("Bridge already running")
            return
        
        self._running = True
        
        # 訂閱事件
        self._subscribe_events()
        
        logger.info("OmO-Methodology-v2 Bridge started (Mode C)")
        logger.info(f"  Mode A (OmO → v2): {'enabled' if self.enable_mode_a else 'disabled'}")
        logger.info(f"  Mode B (v2 → OmO): {'enabled' if self.enable_mode_b else 'disabled'}")
        
        # 保持運行
        try:
            while self._running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
    
    def _subscribe_events(self):
        """訂閱感興趣的事件"""
        # === Mode A: OmO → Methodology-v2 ===
        if self.enable_mode_a:
            # 監聽 OmO 任務完成 → 觸發 v2 品質檢查
            self.bus.subscribe(
                OMEvents.TASK_COMPLETED.value,
                self._on_om_task_completed
            )
            
            # 監聽 OmO 任務失敗 → 觸發 v2 錯誤分類
            self.bus.subscribe(
                OMEvents.TASK_FAILED.value,
                self._on_om_task_failed
            )
        
        # === Mode B: Methodology-v2 → OmO ===
        if self.enable_mode_b:
            # 監聽 v2 任務規劃 → 觸發 OmO 執行
            self.bus.subscribe(
                V2Events.TASK_PLANNED.value,
                self._on_v2_task_planned
            )
    
    # === Mode A Handlers ===
    
    async def _on_om_task_completed(self, event: Event):
        """OmO 任務完成 → v2 品質檢查"""
        logger.info(f"[Mode A] OmO task completed: {event.data.get('task_id')}")
        
        # 提取任務資料
        task_id = event.data.get("task_id", "unknown")
        code = event.data.get("code", "")
        language = event.data.get("language", "python")
        
        # 執行 v2 品質檢查
        result = await self.v2.quality_check(task_id, code, language)
        
        if result["passed"]:
            logger.info(f"[Mode A] Quality check PASSED: score={result['score']:.2f}")
        else:
            logger.warning(f"[Mode A] Quality check FAILED: {len(result['issues'])} issues")
    
    async def _on_om_task_failed(self, event: Event):
        """OmO 任務失敗 → v2 錯誤分類"""
        logger.warning(f"[Mode A] OmO task failed: {event.data.get('error')}")
        
        # 創建錯誤對象
        error_msg = event.data.get("error", "Unknown error")
        error = Exception(error_msg)
        
        # 執行 v2 錯誤分類
        result = await self.v2.classify_error(error)
        
        logger.info(f"[Mode A] Error classified as {result['level']}: {result['action']}")
    
    # === Mode B Handlers ===
    
    async def _on_v2_task_planned(self, event: Event):
        """v2 任務規劃 → OmO 多模型執行"""
        logger.info(f"[Mode B] v2 task planned: {event.data.get('task_id')}")
        
        # 提取任務資料
        task_id = event.data.get("task_id", "unknown")
        instructions = event.data.get("instructions", "")
        preferred_model = event.data.get("preferred_model", "claude-3-opus")
        
        # 使用 OmO 執行任務
        result = await self.om.execute_task(instructions, preferred_model)
        
        if result["success"]:
            logger.info(f"[Mode B] OmO execution SUCCESS: {result.get('output', '')[:50]}...")
        else:
            logger.error(f"[Mode B] OmO execution FAILED: {result.get('error')}")
    
    async def stop(self):
        """停止橋接器"""
        self._running = False
        logger.info("OmO-Methodology-v2 Bridge stopped")
    
    def get_status(self) -> dict:
        """獲取橋接器狀態"""
        return {
            "running": self._running,
            "mode_a_enabled": self.enable_mode_a,
            "mode_b_enabled": self.enable_mode_b,
            "om_status": self.om.get_status(),
            "v2_status": self.v2.get_status(),
            "bus_stats": self.bus.get_stats()
        }


async def run_bridge():
    """運行橋接器"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    
    bridge = EventBridge()
    
    try:
        await bridge.start()
    except KeyboardInterrupt:
        await bridge.stop()


def main():
    """CLI 入口"""
    asyncio.run(run_bridge())


if __name__ == "__main__":
    main()


__all__ = ["EventBridge", "OmOConfig", "V2Config", "get_bus", "set_bus"]
