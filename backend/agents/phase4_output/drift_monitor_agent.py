from backend.agents.base_agent import BaseAgent
from backend.orchestrator.state import PipelineState
from backend.mlops.artifact_store import download_from_s3, upload_to_s3
import pandas as pd
import numpy as np
import json
import io
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

try:
    from evidently.report import Report
    from evidently.metric_preset import DataDriftPreset, TargetDriftPreset
    from evidently.metrics import ColumnDriftMetric, DatasetDriftMetric
    EVIDENTLY_AVAILABLE = True
except ImportError:
    EVIDENTLY_AVAILABLE = False
    logger.warning("Evidently not available, drift monitoring limited")


class DriftMonitorAgent(BaseAgent):
    name: str = "drift_monitor_agent"
    phase: str = "phase4_output"

    def run(self, state: PipelineState) -> Dict[str, Any]:
        ranked_models = state.get("ranked_models", [])[:3]
        test_path = state.get("selected_test_path") or state["cleaned_test_path"].replace("cleaned_test", "selected_test")
        target_column = state["target_column"]
        feature_columns = state.get("selected_features", state.get("feature_columns", []))
        
        if not EVIDENTLY_AVAILABLE:
            return {
                "drift_monitor_config": {
                    "enabled": False,
                    "message": "Evidently not available",
                },
                "current_agent": self.name,
                "progress_pct": 100,
            }
        
        # Load test data as reference with fallback
        try:
            test_df = pd.read_parquet(io.BytesIO(download_from_s3(test_path)))
        except Exception:
            test_path = state["cleaned_test_path"]
            test_df = pd.read_parquet(io.BytesIO(download_from_s3(test_path)))
            
        avail_features = [c for c in feature_columns if c in test_df.columns]
        ref_cols = avail_features + ([target_column] if target_column in test_df.columns else [])
        reference_data = test_df[ref_cols] if ref_cols else test_df
        
        drift_configs = {}
        
        for model_info in ranked_models:
            model_name = model_info["model_name"]
            model_path = model_info.get("model_path", "")
            
            if not model_path or model_name.startswith("Ensemble"):
                continue
            
            # Save reference dataset for this model
            base_path = model_path.rsplit('/', 1)[0]
            ref_path = f"{base_path}/drift_reference.parquet"
            
            ref_buffer = io.BytesIO()
            reference_data.to_parquet(ref_buffer, index=False)
            ref_buffer.seek(0)
            
            s3_ref_path = upload_to_s3(ref_buffer.getvalue(), ref_path)
            
            drift_configs[model_name] = {
                "reference_data_path": s3_ref_path,
                "feature_columns": feature_columns,
                "target_column": target_column,
                "drift_threshold": 0.3,
                "check_interval_hours": 24,
                "alert_threshold_consecutive_days": 3,
                "model_path": model_path,
            }
        
        return {
            "drift_monitor_config": drift_configs,
            "current_agent": self.name,
            "progress_pct": 100,
        }


# Celery periodic task for drift checking
def check_drift():
    """Periodic task to check drift for all deployed models"""
    # This would be called by Celery beat
    # Fetch last 1000 predictions from inference logs
    # Run Evidently drift detection
    # Trigger alert if drift_score > 0.3
    # Auto-retrain if drift persists for 3 days
    pass


drift_monitor_agent = DriftMonitorAgent()