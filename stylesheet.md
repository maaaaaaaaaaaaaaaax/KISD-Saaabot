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

## Imports

```python
# 1. stdlib
import os
from pathlib import Path

# 2. third-party
import httpx
from pydantic import BaseModel

# 3. local
from .user-service import UserService
```

---

## Types

Use type hints everywhere. Prefer `|` union syntax (3.10+).

```python
def get_user(user_id: int) -> User | None:
    ...

def process(items: list[str], limit: int = 10) -> dict[str, int]:
    ...
```

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

## Classes

```python
class UserService:
    """Handles user CRUD and authentication."""

    def __init__(self, db: Database, cache: Cache | None = None) -> None:
        self._db = db
        self._cache = cache

    def get(self, user_id: int) -> User | None:
        """Fetch user by ID."""
        ...

    def create(self, payload: CreateUserPayload) -> User:
        """Create and persist a new user."""
        ...

    def _validate(self, payload: CreateUserPayload) -> None:
        """Internal validation — not part of public API."""
        ...
```

- `__init__` never does heavy work (I/O, network)
- Private methods prefixed with `_`
- Class-level constants in `UPPER_SNAKE_CASE` directly on the class

---

## Constants & Config

```python
# constants.py
MAX_RETRIES: int = 3
DEFAULT_TIMEOUT: float = 30.0
BASE_URL: str = "https://api.example.com"
```

---

## Error Handling

```python
# Define narrow, descriptive exceptions
class NotFoundError(Exception): ...
class ValidationError(Exception): ...

# Catch specific, not broad
try:
    user = fetch_user(user_id)
except NotFoundError:
    return None
except DatabaseError as e:
    logger.error("db failure", exc_info=e)
    raise
```

- Never `except Exception` without re-raising
- Custom exceptions over generic ones

---

## Data Models

Prefer `dataclasses` for plain data, `pydantic` for validation/serialization.

```python
from dataclasses import dataclass, field
from pydantic import BaseModel

@dataclass
class Point:
    x: float
    y: float
    tags: list[str] = field(default_factory=list)

class CreateUserPayload(BaseModel):
    name: str
    email: str
    role: str = "viewer"
```

---

## Async

```python
async def fetch_data(url: str) -> dict:
    """Fetch JSON from a URL.

    Args:
        url: Fully-qualified URL.

    Returns:
        Parsed JSON body.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
```

- Use `async/await` consistently — don't mix sync blocking calls in async functions
- Prefer `asyncio.gather` for concurrent tasks

---

## Formatting

Enforced via tooling, not convention:

| Tool | Purpose |
|---|---|
| `ruff` | Linting + import sorting |

---

## What to Avoid

- `from module import *`
- Mutable default arguments
- Bare `except:` clauses
- `type: ignore` without a comment explaining why
- Logic inside `__init__.py`
