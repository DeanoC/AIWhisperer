# Worktree Path Resolution Fix

## Problem
When running AIWhisperer from a git worktree while using the main repository's virtual environment, the PathManager can get confused about which directory to use for built-in prompts. This causes agent prompts (like debbie_debugger.prompt.md) to not be found, falling back to the generic default.md.

## Root Cause
- The worktree is at: `/home/deano/projects/feature-billy-debugging-help`
- The main repo is at: `/home/deano/projects/AIWhisperer`
- Using venv from main repo: `/home/deano/projects/AIWhisperer/.venv`
- PathManager's app_path can resolve to the wrong location due to module loading paths

## Solutions

### 1. Use Worktree-Specific Virtual Environment (Recommended)
```bash
cd /home/deano/projects/feature-billy-debugging-help
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python -m interactive_server.main
```

### 2. Clear Python Path Before Starting
```bash
cd /home/deano/projects/feature-billy-debugging-help
unset PYTHONPATH
/home/deano/projects/AIWhisperer/.venv/bin/python -m interactive_server.main
```

### 3. Force Correct Path in Server Startup
Add this to the beginning of `interactive_server/main.py`:
```python
import sys
import os
# Ensure we're using modules from the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
```

## Verification
After applying the fix, when you switch to Debbie, she should introduce herself with:
- Her name "Debbie the Debugger"
- The 🐛 emoji
- Her dual roles of debugging and batch processing
- Not the generic "I am an AI assistant" message