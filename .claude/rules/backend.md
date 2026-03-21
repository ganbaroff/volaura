# Backend Rules (FastAPI + Supabase)

## Supabase Client Pattern
```python
# CORRECT: per-request client via Depends()
from app.deps import SupabaseAdmin, SupabaseUser, CurrentUserId

@router.get("/endpoint")
async def my_endpoint(db: SupabaseUser, user_id: CurrentUserId):
    result = await db.table("profiles").select("*").eq("id", user_id).execute()
    return result.data

# WRONG: never use global client
# supabase = acreate_client(URL, KEY)  ← NEVER at module level
```

## Pydantic v2 Only
```python
# CORRECT
from pydantic import BaseModel, ConfigDict, field_validator

class MyModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()

# WRONG — Pydantic v1 syntax
# class Config: orm_mode = True  ← NEVER
# @validator("name")  ← NEVER
```

## Error Handling
Always return structured errors:
```python
from fastapi import HTTPException

raise HTTPException(
    status_code=404,
    detail={"code": "PROFILE_NOT_FOUND", "message": "Profile not found"}
)
```

## Logging
```python
from loguru import logger

logger.info("Processing assessment", user_id=user_id)
logger.error("LLM evaluation failed", error=str(e))
# NEVER: print("something")
```

## LLM Calls
```python
# Primary: Gemini via google-genai
from google import genai
client = genai.Client(api_key=settings.gemini_api_key)

# Use the service from app.services.llm
from app.services.llm import evaluate_with_llm
result = await evaluate_with_llm(prompt, response_format="json")
```

## UTF-8
Always specify encoding when working with files:
```python
with open(path, "r", encoding="utf-8") as f:
    ...
```
