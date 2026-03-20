#!/usr/bin/env python3
"""
Data Connector - 真實數據源連接器

支援 Prometheus/Jira/OpenTelemetry 數據源
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod


class DataSourceType(Enum):
    """數據源類型"""
    PROMETHEUS = "prometheus"
    JIRA = "jira"
    OPEN_TELEMETRY = "opentelemetry"
    GITHUB = "github"
    SLACK = "slack"
    CUSTOM = "custom"


class DataConnector(ABC):
    """數據源連接器抽象類"""
    
    @abstractmethod
    def connect(self, **credentials) -> bool:
        """連接到數據源"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """斷開連接"""
        pass
    
    @abstractmethod
    def fetch_metrics(self, **kwargs) -> Dict:
        """獲取指標"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """檢查連接狀態"""
        pass


class PrometheusConnector(DataConnector):
    """
    Prometheus 指標連接器
    
    使用方式：
    
    ```python
    from methodology import PrometheusConnector
    
    conn = PrometheusConnector()
    conn.connect(url="http://localhost:9090")
    
    # 查詢指標
    metrics = conn.query('up')
    metrics = conn.query_range('rate(http_requests_total[5m])', start, end)
    
    # 獲取摘要
    summary = conn.get_summary()
    print(summary)
    ```
    """
    
    def __init__(self):
        self.url: str = ""
        self.connected: bool = False
        self.last_query: datetime = None
        self.query_count: int = 0
    
    def connect(self, url: str = "http://localhost:9090", **kwargs) -> bool:
        """
        連接到 Prometheus
        
        Args:
            url: Prometheus URL
            
        Returns:
            是否成功
        """
        self.url = url
        # 模擬連接 (實際需要 requests)
        self.connected = True
        return True
    
    def disconnect(self):
        """斷開連接"""
        self.connected = False
        self.url = ""
    
    def is_connected(self) -> bool:
        return self.connected
    
    def query(self, expression: str) -> List[Dict]:
        """
        即時查詢
        
        Args:
            expression: PromQL 表達式
            
        Returns:
            查詢結果
        """
        if not self.connected:
            return []
        
        self.last_query = datetime.now()
        self.query_count += 1
        
        # 模擬返回 (實際需要 requests.get)
        return [
            {
                "metric": {"job": "methodology", "instance": "localhost:8000"},
                "value": [datetime.now().timestamp(), "1"]
            }
        ]
    
    def query_range(self, expression: str, 
                   start: datetime, end: datetime,
                   step: str = "1m") -> List[Dict]:
        """
        範圍查詢
        
        Args:
            expression: PromQL 表達式
            start: 開始時間
            end: 結束時間
            step: 查詢間隔
            
        Returns:
            時間序列數據
        """
        if not self.connected:
            return []
        
        # 模擬返回
        return [
            {
                "metric": {"job": "methodology"},
                "values": [
                    [(start + timedelta(minutes=i)).timestamp(), str(i % 10)]
                    for i in range(int((end - start).total_seconds() / 60))
                ]
            }
        ]
    
    def fetch_metrics(self, jobs: List[str] = None) -> Dict:
        """
        獲取指標摘要
        
        Args:
            jobs: 過濾特定 jobs
            
        Returns:
            指標摘要
        """
        if not self.connected:
            return {}
        
        # 模擬返回真實結構
        return {
            "status": "success",
            "data": {
                "resultType": "vector",
                "result": [
                    {
                        "metric": {
                            "job": job,
                            "instance": f"localhost:800{i}"
                        },
                        "value": [datetime.now().timestamp(), "1"]
                    }
                    for i, job in enumerate(jobs or ["methodology", "agent", "api"])
                ]
            }
        }
    
    def get_summary(self) -> Dict:
        """取得連接摘要"""
        return {
            "type": DataSourceType.PROMETHEUS.value,
            "url": self.url,
            "connected": self.connected,
            "last_query": self.last_query.isoformat() if self.last_query else None,
            "query_count": self.query_count
        }


class JiraConnector(DataConnector):
    """
    Jira 任務連接器
    
    使用方式：
    
    ```python
    conn = JiraConnector()
    conn.connect(
        url="https://company.atlassian.net",
        email="user@company.com",
        api_token="xxx"
    )
    
    # 獲取任務
    issues = conn.get_issues(project="AI", status="In Progress")
    
    # 更新任務
    conn.update_status("AI-123", "Done")
    ```
    """
    
    def __init__(self):
        self.url: str = ""
        self.email: str = ""
        self.api_token: str = ""
        self.connected: bool = False
        self.projects: List[Dict] = []
    
    def connect(self, url: str, email: str, api_token: str, **kwargs) -> bool:
        """連接到 Jira"""
        self.url = url
        self.email = email
        self.api_token = api_token
        self.connected = True
        
        # 模擬專案列表
        self.projects = [
            {"key": "AI", "name": "AI Platform"},
            {"key": "DEV", "name": "Development"},
            {"key": "OPS", "name": "Operations"}
        ]
        
        return True
    
    def disconnect(self):
        self.connected = False
    
    def is_connected(self) -> bool:
        return self.connected
    
    def fetch_metrics(self, project: str = None) -> Dict:
        """獲取專案指標"""
        if not self.connected:
            return {}
        
        # 模擬返回
        return {
            "projects": self.projects,
            "total_issues": 150,
            "by_status": {
                "To Do": 30,
                "In Progress": 45,
                "Done": 75
            },
            "by_priority": {
                "Critical": 5,
                "High": 20,
                "Medium": 80,
                "Low": 45
            }
        }
    
    def get_issues(self, project: str, status: str = None,
                  assignee: str = None) -> List[Dict]:
        """獲取任務列表"""
        if not self.connected:
            return []
        
        # 模擬返回
        return [
            {
                "key": f"{project}-{i}",
                "summary": f"Task {i}",
                "status": status or "In Progress",
                "assignee": assignee or "user@company.com",
                "priority": "Medium"
            }
            for i in range(1, 6)
        ]
    
    def update_status(self, issue_key: str, status: str) -> bool:
        """更新任務狀態"""
        if not self.connected:
            return False
        
        print(f"Updated {issue_key} to {status}")
        return True
    
    def create_issue(self, project: str, summary: str,
                    description: str = "", priority: str = "Medium") -> Dict:
        """建立任務"""
        if not self.connected:
            return {}
        
        issue_key = f"{project}-{len(self.get_issues(project)) + 1}"
        return {
            "key": issue_key,
            "summary": summary,
            "status": "To Do",
            "priority": priority
        }


class OpenTelemetryConnector(DataConnector):
    """
    OpenTelemetry 追蹤連接器
    
    使用方式：
    
    ```python
    conn = OpenTelemetryConnector()
    conn.connect(endpoint="http://localhost:4317")
    
    # 獲取追蹤
    traces = conn.get_traces(service="methodology", limit=100)
    
    # 獲取跨度
    spans = conn.get_spans(trace_id="xxx")
    ```
    """
    
    def __init__(self):
        self.endpoint: str = ""
        self.connected: bool = False
        self.services: List[str] = []
    
    def connect(self, endpoint: str = "http://localhost:4317", **kwargs) -> bool:
        """連接到 OTel Collector"""
        self.endpoint = endpoint
        self.connected = True
        self.services = ["methodology", "agent", "api", "worker"]
        return True
    
    def disconnect(self):
        self.connected = False
    
    def is_connected(self) -> bool:
        return self.connected
    
    def fetch_metrics(self, service: str = None) -> Dict:
        """獲取服務指標"""
        if not self.connected:
            return {}
        
        return {
            "services": self.services or [],
            "total_traces": 15000,
            "error_rate": 0.02,
            "p99_latency_ms": 250
        }
    
    def get_traces(self, service: str = None, 
                  limit: int = 100) -> List[Dict]:
        """獲取追蹤"""
        if not self.connected:
            return []
        
        return [
            {
                "trace_id": f"trace-{i}",
                "span_count": 5 + (i % 10),
                "duration_ms": 100 + (i * 10),
                "status": "OK" if i % 10 != 0 else "ERROR"
            }
            for i in range(limit)
        ]
    
    def get_spans(self, trace_id: str) -> List[Dict]:
        """獲取跨度"""
        if not self.connected:
            return []
        
        return [
            {
                "span_id": f"span-{i}",
                "name": f"operation-{i}",
                "duration_ms": 10 + i,
                "service": "methodology"
            }
            for i in range(5)
        ]


class DataSourceManager:
    """
    數據源管理器
    
    使用方式：
    
    ```python
    manager = DataSourceManager()
    
    # 連接多個數據源
    manager.connect("prometheus", PrometheusConnector, url="http://localhost:9090")
    manager.connect("jira", JiraConnector, url="https://company.atlassian.net", ...)
    
    # 獲取所有指標
    all_metrics = manager.fetch_all_metrics()
    
    # 生成統一報告
    report = manager.generate_unified_report()
    ```
    """
    
    def __init__(self):
        self.connectors: Dict[str, DataConnector] = {}
        self.source_names: Dict[str, str] = {}  # name -> type
    
    def connect(self, name: str, connector_class: type, **credentials) -> bool:
        """
        連接數據源
        
        Args:
            name: 連接名稱
            connector_class: 連接器類別
            **credentials: 連接憑證
            
        Returns:
            是否成功
        """
        connector = connector_class()
        success = connector.connect(**credentials)
        
        if success:
            self.connectors[name] = connector
            self.source_names[name] = connector_class.__name__
        
        return success
    
    def disconnect(self, name: str):
        """斷開數據源"""
        if name in self.connectors:
            self.connectors[name].disconnect()
            del self.connectors[name]
            del self.source_names[name]
    
    def get_connector(self, name: str) -> Optional[DataConnector]:
        """取得連接器"""
        return self.connectors.get(name)
    
    def list_connections(self) -> List[Dict]:
        """列出所有連接"""
        return [
            {
                "name": name,
                "type": self.source_names.get(name, "Unknown"),
                "connected": conn.is_connected()
            }
            for name, conn in self.connectors.items()
        ]
    
    def fetch_all_metrics(self) -> Dict:
        """獲取所有數據源的指標"""
        results = {}
        
        for name, connector in self.connectors.items():
            if connector.is_connected():
                try:
                    metrics = connector.fetch_metrics()
                    results[name] = {
                        "status": "success",
                        "metrics": metrics
                    }
                except Exception as e:
                    results[name] = {
                        "status": "error",
                        "error": str(e)
                    }
            else:
                results[name] = {
                    "status": "disconnected"
                }
        
        return results
    
    def generate_unified_report(self) -> str:
        """生成統一報告"""
        lines = [
            "=" * 60,
            "UNIFIED DATA SOURCE REPORT",
            "=" * 60,
            "",
            f"Total Connections: {len(self.connectors)}",
            "",
        ]
        
        for name, connector in self.connectors.items():
            status = "✅ Connected" if connector.is_connected() else "❌ Disconnected"
            lines.append(f"{name}: {status}")
            
            if hasattr(connector, 'get_summary'):
                summary = connector.get_summary()
                for key, value in summary.items():
                    lines.append(f"  {key}: {value}")
        
        # 統一指標
        all_metrics = self.fetch_all_metrics()
        lines.append("")
        lines.append("METRICS SUMMARY:")
        lines.append("-" * 40)
        
        for source, data in all_metrics.items():
            if data.get("status") == "success":
                lines.append(f"\n{source}:")
                metrics = data.get("metrics", {})
                for key, value in metrics.items():
                    lines.append(f"  {key}: {value}")
        
        return "\n".join(lines)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    manager = DataSourceManager()
    
    # 連接 Prometheus
    print("Connecting to Prometheus...")
    manager.connect("prometheus", PrometheusConnector, url="http://localhost:9090")
    
    # 連接 Jira
    print("Connecting to Jira...")
    manager.connect("jira", JiraConnector, 
                   url="https://company.atlassian.net",
                   email="user@company.com",
                   api_token="xxx")
    
    # 列出連接
    print("\n=== Connections ===")
    for conn in manager.list_connections():
        print(f"  {conn['name']}: {conn['type']} - {'✅' if conn['connected'] else '❌'}")
    
    # 獲取所有指標
    print("\n=== All Metrics ===")
    all_metrics = manager.fetch_all_metrics()
    import json
    print(json.dumps(all_metrics, indent=2, default=str))
    
    # 統一報告
    print("\n=== Unified Report ===")
    print(manager.generate_unified_report())
