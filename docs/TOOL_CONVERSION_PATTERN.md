# Tool Conversion Pattern - Structured Data Returns

## Overview
Tools need to be converted from returning formatted strings to returning structured dictionaries. This improves AI interpretability and fixes verbosity issues.

## Pattern for Clean Tools

### 1. Success Returns
Instead of:
```python
return f"Successfully created {item_name} at {path}"
```

Use:
```python
return {
    "success": True,
    "item_name": item_name,
    "path": path,
    "message": "Item created successfully"  # Optional human-readable message
}
```

### 2. Error Returns
Instead of:
```python
return f"Error: {error_message}"
# or
return f"Error creating item: {str(e)}"
```

Use:
```python
return {
    "error": error_message,  # or "error": str(e)
    "success": False,  # Optional but recommended
    "item_name": item_name,  # Include relevant context
    "operation": "create"  # What failed
}
```

### 3. List/Collection Returns
Instead of:
```python
result = f"Found {len(items)} items:\n"
for item in items:
    result += f"- {item.name}: {item.description}\n"
return result
```

Use:
```python
return {
    "items": [
        {
            "name": item.name,
            "description": item.description,
            # ... other fields
        }
        for item in items
    ],
    "count": len(items),
    "total_count": total_count,  # If different from returned count
    "truncated": len(items) < total_count  # If results were limited
}
```

### 4. Status/Info Returns
Instead of:
```python
return f"Status: {status}\nDetails: {details}"
```

Use:
```python
return {
    "status": status,
    "details": details,
    "timestamp": datetime.now().isoformat(),
    # ... other relevant fields
}
```

## Common Patterns to Fix

### 1. String Concatenation
Look for:
- `result = "..."` followed by `result += "..."`
- `f"..."` formatted strings being returned
- `"".join(...)` being returned
- Multi-line string building

### 2. Error Handling
Look for:
- `return f"Error: ..."`
- `return "Error: " + ...`
- Plain string error returns

### 3. Success Messages
Look for:
- `return f"Successfully ..."`
- `return "Operation completed..."`
- Any formatted success message

### 4. JSON Dumps for Display
Look for:
- `json.dumps(data, indent=2)` being returned as string
- Should return the data structure directly

## Example Conversion

### Before:
```python
def execute(self, arguments: Dict[str, Any]) -> str:
    plan_name = arguments.get('plan_name')
    if not plan_name:
        return "Error: 'plan_name' is required."
    
    try:
        # ... operation logic ...
        if not found:
            return f"Error: Plan '{plan_name}' not found."
        
        # ... more logic ...
        return f"Plan moved successfully!\n\nPlan: {plan_name}\nFrom: {old_status}\nTo: {new_status}"
        
    except Exception as e:
        return f"Error moving plan: {str(e)}"
```

### After:
```python
def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
    plan_name = arguments.get('plan_name')
    if not plan_name:
        return {
            "error": "'plan_name' is required.",
            "plan_name": None,
            "moved": False
        }
    
    try:
        # ... operation logic ...
        if not found:
            return {
                "error": f"Plan '{plan_name}' not found.",
                "plan_name": plan_name,
                "moved": False
            }
        
        # ... more logic ...
        return {
            "moved": True,
            "plan_name": plan_name,
            "previous_status": old_status,
            "new_status": new_status,
            "message": "Plan moved successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": f"Error moving plan: {str(e)}",
            "plan_name": plan_name,
            "moved": False
        }
```

## Key Principles

1. **Consistency**: Always return dictionaries, even for errors
2. **Context**: Include relevant context fields even in error cases
3. **Structure**: Use nested structures for complex data
4. **Completeness**: Include all relevant information
5. **Machine-Readable**: Prioritize structured data over formatted text
6. **Human-Friendly**: Can include optional `message` fields for human readability

## Tools Needing Conversion (Phase 8+)

Based on the audit report, the following tools need conversion:
- delete_plan_tool.py
- format_for_external_agent_tool.py
- parse_external_result_tool.py
- recommend_external_agent_tool.py
- send_mail_with_switch_tool.py
- update_task_status_tool.py
- validate_external_agent_tool.py

Plus any other tools that still return formatted strings instead of structured data.