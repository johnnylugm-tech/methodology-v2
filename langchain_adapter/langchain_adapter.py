"""
LangChain Adapter for methodology-v2

Provides migration tools and wrappers for LangChain ecosystem integration.
"""

import re
import ast
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MigrationResult:
    """Migration result"""
    original_code: str
    migrated_code: str
    warnings: List[str]
    changes: List[str]


class LLMWrapper:
    """Wrapper for LangChain LLMs to work with methodology-v2"""
    
    def __init__(self, langchain_llm):
        self.llm = langchain_llm
    
    def invoke(self, prompt: str) -> str:
        """Invoke LLM with prompt"""
        try:
            return self.llm.invoke(prompt)
        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            return f"Error: {str(e)}"
    
    def __call__(self, prompt: str) -> str:
        return self.invoke(prompt)


class ToolAdapter:
    """Adapter for LangChain tools"""
    
    def convert_tools(self, langchain_tools) -> List[Dict]:
        """Convert LangChain tools to methodology-v2 format"""
        converted = []
        
        for tool in langchain_tools:
            converted.append({
                "name": getattr(tool, "name", "unknown"),
                "description": getattr(tool, "description", ""),
                "args": getattr(tool, "args_schema", {}),
            })
        
        logger.info(f"Converted {len(converted)} tools")
        return converted


class ChainMigrator:
    """Migrate LangChain chains to methodology-v2"""
    
    def __init__(self):
        self.replacements = {
            "from langchain": "# Migrated to methodology-v2\nfrom methodology import",
            "ChatOpenAI": "SmartRouter",
            "ChatAnthropic": "SmartRouter",
            "LLMChain": "Crew",
            "ConversationChain": "Crew",
        }
    
    def migrate(self, code: str) -> MigrationResult:
        """Migrate LangChain code to methodology-v2"""
        warnings = []
        changes = []
        
        # Apply replacements
        migrated = code
        for old, new in self.replacements.items():
            if old in migrated:
                migrated = migrated.replace(old, new)
                changes.append(f"Replaced {old} -> {new}")
        
        # Detect unmigrated patterns
        if "langchain" in migrated.lower():
            warnings.append("Some LangChain references may remain")
        
        # Add methodology-v2 imports
        if "from methodology import" not in migrated:
            migrated = self._add_imports(migrated)
            changes.append("Added methodology-v2 imports")
        
        return MigrationResult(
            original_code=code,
            migrated_code=migrated,
            warnings=warnings,
            changes=changes
        )
    
    def _add_imports(self, code: str) -> str:
        """Add necessary imports"""
        imports = """import sys
sys.path.insert(0, '/workspace/methodology-v2')
from methodology import SmartRouter, Crew, QualityGate

"""
        return imports + code
    
    def migrate_file(self, input_path: str, output_path: str):
        """Migrate a file"""
        with open(input_path, "r") as f:
            code = f.read()
        
        result = self.migrate(code)
        
        with open(output_path, "w") as f:
            f.write(result.migrated_code)
        
        logger.info(f"Migrated {input_path} -> {output_path}")
        logger.info(f"Changes: {len(result.changes)}")
        
        return result


class MemoryBridge:
    """Bridge LangChain memory to methodology-v2 storage"""
    
    def migrate_memory(self, langchain_memory) -> Dict:
        """Convert LangChain memory to methodology-v2 format"""
        # Extract messages if possible
        messages = []
        
        try:
            if hasattr(langchain_memory, "chat_memory"):
                for msg in langchain_memory.chat_memory.messages:
                    messages.append({
                        "type": type(msg).__name__,
                        "content": getattr(msg, "content", ""),
                    })
        except Exception as e:
            logger.warning(f"Could not extract messages: {e}")
        
        return {
            "type": "migrated_memory",
            "messages": messages,
            "storage": "Use methodology-v2 Storage module"
        }


class LangChainAdapter:
    """
    Main LangChain Adapter for methodology-v2.
    
    Usage:
        adapter = LangChainAdapter()
        result = adapter.migrate_chain("old_code.py")
    """
    
    def __init__(self):
        self.chain_migrator = ChainMigrator()
        self.tool_adapter = ToolAdapter()
        self.memory_bridge = MemoryBridge()
        logger.info("LangChainAdapter initialized")
    
    def migrate_chain(self, code: str) -> MigrationResult:
        """Migrate LangChain chain code"""
        return self.chain_migrator.migrate(code)
    
    def wrap_llm(self, langchain_llm) -> LLMWrapper:
        """Wrap LangChain LLM"""
        return LLMWrapper(langchain_llm)
    
    def convert_tools(self, tools) -> List[Dict]:
        """Convert LangChain tools"""
        return self.tool_adapter.convert_tools(tools)
    
    def migrate_memory(self, memory) -> Dict:
        """Migrate LangChain memory"""
        return self.memory_bridge.migrate_memory(memory)


# CLI entry point
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="LangChain Adapter")
    parser.add_argument("command", choices=["analyze", "migrate", "convert-tools"])
    parser.add_argument("--input", required=True, help="Input file")
    parser.add_argument("--output", help="Output file")
    
    args = parser.parse_args()
    
    adapter = LangChainAdapter()
    
    if args.command == "analyze":
        with open(args.input, "r") as f:
            code = f.read()
        
        # Simple analysis
        print("Analysis:")
        print(f"  - Lines: {len(code.split(chr(10)))}")
        print(f"  - LangChain imports: {code.count('from langchain')}")
        print(f"  - LLM calls: {code.count('llm.')}")
    
    elif args.command == "migrate":
        result = adapter.chain_migrator.migrate_file(
            args.input,
            args.output or args.input.replace(".py", "_migrated.py")
        )
        print(f"Migration complete!")
        print(f"  - Changes: {len(result.changes)}")
        for change in result.changes:
            print(f"    {change}")
        if result.warnings:
            print(f"  - Warnings: {result.warnings}")
