# Tools That Need Structured Data Returns

Based on the audit, here are the tools that need to be updated to return structured data instead of formatted strings:

## High Priority (Core Tools)

1. **list_directory_tool.py** - Returns formatted string
   - Should return: `{"path": str, "entries": [{"name": str, "type": "file"|"dir", "size": int}]}`

2. **read_file_tool.py** - Returns formatted string for errors
   - Should return: `{"content": str, "path": str, "lines": int, "error": str|null}`

3. **write_file_tool.py** - Mixed (some dict, some formatted)
   - Should consistently return: `{"status": "success"|"error", "path": str, "message": str}`

4. **execute_command_tool.py** - Mostly good but errors are formatted
   - Already returns: `{"stdout": str, "stderr": str, "returncode": int}`
   - Fix: Error messages in stderr should be plain, not formatted

5. **search_files_tool.py** - Returns formatted strings
   - Should return: `{"matches": [{"path": str, "line": int, "content": str}], "total": int, "error": str|null}`

## RFC/Plan Tools

6. **create_rfc_tool.py** - Returns formatted success/error messages
   - Should return: `{"rfc_id": str, "status": str, "path": str, "error": str|null}`

7. **update_rfc_tool.py** - Returns formatted messages
   - Should return: `{"rfc_id": str, "section": str, "updated": bool, "error": str|null}`

8. **delete_rfc_tool.py** - Returns formatted messages
   - Should return: `{"rfc_id": str, "deleted": bool, "message": str, "error": str|null}`

9. **create_plan_from_rfc_tool.py** - Returns formatted messages
   - Should return: `{"plan_name": str, "type": str, "created": bool, "path": str, "error": str|null}`

## Analysis Tools

10. **analyze_languages_tool.py** - Returns formatted errors
    - Already returns dict for success, just fix error format

11. **find_similar_code_tool.py** - Returns formatted strings
    - Should return: `{"feature": str, "matches": [...], "error": str|null}`

12. **get_project_structure_tool.py** - Returns formatted strings
    - Should return: `{"structure": {...}, "tree": str|null, "error": str|null}`

## Web Tools

13. **fetch_url_tool.py** - Returns formatted error strings
    - Should return: `{"url": str, "content": str, "title": str, "error": str|null}`

14. **web_search_tool.py** - Returns formatted errors
    - Should return: `{"query": str, "results": [...], "error": str|null}`

## Communication Tools

15. **send_mail_tool.py** - Returns formatted success messages
    - Should return: `{"message_id": str, "to": str, "sent": bool, "error": str|null}`

16. **check_mail_tool.py** - Returns plain string for "no messages"
    - Should return: `{"messages": [...], "count": int}`

## Tool Patterns to Fix

### Error Handling Pattern
```python
# BAD: Formatted error string
return f"Error: {error_type} - {details}"

# GOOD: Structured error
return {"error": f"{error_type}: {details}", "success": False}
```

### Success Message Pattern
```python
# BAD: Formatted success string
return f"Successfully created {item}!\n\nDetails: {details}"

# GOOD: Structured success
return {"success": True, "item": item, "details": details}
```

### Empty Result Pattern
```python
# BAD: Plain string
return "No items found."

# GOOD: Structured empty result
return {"items": [], "count": 0}
```

## Tools That Are Already Good ✅

- workspace_stats_tool.py - Returns dict
- find_pattern_tool.py - Returns dict
- python_ast_json_tool.py - Returns dict
- session_health_tool.py - Returns dict
- ai_loop_inspector_tool.py - Mostly dict (just fix error format)
- get_file_content_tool.py - Returns dict

## Implementation Strategy

1. Start with core file system tools (highest usage)
2. Then RFC/plan tools (complex workflows)
3. Then analysis/web tools
4. Finally communication/utility tools

Each tool should:
- Always return a dict/list (structured data)
- Include an "error" field for error cases
- Use consistent field names across similar tools
- Never format messages for display (let AI do that)