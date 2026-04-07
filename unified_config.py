#!/usr/bin/env python3
"""
Unified Config - 統一配置中心

將所有全域設定集中到一個地方管理，方便團隊使用。

包含：
- P2P 設定（預設關閉）
- HITL 設定（預設關閉）
- Hybrid Workflow 設定
- Agent 預設設定
- 系統設定

使用方法：
    from unified_config import UnifiedConfig
    
    # 載入設定
    config = UnifiedConfig.from_json('config.json')
    
    # 檢查功能開關
    if config.is_p2p_enabled():
        print("P2P 已啟用")
    
    if config.is_hitl_enabled():
        print("HITL 已啟用")
    
    # 儲存預設設定
    config.save_defaults()
"""

import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


# ============================================================================
# P2P 設定
# ============================================================================

@dataclass
class P2PSettings:
    """P2P 點對點代理設定"""
    enabled: bool = False                    # 預設關閉
    default_mode: str = "master-sub"       # 預設為單一主代理
    max_spawn_depth: int = 2              # Sub Agent 嵌套深度
    allow_agent_to_agent: bool = True     # 允許 Agent 間直接溝通
    message_queue_size: int = 100         # 訊息佇列大小
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "P2PSettings":
        if not data:
            data = {}
        return cls(
            enabled=data.get("enabled", False),
            default_mode=data.get("default_mode", "master-sub"),
            max_spawn_depth=data.get("maxSpawnDepth", 2),
            allow_agent_to_agent=data.get("allowAgentToAgent", True),
            message_queue_size=data.get("messageQueueSize", 100),
        )


# ============================================================================
# HITL 人類介入設定
# ============================================================================

@dataclass
class HITLSettings:
    """HITL 人類介入設定"""
    enabled: bool = False                 # 預設關閉（向前相容）
    auto_escalate_timeout: int = 3600     # 自動升級超時（秒）
    require_approval_for_all: bool = False  # 是否所有產出都需要審批
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "HITLSettings":
        if not data:
            data = {}
        return cls(
            enabled=data.get("enabled", False),
            auto_escalate_timeout=data.get("auto_escalate_timeout", 3600),
            require_approval_for_all=data.get("require_approval_for_all", False),
        )


# ============================================================================
# Hybrid Workflow 設定
# ============================================================================

@dataclass
class HybridWorkflowSettings:
    """Hybrid Workflow 智慧分流設定"""
    default_mode: str = "hybrid"          # 預設 HYBRID 模式
    small_change_threshold: int = 10      # 小改動門檻（行數）
    large_change_threshold: int = 30       # 大改動門檻（行數）
    auto_approve_comments: bool = True     # 僅註釋改動自動批准
    auto_approve_docs: bool = True        # 僅文件改動自動批准
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "HybridWorkflowSettings":
        if not data:
            data = {}
        return cls(
            default_mode=data.get("default_mode", "hybrid"),
            small_change_threshold=data.get("smallChangeThreshold", 10),
            large_change_threshold=data.get("largeChangeThreshold", 30),
            auto_approve_comments=data.get("autoApproveComments", True),
            auto_approve_docs=data.get("autoApproveDocs", True),
        )


# ============================================================================
# Agent 預設設定
# ============================================================================

@dataclass
class AgentDefaults:
    """Agent 預設設定"""
    max_concurrent_agents: int = 5        # 最大並發 Agent 數
    default_timeout: int = 300             # 預設超時（秒）
    retry_limit: int = 3                   # 重試次數
    idle_timeout: int = 300                # 空閒超時（秒）
    enable_memory: bool = True             # 啟用記憶
    enable_telemetry: bool = True          # 啟用遙測
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "AgentDefaults":
        if not data:
            data = {}
        return cls(
            max_concurrent_agents=data.get("maxConcurrentAgents", 5),
            default_timeout=data.get("defaultTimeout", 300),
            retry_limit=data.get("retryLimit", 3),
            idle_timeout=data.get("idleTimeout", 300),
            enable_memory=data.get("enableMemory", True),
            enable_telemetry=data.get("enableTelemetry", True),
        )


# ============================================================================
# 系統設定
# ============================================================================

@dataclass
class SystemSettings:
    """系統全域設定"""
    log_level: str = "INFO"              # 日誌級別
    log_path: str = "./logs"             # 日誌路徑
    storage_path: str = "./data"           # 資料儲存路徑
    enable_persistence: bool = True       # 啟用持久化
    config_version: str = "1.0"           # 設定版本
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "SystemSettings":
        if not data:
            data = {}
        return cls(
            log_level=data.get("logLevel", "INFO"),
            log_path=data.get("logPath", "./logs"),
            storage_path=data.get("storagePath", "./data"),
            enable_persistence=data.get("enablePersistence", True),
            config_version=data.get("configVersion", "1.0"),
        )


# ============================================================================
# 統一配置中心
# ============================================================================

