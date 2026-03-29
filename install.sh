#!/bin/bash
# PR Sync Installation Script
# Sets up a git alias 'psync' that pushes and then updates PR description

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PR_SYNC_PATH="$SCRIPT_DIR/pr_sync.py"

# Check dependencies
echo "Checking dependencies..."

if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 is required but not installed"
    exit 1
fi

if ! command -v gh &> /dev/null; then
    echo "ERROR: GitHub CLI (gh) is required but not installed"
    echo "Install it: https://cli.github.com/"
    exit 1
fi

if ! gh auth status &> /dev/null; then
    echo "ERROR: GitHub CLI is not authenticated"
    echo "Run: gh auth login"
    exit 1
fi

if ! command -v claude &> /dev/null; then
    echo "ERROR: Claude Code CLI is required but not installed"
    exit 1
fi

echo "All dependencies found!"

# Make pr_sync.py executable
chmod +x "$PR_SYNC_PATH"

# Set up git alias
# The alias: push to remote, then run pr_sync
echo "Setting up git alias 'psync'..."

git config --global alias.psync "!f() { git push \"\$@\" && python3 '$PR_SYNC_PATH'; }; f"

echo ""
echo "Installation complete!"
echo ""
echo "Usage:"
echo "  git psync              # Push and update PR description"
echo "  git psync origin feat  # Push specific branch and update PR"
echo "  python3 $PR_SYNC_PATH --dry-run  # Test without making changes"
echo ""
echo "NOTE: This tool ONLY works with harsh1947-jain/Git_Agent"
echo "      It will refuse to run on any other repository."
