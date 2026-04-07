#!/usr/bin/env python3
"""
Enforcement Configuration - 統一設定
=====================================
將 Enforcement 的相依性包裝成統一設定

預設值：方案 B（輕量級 Local Hook，適合個人/小專案）
其他方案：多平台 CI/CD 支援
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import os
import json

class EnforcementMode(Enum):
    """Enforcement 模式"""
    # 輕量級：本地 CLI + Git Hook，適合個人/小專案
    LOCAL = "local"
    
    # 中量級：本地 + 自架 CI/CD
    SELF_HOSTED = "self_hosted"
    
    # 完整：雲端 CI/CD（GitHub Actions / GitLab CI / Jenkins）
    CLOUD = "cloud"

class Platform(Enum):
    """支援的 CI/CD 平台"""
    NONE = "none"              # 只有 Local Hook
    GITHUB = "github"
    GITLAB = "gitlab"
    JENKINS = "jenkins"
    AZURE = "azure"
    BITBUCKET = "bitbucket"

@dataclass
class EnforcementConfig:
    """
    統一 Enforcement 設定
    
    使用方式：
    
    ```python
    # 載入設定（自動偵測環境）
    config = EnforcementConfig.load()
    
    # 或手動指定
    config = EnforcementConfig(
        mode=EnforcementMode.LOCAL,
        platform=Platform.NONE,
        enforce_on_push=True,
        enforce_on_pr=True,
    )
    
    # 根據設定執行對應的 enforcement
    if config.mode == EnforcementMode.LOCAL:
        # 執行 Local Hook
        run_local_enforcement()
    elif config.mode == EnforcementMode.CLOUD:
        # 執行 CI/CD
        run_cloud_enforcement(config.platform)
    ```
    """
    # 執行模式
    mode: EnforcementMode = EnforcementMode.LOCAL
    
    # CI/CD 平台
    platform: Platform = Platform.NONE
    
    # 執行時機
    enforce_on_commit: bool = True       # commit 時
    enforce_on_push: bool = True         # push 時
    enforce_on_pr: bool = True           # PR 時
    enforce_on_merge: bool = True         # merge 時
    
    # 嚴格程度
    strict_mode: bool = True             # True = 預設阻擋
    allow_bypass: bool = False            # 是否允許繞過
    
    # 閾值
    quality_gate_threshold: float = 90.0
    security_threshold: float = 95.0
    coverage_threshold: float = 80.0
    
    # 平台特定設定
    platform_config: Dict[str, Any] = field(default_factory=dict)
    
    # 額外選項
    enable_registry: bool = True         # 啟用 Execution Registry
    enable_constitution_check: bool = True
    enable_policy_engine: bool = True
    
    @classmethod
    def load(cls, config_path: str = ".methodology/enforcement.json") -> "EnforcementConfig":
        """
        載入設定
        
        優先順序：
        1. 環境變數 METHODOLOGY_ENFORCEMENT_CONFIG
        2. .methodology/enforcement.json
        3. 預設值（LOCAL 模式）
        """
        # 1. 檢查環境變數
        env_config = os.environ.get('METHODOLOGY_ENFORCEMENT_CONFIG')
        if env_config:
            return cls.from_json(env_config)
        
        # 2. 檢查設定檔
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                data = json.load(f)
            return cls.from_dict(data)
        
        # 3. 預設值（LOCAL 模式）
        return cls()
    
    @classmethod
    def from_dict(cls, data: Dict) -> "EnforcementConfig":
        """從字典建立"""
        return cls(
            mode=EnforcementMode(data.get('mode', 'local')),
            platform=Platform(data.get('platform', 'none')),
            enforce_on_commit=data.get('enforce_on_commit', True),
            enforce_on_push=data.get('enforce_on_push', True),
            enforce_on_pr=data.get('enforce_on_pr', True),
            enforce_on_merge=data.get('enforce_on_merge', True),
            strict_mode=data.get('strict_mode', True),
            allow_bypass=data.get('allow_bypass', False),
            quality_gate_threshold=data.get('quality_gate_threshold', 90.0),
            security_threshold=data.get('security_threshold', 95.0),
            coverage_threshold=data.get('coverage_threshold', 80.0),
            platform_config=data.get('platform_config', {}),
            enable_registry=data.get('enable_registry', True),
            enable_constitution_check=data.get('enable_constitution_check', True),
            enable_policy_engine=data.get('enable_policy_engine', True),
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "EnforcementConfig":
        """從 JSON 字串建立"""
        return cls.from_dict(json.loads(json_str))
    
    def to_dict(self) -> Dict:
        """轉為字典"""
        return {
            'mode': self.mode.value,
            'platform': self.platform.value,
            'enforce_on_commit': self.enforce_on_commit,
            'enforce_on_push': self.enforce_on_push,
            'enforce_on_pr': self.enforce_on_pr,
            'enforce_on_merge': self.enforce_on_merge,
            'strict_mode': self.strict_mode,
            'allow_bypass': self.allow_bypass,
            'quality_gate_threshold': self.quality_gate_threshold,
            'security_threshold': self.security_threshold,
            'coverage_threshold': self.coverage_threshold,
            'platform_config': self.platform_config,
            'enable_registry': self.enable_registry,
            'enable_constitution_check': self.enable_constitution_check,
            'enable_policy_engine': self.enable_policy_engine,
        }
    
    def to_json(self) -> str:
        """轉為 JSON"""
        return json.dumps(self.to_dict(), indent=2)
    
    def save(self, config_path: str = ".methodology/enforcement.json"):
        """儲存設定"""
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            f.write(self.to_json())
    
    def get_summary(self) -> str:
        """取得摘要"""
        lines = [
            "=" * 50,
            "Enforcement Configuration",
            "=" * 50,
            f"Mode: {self.mode.value}",
            f"Platform: {self.platform.value}",
            f"Strict: {self.strict_mode}",
            f"Allow Bypass: {self.allow_bypass}",
            "",
            "Enforcement Triggers:",
            f"  - Commit: {self.enforce_on_commit}",
            f"  - Push: {self.enforce_on_push}",
            f"  - PR: {self.enforce_on_pr}",
            f"  - Merge: {self.enforce_on_merge}",
            "",
            "Thresholds:",
            f"  - Quality Gate: {self.quality_gate_threshold}",
            f"  - Security: {self.security_threshold}",
            f"  - Coverage: {self.coverage_threshold}",
            "=" * 50,
        ]
        return "\n".join(lines)


class ConfigGenerator:
    """
    設定產生器
    
    根據不同平台產生對應的設定
    """
    
    @staticmethod
    def local_only() -> EnforcementConfig:
        """本地 only（輕量級，預設）"""
        return EnforcementConfig(
            mode=EnforcementMode.LOCAL,
            platform=Platform.NONE,
            enforce_on_commit=True,
            enforce_on_push=False,
            enforce_on_pr=False,
            enforce_on_merge=False,
        )
    
    @staticmethod
    def github_actions() -> EnforcementConfig:
        """GitHub Actions"""
        return EnforcementConfig(
            mode=EnforcementMode.CLOUD,
            platform=Platform.GITHUB,
            enforce_on_commit=True,
            enforce_on_push=True,
            enforce_on_pr=True,
            enforce_on_merge=True,
            platform_config={
                'workflow_file': '.github/workflows/enforcement.yml',
            }
        )
    
    @staticmethod
    def gitlab_ci() -> EnforcementConfig:
        """GitLab CI"""
        return EnforcementConfig(
            mode=EnforcementMode.CLOUD,
            platform=Platform.GITLAB,
            enforce_on_commit=True,
            enforce_on_push=True,
            enforce_on_pr=True,
            enforce_on_merge=True,
            platform_config={
                'workflow_file': '.gitlab-ci.yml',
            }
        )
    
    @staticmethod
    def jenkins() -> EnforcementConfig:
        """Jenkins"""
        return EnforcementConfig(
            mode=EnforcementMode.SELF_HOSTED,
            platform=Platform.JENKINS,
            enforce_on_commit=True,
            enforce_on_push=True,
            enforce_on_pr=True,
            enforce_on_merge=True,
            platform_config={
                'jenkinsfile': 'Jenkinsfile',
                'agent_label': 'methodology-enforcement',
            }
        )
    
    @staticmethod
    def azure_pipelines() -> EnforcementConfig:
        """Azure DevOps"""
        return EnforcementConfig(
            mode=EnforcementMode.CLOUD,
            platform=Platform.AZURE,
            enforce_on_commit=True,
            enforce_on_push=True,
            enforce_on_pr=True,
            enforce_on_merge=True,
            platform_config={
                'pipeline_file': 'azure-pipelines.yml',
            }
        )
    
    @staticmethod
    def auto_detect() -> EnforcementConfig:
        """自動偵測環境"""
        # 檢查 CI 環境變數
        if os.environ.get('GITHUB_ACTIONS'):
            return ConfigGenerator.github_actions()
        elif os.environ.get('GITLAB_CI'):
            return ConfigGenerator.gitlab_ci()
        elif os.environ.get('JENKINS_URL'):
            return ConfigGenerator.jenkins()
        elif os.environ.get('AZURE Pipelines'):
            return ConfigGenerator.azure_pipelines()
        else:
            # 預設本地模式
            return ConfigGenerator.local_only()


def main():
    """CLI 入口"""
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "show":
            config = EnforcementConfig.load()
            print(config.get_summary())
        
        elif cmd == "set":
            if len(sys.argv) < 3:
                print("Usage: enforcement_config set <mode>")
                print("Modes: local, github, gitlab, jenkins, azure")
                sys.exit(1)
            
            mode = sys.argv[2].lower()
            
            if mode == "local":
                config = ConfigGenerator.local_only()
            elif mode == "github":
                config = ConfigGenerator.github_actions()
            elif mode == "gitlab":
                config = ConfigGenerator.gitlab_ci()
            elif mode == "jenkins":
                config = ConfigGenerator.jenkins()
            elif mode == "azure":
                config = ConfigGenerator.azure_pipelines()
            else:
                print(f"Unknown mode: {mode}")
                sys.exit(1)
            
            config.save()
            print(f"✅ Configuration saved: {mode}")
            print(config.get_summary())
        
        elif cmd == "detect":
            config = ConfigGenerator.auto_detect()
            print(f"🔍 Detected: {config.mode.value} ({config.platform.value})")
            print(config.get_summary())
        
        elif cmd == "init":
            # 初始化設定檔
            config = ConfigGenerator.local_only()
            config.save()
            print("✅ Initialized with LOCAL mode (default)")
            print("   Use 'enforcement_config set <mode>' to change")
        
        else:
            print(f"Unknown command: {cmd}")
            sys.exit(1)
    else:
        # 顯示目前設定
        config = EnforcementConfig.load()
        print(config.get_summary())


if __name__ == "__main__":
    main()
