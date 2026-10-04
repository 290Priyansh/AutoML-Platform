try:
    import mlflow
    MLFLOW_AVAILABLE = True
except ImportError:
    mlflow = None
    MLFLOW_AVAILABLE = False

import numpy as np
from backend.config import settings
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

_mlflow_initialized = False

def init_mlflow():
    """Initialize MLflow tracking"""
    global _mlflow_initialized
    if not MLFLOW_AVAILABLE:
        return
    if not _mlflow_initialized:
        try:
            mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
            _mlflow_initialized = True
        except Exception as e:
            logger.warning(f"Could not set MLflow tracking URI: {e}")

def patch_langgraph_checkpoint_msgpack():
    """Ensure LangGraph checkpoint msgpack serializer handles numpy scalar and array types seamlessly."""
    try:
        import numpy as np
        import langgraph.checkpoint.serde.jsonplus as j
        if getattr(j, "_numpy_patch_applied", False):
            return
        orig = j._msgpack_default
        def safe_msgpack_default(obj):
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, np.bool_):
                return bool(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return orig(obj)
        j._msgpack_default = safe_msgpack_default
        j._numpy_patch_applied = True
    except Exception as e:
        logger.warning(f"Could not patch langgraph msgpack serializer: {e}")

# Apply patch at module import
patch_langgraph_checkpoint_msgpack()

def get_checkpointer():
    """Get Postgres checkpointer for LangGraph with graceful MemorySaver fallback"""
    patch_langgraph_checkpoint_msgpack()
    try:
        from langgraph.checkpoint.postgres import PostgresSaver
        from psycopg_pool import ConnectionPool
        pool = ConnectionPool(conninfo=settings.POSTGRES_URL.replace("+asyncpg", ""), max_size=10)
        return PostgresSaver(pool)
    except Exception as e:
        logger.info(f"Postgres checkpointer not available ({e}), falling back to MemorySaver")
        try:
            from langgraph.checkpoint.memory import MemorySaver
            return MemorySaver()
        except Exception:
            return None

def start_job_run(job_id: str, problem_type: str) -> str:
    """Start a parent MLflow run for the entire job."""
    try:
        init_mlflow()
        with mlflow.start_run(run_name=f"automl-{job_id}") as run:
            mlflow.set_tags({
                "job_id": job_id, 
                "problem_type": problem_type, 
                "source": "automl-platform"
            })
            return run.info.run_id
    except Exception as e:
        logger.warning(f"MLflow start_job_run failed: {e}")
        return ""

def log_model_run(job_id: str, model_name: str, params: Dict[str, Any], 
                  metrics: Dict[str, float], model_obj, preprocessor=None):
    """Log a single model as a child run with its preprocessor pipeline."""
    try:
        init_mlflow()
        from sklearn.pipeline import Pipeline
        numeric_metrics = {k: float(v) for k, v in metrics.items() if isinstance(v, (int, float, np.number))}
        with mlflow.start_run(run_name=f"{model_name}-{job_id}", nested=True):
            if params:
                mlflow.log_params(params)
            if numeric_metrics:
                mlflow.log_metrics(numeric_metrics)
            # Log the full sklearn pipeline (preprocessor + model)
            if preprocessor is not None:
                pipeline = Pipeline([("preprocessor", preprocessor), ("model", model_obj)])
            else:
                pipeline = Pipeline([("model", model_obj)])
            mlflow.sklearn.log_model(
                pipeline, 
                artifact_path="model",
                registered_model_name=f"automl-{model_name}"
            )
    except Exception as e:
        logger.warning(f"MLflow log_model_run failed for {model_name}: {e}")

def log_agent_run(job_id: str, agent: str, duration: float, success: bool, error: str = None):
    """Log agent execution metrics."""
    try:
        init_mlflow()
        mlflow.log_metrics({
            f"{agent}_duration_s": duration,
            f"{agent}_success": int(success),
        })
        if error:
            mlflow.log_param(f"{agent}_error", error)
    except Exception as e:
        logger.debug(f"MLflow log_agent_run failed: {e}")