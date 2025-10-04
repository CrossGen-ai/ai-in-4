# Backend API Route Pattern

This document shows the standard pattern for creating new API routes with FastAPI.

## Overview

API routes in this application follow a consistent structure:
- Routes are organized by feature in `app/server/api/routes/`
- Each route file exports a FastAPI `APIRouter`
- Routers are registered in `app/server/main.py`
- Request/response validation uses Pydantic models

## Basic Route Structure

```python
# app/server/api/routes/<feature_name>.py
from fastapi import APIRouter, HTTPException
from typing import List
from models.schemas import YourRequest, YourResponse

router = APIRouter()

@router.get("/<endpoint>")
async def get_items():
    """
    GET endpoint - retrieve data

    Returns:
        dict: Response with data
    """
    return {"items": [], "total": 0}

@router.post("/<endpoint>")
async def create_item(request: YourRequest):
    """
    POST endpoint - create new data

    Args:
        request: Validated request body (Pydantic automatically validates)

    Returns:
        YourResponse: Created item response
    """
    # Business logic here
    return YourResponse(
        id=1,
        message=f"Created: {request.name}"
    )

@router.get("/<endpoint>/{item_id}")
async def get_item(item_id: int):
    """
    GET endpoint with path parameter

    Args:
        item_id: ID of the item to retrieve

    Raises:
        HTTPException: 404 if item not found

    Returns:
        dict: Item data
    """
    # Example error handling
    if item_id < 1:
        raise HTTPException(status_code=404, detail="Item not found")

    return {"id": item_id, "name": "Example"}
```

## Pydantic Models

Define request/response schemas in `app/server/models/schemas.py`:

```python
# app/server/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional

class YourRequest(BaseModel):
    """Request model with validation"""
    name: str = Field(..., min_length=1, max_length=100)
    value: int = Field(..., ge=0)
    optional_field: Optional[str] = None

class YourResponse(BaseModel):
    """Response model"""
    id: int
    message: str
    timestamp: Optional[str] = None
```

## Router Registration

Register your router in `app/server/main.py`:

```python
# app/server/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from api.routes import health, your_feature  # Import your router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(your_feature.router, prefix="/api", tags=["your_feature"])
```

## Error Handling

Use FastAPI's `HTTPException` for API errors:

```python
from fastapi import HTTPException

# 400 Bad Request
if not valid:
    raise HTTPException(status_code=400, detail="Invalid input")

# 404 Not Found
if not found:
    raise HTTPException(status_code=404, detail="Resource not found")

# 500 Internal Server Error (FastAPI handles automatically)
# Just raise regular exceptions for unexpected errors
```

## Dependency Injection (Advanced)

For shared dependencies like database connections or authentication:

```python
from fastapi import Depends
from core.dependencies import get_db, get_current_user

@router.get("/protected")
async def protected_route(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Route with dependencies"""
    return {"user": current_user.email}
```

## Testing

See `app/server/tests/README.md` for testing patterns. Basic test structure:

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_your_endpoint():
    response = client.get("/api/your-endpoint")
    assert response.status_code == 200
    assert response.json()["message"] == "expected"
```

## Working Example

See `app/server/api/routes/health.py` for the simplest working implementation:

```python
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }
```

## Best Practices

1. **One router per feature** - Keep related endpoints together
2. **Use Pydantic models** - Automatic validation and documentation
3. **Document endpoints** - Add docstrings with Args, Returns, Raises
4. **Handle errors gracefully** - Use appropriate HTTP status codes
5. **Keep routes thin** - Move business logic to `services/`
6. **Test your endpoints** - Write tests for each route

## Common Patterns

### Query Parameters
```python
@router.get("/items")
async def list_items(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None
):
    """List items with pagination and search"""
    return {"items": [], "skip": skip, "limit": limit}
```

### File Upload
```python
from fastapi import File, UploadFile

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file"""
    contents = await file.read()
    return {"filename": file.filename, "size": len(contents)}
```

### Background Tasks
```python
from fastapi import BackgroundTasks

@router.post("/send-email")
async def send_email(
    background_tasks: BackgroundTasks,
    email: str
):
    """Send email in background"""
    background_tasks.add_task(send_email_task, email)
    return {"message": "Email will be sent"}
```

## See Also

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Pydantic Models](https://docs.pydantic.dev)
- Working example: `app/server/api/routes/health.py`
- Test patterns: `app/server/tests/README.md`
