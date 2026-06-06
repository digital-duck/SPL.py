This step introduces a `schemas.py` file with two Pydantic request-body models — `TodoCreate` (requiring `title`, optional `completed`) and `TodoUpdate` (all fields optional for partial updates) — keeping input shapes separate from the `Todo` domain model. FastAPI's built-in Pydantic integration automatically returns 422 Unprocessable Entity when validation fails, while `routes.py` is updated to declare these schemas as handler parameter types and standardize the existing `HTTPException(404)` raises.

**Files created/modified:**
- `schemas.py` — `TodoCreate` and `TodoUpdate` Pydantic models
- `routes.py` — handlers updated to accept schema types and raise typed 404s