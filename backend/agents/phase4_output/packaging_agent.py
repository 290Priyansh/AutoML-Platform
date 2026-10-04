from backend.agents.base_agent import BaseAgent
from backend.orchestrator.state import PipelineState
from backend.mlops.artifact_store import download_from_s3, upload_to_s3
from backend.mlops.mlflow_client import log_model_run
import pandas as pd
import numpy as np
import io
import joblib
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any

logger = logging.getLogger(__name__)

try:
    import skl2onnx
    from skl2onnx import convert_sklearn
    from skl2onnx.common.data_types import FloatTensorType
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    logger.warning("skl2onnx not available, ONNX export disabled")


class PackagingAgent(BaseAgent):
    name: str = "packaging_agent"
    phase: str = "phase4_output"

    def run(self, state: PipelineState) -> Dict[str, Any]:
        ranked_models = state.get("ranked_models", [])[:3]
        if not ranked_models:
            return {
                "packaged_models": {},
                "current_agent": self.name,
                "progress_pct": 100,
            }
            
        target_column = state["target_column"]
        problem_type = state["problem_type"]
        feature_columns = state.get("selected_features", state.get("feature_columns", []))
        
        packaged_models = {}
        
        for i, model_info in enumerate(ranked_models):
            model_name = model_info["model_name"]
            model_path = model_info.get("model_path", "")
            
            if not model_path or model_name.startswith("Ensemble"):
                # For ensemble models, we'd need special handling
                logger.warning(f"Skipping packaging for ensemble model: {model_name}")
                continue
            
            logger.info(f"Packaging {model_name}...")
            
            try:
                # Load full pipeline
                model_bytes = download_from_s3(model_path)
                pipeline = joblib.load(io.BytesIO(model_bytes))
                
                # 1. Save joblib
                joblib_buffer = io.BytesIO()
                joblib.dump(pipeline, joblib_buffer)
                joblib_buffer.seek(0)
                
                base_path = model_path.rsplit('/', 1)[0]
                joblib_path = upload_to_s3(joblib_buffer.getvalue(), f"{base_path}/{model_name}_final.joblib")
                
                # 2. Export to ONNX
                onnx_path = ""
                if ONNX_AVAILABLE:
                    try:
                        onnx_path = self._export_onnx(pipeline, feature_columns, base_path, model_name)
                    except Exception as e:
                        logger.warning(f"ONNX export failed for {model_name}: {e}")
                
                # 3. Register in MLflow
                registry_version = self._register_mlflow(state, model_name, pipeline, model_info, problem_type)
                
                # 4. Create model card
                model_card = self._create_model_card(state, model_name, model_info, feature_columns, problem_type)
                model_card_path = upload_to_s3(
                    json.dumps(model_card, indent=2).encode(),
                    f"{base_path}/{model_name}_model_card.json"
                )
                
                packaged_models[model_name] = {
                    "joblib_path": joblib_path,
                    "onnx_path": onnx_path,
                    "registry_version": registry_version,
                    "model_card_path": model_card_path,
                    "rank": int(model_info.get("rank", 1)),
                    "composite_score": float(model_info.get("composite_score", 0.0)),
                }
                
            except Exception as e:
                logger.error(f"Failed to package {model_name}: {e}")
        
        return {
            "packaged_models": packaged_models,
            "current_agent": self.name,
            "progress_pct": 100,
        }
    
    def _export_onnx(self, pipeline, feature_columns: list, base_path: str, model_name: str) -> str:
        """Export pipeline to ONNX format"""
        # Get the model from pipeline
        model = pipeline.named_steps.get('model', pipeline) if hasattr(pipeline, 'named_steps') else pipeline
        
        # Define input type
        n_features = len(feature_columns)
        initial_type = [('float_input', FloatTensorType([None, n_features]))]
        
        # Convert
        onnx_model = convert_sklearn(model, initial_types=initial_type)
        
        # Save
        onnx_buffer = io.BytesIO()
        onnx_model.SerializeToString()
        onnx_buffer.write(onnx_model.SerializeToString())
        onnx_buffer.seek(0)
        
        return upload_to_s3(onnx_buffer.getvalue(), f"{base_path}/{model_name}.onnx")
    
    def _register_mlflow(self, state: PipelineState, model_name: str, pipeline, model_info: dict, problem_type: str) -> str:
        """Register model in MLflow Model Registry"""
        try:
            import mlflow
            from backend.config import settings
            
            mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
            
            # Log the model
            with mlflow.start_run(run_name=f"{model_name}-{state['job_id']}", nested=True) as run:
                raw_params = model_info.get("params", {})
                params_to_log = {k: str(v)[:250] for k, v in raw_params.items() if isinstance(v, (str, int, float, bool))}
                if params_to_log:
                    mlflow.log_params(params_to_log)
                    
                raw_metrics = model_info.get("metrics", {})
                metrics_to_log = {
                    k: float(v) for k, v in raw_metrics.items()
                    if isinstance(v, (int, float)) and not isinstance(v, bool) and not np.isnan(v)
                }
                if metrics_to_log:
                    mlflow.log_metrics(metrics_to_log)
                
                # Log the full pipeline
                mlflow.sklearn.log_model(
                    pipeline,
                    artifact_path="model",
                    registered_model_name=f"automl-{model_name}",
                )
                
                # Get the registered model version
                model_uri = f"runs:/{run.info.run_id}/model"
                mv = mlflow.register_model(model_uri, f"automl-{model_name}")
                
                # Tag the model
                client = mlflow.tracking.MlflowClient()
                client.set_model_version_tag(
                    name=f"automl-{model_name}",
                    version=mv.version,
                    key="stage",
                    value="Staging"
                )
                client.set_model_version_tag(
                    name=f"automl-{model_name}",
                    version=mv.version,
                    key="job_id",
                    value=state["job_id"]
                )
                client.set_model_version_tag(
                    name=f"automl-{model_name}",
                    version=mv.version,
                    key="composite_score",
                    value=str(model_info["composite_score"])
                )
                client.set_model_version_tag(
                    name=f"automl-{model_name}",
                    version=mv.version,
                    key="problem_type",
                    value=problem_type
                )
                
                return f"v{mv.version}"
                
        except Exception as e:
            logger.warning(f"MLflow registration failed for {model_name}: {e}")
            return "unregistered"
    
    def _create_model_card(self, state: PipelineState, model_name: str, model_info: dict, 
                          feature_columns: list, problem_type: str) -> Dict[str, Any]:
        """Create model card with metadata"""
        return {
            "model_name": model_name,
            "model_type": model_name,
            "problem_type": problem_type,
            "training_date": datetime.now(timezone.utc).isoformat(),
            "job_id": state["job_id"],
            "composite_score": float(model_info.get("composite_score", 0.0)),
            "rank": int(model_info.get("rank", 1)),
            "metrics": {str(k): float(v) for k, v in model_info.get("metrics", {}).items() if isinstance(v, (int, float, np.number)) and not np.isnan(v)},
            "features": feature_columns,
            "target_column": state["target_column"],
            "training_time_seconds": model_info.get("train_time", 0),
            "data_quality_score": state.get("data_quality_score", 0),
            "preprocessing": {
                "encoding": state.get("encoding_map", {}),
                "scaling": state.get("scaler_type", "none"),
                "imbalance_handling": state.get("imbalance_strategy", "none"),
                "feature_engineering": len(state.get("engineered_features", [])),
                "feature_selection": len(state.get("selected_features", [])),
            },
            "limitations": [
                "Model trained on historical data - may not generalize to distribution shifts",
                "No causal guarantees - correlations only",
                "Fairness not guaranteed across all subgroups",
            ],
            "intended_use": f"Automated {problem_type} predictions for similar data distributions",
            "ethical_considerations": "Review bias_fairness_agent output before deployment",
        }


packaging_agent = PackagingAgent()