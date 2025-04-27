🚀 AI Coding Rules for FastAPI + LangChain Codebase
🧹 General Code Style
Follow PEP8 standards (formatting, naming, etc).

Use type hints for all functions and class methods.

Write docstrings for every public class, method, and function.

Prefer 88 characters max per line (good for readability and Black formatter).

Use snake_case for functions and variables.

Use PascalCase for class names.

Prefer f-strings over .format() or % formatting.

🛡️ API Design (FastAPI)
Every API endpoint must have:

Request model (pydantic.BaseModel)

Response model (pydantic.BaseModel)

Validation at input level, not inside business logic.

Always document the endpoint with:

A summary

A description

Handle all exceptions using FastAPI exception handlers.

Example:

python
Copy
Edit
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

@router.post("/users", response_model=UserResponse, summary="Create User", description="Creates a new user.")
async def create_user(user: UserRequest):
    if user.age < 0:
        raise HTTPException(status_code=400, detail="Age must be positive.")
    return UserResponse(id=1, name=user.name, age=user.age)
🧠 AI/ML (LangChain, LangSmith, Langflow)
Prompt templates must be version-controlled and kept modular.

Always define chains and tools with explicit inputs/outputs.

Use async LangChain functions wherever possible.

Log important steps using LangSmith if observability is enabled.

Keep large LLM calls in a services/ or llm/ folder, not mixed inside API routes.

🔥 Database (Postgres, Asyncpg, SQLAlchemy)
All DB operations must be async.

Separate DB models, schemas (Pydantic), and CRUD operations into separate files.

Migrations should only be done through Alembic.

Connection pool management should happen in db.py or database.py.

🔒 Security
Always use OAuth2 / JWT tokens for protected endpoints.

Hash all sensitive data (e.g., passwords) using bcrypt.

Never expose secrets or keys in logs.

📂 Project Structure Best Practice
bash
Copy
Edit
/app
    /api
    /core
    /db
    /llm
    /models
    /schemas
    /services
    main.py
✨ Bonus Best Practices
Use dotenv for environment variables.

Always add basic rate limiting and CORS setup on FastAPI.

Write unit tests for:

API routes

Services

LLM Chains
