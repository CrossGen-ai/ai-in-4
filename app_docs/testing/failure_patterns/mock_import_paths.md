# Mock Import Path Mistakes

**Pattern ID:** `mock-import-path`
**Frequency:** 5 occurrences (2025-10-06)
**Stack:** Python unittest.mock + FastAPI

## Error Signature

```
Mock not called / assert_called_once() fails
Mock object has no attribute 'assert_called_once'
Expected mock to be called but it wasn't
```

## Root Cause

**Critical Principle:** Mock where the function is USED, not where it's DEFINED.

Python imports create local references. When `module_a.py` does `from module_b import func`,
it creates a reference `module_a.func`. Patching `module_b.func` doesn't affect `module_a.func`.

## Common Triggers

1. **Mocking at definition site instead of usage site**
2. **Not understanding Python's import mechanism**
3. **Copy-pasting mock paths without checking imports**

## Fix Pattern

### Before (Fails)
```python
# File structure:
# services/email.py defines send_email()
# api/routes/auth.py imports: from services.email import send_email
# tests/test_auth.py tests the route

# ❌ WRONG - mocks where defined, not where used
with patch('services.email.send_email') as mock:
    response = client.post("/api/auth/register")
    mock.assert_called_once()  # FAILS - never called
```

### After (Works)
```python
# ✅ CORRECT - mocks where used
with patch('api.routes.auth.send_email') as mock:
    response = client.post("/api/auth/register")
    mock.assert_called_once()  # PASSES - intercepted the call
```

## How to Find the Correct Path

1. **Find where function is USED** (not defined)
   ```python
   # In api/routes/auth.py
   from services.email import send_email  # ← This creates api.routes.auth.send_email
   ```

2. **Mock that path**
   ```python
   # In test
   patch('api.routes.auth.send_email')  # ← Mock the local reference
   ```

## Quick Diagnostic

If mock isn't being called:
1. Find the module that CALLS the function
2. Check its imports at the top
3. Mock using: `<calling_module>.<function_name>`

## Prevention

- Always trace import paths before mocking
- Use IDE "Go to Definition" to find usage sites
- Add comment explaining mock path: `# Mock where auth.py imported it`

## Related

- [FastAPI Route Tests](../stack_guides/fastapi_route_tests.md#the-import-path-rule)

## Occurrences

1. tests/test_auth.py:12 (2025-10-06) - FIXED (send_magic_link_email)
2. tests/test_auth.py:34 (2025-10-06) - FIXED (send_magic_link_email)
3. tests/test_auth.py:94 (2025-10-06) - FIXED (send_magic_link_email)
4. tests/test_users.py:80 (2025-10-06) - FIXED (validate_session_token)
5. tests/test_users.py:122 (2025-10-06) - FIXED (get_user_experience)
