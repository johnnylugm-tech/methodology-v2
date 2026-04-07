#!/usr/bin/env python3
"""
Extensions - 整合層

將所有 Extensions 整合到核心流程
"""

from typing import Dict, List, Optional, Any


class Extensions:
    """
    Extensions 整合管理器
    
    提供對所有 Extensions 的統一訪問介面
    """
    
    def __init__(self, core=None):
        self.core = core
        self._initialized = {}
    
    # ==================== MCP Adapter ====================
    
    @property
    def mcp(self):
        """MCP 企業服務整合"""
        if "mcp" not in self._initialized:
            from .mcp_adapter import MCPAdapter
            self._initialized["mcp"] = MCPAdapter()
        return self._initialized["mcp"]
    
    def connect_service(self, service: str, **credentials):
        """連接企業服務"""
        return self.mcp.connect(service, **credentials)
    
    def execute_across_services(self, task: str):
        """跨服務執行"""
        return self.mcp.execute(task)
    
    # ==================== Cost Optimizer ====================
    
    @property
    def cost(self):
        """成本優化"""
        if "cost" not in self._initialized:
            # 使用 core 的 router
            if self.core and hasattr(self.core, 'tasks'):
                # 嘗試從 core 获取
                pass
            from .cost_optimizer import CostOptimizer
            self._initialized["cost"] = CostOptimizer()
        return self._initialized["cost"]
    
    def track_cost(self, model: str, input_tokens: int, output_tokens: int):
        """記錄成本"""
        return self.cost.track(model=model, 
                            prompt_tokens=input_tokens,
                            completion_tokens=output_tokens)
    
    def get_cost_report(self):
        """取得成本報告"""
        return self.cost.get_report()
    
    # ==================== Vertical Templates ====================
    
    @property
    def templates(self):
        """垂直領域模板"""
        if "templates" not in self._initialized:
            from .vertical_templates import CustomerServiceAgent, LegalAgent
            self._initialized["templates"] = {
                "customer_service": CustomerServiceAgent,
                "legal": LegalAgent,
            }
        return self._initialized["templates"]
    
    def create_customer_service_agent(self, **kwargs):
        """建立客服 Agent"""
        from .vertical_templates import CustomerServiceAgent
        return CustomerServiceAgent(**kwargs)
    
    def create_legal_agent(self, **kwargs):
        """建立法律 Agent"""
        from .vertical_templates import LegalAgent
        return LegalAgent(**kwargs)
    
    # ==================== Security Audit ====================
    
    @property
    def security(self):
        """安全審計"""
        if "security" not in self._initialized:
            from .security_audit import SecurityAuditor
            self._initialized["security"] = SecurityAuditor()
        return self._initialized["security"]
    
    def scan_security(self, target: str):
        """安全掃描"""
        return self.security.scan(target)
    
    def check_api_keys(self, code: str):
        """檢查 API Key 洩漏"""
        return self.security.scan_code(code)
    
    # ==================== LangChain Adapter ====================
    
    @property
    def langchain(self):
        """LangChain 遷移"""
        if "langchain" not in self._initialized:
            from .langchain_adapter import ChainMigrator
            self._initialized["langchain"] = ChainMigrator()
        return self._initialized["langchain"]
    
    def migrate_chain(self, file_path: str):
        """遷移 LangChain 程式碼"""
        return self.langchain.migrate_file(file_path)
    
    # ==================== Local Deployment ====================
    
    @property
    def local_deploy(self):
        """本地部署"""
        if "local" not in self._initialized:
            from .local_deployment import LocalDeploy
            self._initialized["local"] = LocalDeploy()
        return self._initialized["local"]
    
    def deploy_local(self):
        """本地部署"""
        return self.local_deploy.deploy()
    
    # ==================== Workflow Visualizer ====================
    
    @property
    def visualize(self):
        """工作流視覺化"""
        if "visualize" not in self._initialized:
            from .workflow_visualizer import WorkflowVisualizer
            self._initialized["visualize"] = WorkflowVisualizer()
        return self._initialized["visualize"]
    
    def generate_diagram(self, workflow):
        """生成工作流圖表"""
        return self.visualize.generate_diagram_from_workflow(workflow)


# ============================================================================
# 工廠函數
# ============================================================================

def create_extensions(core=None) -> Extensions:
    """建立 Extensions 管理器"""
    return Extensions(core=core)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("=== Extensions Demo ===\n")
    
    ext = create_extensions()
    
    # MCP
    print("1. MCP Services: Available services")
    # ext.connect_service("slack", token="xxx")
    
    # Cost
    print("\n2. Cost Tracking")
    # ext.track_cost("gpt-4o", 1000, 500)
    
    # Security
    print("\n3. Security Audit")
    # report = ext.scan_security("src/code.py")
    
    print("\nExtensions ready!")
