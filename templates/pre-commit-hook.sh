#!/bin/bash
# pre-commit hook - 自動執行 Enforcement
# 
# 使用方式：
# cp .methodology/templates/pre-commit-hook.sh .git/hooks/pre-commit
# chmod +x .git/hooks/pre-commit

echo "🔍 Running Framework Enforcement..."

# 執行 Framework Enforcement
methodology enforce --level BLOCK
if [ $? -ne 0 ]; then
    echo "❌ Enforcement failed. Commit blocked."
    echo "   Fix issues or use --no-verify to bypass"
    exit 1
fi

echo "✅ Enforcement passed"
exit 0
