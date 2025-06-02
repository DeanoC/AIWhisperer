# Git Worktree Setup Guide for AIWhisperer

## Why This Matters

When working with git worktrees, Python module resolution can get confused, especially when:
- Using a shared virtual environment from the main repository
- The main repo and worktree have different versions of files
- Agent prompt files exist in one location but not another

## Current Setup

- Main repository: `/home/deano/projects/AIWhisperer`
- This worktree: `/home/deano/projects/feature-billy-debugging-help`
- Shared venv: `/home/deano/projects/AIWhisperer/.venv`

## The Path Resolution Issue

When using the main repo's venv while running from a worktree:
1. Python's module import system might load modules from unexpected locations
2. PathManager's `app_path` (based on `__file__`) can resolve incorrectly
3. Prompt files might be looked up in the wrong directory
4. Agent-specific prompts (like debbie_debugger.prompt.md) might not be found

## Solutions Implemented

### 1. Path Priority Fix (main.py)
Added code to ensure the worktree's modules are loaded first:
```python
# Ensure we're using modules from the current worktree directory
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
```

### 2. Enhanced Logging
- PathManager now logs all paths it's using
- Prompt resolution logs all attempted paths when falling back
- Server startup shows which prompts are found

### 3. Better Fallback Prompt
The default.md now clearly indicates when it's being used as a fallback, helping identify path issues immediately.

## Recommended Workflows

### Option 1: Worktree-Specific Virtual Environment (Recommended)
```bash
# One-time setup
./setup_worktree_venv.sh

# Start server
source .venv/bin/activate
python -m interactive_server.main
```

**Pros:**
- Complete isolation between branches
- No path confusion
- Can have different dependencies per branch

**Cons:**
- Uses more disk space
- Need to install dependencies for each worktree

### Option 2: Shared venv with Path Management
```bash
# Start server with path management
./start_server.sh
```

**Pros:**
- Saves disk space
- Faster to switch between worktrees

**Cons:**
- Potential path confusion
- Dependencies must be compatible across all branches

### Option 3: Manual Path Control
```bash
cd /home/deano/projects/feature-billy-debugging-help
unset PYTHONPATH
export PYTHONPATH="$(pwd):$PYTHONPATH"
python -m interactive_server.main
```

## Verifying Correct Setup

After starting the server, check the logs for:
1. "Project root: /home/deano/projects/feature-billy-debugging-help"
2. "✓ Debbie's prompt file found"
3. No warnings about fallback prompts

When switching to Debbie, she should introduce herself as "Debbie the Debugger" with the 🐛 emoji, not as a generic AI assistant.

## Troubleshooting

If prompts are still not found:
1. Check the server startup logs for PathManager paths
2. Look for "FALLBACK" warnings in the logs
3. Verify prompt files exist: `ls prompts/agents/`
4. Check Python module locations: `python -c "import ai_whisperer; print(ai_whisperer.__file__)"`

## Design Philosophy

The prompt loading system is designed with these priorities:
1. **Customization**: Users can override built-in prompts by placing custom versions in their project
2. **Fallback**: Built-in prompts in app_path serve as reliable defaults
3. **Transparency**: Clear logging and error messages when prompts can't be found
4. **Safety**: A generic fallback prompt ensures the system still works even if specific prompts are missing

This allows technical users to customize agent behavior while maintaining a working system out of the box.