#!/usr/bin/env python3
"""
LangGraph Migration Tool

提供：
- 從現行框架 → LangGraph 自動遷移
- 語法轉換
- 架構重構建議
- 測試迁移
"""

import ast
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Set
from enum import Enum


class NodeType(Enum):
    """節點類型"""
    AGENT = "agent"
    TOOL = "tool"
    CONDITION = "condition"
    LOOP = "loop"
    START = "start"
    END = "end"
    STATE_UPDATE = "state_update"
    LLM_CALL = "llm_call"


@dataclass
class ASTNode:
    """程式碼 AST 節點"""
    id: str
    node_type: NodeType
    name: str
    
    # 原始程式碼
    source: str = ""
    line_number: int = 0
    
    # 依賴
    dependencies: List[str] = field(default_factory=list)
    
    # LangGraph 等效
    langgraph_code: str = ""
    
    # 風險
    risk_level: str = "low"  # low, medium, high
    risk_reasons: List[str] = field(default_factory=list)


@dataclass
class MigrationResult:
    """遷移結果"""
    original_file: str
    output_file: str
    
    # 節點
    nodes: List[ASTNode] = field(default_factory=list)
    
    # 生成的程式碼
    generated_code: str = ""
    
    # 風險評估
    overall_risk: str = "medium"
    risk_summary: List[str] = field(default_factory=list)
    
    # 統計
    lines_analyzed: int = 0
    nodes_found: int = 0
    transformations: int = 0


@dataclass
class PatternMapping:
    """模式對應"""
    pattern_name: str
    original_pattern: str
    langgraph_pattern: str
    description: str = ""
    risk: str = "low"


