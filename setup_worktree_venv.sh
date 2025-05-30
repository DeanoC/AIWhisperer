#!/bin/bash
# Setup script for creating a worktree-specific virtual environment

echo "=== Setting up worktree-specific virtual environment ==="

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if .venv already exists
if [ -d ".venv" ]; then
    echo "⚠️  .venv already exists. Remove it first if you want to recreate it."
    echo "   Run: rm -rf .venv"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv .venv

# Activate it
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
else
    echo "⚠️  requirements.txt not found!"
fi

echo ""
echo "✅ Virtual environment setup complete!"
echo ""
echo "To activate this virtual environment in the future, run:"
echo "   source .venv/bin/activate"
echo ""
echo "To start the server with the correct paths:"
echo "   python -m interactive_server.main"
echo ""
echo "Note: Using a worktree-specific venv ensures that all paths resolve correctly"
echo "      and prevents cross-contamination between branches."