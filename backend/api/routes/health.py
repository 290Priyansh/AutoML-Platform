from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"

class MetricsResponse(BaseModel):
    message: str = "Prometheus metrics available at /metrics"

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse()

@router.get("/metrics", response_model=MetricsResponse)
async def metrics():
    return MetricsResponse()