class LangGraphMigrationTool:
    """LangGraph 遷移工具"""
    
    # 預設模式對應
    DEFAULT_MAPPINGS = [
        # State
        PatternMapping(
            "state_dict",
            r"state\s*=\s*\{([^}]+)\}",
            "from typing import TypedDict\n\nclass State(TypedDict):\n    \\1",
            "Convert state dict to TypedDict class"
        ),
        
        # Agent Definition
        PatternMapping(
            "agent_class",
            r"class\s+(\w+Agent)\s*\((.*?)\):",
            "def \\1(state: State) -> State:\n    \"\"\"Agent node\"\"\"\n    \\2",
            "Convert Agent class to agent function"
        ),
        
        # Tool Call
        PatternMapping(
            "tool_decorator",
            r"@tool\s*\n\s*def\s+(\w+)\s*\(([^)]*)\)\s*->\s*([^:]+):",
            "@tool\ndef \\1(\\2) -> \\3:",
            "Tool definitions are similar in LangGraph"
        ),
        
        # Conditional Branch
        PatternMapping(
            "if_condition",
            r"if\s+(.*?):\s*->\s*['\"](\w+)['\"]",
            "def should_\\2(state: State) -> str:\n    return \"\\2\" if \\1 else \"other\"",
            "Convert conditional to routing function"
        ),
        
        # LLM Call
        PatternMapping(
            "llm_call",
            r"llm\.call\s*\(\s*['\"](.*?)['\"]\s*\)",
            'messages = [HumanMessage(content="\\1")]\nresponse = llm.invoke(messages)',
            "Update LLM call syntax"
        ),
        
        # Message History
        PatternMapping(
            "message_history",
            r"message_history\s*=\s*\[\]",
            "messages: List[BaseMessage] = []",
            "Use LangGraph message list"
        ),
    ]
    
    def __init__(self):
        self.patterns: List[PatternMapping] = self.DEFAULT_MAPPINGS.copy()
        self.migration_results: List[MigrationResult] = []
    
    def analyze_file(self, file_path: str) -> MigrationResult:
        """分析檔案"""
        result = MigrationResult(
            original_file=file_path,
            output_file=file_path.replace(".py", "_migrated.py")
        )
        
        with open(file_path, 'r') as f:
            source = f.read()
        
        result.lines_analyzed = len(source.splitlines())
        
        # 解析 AST
        try:
            tree = ast.parse(source)
            result = self._analyze_ast(tree, source, result)
        except SyntaxError as e:
            result.risk_summary.append(f"Syntax error: {e}")
            result.overall_risk = "high"
        
        self.migration_results.append(result)
        return result
    
    def _analyze_ast(self, tree: ast.AST, source: str, result: MigrationResult) -> MigrationResult:
        """分析 AST"""
        
        class NodeVisitor(ast.NodeVisitor):
            def __init__(self, res):
                self.result = res
                self.current_class = None
            
            def visit_ClassDef(self, node):
                self.current_class = node.name
                
                # Agent class
                if "Agent" in node.name:
                    ast_node = ASTNode(
                        id=f"node_{len(self.result.nodes)}",
                        node_type=NodeType.AGENT,
                        name=node.name,
                        source=ast.get_source_segment(source, node) or "",
                        line_number=node.lineno
                    )
                    self.result.nodes.append(ast_node)
                
                self.generic_visit(node)
            
            def visit_FunctionDef(self, node):
                name = node.name
                
                # Tool
                if any(decorator.name == "tool" for decorator in node.decorator_list if isinstance(decorator, ast.Name)):
                    ast_node = ASTNode(
                        id=f"node_{len(self.result.nodes)}",
                        node_type=NodeType.TOOL,
                        name=name,
                        source=ast.get_source_segment(source, node) or "",
                        line_number=node.lineno
                    )
                    self.result.nodes.append(ast_node)
                
                # LLM call
                elif "llm" in name.lower() or "generate" in name.lower():
                    ast_node = ASTNode(
                        id=f"node_{len(self.result.nodes)}",
                        node_type=NodeType.LLM_CALL,
                        name=name,
                        source=ast.get_source_segment(source, node) or "",
                        line_number=node.lineno
                    )
                    self.result.nodes.append(ast_node)
                
                self.generic_visit(node)
            
            def visit_If(self, node):
                # Condition node
                ast_node = ASTNode(
                    id=f"node_{len(self.result.nodes)}",
                    node_type=NodeType.CONDITION,
                    name=f"condition_{node.lineno}",
                    source=ast.get_source_segment(source, node) or "",
                    line_number=node.lineno
                )
                self.result.nodes.append(ast_node)
                self.generic_visit(node)
        
        visitor = NodeVisitor(result)
        visitor.visit(tree)
        
        result.nodes_found = len(result.nodes)
        
        # 分析風險
        result = self._assess_risk(result)
        
        return result
    
    def _assess_risk(self, result: MigrationResult) -> MigrationResult:
        """評估遷移風險"""
        high_risk_count = 0
        medium_risk_count = 0
        
        for node in result.nodes:
            # 檢查風險因素
            if "while" in node.source or "for" in node.source:
                node.node_type = NodeType.LOOP
                node.risk_level = "high"
                node.risk_reasons.append("Contains loops - may need restructure")
                high_risk_count += 1
            
            if len(node.dependencies) > 3:
                node.risk_level = "medium"
                node.risk_reasons.append(f"High dependencies ({len(node.dependencies)})")
                medium_risk_count += 1
            
            # 特殊關鍵字
            risky_keywords = ["global", "yield", "async", "await"]
            for keyword in risky_keywords:
                if keyword in node.source:
                    node.risk_reasons.append(f"Contains '{keyword}'")
                    if node.risk_level != "high":
                        node.risk_level = "medium"
        
        # 整體風險
        if high_risk_count > 0:
            result.overall_risk = "high"
        elif medium_risk_count > 0:
            result.overall_risk = "medium"
        else:
            result.overall_risk = "low"
        
        return result
    
    def generate_langgraph_code(self, result: MigrationResult) -> str:
        """生成 LangGraph 代碼"""
        lines = []
        lines.append("# Migrated to LangGraph")
        lines.append("# Original file: " + result.original_file)
        lines.append("")
        
        # Imports
        lines.append("from typing import TypedDict, Annotated, List")
        lines.append("from langgraph.graph import StateGraph, END, START")
        lines.append("from langchain_openai import ChatOpenAI")
        lines.append("from langchain_core.messages import HumanMessage, BaseMessage")
        lines.append("")
        
        # State definition
        lines.append("# State Definition")
        lines.append("class State(TypedDict):")
        lines.append("    messages: List[BaseMessage]")
        lines.append("    current_node: str")
        lines.append("    context: dict")
        lines.append("")
        
        # Generate nodes
        lines.append("# Node Functions")
        for node in result.nodes:
            if node.node_type == NodeType.AGENT:
                lines.append(f"\ndef {node.name.lower()}_node(state: State) -> State:")
                lines.append(f'    """Agent node: {node.name}"""')
                lines.append("    # TODO: Implement agent logic")
                lines.append("    return state")
                result.transformations += 1
            
            elif node.node_type == NodeType.TOOL:
                lines.append(f"\ndef {node.name}_tool(state: State) -> State:")
                lines.append(f'    """Tool: {node.name}"""')
                lines.append("    # TODO: Implement tool")
                lines.append("    return state")
                result.transformations += 1
            
            elif node.node_type == NodeType.LLM_CALL:
                lines.append(f"\ndef {node.name}_node(state: State) -> State:")
                lines.append(f'    """LLM call: {node.name}"""')
                lines.append("    llm = ChatOpenAI(model='gpt-4')")
                lines.append("    response = llm.invoke(state['messages'])")
                lines.append("    state['messages'].append(response)")
                lines.append("    return state")
                result.transformations += 1
        
        # Build graph
        lines.append("")
        lines.append("# Build Graph")
        lines.append("def build_graph():")
        lines.append("    graph = StateGraph(State)")
        lines.append("")
        lines.append("    # Add nodes")
        for node in result.nodes:
            node_name = f"{node.name.lower()}_node" if node.node_type != NodeType.TOOL else f"{node.name}_tool"
            lines.append(f'    graph.add_node("{node.name}", {node_name})')
        lines.append("")
        lines.append("    # Add edges")
        lines.append("    graph.add_edge(START, \"entry\")")
        
        for node in result.nodes:
            lines.append(f'    graph.add_edge("{node.name}", END)')
        
        lines.append("")
        lines.append("    return graph.compile()")
        
        result.generated_code = "\n".join(lines)
        return result.generated_code
    
    def migrate_file(self, file_path: str, output_path: str = None) -> MigrationResult:
        """遷移檔案"""
        result = self.analyze_file(file_path)
        
        if output_path:
            result.output_file = output_path
        
        # 生成代碼
        self.generate_langgraph_code(result)
        
        # 寫出
        with open(result.output_file, 'w') as f:
            f.write(result.generated_code)
        
        return result
    
    def generate_report(self, result: MigrationResult) -> str:
        """產生遷移報告"""
        lines = []
        lines.append("╔" + "═" * 70 + "╗")
        lines.append("║" + f" 🔄 Migration Report: {result.original_file} ".center(70) + "║")
        lines.append("╚" + "═" * 70 + "╝")
        lines.append("")
        
        # 基本統計
        lines.append("## 📊 Statistics")
        lines.append(f"- **Lines Analyzed**: {result.lines_analyzed}")
        lines.append(f"- **Nodes Found**: {result.nodes_found}")
        lines.append(f"- **Transformations**: {result.transformations}")
        lines.append(f"- **Overall Risk**: {result.overall_risk.upper()}")
        lines.append("")
        
        # 節點列表
        if result.nodes:
            lines.append("## 📋 Nodes")
            lines.append("")
            lines.append("| Node | Type | Risk | Line |")
            lines.append("|------|------|------|------|")
            for node in result.nodes:
                risk_icon = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(node.risk_level, "⚪")
                lines.append(f"| {node.name} | {node.node_type.value} | {risk_icon} | {node.line_number} |")
            lines.append("")
        
        # 風險摘要
        if result.risk_summary:
            lines.append("## ⚠️ Risk Summary")
            for risk in result.risk_summary:
                lines.append(f"- {risk}")
            lines.append("")
        
        # 建議
        lines.append("## 💡 Recommendations")
        
        if result.overall_risk == "high":
            lines.append("- ⚠️ High risk migration - manual review required")
            lines.append("- Consider breaking into smaller components")
            lines.append("- Test thoroughly after migration")
        elif result.overall_risk == "medium":
            lines.append("- 🟡 Medium risk - some manual work may be needed")
            lines.append("- Review generated code before running")
        else:
            lines.append("- 🟢 Low risk - should migrate cleanly")
        
        lines.append("")
        lines.append(f"**Output File**: `{result.output_file}`")
        lines.append("")
        
        return "\n".join(lines)
    
    def add_pattern(self, mapping: PatternMapping):
        """新增遷移模式"""
        self.patterns.append(mapping)
    
    def validate_langgraph_syntax(self, code: str) -> Tuple[bool, str]:
        """驗證 LangGraph 語法"""
        try:
            ast.parse(code)
            return True, "Valid Python syntax"
        except SyntaxError as e:
            return False, f"Syntax error: {e}"

    def export_to_crewai(self, langgraph_file: str, output_file: str = None) -> MigrationResult:
        """
        將 LangGraph 檔案匯出為 CrewAI 格式

        Args:
            langgraph_file: LangGraph .py 檔案路徑
            output_file: 輸出檔案路徑 (預設: <原檔名>_migrated_to_crewai.py)

        Returns:
            MigrationResult
        """
        result = MigrationResult(
            original_file=langgraph_file,
            output_file=output_file or langgraph_file.replace(".py", "_migrated_to_crewai.py")
        )

        try:
            with open(langgraph_file, 'r') as f:
                source = f.read()

            result.lines_analyzed = len(source.splitlines())

            # 解析 LangGraph 節點
            tree = ast.parse(source)
            result = self._analyze_ast(tree, source, result)

            # 生成 CrewAI 代碼
            crewai_code = self._generate_crewai_code(source, result)

            with open(result.output_file, 'w') as f:
                f.write(crewai_code)

            result.generated_code = crewai_code

        except Exception as e:
            result.risk_summary.append(f"Export error: {e}")
            result.overall_risk = "high"

        self.migration_results.append(result)
        return result

    def _generate_crewai_code(self, source: str, result: MigrationResult) -> str:
        """生成 CrewAI 代碼"""
        lines = []
        lines.append("# Exported from LangGraph to CrewAI")
        lines.append("# Generated by LangGraphMigrationTool")
        lines.append("")
        lines.append("from crewai import Agent, Task, Crew, Process")
        lines.append("from langchain_openai import ChatOpenAI")
        lines.append("")

        # 提取節點
        node_pattern = r'def\s+(\w+)\s*\([^)]*state[^)]*\)\s*(?:->\s*State)?:'
        nodes = re.findall(node_pattern, source)

        # 提取 state 定義
        state_pattern = r'class\s+State\s*\(TypedDict\):\s*\n((?:.*\n)*?)(?=\nclass|\ndef|\Z)'
        state_match = re.search(state_pattern, source)

        # 生成 agents
        lines.append("# Agents")
        for node in nodes:
            agent_name = node.replace('_node', '').replace('_agent', '').title().replace('_', '')
            lines.append(f"{agent_name.lower()}_agent = Agent(")
            lines.append(f'    role="{agent_name} Agent",')
            lines.append(f'    goal="Complete the assigned {agent_name} task",')
            lines.append(f'    backstory="You are an experienced {agent_name} agent",')
            lines.append(f'    verbose=True,')
            lines.append(f'    llm=ChatOpenAI(model="gpt-4")')
            lines.append(")")
            lines.append("")

        if not nodes:
            # 預設 agent
            lines.append("default_agent = Agent(")
            lines.append('    role="Default Agent",')
            lines.append('    goal="Complete the assigned task",')
            lines.append('    backstory="You are a helpful AI agent",')
            lines.append('    verbose=True,')
            lines.append('    llm=ChatOpenAI(model="gpt-4")')
            lines.append(")")
            lines.append("")

        # 生成 tasks
        lines.append("# Tasks")
        agent_refs = [n.replace('_node', '').replace('_agent', '').lower() + '_agent' for n in nodes] or ["default_agent"]
        for i, agent_ref in enumerate(agent_refs, 1):
            lines.append(f"task{i} = Task(")
            lines.append(f'    description="Execute the {agent_ref.replace("_agent", "")} workflow",')
            lines.append(f'    agent={agent_ref},')
            lines.append(f'    expected_output="Task completion result"')
            lines.append(")")
            lines.append("")

        # 生成 crew
        lines.append("# Crew")
        lines.append("crew = Crew(")
        lines.append(f"    agents=[{', '.join(agent_refs)}],")
        lines.append("    tasks=[task1],")
        lines.append("    process=Process.sequential")
        lines.append(")")
        lines.append("")
        lines.append("# Kickoff")
        lines.append("result = crew.kickoff()")
        lines.append("print(result)")

        result.transformations = len(nodes) if nodes else 1
        return "\n".join(lines)