@dataclass
class UnifiedConfig:
    """
    統一配置中心
    
    集中管理所有全域設定，方便團隊使用。
    """
    
    p2p: P2PSettings = field(default_factory=P2PSettings)
    hitl: HITLSettings = field(default_factory=HITLSettings)
    hybrid_workflow: HybridWorkflowSettings = field(default_factory=HybridWorkflowSettings)
    agent_defaults: AgentDefaults = field(default_factory=AgentDefaults)
    system: SystemSettings = field(default_factory=SystemSettings)
    
    @classmethod
    def from_json(cls, path: str) -> "UnifiedConfig":
        """從 JSON 檔案載入"""
        file_path = Path(path)
        if not file_path.exists():
            # 檔案不存在，返回預設設定
            return cls()
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, config: dict) -> "UnifiedConfig":
        """從字典建立"""
        return cls(
            p2p=P2PSettings.from_dict(config.get("p2p", {})),
            hitl=HITLSettings.from_dict(config.get("hitl", {})),
            hybrid_workflow=HybridWorkflowSettings.from_dict(config.get("hybridWorkflow", {})),
            agent_defaults=AgentDefaults.from_dict(config.get("agentDefaults", {})),
            system=SystemSettings.from_dict(config.get("system", {})),
        )
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return {
            "p2p": self.p2p.to_dict(),
            "hitl": self.hitl.to_dict(),
            "hybridWorkflow": self.hybrid_workflow.to_dict(),
            "agentDefaults": self.agent_defaults.to_dict(),
            "system": self.system.to_dict(),
        }
    
    def to_json(self, path: str):
        """儲存為 JSON 檔案"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    # === 便捷方法 ===
    
    def is_p2p_enabled(self) -> bool:
        """檢查 P2P 是否啟用"""
        return self.p2p.enabled
    
    def is_hitl_enabled(self) -> bool:
        """檢查 HITL 是否啟用"""
        return self.hitl.enabled
    
    def is_hybrid_enabled(self) -> bool:
        """檢查 Hybrid Workflow 是否為 hybrid 模式"""
        return self.hybrid_workflow.default_mode == "hybrid"
    
    # === 預設設定 ===
    
    @classmethod
    def default_poc(cls) -> "UnifiedConfig":
        """POC/小型專案預設"""
        return cls(
            p2p=P2PSettings(enabled=False),
            hitl=HITLSettings(enabled=False),
            hybrid_workflow=HybridWorkflowSettings(default_mode="off"),
        )
    
    @classmethod
    def default_team(cls) -> "UnifiedConfig":
        """中型團隊預設"""
        return cls(
            p2p=P2PSettings(enabled=False),
            hitl=HITLSettings(enabled=True),
            hybrid_workflow=HybridWorkflowSettings(default_mode="hybrid"),
        )
    
    @classmethod
    def default_enterprise(cls) -> "UnifiedConfig":
        """企業級預設"""
        return cls(
            p2p=P2PSettings(enabled=True),
            hitl=HITLSettings(enabled=True, require_approval_for_all=True),
            hybrid_workflow=HybridWorkflowSettings(default_mode="on"),
        )
    
    def save_defaults(self, path: str = "config.defaults.json"):
        """儲存為預設設定檔"""
        self.to_json(path)
    
    @classmethod
    def load_defaults(cls, path: str = "config.defaults.json") -> "UnifiedConfig":
        """載入預設設定檔"""
        return cls.from_json(path)


# ============================================================================
# 範例設定檔
# ============================================================================

DEFAULT_CONFIG_JSON = """{
  "_meta": {
    "version": "1.0",
    "description": "methodology-v2 統一設定檔",
    "last_updated": "2026-03-22"
  },
  
  "p2p": {
    "_description": "P2P 點對點代理設定（預設關閉）",
    "enabled": false,
    "default_mode": "master-sub",
    "maxSpawnDepth": 2,
    "allowAgentToAgent": true,
    "messageQueueSize": 100
  },
  
  "hitl": {
    "_description": "HITL 人類介入設定（預設關閉，向前相容）",
    "enabled": false,
    "auto_escalate_timeout": 3600,
    "require_approval_for_all": false
  },
  
  "hybridWorkflow": {
    "_description": "Hybrid Workflow 智慧分流設定（預設 hybrid）",
    "default_mode": "hybrid",
    "smallChangeThreshold": 10,
    "largeChangeThreshold": 30,
    "autoApproveComments": true,
    "autoApproveDocs": true
  },
  
  "agentDefaults": {
    "_description": "Agent 預設設定",
    "maxConcurrentAgents": 5,
    "defaultTimeout": 300,
    "retryLimit": 3,
    "idleTimeout": 300,
    "enableMemory": true,
    "enableTelemetry": true
  },
  
  "system": {
    "_description": "系統全域設定",
    "logLevel": "INFO",
    "logPath": "./logs",
    "storagePath": "./data",
    "enablePersistence": true
  }
}"""


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--generate":
            # 產生預設設定檔
            print("產生預設設定檔：config.default.json")
            with open("config.default.json", "w", encoding="utf-8") as f:
                f.write(DEFAULT_CONFIG_JSON)
            print("完成！")
        elif sys.argv[1] == "--poc":
            # POC 預設
            config = UnifiedConfig.default_poc()
            config.to_json("config.poc.json")
            print("已產生 POC 設定：config.poc.json")
        elif sys.argv[1] == "--team":
            # 團隊預設
            config = UnifiedConfig.default_team()
            config.to_json("config.team.json")
            print("已產生團隊設定：config.team.json")
        elif sys.argv[1] == "--enterprise":
            # 企業預設
            config = UnifiedConfig.default_enterprise()
            config.to_json("config.enterprise.json")
            print("已產生企業設定：config.enterprise.json")
        else:
            # 載入並顯示設定
            config = UnifiedConfig.from_json(sys.argv[1])
            print(json.dumps(config.to_dict(), indent=2))
    else:
        # 顯示說明
        print("Unified Config - 統一配置中心")
        print()
        print("用法：")
        print("  python unified_config.py --generate    # 產生預設設定檔")
        print("  python unified_config.py --poc       # POC 預設")
        print("  python unified_config.py --team      # 團隊預設")
        print("  python unified_config.py --enterprise # 企業預設")
        print("  python unified_config.py config.json # 載入並顯示設定")
