# Python Style Guide

A modern Python stylesheet with naming conventions mirrored from TypeScript.

---

## Naming

| Construct | Convention | Example |
|---|---|---|
| Files | `kebab-case` | `user-service.py`, `auth.py` |
| Variables | `snake_case` | `user_id`, `is_active` |
| Functions | `snake_case` | `get_user()`, `parse_token()` |
| Classes | `PascalCase` | `UserService`, `HttpClient` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRIES`, `BASE_URL` |
| Type aliases | `PascalCase` | `UserId = int` |
| Enums | `PascalCase` members `UPPER_SNAKE` | `class Status(Enum): ACTIVE = "active"` |
| Private | leading underscore | `_internal_state` |

---

## Files

```
src/
  user-service.py
  auth-middleware.py
  db.py
tests/
  test-user-service.py
```

- One primary class or concern per file
- Test files mirror source: `user-service.py` -> `test-user-service.py`

---

## Functions

```python
def fetch_user(user_id: int, include_roles: bool = False) -> User | None:
    """Fetch a user by ID.

    Args:
        user_id: The user's primary key.
        include_roles: Whether to hydrate role data.

    Returns:
        User if found, None otherwise.

    Raises:
        DatabaseError: On connection failure.
    """
    ...
```

- Keep docstrings short — one line summary, then args/returns only if non-obvious
- Default args go last
- No mutable defaults (`[]`, `{}`) — use `None` and guard inside

---

## Formatting

Enforced via tooling, not convention:

| Tool | Purpose |
|---|---|
| `ruff` | Linting + import sorting + formatting |

---

## What to Avoid

- `from module import *`
- Mutable default arguments
- Bare `except:` clauses
- `type: ignore` without a comment explaining why
- Logic inside `__init__.py`