# ==================== Quick Migration Helpers ====================

def quick_migrate_agent(agent_code: str) -> str:
    """快速遷移 Agent 為 LangGraph 格式"""
    
    # Extract state
    state_match = re.search(r'state\s*=\s*\{([^}]+)\}', agent_code)
    state_fields = state_match.group(1) if state_match else "messages: list"
    
    # Generate
    result = f'''
from typing import TypedDict, List
from langgraph.graph import StateGraph, END, START

class State(TypedDict):
    {state_fields}

def agent_node(state: State) -> State:
    """Migrated agent"""
    # TODO: Add agent logic
    return state

def build_agent_graph():
    graph = StateGraph(State)
    graph.add_node("agent", agent_node)
    graph.add_edge(START, "agent")
    graph.add_edge("agent", END)
    return graph.compile()

# Usage
graph = build_agent_graph()
'''
    return result


def analyze_complexity(code: str) -> Dict[str, Any]:
    """分析程式碼複雜度"""
    try:
        tree = ast.parse(code)
    except:
        return {"error": "Cannot parse code"}
    
    class ComplexityVisitor(ast.NodeVisitor):
        def __init__(self):
            self.functions = 0
            self.classes = 0
            self.conditionals = 0
            self.loops = 0
            self.try_blocks = 0
        
        def visit_FunctionDef(self, node):
            self.functions += 1
        
        def visit_ClassDef(self, node):
            self.classes += 1
        
        def visit_If(self, node):
            self.conditionals += 1
        
        def visit_For(self, node):
            self.loops += 1
        
        def visit_While(self, node):
            self.loops += 1
        
        def visit_Try(self, node):
            self.try_blocks += 1
    
    visitor = ComplexityVisitor()
    visitor.visit(tree)
    
    complexity_score = (
        visitor.functions * 1 +
        visitor.classes * 2 +
        visitor.conditionals * 1.5 +
        visitor.loops * 2 +
        visitor.try_blocks * 1.5
    )
    
    return {
        "functions": visitor.functions,
        "classes": visitor.classes,
        "conditionals": visitor.conditionals,
        "loops": visitor.loops,
        "try_blocks": visitor.try_blocks,
        "complexity_score": complexity_score,
        "complexity_level": "high" if complexity_score > 20 else "medium" if complexity_score > 10 else "low"
    }


# ==================== Main ====================

if __name__ == "__main__":
    pass # Removed print-debug
    pass # Removed print-debug
    pass # Removed print-debug
    
    # 建立工具
    tool = LangGraphMigrationTool()
    
    # 測試複雜度分析
    test_code = '''
class MyAgent:
    def __init__(self):
        self.state = {"messages": []}
    
    def process(self, input_text):
        if len(input_text) > 100:
            return self.summarize(input_text)
        else:
            return input_text
    
    def summarize(self, text):
        for i in range(3):
            pass # Removed print-debug
        return text[:100]
'''
    
    pass # Removed print-debug
    complexity = analyze_complexity(test_code)
    for k, v in complexity.items():
        pass # Removed print-debug
    pass # Removed print-debug
    
    # 測試快速遷移
    pass # Removed print-debug
    agent_code = '''
state = {
    "messages": [],
    "context": {},
    "current_step": 0
}
'''
    migrated = quick_migrate_agent(agent_code)
    pass # Removed print-debug
    pass # Removed print-debug
    
    # 顯示預設模式
    pass # Removed print-debug
    for i, p in enumerate(tool.patterns[:5], 1):
        pass # Removed print-debug
