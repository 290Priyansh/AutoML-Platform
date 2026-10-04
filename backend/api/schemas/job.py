from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class JobCreate(BaseModel):
    model: Optional[str] = None
    target_col: Optional[str] = None

class JobStatus(BaseModel):
    job_id: str
    status: str
    current_agent: str
    progress_pct: int
    error: Optional[str] = None
    created_at: datetime

class JobResult(BaseModel):
    job_id: str
    status: str
    ranked_models: List[Dict[str, Any]]
    report_url: Optional[str] = None
    model_urls: List[str] = []

class RankedModel(BaseModel):
    rank: int
    model_name: str
    composite_score: float
    metrics: Dict[str, float]
    training_time: float
    model_path: str
    onnx_path: str
    registry_version: str

class ModelInfo(BaseModel):
    name: str
    type: str
    problem_type: str
    description: Optional[str] = None