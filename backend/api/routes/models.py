from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

class ModelInfo(BaseModel):
    name: str
    type: str
    problem_type: str

@router.get("/models/available", response_model=List[ModelInfo])
async def get_available_models():
    """List all model types the system supports"""
    return [
        ModelInfo(name="LogisticRegression", type="classification", problem_type="classification"),
        ModelInfo(name="RandomForestClassifier", type="classification", problem_type="classification"),
        ModelInfo(name="XGBClassifier", type="classification", problem_type="classification"),
        ModelInfo(name="LGBMClassifier", type="classification", problem_type="classification"),
        ModelInfo(name="MLPClassifier", type="classification", problem_type="classification"),
        ModelInfo(name="SVC", type="classification", problem_type="classification"),
        ModelInfo(name="KNeighborsClassifier", type="classification", problem_type="classification"),
        ModelInfo(name="AdaBoostClassifier", type="classification", problem_type="classification"),
        ModelInfo(name="LinearRegression", type="regression", problem_type="regression"),
        ModelInfo(name="Ridge", type="regression", problem_type="regression"),
        ModelInfo(name="RandomForestRegressor", type="regression", problem_type="regression"),
        ModelInfo(name="XGBRegressor", type="regression", problem_type="regression"),
        ModelInfo(name="LGBMRegressor", type="regression", problem_type="regression"),
        ModelInfo(name="SVR", type="regression", problem_type="regression"),
        ModelInfo(name="MLPRegressor", type="regression", problem_type="regression"),
        ModelInfo(name="GradientBoostingRegressor", type="regression", problem_type="regression"),
    ]