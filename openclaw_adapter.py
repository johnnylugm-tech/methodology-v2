#!/usr/bin/env python3
"""
OpenClaw Adapter - OpenClaw 整合適配器

讓 methodology-v2 可以與 OpenClaw 無縫整合
"""

import os
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


class AgentType(Enum):
    """Agent 類型"""
    MUSK = "musk"
    RESEARCHER = "researcher"
    DEVELOPER = "developer"
    ANALYZER = "analyzer"
    CUSTOM = "custom"


@dataclass
class OpenClawConfig:
    """OpenClaw 配置"""
    agent_id: str = "musk"
    model: str = "minimax/MiniMax-M2.5"
    temperature: float = 0.7
    max_tokens: int = 4000
    thinking: str = "auto"


class OpenClawAdapter:
    """OpenClaw 適配器"""
    
    def __init__(self, config: OpenClawConfig = None):
        """
        初始化
        
        Args:
            config: OpenClaw 配置
        """
        self.config = config or OpenClawConfig()
        self.session_id = None
        self.conversation_history: List[Dict] = []
    
    def spawn_agent(self, task: str, agent_type: AgentType = None, 
                   **kwargs) -> Dict:
        """
        建立子 Agent
        
        Args:
            task: 任務描述
            agent_type: Agent 類型
            **kwargs: 其他參數
            
        Returns:
            Agent 結果
        """
        # 模擬 OpenClaw sessions_spawn
        agent_id = kwargs.get("agent_id", agent_type.value if agent_type else "musk")
        
        result = {
            "session_id": self.session_id or "new-session",
            "agent_id": agent_id,
            "task": task,
            "status": "spawned",
            "timestamp": "2026-03-20T02:20:00"
        }
        
        print(f"[OpenClawAdapter] Spawned {agent_id} for task: {task[:50]}...")
        
        return result
    
    def send_message(self, message: str, **kwargs) -> str:
        """
        發送訊息
        
        Args:
            message: 訊息內容
            **kwargs: 其他參數
            
        Returns:
            回覆內容
        """
        # 記錄對話歷史
        self.conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": kwargs.get("timestamp")
        })
        
        # 模擬回覆
        response = self._generate_response(message)
        
        self.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": kwargs.get("timestamp")
        })
        
        return response
    
    def _generate_response(self, message: str) -> str:
        """生成回覆（實際應該調用 OpenClaw API）"""
        # 這裡應該調用 OpenClaw 的 API
        # 暫時返回模擬回覆
        return f"[OpenClaw] 已收到訊息: {message[:50]}..."
    
    def get_history(self) -> List[Dict]:
        """
        獲取對話歷史
        
        Returns:
            對話歷史
        """
        return self.conversation_history
    
    def clear_history(self):
        """清除對話歷史"""
        self.conversation_history = []
    
    def get_status(self) -> Dict:
        """
        獲取狀態
        
        Returns:
            狀態資訊
        """
        return {
            "agent_id": self.config.agent_id,
            "model": self.config.model,
            "session_id": self.session_id,
            "message_count": len(self.conversation_history)
        }


class AgentWrapper:
    """Agent 包裝器"""
    
    def __init__(self, adapter: OpenClawAdapter, agent_type: AgentType):
        """
        初始化
        
        Args:
            adapter: OpenClawAdapter
            agent_type: Agent 類型
        """
        self.adapter = adapter
        self.agent_type = agent_type
    
    def execute(self, task: str, **kwargs) -> Dict:
        """執行任務"""
        return self.adapter.spawn_agent(task, self.agent_type, **kwargs)
    
    def chat(self, message: str) -> str:
        """聊天"""
        return self.adapter.send_message(message)


class MultiAgentOrchestrator:
    """多 Agent 協調器"""
    
    def __init__(self):
        """初始化"""
        self.adapter = OpenClawAdapter()
        self.agents: Dict[str, AgentWrapper] = {}
    
    def register_agent(self, name: str, agent_type: AgentType) -> AgentWrapper:
        """
        註冊 Agent
        
        Args:
            name: Agent 名稱
            agent_type: Agent 類型
            
        Returns:
            AgentWrapper
        """
        wrapper = AgentWrapper(self.adapter, agent_type)
        self.agents[name] = wrapper
        print(f"[Orchestrator] Registered agent: {name} ({agent_type.value})")
        return wrapper
    
    def execute_parallel(self, tasks: Dict[str, str]) -> Dict[str, Any]:
        """
        並行執行任務
        
        Args:
            tasks: 任務字典 {agent_name: task}
            
        Returns:
            結果字典
        """
        results = {}
        
        for agent_name, task in tasks.items():
            if agent_name in self.agents:
                results[agent_name] = self.agents[agent_name].execute(task)
            else:
                results[agent_name] = {"error": f"Agent {agent_name} not found"}
        
        return results
    
    def execute_sequential(self, tasks: List[tuple]) -> List[Dict]:
        """
        串聯執行任務
        
        Args:
            tasks: 任務列表 [(agent_name, task), ...]
            
        Returns:
            結果列表
        """
        results = []
        
        for agent_name, task in tasks:
            if agent_name in self.agents:
                result = self.agents[agent_name].execute(task)
                results.append(result)
            else:
                results.append({"error": f"Agent {agent_name} not found"})
        
        return results


# ============================================================================
# 便捷函數
# ============================================================================

def create_musk_agent() -> AgentWrapper:
    """建立 Musk Agent"""
    adapter = OpenClawAdapter(OpenClawConfig(agent_id="musk"))
    return AgentWrapper(adapter, AgentType.MUSK)


def create_researcher_agent() -> AgentWrapper:
    """建立 Researcher Agent"""
    adapter = OpenClawAdapter(OpenClawConfig(agent_id="researcher"))
    return AgentWrapper(adapter, AgentType.RESEARCHER)


def create_developer_agent() -> AgentWrapper:
    """建立 Developer Agent"""
    adapter = OpenClawAdapter(OpenClawConfig(agent_id="developer"))
    return AgentWrapper(adapter, AgentType.DEVELOPER)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("=== OpenClaw Adapter Demo ===\n")
    
    # 建立協調器
    orchestrator = MultiAgentOrchestrator()
    
    # 註冊 Agents
    orchestrator.register_agent("musk", AgentType.MUSK)
    orchestrator.register_agent("researcher", AgentType.RESEARCHER)
    orchestrator.register_agent("developer", AgentType.DEVELOPER)
    
    # 並行執行
    print("\n=== Parallel Execution ===")
    results = orchestrator.execute_parallel({
        "researcher": "研究最新的 AI 趨勢",
        "developer": "開發一個 Python 函數",
        "musk": "總結團隊進展"
    })
    
    for name, result in results.items():
        print(f"{name}: {result['status']}")
    
    # 串聯執行
    print("\n=== Sequential Execution ===")
    seq_results = orchestrator.execute_sequential([
        ("researcher", "研究 AI Agents"),
        ("developer", "根據研究開發功能"),
        ("musk", "審查最終結果")
    ])
    
    for result in seq_results:
        print(f"- {result.get('agent_id', 'unknown')}: {result.get('status')}")
