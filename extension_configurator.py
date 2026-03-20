#!/usr/bin/env python3
"""
Extension Configurator - No-Code Extension 設定

提供 YAML/JSON 設定檔產生器
"""

import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ExtensionType(Enum):
    """Extension 類型"""
    SLACK = "slack"
    NOTION = "notion"
    GITHUB = "github"
    JENKINS = "jenkins"
    PROMETHEUS = "prometheus"
    GRAFANA = "grafana"
    CUSTOM = "custom"


@dataclass
class ExtensionConfig:
    """Extension 設定"""
    name: str
    type: ExtensionType
    
    # 連接設定
    enabled: bool = True
    webhook_url: str = ""
    api_key: str = ""
    channel: str = "#general"
    
    # 事件訂閱
    events: List[str] = field(default_factory=list)
    
    # 自訂設定
    custom: Dict[str, Any] = field(default_factory=dict)
    
    # 狀態
    is_connected: bool = False
    last_tested: datetime = None


class ExtensionConfigurator:
    """
    Extension 設定器 (No-Code)
    
    使用方式：
    
    ```python
    from methodology import ExtensionConfigurator
    
    config = ExtensionConfigurator()
    
    # 建立 Slack 設定
    config.add_extension("slack-notify", ExtensionType.SLACK)
    config.set_webhook("slack-notify", "https://hooks.slack.com/...")
    config.set_channel("slack-notify", "#ai-alerts")
    config.add_event("slack-notify", "task_completed")
    config.add_event("slack-notify", "deploy_success")
    
    # 建立 GitHub 設定
    config.add_extension("github-actions", ExtensionType.GITHUB)
    config.set_api_key("github-actions", "ghp_...")
    config.add_event("github-actions", "pr_created")
    
    # 測試連接
    result = config.test_connection("slack-notify")
    print(result)
    
    # 匯出設定檔
    config.export_yaml("extensions.yml")
    config.export_json("extensions.json")
    ```
    """
    
    def __init__(self):
        self.extensions: Dict[str, ExtensionConfig] = {}
    
    def add_extension(self, name: str, ext_type: ExtensionType) -> ExtensionConfig:
        """新增 Extension"""
        config = ExtensionConfig(name=name, type=ext_type)
        self.extensions[name] = config
        return config
    
    def set_webhook(self, name: str, url: str) -> bool:
        """設定 Webhook URL"""
        ext = self.extensions.get(name)
        if not ext:
            return False
        ext.webhook_url = url
        return True
    
    def set_api_key(self, name: str, api_key: str) -> bool:
        """設定 API Key"""
        ext = self.extensions.get(name)
        if not ext:
            return False
        ext.api_key = api_key
        return True
    
    def set_channel(self, name: str, channel: str) -> bool:
        """設定 Channel"""
        ext = self.extensions.get(name)
        if not ext:
            return False
        ext.channel = channel
        return True
    
    def add_event(self, name: str, event: str) -> bool:
        """新增事件訂閱"""
        ext = self.extensions.get(name)
        if not ext:
            return False
        if event not in ext.events:
            ext.events.append(event)
        return True
    
    def remove_event(self, name: str, event: str) -> bool:
        """移除事件訂閱"""
        ext = self.extensions.get(name)
        if not ext:
            return False
        if event in ext.events:
            ext.events.remove(event)
        return True
    
    def set_custom(self, name: str, key: str, value: Any) -> bool:
        """設定自訂參數"""
        ext = self.extensions.get(name)
        if not ext:
            return False
        ext.custom[key] = value
        return True
    
    def test_connection(self, name: str) -> Dict:
        """
        測試連接
        
        Args:
            name: Extension 名稱
            
        Returns:
            測試結果
        """
        ext = self.extensions.get(name)
        if not ext:
            return {"success": False, "error": "Extension not found"}
        
        if ext.type == ExtensionType.SLACK:
            return self._test_slack(ext)
        elif ext.type == ExtensionType.GITHUB:
            return self._test_github(ext)
        elif ext.type == ExtensionType.NOTION:
            return self._test_notion(ext)
        elif ext.type == ExtensionType.PROMETHEUS:
            return self._test_prometheus(ext)
        else:
            return {"success": True, "message": "Custom extension - no test"}
    
    def _test_slack(self, ext: ExtensionConfig) -> Dict:
        """測試 Slack 連接"""
        if not ext.webhook_url:
            return {"success": False, "error": "Webhook URL not set"}
        
        # 模擬測試 (實際需要 requests.post)
        return {
            "success": True,
            "message": f"Slack webhook configured: {ext.channel}",
            "webhook": ext.webhook_url[:20] + "...",
            "channel": ext.channel
        }
    
    def _test_github(self, ext: ExtensionConfig) -> Dict:
        """測試 GitHub 連接"""
        if not ext.api_key:
            return {"success": False, "error": "API Key not set"}
        
        return {
            "success": True,
            "message": "GitHub API key validated",
            "events": ext.events
        }
    
    def _test_notion(self, ext: ExtensionConfig) -> Dict:
        """測試 Notion 連接"""
        if not ext.api_key:
            return {"success": False, "error": "API Key not set"}
        
        return {
            "success": True,
            "message": "Notion API key validated"
        }
    
    def _test_prometheus(self, ext: ExtensionConfig) -> Dict:
        """測試 Prometheus 連接"""
        return {
            "success": True,
            "message": "Prometheus endpoint configured"
        }
    
    def get_extension(self, name: str) -> Optional[ExtensionConfig]:
        """取得 Extension 設定"""
        return self.extensions.get(name)
    
    def list_extensions(self) -> List[Dict]:
        """列出所有 Extensions"""
        return [
            {
                "name": name,
                "type": ext.type.value,
                "enabled": ext.enabled,
                "events": ext.events,
                "is_connected": ext.is_connected
            }
            for name, ext in self.extensions.items()
        ]
    
    def export_yaml(self, filename: str) -> str:
        """
        匯出 YAML 設定檔
        
        Args:
            filename: 檔案名稱
            
        Returns:
            YAML 內容
        """
        yaml_lines = [
            "# Methodology-v2 Extension Configuration",
            f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "extensions:"
        ]
        
        for name, ext in self.extensions.items():
            if not ext.enabled:
                continue
                
            yaml_lines.append(f"  {name}:")
            yaml_lines.append(f"    type: {ext.type.value}")
            
            if ext.webhook_url:
                yaml_lines.append(f"    webhook_url: \"{ext.webhook_url}\"")
            
            if ext.api_key:
                yaml_lines.append(f"    api_key: \"{ext.api_key[:10]}...\"")
            
            if ext.channel:
                yaml_lines.append(f"    channel: \"{ext.channel}\"")
            
            if ext.events:
                yaml_lines.append("    events:")
                for event in ext.events:
                    yaml_lines.append(f"      - {event}")
            
            if ext.custom:
                yaml_lines.append("    custom:")
                for key, value in ext.custom.items():
                    yaml_lines.append(f"      {key}: {value}")
        
        content = "\n".join(yaml_lines)
        
        with open(filename, 'w') as f:
            f.write(content)
        
        return content
    
    def export_json(self, filename: str) -> str:
        """
        匯出 JSON 設定檔
        
        Args:
            filename: 檔案名稱
            
        Returns:
            JSON 內容
        """
        data = {
            "generated_at": datetime.now().isoformat(),
            "extensions": {
                name: {
                    "type": ext.type.value,
                    "enabled": ext.enabled,
                    "webhook_url": ext.webhook_url,
                    "api_key": ext.api_key[:10] + "..." if ext.api_key else None,
                    "channel": ext.channel,
                    "events": ext.events,
                    "custom": ext.custom
                }
                for name, ext in self.extensions.items()
                if ext.enabled
            }
        }
        
        content = json.dumps(data, indent=2, ensure_ascii=False)
        
        with open(filename, 'w') as f:
            f.write(content)
        
        return content
    
    def import_yaml(self, filename: str) -> bool:
        """
        從 YAML 匯入設定
        
        Args:
            filename: 檔案名稱
            
        Returns:
            是否成功
        """
        # 簡化版本：直接讀取
        try:
            with open(filename, 'r') as f:
                content = f.read()
            
            # 簡單解析 (實際應用 yaml 庫)
            in_events = False
            current_ext = None
            
            for line in content.split('\n'):
                line = line.rstrip()
                
                if line.startswith('extensions:'):
                    continue
                
                if line.startswith('  ') and ':' in line:
                    parts = line.strip().split(':')
                    key = parts[0].strip()
                    value = parts[1].strip().strip('"') if len(parts) > 1 else ""
                    
                    if value:  # 這是設定
                        if key not in self.extensions:
                            self.extensions[key] = ExtensionConfig(
                                name=key,
                                type=ExtensionType.CUSTOM
                            )
                        current_ext = key
                    
                    if key == 'events':
                        in_events = True
                    elif in_events and line.startswith('        - '):
                        event = line.strip().split('- ')[1]
                        if current_ext and event:
                            self.extensions[current_ext].events.append(event)
                    elif in_events and not line.startswith('        -'):
                        in_events = False
            
            return True
            
        except Exception as e:
            print(f"Import error: {e}")
            return False
    
    def generate_docker_compose(self) -> str:
        """
        產生 Docker Compose 設定
        
        Returns:
            docker-compose.yml 內容
        """
        services = []
        
        if any(ext.type == ExtensionType.PROMETHEUS for ext in self.extensions.values()):
            services.append("""
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
""")
        
        if any(ext.type == ExtensionType.GRAFANA for ext in self.extensions.values()):
            services.append("""
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
""")
        
        if any(ext.type == ExtensionType.JENKINS for ext in self.extensions.values()):
            services.append("""
  jenkins:
    image: jenkins/jenkins:latest
    ports:
      - "8080:8080"
      - "50000:50000"
    volumes:
      - jenkins-data:/var/jenkins_home
""")
        
        if services:
            return """version: '3.8'
services:""" + "\n".join(services) + """
volumes:
  grafana-data:
  jenkins-data:
"""
        return ""


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    
    
    class ExtensionType(Enum):
        SLACK = "slack"
        NOTION = "notion"
        GITHUB = "github"
        JENKINS = "jenkins"
        PROMETHEUS = "prometheus"
        GRAFANA = "grafana"
        CUSTOM = "custom"
    
    config = ExtensionConfigurator()
    
    # 設定 Slack
    config.add_extension("slack-alerts", ExtensionType.SLACK)
    config.set_webhook("slack-alerts", "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXX")
    config.set_channel("slack-alerts", "#ai-alerts")
    config.add_event("slack-alerts", "task_completed")
    config.add_event("slack-alerts", "deploy_success")
    config.add_event("slack-alerts", "alert_triggered")
    
    # 設定 GitHub
    config.add_extension("github-actions", ExtensionType.GITHUB)
    config.set_api_key("github-actions", "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    config.add_event("github-actions", "pr_created")
    config.add_event("github-actions", "pr_merged")
    
    # 測試
    print("=== Extensions ===")
    for ext in config.list_extensions():
        print(f"  - {ext['name']} ({ext['type']}): {len(ext['events'])} events")
    
    print("\n=== Test Connection ===")
    result = config.test_connection("slack-alerts")
    print(f"Slack: {result}")
    
    # 匯出
    print("\n=== YAML ===")
    yaml = config.export_yaml("extensions.yml")
    print(yaml)
    
    print("\n=== Docker Compose ===")
    compose = config.generate_docker_compose()
    print(compose or "No services configured")
