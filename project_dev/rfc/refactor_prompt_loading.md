# Refactor Prompt Loading

Our prompt system has evolved and become increasingly complex. Let's refactor it to be cleaner, more maintainable, and easier to test.

## Goals

1. **Centralized Access:** Once the config is loaded, all systems should access prompts exclusively from the config.
2. **Unified Structure:** Prompts are organized into sections (e.g., subtask prompts, command prompts, system prompts). All sections should reside under a single config section with standardized naming, allowing for future expansion.
3. **Section Defaults:** Most sections have a default prompt, which can be overridden. Some sections may not have a default.
4. **Lazy Loading:** Prompts are loaded only when first accessed (lazy loading).

## Requirements

- **User Overrides:** Users can override any prompt in the config by specifying a file path.
- **Default Fallbacks:** If a prompt is not specified in the config, a default is used.
- **App Defaults:** Fallback defaults are stored in the `{app_path}/prompts` folder, ensuring prompts are always available even if not specified by the user.
- **Section Defaults:** If a section has a default, it can be overridden in the config. This section default is used for any prompts in that section not explicitly overridden.
- **No Section Default:** If a section lacks a default, prompts in that section fall back to the app default or raise an error if none exists.

## Examples

```text
[A][bob] = `stuff`         ; When using section A, prompt 'bob', use this value from config
[A] = `stuff`              ; When using section A, any prompt not explicitly set uses this section default
[B][bob]                   ; When using section B, prompt 'bob', use this value if set
(no [B])                   ; When using section B, any prompt not set uses the app default for B
(no [C])                   ; When using section C, any prompt uses the app default for C (no section default)
(no [D][bob])              ; Section D has no default; prompt 'bob' in D uses the app default or raises an error
```

## Summary

- All prompts are accessed via config after loading.
- Prompts are organized by section, with standardized naming.
- Users can override prompts or section defaults via config.
- Fallbacks ensure prompts are always available, with clear error handling if not.
- Prompts are loaded
