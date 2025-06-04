# Tool Conversion Pattern - Structured Data Returns

## Overview
All tools should return structured data (dictionaries) instead of plain strings. This improves AI parsing and reduces verbosity in agent responses.

## Conversion Pattern

### Before (Plain String Returns)
```python
def execute(self, arguments: Dict[str, Any]) -> str:
    if not arguments.get('required_field'):
        return "Error: 'required_field' is required."
    
    # ... processing ...
    
    return f"Success! Created {item_name} at {location}."
```

### After (Structured Data Returns)
```python
def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
    if not arguments.get('required_field'):
        return {
            "error": "'required_field' is required.",
            "success": False,
            # Include relevant context fields even in error cases
            "item_name": None,
            "created": False
        }
    
    # ... processing ...
    
    return {
        "success": True,
        "created": True,
        "item_name": item_name,
        "location": location,
        "timestamp": datetime.now().isoformat(),
        # Include helpful metadata
        "next_steps": ["Review the item", "Update if needed"]
    }
```

## Key Principles

1. **Always Return Dictionaries** - Never return plain strings
2. **Consistent Structure** - Include relevant fields even in error cases
3. **Error Handling** - Errors are `{"error": "message", ...}` with context
4. **Success Indicators** - Boolean flags like `created`, `deleted`, `updated`
5. **Rich Metadata** - Include timestamps, counts, IDs, and other useful info
6. **Next Steps** - Optionally include suggested actions for the user

## Common Patterns

### Error Returns
```python
return {
    "error": "Specific error message",
    "success": False,
    "operation": "what_was_attempted",
    # Include any partial results or context
}
```

### Success Returns
```python
return {
    "success": True,
    "operation_completed": True,  # e.g., created, deleted, updated
    "result_data": {...},
    "metadata": {
        "timestamp": "...",
        "affected_items": 5,
        "duration_ms": 123
    },
    "recommendations": ["Next action 1", "Next action 2"]
}
```

### Listing/Query Returns
```python
return {
    "items": [...],
    "total_count": 42,
    "filtered_count": 10,
    "query_params": {...},
    "has_more": False
}
```

## Benefits

1. **Reduced AI Verbosity** - AI doesn't need to reformat or explain tool results
2. **Better Error Handling** - Structured errors are easier to parse and act on
3. **Consistent Interface** - All tools follow the same pattern
4. **Machine Readable** - Other tools can easily consume the output
5. **Self-Documenting** - Field names describe the data

## Tools Already Converted

See `scripts/tool_audit_report.json` for the current status of all tools.