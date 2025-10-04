from pydantic import BaseModel
from typing import Optional

# Define your Pydantic models here
class HealthCheckResponse(BaseModel):
    status: str
    timestamp: Optional[str] = None
