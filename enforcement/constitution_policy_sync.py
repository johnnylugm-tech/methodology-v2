#!/usr/bin/env python3
"""
Constitution Policy Sync
========================
從 Constitution.md 自動生成 Policy Engine 政策

目的：
- 解決政策是硬編碼的問題
- 讓 Constitution 和 Policy Engine 保持同步
- 政策定義在一處（Constitution），其他地方自動衍生
"""

import re
import os
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path

from enforcement.policy_engine import PolicyEngine, Policy, EnforcementLevel
from enforcement.constitution_as_code import ConstitutionAsCode, Rule, RuleSeverity


class ConstitutionPolicyGenerator:
    """
    從 Constitution.md 自動生成 Policy
    
    使用方式：
    
    ```python
    generator = ConstitutionPolicyGenerator()
    
    # 生成 Policy 列表
    policies = generator.generate("CONSTITUTION.md")
    
    # 或者直接同步到 PolicyEngine
    generator.sync()
    ```
    """
    
    # 預設的 Constitution 路徑
    DEFAULT_CONSTITUTION_PATHS = [
        "CONSTITUTION.md",
        "constitution/CONSTITUTION.md",
        ".methodology/CONSTITUTION.md",
    ]
    
    def __init__(self):
        self.rules: List[Dict[str, Any]] = []
    
    def find_constitution(self) -> Optional[str]:
        """找到 Constitution.md 的位置"""
        for path in self.DEFAULT_CONSTITUTION_PATHS:
            if os.path.exists(path):
                return path
        return None
    
    def parse_constitution(self, path: str) -> List[Dict[str, Any]]:
        """
        解析 Constitution.md 中的規則
        
        支援的格式：
        
        ## Rule: commit-has-task-id
        [SEVERITY: critical]
        [THRESHOLD: 90]
        所有 commit 必須包含 task_id，格式：[TASK-XXX]
        
        或者：
        
        ### R001: Quality Gate
        **Severity**: critical
        **Threshold**: 90
        描述...
        """
        rules = []
        
        with open(path, 'r') as f:
            content = f.read()
        
        # 解析 ## Rule: xxx 或 ### Rxxx 格式
        pattern = r'## Rule: (\w+)|### (R\d+): (.+)'
        
        current_rule = None
        
        for line in content.split('\n'):
            # 新規則開始
            match = re.match(r'## Rule: (\w+)', line)
            if match:
                if current_rule:
                    rules.append(current_rule)
                current_rule = {
                    'id': match.group(1),
                    'description': '',
                    'severity': 'medium',
                    'threshold': None,
                    'check_type': 'commit_message',
                }
                continue
            
            # 解析 R001 格式
            match = re.match(r'### (R\d+): (.+)', line)
            if match and not current_rule:
                current_rule = {
                    'id': match.group(1),
                    'description': match.group(2),
                    'severity': 'medium',
                    'threshold': None,
                    'check_type': 'general',
                }
                continue
            
            # 解析屬性
            if current_rule:
                # [SEVERITY: xxx]
                match = re.match(r'\[SEVERITY: (\w+)\]', line, re.IGNORECASE)
                if match:
                    current_rule['severity'] = match.group(1).lower()
                    continue
                
                # [THRESHOLD: xxx]
                match = re.match(r'\[THRESHOLD: ([\d.]+)\]', line)
                if match:
                    current_rule['threshold'] = float(match.group(1))
                    continue
                
                # **Severity**: xxx
                match = re.match(r'\*\*Severity\*\*:\s*(\w+)', line, re.IGNORECASE)
                if match:
                    current_rule['severity'] = match.group(1).lower()
                    continue
                
                # **Threshold**: xxx
                match = re.match(r'\*\*Threshold\*\*:\s*([\d.]+)', line)
                if match:
                    current_rule['threshold'] = float(match.group(1))
                    continue
                
                # 描述累加
                if line.strip() and not line.startswith('#') and not line.startswith('['):
                    current_rule['description'] += ' ' + line.strip()
        
        if current_rule:
            rules.append(current_rule)
        
        self.rules = rules
        return rules
    
    def create_check_fn(self, rule: Dict[str, Any]) -> Callable:
        """根據規則類型創建檢查函數"""
        check_type = rule.get('check_type', 'general')
        threshold = rule.get('threshold')
        
        if check_type == 'commit_message':
            def check_fn():
                import os
                commit_file = os.environ.get('COMMIT_MSG_FILE', '.git/COMMIT_EDITMSG')
                if os.path.exists(commit_file):
                    with open(commit_file, 'r') as f:
                        msg = f.read()
                    return bool(re.search(r'\[[A-Z]+-\d+\]', msg))
                return True  # 沒有檔案時通過
            return check_fn
        
        elif check_type == 'quality_gate':
            def check_fn():
                score_file = ".methodology/.quality_score"
                if os.path.exists(score_file):
                    with open(score_file, 'r') as f:
                        return float(f.read().strip()) >= (threshold or 90)
                return True
            return check_fn
        
        elif check_type == 'coverage':
            def check_fn():
                coverage_file = ".methodology/.coverage"
                if os.path.exists(coverage_file):
                    with open(coverage_file, 'r') as f:
                        return float(f.read().strip()) >= (threshold or 80)
                return True
            return check_fn
        
        elif check_type == 'security':
            def check_fn():
                score_file = ".methodology/.security_score"
                if os.path.exists(score_file):
                    with open(score_file, 'r') as f:
                        return float(f.read().strip()) >= (threshold or 95)
                return True
            return check_fn
        
        else:
            # 通用檢查（總是通過）
            return lambda: True
    
    def generate(self, constitution_path: str = None) -> List[Policy]:
        """
        生成 Policy 列表
        
        Returns:
            List[Policy]: 從 Constitution 生成的 Policy 列表
        """
        if constitution_path is None:
            constitution_path = self.find_constitution()
        
        if constitution_path is None:
            print("⚠️ Constitution.md not found, using default policies")
            return []
        
        rules = self.parse_constitution(constitution_path)
        
        policies = []
        
        for rule in rules:
            policy = Policy(
                id=rule['id'],
                description=rule['description'].strip(),
                check_fn=self.create_check_fn(rule),
                enforcement=EnforcementLevel.BLOCK if rule['severity'] == 'critical' else EnforcementLevel.WARN,
                severity=rule['severity'],
                metadata={
                    'threshold': rule.get('threshold'),
                    'check_type': rule.get('check_type'),
                }
            )
            policies.append(policy)
        
        return policies
    
    def sync_to_engine(self, engine: PolicyEngine = None):
        """
        同步到 PolicyEngine
        
        Args:
            engine: 目標 PolicyEngine，如果為 None，會創建新的
        """
        policies = self.generate()
        
        if engine is None:
            engine = PolicyEngine()
        
        # 清除現有政策
        engine.policies.clear()
        
        # 添加新政策
        for policy in policies:
            engine.policies.append(policy)
        
        return engine
    
    def sync(self, output_path: str = ".methodology/policies_generated.py"):
        """
        同步並儲存為 Python 檔案
        
        這讓 Commit Hook 可以直接 import 使用
        """
        policies = self.generate()
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write("# Auto-generated from Constitution.md\n")
            f.write("# Do not edit manually\n\n")
            f.write("POLICIES = [\n")
            
            for p in policies:
                f.write(f'    # {p.id}: {p.description}\n')
                f.write(f'    # severity: {p.severity}, enforcement: {p.enforcement.value}\n')
                f.write(f'    # threshold: {p.metadata.get("threshold")}\n\n')
            
            f.write("]\n")
        
        print(f"✅ Synced {len(policies)} policies to {output_path}")
        return policies


def main():
    """CLI 入口"""
    import sys
    
    generator = ConstitutionPolicyGenerator()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "sync":
            # 同步 Constitution 到 Policy
            generator.sync()
        
        elif cmd == "generate":
            # 生成並顯示
            policies = generator.generate()
            print(f"Generated {len(policies)} policies:")
            for p in policies:
                print(f"  - {p.id}: {p.description[:50]}... [{p.severity}]")
        
        elif cmd == "preview":
            # 預覽 Constitution 中的規則
            path = generator.find_constitution()
            if path:
                rules = generator.parse_constitution(path)
                print(f"Found {len(rules)} rules in {path}:")
                for r in rules:
                    print(f"  - {r['id']}: {r.get('description', '')[:50]}... [{r['severity']}]")
            else:
                print("❌ Constitution.md not found")
    
    else:
        # 預設：同步
        generator.sync()


if __name__ == "__main__":
    main()
