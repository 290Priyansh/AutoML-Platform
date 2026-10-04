from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ModelInfo(BaseModel):
    name: str
    type: str
    problem_type: str
    description: Optional[str] = None

class RankedModel(BaseModel):
    rank: int
    model_name: str
    composite_score: float
    metrics: Dict[str, float]
    training_time: float
    model_path: str
    onnx_path: str
    registry_version: str