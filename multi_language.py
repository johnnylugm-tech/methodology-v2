#!/usr/bin/env python3
"""
Multi-Language Support - 多語言/多平台支援

支援 Python、JavaScript、TypeScript、Go、Rust 等
"""

import os
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


class Language(Enum):
    """程式語言"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    JAVA = "java"
    CSHARP = "csharp"
    CPP = "cpp"
    UNKNOWN = "unknown"


@dataclass
class LanguageConfig:
    """語言配置"""
    language: Language
    file_extensions: List[str]
    linter: str
    formatter: str
    test_framework: str
    package_manager: str


class MultiLanguageSupport:
    """多語言支援管理器"""
    
    # 語言配置
    LANG_CONFIGS = {
        Language.PYTHON: LanguageConfig(
            language=Language.PYTHON,
            file_extensions=[".py"],
            linter="pylint",
            formatter="black",
            test_framework="pytest",
            package_manager="pip"
        ),
        Language.JAVASCRIPT: LanguageConfig(
            language=Language.JAVASCRIPT,
            file_extensions=[".js", ".mjs"],
            linter="eslint",
            formatter="prettier",
            test_framework="jest",
            package_manager="npm"
        ),
        Language.TYPESCRIPT: LanguageConfig(
            language=Language.TYPESCRIPT,
            file_extensions=[".ts", ".tsx"],
            linter="eslint",
            formatter="prettier",
            test_framework="jest",
            package_manager="npm"
        ),
        Language.GO: LanguageConfig(
            language=Language.GO,
            file_extensions=[".go"],
            linter="golangci-lint",
            formatter="gofmt",
            test_framework="testing",
            package_manager="go mod"
        ),
        Language.RUST: LanguageConfig(
            language=Language.RUST,
            file_extensions=[".rs"],
            linter="clippy",
            formatter="rustfmt",
            test_framework="cargo test",
            package_manager="cargo"
        ),
        Language.JAVA: LanguageConfig(
            language=Language.JAVA,
            file_extensions=[".java"],
            linter="checkstyle",
            formatter="google-java-format",
            test_framework="junit",
            package_manager="maven"
        ),
    }
    
    def __init__(self):
        self.detected_languages: Dict[str, Language] = {}
        self.project_root = "."
    
    def detect_language(self, file_path: str) -> Language:
        """
        檢測檔案語言
        
        Args:
            file_path: 檔案路徑
            
        Returns:
            語言類型
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        for lang, config in self.LANG_CONFIGS.items():
            if ext in config.file_extensions:
                return lang
        
        return Language.UNKNOWN
    
    def detect_project_languages(self, root_path: str = ".") -> List[Tuple[Language, int]]:
        """
        檢測專案使用的所有語言
        
        Args:
            root_path: 專案根目錄
            
        Returns:
            [(語言, 檔案數量)]
        """
        language_counts: Dict[Language, int] = {}
        
        for root, dirs, files in os.walk(root_path):
            # 跳過常見的無關目錄
            dirs[:] = [d for d in dirs if d not in [
                'node_modules', '.git', '__pycache__', 
                'venv', '.venv', 'target', 'build'
            ]]
            
            for file in files:
                lang = self.detect_language(file)
                if lang != Language.UNKNOWN:
                    language_counts[lang] = language_counts.get(lang, 0) + 1
        
        # 按數量排序
        sorted_langs = sorted(
            language_counts.items(),
            key=lambda x: -x[1]
        )
        
        return sorted_langs
    
    def get_language_config(self, language: Language) -> LanguageConfig:
        """取得語言配置"""
        return self.LANG_CONFIGS.get(language)
    
    def generate_linter_config(self, language: Language) -> str:
        """生成 Linter 配置"""
        if language == Language.PYTHON:
            return """[MASTER]
ignore=E501,W503,E203
max-line-length=100
"""
        elif language == Language.JAVASCRIPT:
            return """{
  "extends": ["eslint:recommended"],
  "rules": {
    "no-unused-vars": "warn",
    "no-console": "off"
  }
}
"""
        elif language == Language.TYPESCRIPT:
            return """{
  "extends": ["eslint:recommended", "plugin:@typescript-eslint/recommended"],
  "rules": {
    "@typescript-eslint/no-unused-vars": "warn"
  }
}
"""
        elif language == Language.GO:
            return """linters-settings:
  golint:
    min-confidence: 0
  gocyclo:
    min-complexity: 15
"""
        elif language == Language.RUST:
            return """[clippy]
cognitive_complexity = 15
"""
        return ""
    
    def generate_test_command(self, language: Language, file_path: str = None) -> str:
        """生成測試命令"""
        config = self.LANG_CONFIGS.get(language)
        if not config:
            return ""
        
        if language == Language.PYTHON:
            return f"pytest {file_path or 'tests/'}"
        elif language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return f"npm test {file_path or ''}"
        elif language == Language.GO:
            return f"go test {file_path or './...'}"
        elif language == Language.RUST:
            return f"cargo test {file_path or ''}"
        
        return ""
    
    def generate_build_command(self, language: Language) -> str:
        """生成建置命令"""
        if language == Language.PYTHON:
            return "python setup.py build"
        elif language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return "npm run build"
        elif language == Language.GO:
            return "go build ./..."
        elif language == Language.RUST:
            return "cargo build --release"
        
        return ""
    
    def route_to_agent(self, task: str, languages: List[Language] = None) -> Dict:
        """
        根據任務路由到合適的 Agent
        
        Args:
            task: 任務描述
            languages: 可用語言列表
            
        Returns:
            路由建議
        """
        task_lower = task.lower()
        
        # 根據關鍵詞判斷語言
        language_scores: Dict[Language, float] = {}
        
        keywords = {
            Language.PYTHON: ["python", "django", "flask", "fastapi", "script", "ml", "ai", "data"],
            Language.JAVASCRIPT: ["javascript", "node", "react", "vue", "frontend", "web"],
            Language.TYPESCRIPT: ["typescript", "angular", "nextjs", "nestjs"],
            Language.GO: ["golang", "go ", "microservice", "concurrent", "kubernetes"],
            Language.RUST: ["rust", "performance", "system", "embedded", "wasm"],
            Language.JAVA: ["java", "spring", "backend", "enterprise"],
        }
        
        for lang, kws in keywords.items():
            if languages and lang not in languages:
                continue
            
            score = sum(1 for kw in kws if kw in task_lower)
            if score > 0:
                language_scores[lang] = score
        
        if not language_scores:
            # 預設 Python
            recommended = Language.PYTHON
            confidence = 0.5
        else:
            recommended = max(language_scores, key=language_scores.get)
            max_score = language_scores[recommended]
            confidence = min(1.0, max_score / 3)
        
        return {
            "recommended_language": recommended.value,
            "confidence": confidence,
            "alternative_languages": [
                lang.value for lang, score in sorted(
                    language_scores.items(),
                    key=lambda x: -x[1]
                ) if lang != recommended
            ][:3],
            "agent_type": self._get_agent_type(recommended),
        }
    
    def _get_agent_type(self, language: Language) -> str:
        """根據語言獲取 Agent 類型"""
        agent_map = {
            Language.PYTHON: "developer-python",
            Language.JAVASCRIPT: "developer-js",
            Language.TYPESCRIPT: "developer-ts",
            Language.GO: "developer-go",
            Language.RUST: "developer-rust",
            Language.JAVA: "developer-java",
        }
        return agent_map.get(language, "developer")
    
    def generate_polyglot_project(self, name: str) -> Dict[str, str]:
        """
        生成多語言專案結構
        
        Args:
            name: 專案名稱
            
        Returns:
            {檔案路徑: 內容}
        """
        return {
            f"{name}/README.md": f"# {name}\n\nMulti-language project\n",
            f"{name}/Makefile": f""".PHONY: install test lint

install:
\tpip install -e .
\tnpm install

test:
\tpytest tests/
\tnpm test

lint:
\tpylint src/
\tnpm run lint
""",
            f"{name}/pyproject.toml": """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "project"
version = "0.1.0"
requires-python = ">=3.8"
""",
            f"{name}/package.json": """{
  "name": "project",
  "version": "0.1.0",
  "scripts": {
    "test": "jest",
    "lint": "eslint src/"
  }
}
""",
        }


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    ml = MultiLanguageSupport()
    
    print("=== Detect Language ===")
    test_files = ["test.py", "app.js", "main.ts", "server.go", "lib.rs"]
    for f in test_files:
        lang = ml.detect_language(f)
        print(f"{f} -> {lang.value}")
    
    print("\n=== Route to Agent ===")
    tasks = [
        "build a Python API with FastAPI",
        "create a React frontend component",
        "develop a Go microservice",
        "implement machine learning model",
    ]
    for task in tasks:
        route = ml.route_to_agent(task)
        print(f"\nTask: {task}")
        print(f"  -> Language: {route['recommended_language']}")
        print(f"  -> Agent: {route['agent_type']}")
        print(f"  -> Confidence: {route['confidence']:.1%}")
    
    print("\n=== Test Command ===")
    for lang in [Language.PYTHON, Language.JAVASCRIPT, Language.GO]:
        cmd = ml.generate_test_command(lang)
        print(f"{lang.value}: {cmd}")
