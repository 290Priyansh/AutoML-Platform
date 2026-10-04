from backend.agents.base_agent import BaseAgent
from backend.orchestrator.state import PipelineState
from backend.mlops.artifact_store import download_from_s3, upload_to_s3
from backend.mlops.mlflow_client import log_model_run
from backend.monitoring.prometheus import MODEL_TRAIN_DURATION
import pandas as pd
import numpy as np
import io
import joblib
import time
import logging
from typing import Dict, Any
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, AdaBoostClassifier, GradientBoostingRegressor
from sklearn.svm import SVC, SVR
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier, MLPRegressor
try:
    from xgboost import XGBClassifier, XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBClassifier, XGBRegressor = None, None
    XGBOOST_AVAILABLE = False

try:
    from lightgbm import LGBMClassifier, LGBMRegressor
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LGBMClassifier, LGBMRegressor = None, None
    LIGHTGBM_AVAILABLE = False

logger = logging.getLogger(__name__)


class TrainingAgent(BaseAgent):
    name: str = "training_agent"
    phase: str = "phase3_modeling"

    def run(self, state: PipelineState) -> Dict[str, Any]:
        problem_type = state["problem_type"]
        train_path = state.get("resampled_train_path") or state["cleaned_train_path"].replace("cleaned_train", "resampled_train")
        val_path = state.get("selected_val_path") or state["cleaned_val_path"].replace("cleaned_val", "selected_val")
        target_column = state["target_column"]
        preprocessor_path = state.get("preprocessor_path", "")
        
        # Load data with fallback
        try:
            train_df = pd.read_parquet(io.BytesIO(download_from_s3(train_path)))
        except Exception:
            try:
                train_path = state.get("selected_train_path") or state["cleaned_train_path"].replace("cleaned_train", "selected_train")
                train_df = pd.read_parquet(io.BytesIO(download_from_s3(train_path)))
            except Exception:
                train_path = state["cleaned_train_path"]
                train_df = pd.read_parquet(io.BytesIO(download_from_s3(train_path)))

        try:
            val_df = pd.read_parquet(io.BytesIO(download_from_s3(val_path)))
        except Exception:
            val_path = state["cleaned_val_path"]
            val_df = pd.read_parquet(io.BytesIO(download_from_s3(val_path)))
        
        X_train = train_df.drop(columns=[target_column]) if target_column in train_df.columns else train_df
        y_train = train_df[target_column] if target_column in train_df.columns else None
        X_val = val_df.drop(columns=[target_column]) if target_column in val_df.columns else val_df
        y_val = val_df[target_column] if target_column in val_df.columns else None

        # Encode string/object classification target labels if present
        label_encoder = None
        if problem_type == "classification" and y_train is not None:
            if not pd.api.types.is_numeric_dtype(y_train) or y_train.dtype == 'object':
                from sklearn.preprocessing import LabelEncoder
                label_encoder = LabelEncoder()
                y_train = pd.Series(label_encoder.fit_transform(y_train.astype(str)), index=train_df.index)
                if y_val is not None:
                    y_val = pd.Series(label_encoder.transform(y_val.astype(str)), index=val_df.index)
        
        # Define models to train
        if problem_type == "classification":
            models = self._get_classification_models()
        else:
            models = self._get_regression_models()
        
        trained_models = {}
        
        base_path = train_path.replace("resampled_train.parquet", "").replace("selected_train.parquet", "").replace("cleaned_train.parquet", "") if ("resampled_train.parquet" in train_path or "selected_train.parquet" in train_path or "cleaned_train.parquet" in train_path) else f"{train_path.rsplit('/', 1)[0]}/"
        
        label_encoder_path = None
        if label_encoder is not None:
            le_buffer = io.BytesIO()
            joblib.dump(label_encoder, le_buffer)
            le_buffer.seek(0)
            label_encoder_path = f"{base_path}label_encoder.joblib"
            upload_to_s3(le_buffer.getvalue(), label_encoder_path)

        for model_name, model in models.items():
            logger.info(f"Training {model_name}...")
            start_time = time.time()
            
            try:
                full_pipeline = Pipeline([
                    ('model', model)
                ])
                
                # Train
                full_pipeline.fit(X_train, y_train)
                
                # Evaluate on validation set
                val_score = full_pipeline.score(X_val, y_val) if y_val is not None else 0.0
                train_time = time.time() - start_time
                
                # Save model
                model_buffer = io.BytesIO()
                joblib.dump(full_pipeline, model_buffer)
                model_buffer.seek(0)
                
                model_path = upload_to_s3(model_buffer.getvalue(), f"{base_path}models/{model_name}.joblib")
                
                trained_models[model_name] = {
                    "path": model_path,
                    "params": model.get_params(),
                    "val_score": float(val_score),
                    "train_time": train_time,
                }
                
                # Log to Prometheus
                MODEL_TRAIN_DURATION.labels(model_name=model_name).observe(train_time)
                
                logger.info(f"{model_name} trained in {train_time:.2f}s, val_score: {val_score:.4f}")
                
            except Exception as e:
                logger.error(f"Failed to train {model_name}: {e}")
                trained_models[model_name] = {
                    "path": "",
                    "params": {},
                    "val_score": 0.0,
                    "train_time": 0.0,
                    "error": str(e),
                }
        
        result = {
            "trained_models": trained_models,
            "current_agent": self.name,
            "progress_pct": 90,
        }
        if label_encoder_path:
            result["label_encoder_path"] = label_encoder_path
        return result
    
    def _get_classification_models(self) -> Dict[str, Any]:
        models = {
            "LogisticRegression": LogisticRegression(max_iter=1000, random_state=42),
            "RandomForestClassifier": RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=1),
            "MLPClassifier": MLPClassifier(hidden_layer_sizes=(100, 50), max_iter=500, random_state=42),
            "SVC": SVC(probability=True, random_state=42, max_iter=2000),
            "KNeighborsClassifier": KNeighborsClassifier(n_neighbors=5),
            "AdaBoostClassifier": AdaBoostClassifier(n_estimators=100, random_state=42),
        }
        if XGBOOST_AVAILABLE and XGBClassifier is not None:
            models["XGBClassifier"] = XGBClassifier(n_estimators=100, eval_metric='logloss', random_state=42, n_jobs=1)
        if LIGHTGBM_AVAILABLE and LGBMClassifier is not None:
            models["LGBMClassifier"] = LGBMClassifier(n_estimators=100, random_state=42, verbose=-1, n_jobs=1)
        return models
    
    def _get_regression_models(self) -> Dict[str, Any]:
        models = {
            "LinearRegression": LinearRegression(),
            "Ridge": Ridge(alpha=1.0),
            "RandomForestRegressor": RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=1),
            "SVR": SVR(kernel='rbf', max_iter=2000),
            "MLPRegressor": MLPRegressor(hidden_layer_sizes=(100, 50), max_iter=500, random_state=42),
            "GradientBoostingRegressor": GradientBoostingRegressor(n_estimators=100, random_state=42),
        }
        if XGBOOST_AVAILABLE and XGBRegressor is not None:
            models["XGBRegressor"] = XGBRegressor(n_estimators=100, random_state=42, n_jobs=1)
        if LIGHTGBM_AVAILABLE and LGBMRegressor is not None:
            models["LGBMRegressor"] = LGBMRegressor(n_estimators=100, random_state=42, verbose=-1, n_jobs=1)
        return models


training_agent = TrainingAgent()