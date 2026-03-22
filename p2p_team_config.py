#!/usr/bin/env python3
"""
P2P Team Config - JSON 驅動的 P2P 團隊配置

支援從 JSON 檔案或字典載入團隊設定
"""

import json
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class P2PGlobalSettings:
    """P2P 全域設定（預設關閉）"""
    enabled: bool = False                    # 預設關閉
    default_mode: str = "master-sub"         # 預設為單一主代理模式
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "P2PGlobalSettings":
        if not data:
            data = {}
        return cls(
            enabled=data.get("enabled", False),
            default_mode=data.get("default_mode", "master-sub"),
        )
    
    def is_enabled(self) -> bool:
        """檢查是否啟用 P2P 模式"""
        return self.enabled


@dataclass
class P2PTeamSettings:
    """P2P 團隊設定"""
    mode: str = "peer-to-peer"
    max_spawn_depth: int = 2
    allow_agent_to_agent: bool = True
    message_queue_size: int = 100

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "P2PTeamSettings":
        return cls(
            mode=data.get("mode", "peer-to-peer"),
            max_spawn_depth=data.get("maxSpawnDepth", 2),
            allow_agent_to_agent=data.get("allowAgentToAgent", True),
            message_queue_size=data.get("messageQueueSize", 100),
        )


@dataclass
class TeamMember:
    """團隊成員"""
    agent_id: str
    role: str
    peer_memory_enabled: bool = True
    can_spawn_subagent: bool = True

    def to_dict(self) -> dict:
        return {
            "agentId": self.agent_id,
            "role": self.role,
            "peerMemoryEnabled": self.peer_memory_enabled,
            "canSpawnSubagent": self.can_spawn_subagent,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TeamMember":
        return cls(
            agent_id=data["agentId"],
            role=data["role"],
            peer_memory_enabled=data.get("peerMemoryEnabled", True),
            can_spawn_subagent=data.get("canSpawnSubagent", True),
        )


@dataclass
class TeamMeta:
    """團隊元資料"""
    team_id: str = "default-team"

    def to_dict(self) -> dict:
        return {"teamId": self.team_id}

    @classmethod
    def from_dict(cls, data: dict) -> "TeamMeta":
        return cls(team_id=data.get("teamId", "default-team"))


class P2PTeamConfig:
    """P2P 團隊配置管理器"""

    def __init__(
        self,
        team_meta: TeamMeta,
        settings: P2PTeamSettings,
        members: List[TeamMember],
        global_settings: P2PGlobalSettings = None,
    ):
        self.team_meta = team_meta
        self.settings = settings
        self.members = members
        self.global_settings = global_settings or P2PGlobalSettings()  # 預設關閉
    
    def is_p2p_enabled(self) -> bool:
        """檢查 P2P 模式是否啟用"""
        return self.global_settings.enabled if self.global_settings else False

    @classmethod
    def from_json(cls, config_path: str) -> "P2PTeamConfig":
        """從 JSON 檔案載入"""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, config: dict) -> "P2PTeamConfig":
        """從字典建立"""
        # 讀取全域設定（預設關閉）
        global_data = config.get("p2p", {})
        global_settings = P2PGlobalSettings.from_dict(global_data)
        
        team_data = config.get("team", {})
        settings_data = team_data.get("settings", {})
        members_data = config.get("members", [])

        team_meta = TeamMeta.from_dict(team_data)
        settings = P2PTeamSettings.from_dict(settings_data)
        members = [TeamMember.from_dict(m) for m in members_data]

        return cls(
            team_meta=team_meta,
            settings=settings,
            members=members,
            global_settings=global_settings
        )

    def to_dict(self) -> dict:
        """轉換為字典"""
        return {
            "p2p": {
                "enabled": self.global_settings.enabled if self.global_settings else False,
                "default_mode": self.global_settings.default_mode if self.global_settings else "master-sub",
            },
            "team": {
                "teamId": self.team_meta.team_id,
                "mode": self.settings.mode,
                "settings": {
                    "maxSpawnDepth": self.settings.max_spawn_depth,
                    "allowAgentToAgent": self.settings.allow_agent_to_agent,
                    "messageQueueSize": self.settings.message_queue_size,
                },
            },
            "members": [m.to_dict() for m in self.members],
        }

    def validate(self) -> bool:
        """驗證設定是否正確"""
        # 檢查團隊 ID
        if not self.team_meta.team_id:
            return False

        # 檢查模式
        valid_modes = ("peer-to-peer", "master-sub")
        if self.settings.mode not in valid_modes:
            return False

        # 檢查深度
        if self.settings.max_spawn_depth < 0 or self.settings.max_spawn_depth > 5:
            return False

        # 檢查成員
        if not self.members:
            return False

        agent_ids = set()
        for member in self.members:
            if not member.agent_id:
                return False
            if member.agent_id in agent_ids:
                return False  #  duplicate ID
            agent_ids.add(member.agent_id)

        return True

    def get_member(self, agent_id: str) -> Optional[TeamMember]:
        """依 ID 取得成員"""
        for m in self.members:
            if m.agent_id == agent_id:
                return m
        return None

    def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有成員"""
        return [
            {
                "agentId": m.agent_id,
                "role": m.role,
                "peerMemoryEnabled": m.peer_memory_enabled,
                "canSpawnSubagent": m.can_spawn_subagent,
            }
            for m in self.members
        ]

    def summary(self) -> Dict[str, Any]:
        """取得團隊摘要"""
        return {
            "teamId": self.team_meta.team_id,
            "mode": self.settings.mode,
            "memberCount": len(self.members),
            "roles": [m.role for m in self.members],
            "maxSpawnDepth": self.settings.max_spawn_depth,
            "allowAgentToAgent": self.settings.allow_agent_to_agent,
        }
