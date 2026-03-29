#!/bin/bash
# =============================================================================
# Git Hooks Setup Script
# =============================================================================
# 為 methodology-v2 專案設定 Git Hooks，確保每次 commit 前檢查 Phase 狀態
#
# 使用方式：
#   bash scripts/setup-git-hooks.sh
# =============================================================================

set -e  # 遇到錯誤時退出

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "Git Hooks Setup for methodology-v2"
echo "=============================================="
echo

# 取得專案根目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

# 檢查是否為 Git 專案
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo -e "${RED}Error: Not a Git repository${NC}"
    echo "Please run this script from the project root."
    exit 1
fi

# 確保 hooks 目錄存在
mkdir -p "$HOOKS_DIR"

# =============================================================================
# prepare-commit-msg Hook
# =============================================================================
# 在 commit message 編輯前觸發
# 檢查當前 Phase 的 Quality Gate 是否通過
# =============================================================================

PREPARE_COMMIT_MSG_HOOK="$HOOKS_DIR/prepare-commit-msg"

cat > "$PREPARE_COMMIT_MSG_HOOK" << 'HOOK_SCRIPT'
#!/bin/bash
# =============================================================================
# prepare-commit-msg hook
# =============================================================================
# 檢查當前 Phase 的 Quality Gate 是否通過
# 若未通過，阻止 commit
# =============================================================================

set -e

# 取得專案根目錄
GIT_DIR=$(git rev-parse --show-toplevel)
QUALITY_CLI="$GIT_DIR/quality_gate/cli/quality.py"

# 取得當前 Phase（從 git config 或預設為 1）
PHASE=$(git config --local --get quality.phase 2>/dev/null || echo "1")

# 檢查 Python 是否可用
if ! command -v python3 &> /dev/null; then
    echo "Warning: python3 not found, skipping quality gate check"
    exit 0
fi

# 檢查 quality CLI 是否存在
if [ ! -f "$QUALITY_CLI" ]; then
    echo "Warning: quality CLI not found, skipping quality gate check"
    exit 0
fi

# 執行 Quality Gate 檢查
echo "Running Phase $PHASE Quality Gate check..."

cd "$GIT_DIR"
python3 -m quality_gate.cli quality check-phase "$PHASE" --block

RESULT=$?

if [ $RESULT -ne 0 ]; then
    echo ""
    echo "=============================================="
    echo "❌ QUALITY GATE FAILED"
    echo "=============================================="
    echo ""
    echo "Phase $PHASE has not passed Quality Gate."
    echo "Please fix the issues before committing."
    echo ""
    echo "To update the current Phase, run:"
    echo "  git config quality.phase <phase_number>"
    echo ""
    exit 1
fi

echo "✅ Phase $PHASE Quality Gate passed!"
exit 0
HOOK_SCRIPT

chmod +x "$PREPARE_COMMIT_MSG_HOOK"

echo -e "${GREEN}✓${NC} Created prepare-commit-msg hook"


# =============================================================================
# post-merge Hook
# =============================================================================
# 在合併完成後觸發
# 自動檢查合併後的 Phase 狀態
# =============================================================================

POST_MERGE_HOOK="$HOOKS_DIR/post-merge"

cat > "$POST_MERGE_HOOK" << 'HOOK_SCRIPT'
#!/bin/bash
# =============================================================================
# post-merge hook
# =============================================================================
# 合併後自動檢查 Phase 狀態
# =============================================================================

set -e

# 取得專案根目錄
GIT_DIR=$(git rev-parse --show-toplevel)
QUALITY_CLI="$GIT_DIR/quality_gate/cli/quality.py"

# 取得當前 Phase
PHASE=$(git config --local --get quality.phase 2>/dev/null || echo "1")

# 檢查 Python 是否可用
if ! command -v python3 &> /dev/null; then
    echo "Warning: python3 not found, skipping quality gate check"
    exit 0
fi

# 檢查 quality CLI 是否存在
if [ ! -f "$QUALITY_CLI" ]; then
    echo "Warning: quality CLI not found, skipping quality gate check"
    exit 0
fi

# 執行 Quality Gate 檢查
echo ""
echo "Running Phase $PHASE Quality Gate check after merge..."
echo ""

