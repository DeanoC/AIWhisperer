# Workspace Health Report

**Workspace:** `/home/deano/projects/feature-better-progress-ui`
**Generated:** 2025-05-31 11:11:46
**Overall Status:** WARNING

## Summary
- pass: 17
- warning: 4
- fail: 0
- info: 0

## Detailed Checks

### Structure
- ✅ **.WHISPER directory**: .WHISPER directory exists
- ⚠️ **.WHISPER/logs**: Directory .WHISPER/logs not found
  - *Recommendation:* Create directory: mkdir -p /home/deano/projects/feature-better-progress-ui/.WHISPER/logs
- ⚠️ **.WHISPER/state**: Directory .WHISPER/state not found
  - *Recommendation:* Create directory: mkdir -p /home/deano/projects/feature-better-progress-ui/.WHISPER/state
- ⚠️ **.WHISPER/output**: Directory .WHISPER/output not found
  - *Recommendation:* Create directory: mkdir -p /home/deano/projects/feature-better-progress-ui/.WHISPER/output
- ✅ **ai_whisperer directory**: Core package directory directory exists
- ✅ **prompts directory**: Prompt templates directory exists
- ✅ **tests directory**: Test suite directory exists
- ✅ **docs directory**: Documentation directory exists

### Configuration
- ✅ **API Key**: API key configured
- ⚠️ **Model Configuration**: No model specified in config
  - *Recommendation:* Add 'model' field to config.yaml
- ✅ **Debbie Agent**: Debbie the Debugger is configured

### Dependencies
- ✅ **requirements.txt**: Requirements file exists
- ✅ **fastapi module**: Web framework for interactive server is available
- ✅ **websockets module**: WebSocket support is available
- ✅ **pydantic module**: Data validation is available
- ✅ **yaml module**: Configuration parsing is available

### Permissions
- ✅ **Write permissions**: Can write to .WHISPER directory

### Integration
- ✅ **Batch mode**: Batch mode components installed
- ✅ **session_inspector tool**: Debugging tool session_inspector available
- ✅ **message_injector tool**: Debugging tool message_injector available
- ✅ **workspace_validator tool**: Debugging tool workspace_validator available

## Recommendations
1. Create directory: mkdir -p /home/deano/projects/feature-better-progress-ui/.WHISPER/logs
2. Create directory: mkdir -p /home/deano/projects/feature-better-progress-ui/.WHISPER/state
3. Create directory: mkdir -p /home/deano/projects/feature-better-progress-ui/.WHISPER/output
4. Add 'model' field to config.yaml
