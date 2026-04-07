#!/bin/bash
# CQG 安裝脚本
# 用法: bash install_cqg.sh

set -e

echo "Installing CQG dependencies..."

# Check if pip available
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 not found"
    exit 1
fi

# Install Python packages
pip3 install -r requirements-cqg.txt

# Check eslint (optional)
if command -v npm &> /dev/null; then
    echo "Installing eslint..."
    npm install -g eslint 2>/dev/null || echo "npm eslint install failed (non-critical)"
else
    echo "npm not found, skipping eslint"
fi

echo ""
echo "CQG installation complete!"
echo ""
echo "Installed tools:"
pip3 show pylint radon coverage 2>/dev/null | grep -E "^Name:|^Version:"
echo ""
echo "Usage:"
echo "  python quality_gate/unified_gate.py --path /your/project"
