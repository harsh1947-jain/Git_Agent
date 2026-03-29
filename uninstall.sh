#!/bin/bash
# PR Sync Uninstall Script

echo "Removing git alias 'psync'..."
git config --global --unset alias.psync 2>/dev/null || true

echo "Uninstall complete!"
echo "Note: The pr_sync.py file remains - delete it manually if needed."
