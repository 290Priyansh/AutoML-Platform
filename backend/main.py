from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.api.routes import health, jobs, models
from backend.api.websocket import router as websocket_router
import logging

try:
    from prometheus_fastapi_instrumentator import Instrumentator
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AutoML Platform API",
    description="AutoML-as-a-Service backend",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
if PROMETHEUS_AVAILABLE:
    Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

# Include routers
app.include_router(health.router, tags=["health-root"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])
app.include_router(models.router, prefix="/api/v1", tags=["models"])
app.include_router(websocket_router, prefix="/api/v1", tags=["websocket"])

@app.on_event("startup")
async def startup_event():
    logger.info("AutoML Platform API starting up...")
    # Initialize MLflow and serializer patches
    from backend.mlops.mlflow_client import init_mlflow, patch_langgraph_checkpoint_msgpack
    patch_langgraph_checkpoint_msgpack()
    init_mlflow()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("AutoML Platform API shutting down...")