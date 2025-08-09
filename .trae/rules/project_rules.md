Here’s the cleaned-up and professionally structured version of your **AI Coding Rules for FastAPI + LangChain Codebase**, integrating best practices from your current folder structure, conventions, and team guidelines:

---

# 🚀 AI Coding Standards for VecApp (FastAPI + LangChain)

## 🧹 General Code Style

* Follow **PEP8** and use **Black** for formatting (88-character line length preferred).
* Always use **type hints** on function signatures.
* Add **docstrings** to all public classes, functions, and methods.
* Use `snake_case` for variables and functions; `PascalCase` for class names.
* Prefer **f-strings** (`f"{name}"`) over `.format()` or `%` formatting.
* Use **async/await** where appropriate — especially for I/O, DB, and LLM calls.

---

## 🛡️ FastAPI API Design

### ✅ Required for Every Endpoint:

* A **Pydantic Request Model** (`BaseModel`).
* A **Pydantic Response Model**.
* Input validation must be enforced in the model layer, not in the business logic.
* Use:

  * `summary` and `description` in route decorators.
  * Proper `response_model` declaration.
* All exceptions must use FastAPI's built-in handlers (e.g., `HTTPException`).

### 🔍 Example:

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class UserRequest(BaseModel):
    name: str
    age: int

class UserResponse(BaseModel):
    id: int
    name: str
    age: int

@router.post(
    "/users",
    response_model=UserResponse,
    summary="Create User",
    description="Creates a new user."
)
async def create_user(user: UserRequest):
    if user.age < 0:
        raise HTTPException(status_code=400, detail="Age must be positive.")
    return UserResponse(id=1, name=user.name, age=user.age)
```

---

## 🧠 AI/ML Integration (LangChain / LangSmith / Langflow)

* Prompt templates must be:

  * **Version-controlled**
  * **Modular and reusable**
* Define all **Chains and Tools** with **explicit input/output schemas**.
* Prefer **async LangChain** integrations for LLM calls.
* Log key steps using **LangSmith** (when observability is enabled).
* Place all LLM chains/tools in `llm/` or `services/llm_service.py`; never inline in `api/routes`.

---

## 🔥 Database Layer (Postgres, SQLAlchemy, AsyncPG)

* All DB interactions must be **async**.
* Follow separation of concerns:

  * `models/` – SQLAlchemy models
  * `schemas/` – Pydantic schemas (for API)
  * `repositories/` – DB access layer
* Manage DB connections in a centralized `database.py` or `db.py`.
* All migrations must go through Alembic, using:

  * `app/database/migrations/public/`
  * `app/database/migrations/tenant/`
* ❌ Do not use or place files in the legacy `/migrations/` folder at root.

---

## 🔒 Security

* Use **OAuth2 / JWT** for protecting endpoints.
* Always hash passwords and sensitive data using `bcrypt`.
* Never log secrets, tokens, or credentials.
* Enforce **RBAC** (role-based access control) at the API and database levels.

---

## 📂 Folder & File Structure Guidelines

### ✅ Placement Rules

| Type                      | Path                         | Example File                                |
| ------------------------- | ---------------------------- | ------------------------------------------- |
| FastAPI routes            | `app/api/routes/`            | `visitor.py`, `feedback.py`                 |
| Pydantic schemas          | `app/api/schemas/`           | `visitor.py`, `notes.py`                    |
| LangChain agents          | `app/agents/`                | `followup_note_agent.py`                    |
| LLM prompt/chains         | `llm/`                       | `prompts.py`, `chains.py`                   |
| Services / business logic | `app/services/`              | `langchain_service.py`, `report_service.py` |
| DB models                 | `app/database/models/`       | `visitor.py`, `feedback.py`                 |
| DB migrations             | `app/database/migrations/`   | `tenant/`, `public/`                        |
| DB repositories           | `app/database/repositories/` | `visitor_repository.py`                     |
| Caching                   | `app/data/cache/`            | `repository_cache.py`                       |
| Event handling            | `app/data/events/`           | `visitor_event_listener.py`                 |
| Testing                   | `tests/` or `app/tests/`     | `test_followup_api.py`                      |
| Documentation             | `docs/`                      | `FOLLOWUP_NOTES_README.md`                  |
| Infra / deployment        | `infra/`, `deployments/`     | `k8s-local/`, `vecapp-ai-depl.yaml`         |

### ❌ Avoid:

* Placing **app logic in root** (outside `/app/`)
* Storing migration files in root `/migrations/`
* Writing **raw SQL in route handlers** (use repository pattern)

---

## ✨ Engineering Best Practices

* Use **dotenv** for managing secrets and environment configuration.
* Set up **rate limiting and CORS policies** for all production APIs.
* All long-running or task-heavy logic should go through **background tasks** or **worker queues (e.g., Celery, AWS SQS)**.

---

## 🧪 Testing Requirements

* Write tests for:

  * API routes (`app/tests/test_*.py`)
  * LangChain agents and chains
  * Services and repositories
* Use **Pytest** + **Async fixtures**
* Target code coverage ≥ 90% on all critical paths.

