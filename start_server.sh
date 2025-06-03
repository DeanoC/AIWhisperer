#!/bin/bash
# Startup script that ensures correct module loading for worktree

echo "=== Starting AIWhisperer Server from Worktree ==="

# Get the directory of this script (the worktree root)
WORKTREE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$WORKTREE_DIR"

echo "Working directory: $WORKTREE_DIR"

# Clear any existing PYTHONPATH to avoid confusion
unset PYTHONPATH
echo "Cleared PYTHONPATH"

# Check which Python we're using
echo "Python executable: $(which python)"

# If there's a local .venv, use it
if [ -d "$WORKTREE_DIR/.venv" ]; then
    echo "Found local .venv, activating it..."
    source "$WORKTREE_DIR/.venv/bin/activate"
    echo "Using Python: $(which python)"
else
    echo "No local .venv found. Using current Python environment."
    echo "⚠️  Warning: This may cause path resolution issues."
    echo "   Consider running: ./setup_worktree_venv.sh"
fi

# Set PYTHONPATH to ensure our modules are found first
export PYTHONPATH="$WORKTREE_DIR:$PYTHONPATH"
echo "Set PYTHONPATH to prioritize worktree: $WORKTREE_DIR"

# Start the server
echo ""
echo "Starting server..."
python -m interactive_server.main --config config/main.yaml "$@"