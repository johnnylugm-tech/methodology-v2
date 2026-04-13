#!/usr/bin/env python3
"""
IMPLEMENTATION Constitution Checker
==================================
檢查 Implementation 文檔是否符合 Constitution 原則

Phase 3: 實作與整合

原則檢查:
1. 正確性 100% - 代碼符合 SAD、模組職責清晰
2. 安全性 100% - 安全實踐到位
3. 可維護性 > 80% - 代碼可讀、文件完整

Usage:
    from implementation_constitution_checker import check_implementation_constitution
    result = check_implementation_constitution("/path/to/src")
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from . import (
    CONSTITUTION_THRESHOLDS,
    ConstitutionCheckResult
)

@dataclass
class ImplementationChecklist:
    """Implementation 檢查清單"""
    # 正確性
    code_matches_sad: bool = False
    module_responsibilities_clear: bool = False
    error_handling_complete: bool = False
    
    # 安全性
    input_validation: bool = False
    secure_dependencies: bool = False
    secrets_management: bool = False
    
    # 可維護性
    code_documentation: bool = False
    clear_naming: bool = False
    test_coverage: bool = False
    
    # 其他
    version_info: bool = False

def check_implementation_constitution(
    path: str,
    allow_missing: bool = False  # v6.56: preflight 時允許還沒有 implementation
) -> ConstitutionCheckResult:
    """執行 Implementation Constitution 檢查
    
    Args:
        path: 專案根目錄路徑
        allow_missing: 若為 True，當沒有代碼檔案時返回 pass（用於 Pre-flight）
                       因為 Phase 3 的 Pre-flight 檢查時，implementation 還沒產生
    """
    path_obj = Path(path)
    
    violations = []
    recommendations = []
    checklist = ImplementationChecklist()
    
    # 檢查代碼檔案
    code_files = list(path_obj.rglob("*.py")) + list(path_obj.rglob("*.js"))
    
    # === v6.56 FIX: Pre-flight 時 allow_missing ===
    if allow_missing and not code_files:
        return ConstitutionCheckResult(
            check_type="implementation",
            passed=True,                    # ✅ 不阻擋
            score=100.0,
            violations=[],
            details={
                "status": "no_implementation_yet",
                "reason": "Pre-flight: Phase 3 implementation not generated yet"
            },
            recommendations=["Implementation will be generated during Phase 3 execution"]
        )
    
    # 1. 檢查 README 或文件
    has_docs = any(path_obj.glob("README*")) or any(path_obj.glob("*.md"))
    checklist.code_documentation = has_docs
    
    # 2. 檢查錯誤處理
    error_handling_patterns = ["try:", "except:", "raise", "catch"]
    has_error_handling = False
    for f in code_files[:10]:  # 抽樣檢查
        try:
            content = f.read_text(errors="ignore")
            if any(p in content for p in error_handling_patterns):
                has_error_handling = True
                break
        except Exception:
            continue
    checklist.error_handling_complete = has_error_handling
    
    # 3. 檢查測試覆蓋
    test_files = list(path_obj.rglob("test_*.py")) + list(path_obj.rglob("*_test.py"))
    checklist.test_coverage = len(test_files) > 0
    
    # 4. Security 檢查（v7.97: Phase 3 implementation security）
    security_keywords = {
        "input_validation": ["validate", "sanitize", "InputValidator", "input_validation", "輸入驗證"],
        "secure_dependencies": ["requirements.txt", "package.json", "pip install", "npm install", "dependency"],
        "secrets_management": ["getenv", "os.environ", "secret", "API_KEY", "password", "密鑰", "密碼"],
        "auth_implementation": ["AuthMiddleware", "authenticate", "login", "登入", "認證"],
        "error_handling_security": ["try:", "except:", "raise", "catch", "finally:"],
    }
    
    # 讀取代碼內容進行關鍵字檢查
    code_content = ""
    for f in code_files[:10]:
        try:
            code_content += f.read_text(errors="ignore") + "\n"
        except:
            continue
    
    for check_name, keywords in security_keywords.items():
        if any(kw.lower() in code_content.lower() for kw in keywords):
            setattr(checklist, check_name, True)
    
    # 評分
    checks = [
        checklist.code_documentation,
        checklist.error_handling_complete,
        checklist.test_coverage,
        checklist.input_validation,
        checklist.secure_dependencies,
        checklist.secrets_management,
        checklist.auth_implementation,
    ]
    score = (sum(checks) / len(checks)) * 100 if checks else 0
    
    # 違規
    if not checklist.code_documentation:
        violations.append({
            "type": "missing_documentation",
            "message": "Implementation 缺少 README 或文件",
            "severity": "MEDIUM"
        })
        recommendations.append("添加 README.md 描述代碼結構和運行方式")
    
    if not checklist.error_handling_complete:
        violations.append({
            "type": "insufficient_error_handling",
            "message": "Implementation 缺少錯誤處理",
            "severity": "HIGH"
        })
        recommendations.append("確保所有模組有 try/except 錯誤處理")
    
    if not checklist.test_coverage:
        violations.append({
            "type": "no_test_coverage",
            "message": "Implementation 缺少測試",
            "severity": "MEDIUM"
        })
        recommendations.append("添加單元測試")
    
    passed = score >= CONSTITUTION_THRESHOLDS["maintainability"]
    
    return ConstitutionCheckResult(
        check_type="implementation",
        passed=passed,
        score=score,
        violations=violations,
        details={
            "files_checked": len(code_files),
            "has_documentation": checklist.code_documentation,
            "has_error_handling": checklist.error_handling_complete,
            "has_tests": checklist.test_coverage,
        },
        recommendations=recommendations
    )
