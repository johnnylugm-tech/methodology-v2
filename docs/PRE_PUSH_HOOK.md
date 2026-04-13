#!/bin/bash
# pre-push hook for methodology-v2
# 用途：push 前自動執行路徑一致性檢查

echo "Running pre-push checks..."

# 執行路徑一致性檢查
python3 scripts/verify_path_consistency.py
if [ $? -ne 0 ]; then
    echo "❌ Path consistency check FAILED"
    echo "Please fix the issues before pushing"
    exit 1
fi

# 執行路徑合約測試（如果存在）
if [ -f "tests/test_phase_paths.py" ]; then
    python3 tests/test_phase_paths.py
    if [ $? -ne 0 ]; then
        echo "❌ Path contract tests FAILED"
        echo "Please fix the issues before pushing"
        exit 1
    fi
fi

echo "✅ All pre-push checks passed"
exit 0
