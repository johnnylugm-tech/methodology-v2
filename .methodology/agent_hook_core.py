#!/usr/bin/env python3
"""
Agent Hook Core
===============
This is the core enforcement logic that cannot be easily bypassed.
It lives in .methodology/ which is less obvious than .git/hooks/
"""

import os
import re
import sys

def enforce():
    """
    Main enforcement function
    Called by the pre-commit hook wrapper
    """
    print("🔍 Agent-Proof Hook: Running checks...")
    
    # 1. Check commit message
    commit_msg_file = os.environ.get('COMMIT_MSG_FILE', '.git/COMMIT_EDITMSG')
    
    if os.path.exists(commit_msg_file):
        with open(commit_msg_file, 'r') as f:
            msg = f.read().strip()
        
        # Check for task ID
        if not re.search(r'\[[A-Z]+-\d+\]', msg):
            print("❌ Commit message must include task ID (e.g., [TASK-123])")
            print(f"   Your message: {msg[:50]}...")
            sys.exit(1)
        
        print(f"   ✅ Task ID found in commit message")
    
    # 2. Check for bypass attempts
    suspicious_env = os.environ.get('GIT_COMMAND', '')
    bypass_keywords = ['--no-verify', '--bypass', '--skip-hooks']
    
    for kw in bypass_keywords:
        if kw in suspicious_env:
            print(f"❌ Suspicious bypass keyword detected: {kw}")
            sys.exit(1)
    
    # 3. All checks passed
    print("✅ All Agent-Proof checks passed")


if __name__ == "__main__":
    enforce()