cd "$GIT_DIR"
python3 -m quality_gate.cli quality check-phase "$PHASE" --strict || true

echo ""
echo "Post-merge quality check completed."
exit 0
HOOK_SCRIPT

chmod +x "$POST_MERGE_HOOK"

echo -e "${GREEN}✓${NC} Created post-merge hook"


# =============================================================================
# pre-push Hook (可選)
# =============================================================================
# 在 push 前觸發
# 檢查即將推送的 commit 是否通過 Quality Gate
# =============================================================================

PRE_PUSH_HOOK="$HOOKS_DIR/pre-push"

cat > "$PRE_PUSH_HOOK" << 'HOOK_SCRIPT'
#!/bin/bash
# =============================================================================
# pre-push hook
# =============================================================================
# 在 push 前檢查 Quality Gate
# =============================================================================

set -e

# 取得專案根目錄
GIT_DIR=$(git rev-parse --show-toplevel)
QUALITY_CLI="$GIT_DIR/quality_gate/cli/quality.py"

# 取得當前 Phase
PHASE=$(git config --local --get quality.phase 2>/dev/null || echo "1")

# 檢查 Python 是否可用
if ! command -v python3 &> /dev/null; then
    echo "Warning: python3 not found, skipping quality gate check"
    exit 0
fi

# 檢查 quality CLI 是否存在
if [ ! -f "$QUALITY_CLI" ]; then
    echo "Warning: quality CLI not found, skipping quality gate check"
    exit 0
fi

# 檢查最近一個 commit 是否通過 Quality Gate
echo ""
echo "Checking recent commit for Quality Gate..."

cd "$GIT_DIR"
LAST_COMMIT_MSG=$(git log -1 --pretty=%B | head -n 1)

if [[ "$LAST_COMMIT_MSG" == *"STAGE_PASS"* ]]; then
    echo "Found STAGE_PASS in last commit, skipping check"
    exit 0
fi

# 執行檢查
python3 -m quality_gate.cli quality check-phase "$PHASE" --block

RESULT=$?

if [ $RESULT -ne 0 ]; then
    echo ""
    echo "=============================================="
    echo "❌ PRE-PUSH QUALITY GATE FAILED"
    echo "=============================================="
    echo ""
    echo "Last commit did not pass Quality Gate."
    echo "Please ensure all Phase checks pass before pushing."
    echo ""
    exit 1
fi

echo "✅ Pre-push check passed!"
exit 0
HOOK_SCRIPT

chmod +x "$PRE_PUSH_HOOK"

echo -e "${GREEN}✓${NC} Created pre-push hook"


# =============================================================================
# 設定 git config
# =============================================================================

echo ""
echo "=============================================="
echo "Configuration"
echo "=============================================="
echo

# 設定預設 Phase
read -p "Enter current Phase (1-8) [default: 1]: " PHASE
PHASE=${PHASE:-1}

git config --local quality.phase "$PHASE"
echo -e "${GREEN}✓${NC} Set quality.phase to $PHASE"

# 詢問是否啟用自動 Block
read -p "Enable automatic block on Quality Gate failure? (y/n) [default: y]: " ENABLE_BLOCK
ENABLE_BLOCK=${ENABLE_BLOCK:-y}

if [ "$ENABLE_BLOCK" = "y" ]; then
    git config --local quality.block_on_failure true
    echo -e "${GREEN}✓${NC} Enabled block on failure"
else
    git config --local quality.block_on_failure false
    echo -e "${GREEN}✓${NC} Disabled block on failure"
fi


# =============================================================================
# 完成
# =============================================================================

echo ""
echo "=============================================="
echo -e "${GREEN}Git Hooks Setup Complete!${NC}"
echo "=============================================="
echo ""
echo "Hooks installed:"
echo "  - prepare-commit-msg: Block commits if Phase not passed"
echo "  - post-merge: Check Phase status after merge"
echo "  - pre-push: Check before pushing"
echo ""
echo "Current Phase: $PHASE"
echo ""
echo "To change Phase:"
echo "  git config quality.phase <phase_number>"
echo ""
echo "To check Phase status manually:"
echo "  python -m quality_gate.cli quality check-phase $PHASE"
echo ""