# Technical Debt Log

## React.StrictMode Compatibility

**Issue:**
The frontend currently does not work correctly with React.StrictMode enabled. StrictMode double-invokes certain effects and state logic in development, which exposed a bug where AI messages were displayed twice in the chat. The current workaround is to disable StrictMode in `index.tsx`.

**Risk:**
Without StrictMode, we may miss early warnings about side effects, unsafe patterns, or deprecated APIs. This could allow subtle bugs to go unnoticed until later.

**Action Item:**
Refactor the frontend code (especially state and effect logic in chat and WebSocket handling) to be idempotent and robust to StrictMode's double-invocation. Re-enable StrictMode in development once fixed.

**Date Logged:** 2025-05-27

---

Add further technical debt items below as needed.
