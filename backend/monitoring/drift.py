try:
    from evidently.report import Report
    from evidently.metric_preset import DataDriftPreset, TargetDriftPreset
    from evidently.metrics import ColumnDriftMetric, DatasetDriftMetric
    EVIDENTLY_AVAILABLE = True
except ImportError:
    EVIDENTLY_AVAILABLE = False
from backend.config import settings
from backend.mlops.artifact_store import download_from_s3, upload_to_s3
import pandas as pd
import json
import logging

logger = logging.getLogger(__name__)

def create_drift_monitor_config(reference_data_path: str, feature_columns: list, target_column: str) -> dict:
    """Create Evidently drift monitoring configuration"""
    return {
        "reference_data_path": reference_data_path,
        "feature_columns": feature_columns,
        "target_column": target_column,
        "drift_threshold": 0.3,
        "check_interval_hours": 24,
        "alert_threshold_consecutive_days": 3,
    }

def run_drift_check(
    reference_data_path: str,
    current_data_path: str,
    feature_columns: list,
    target_column: str = None,
) -> dict:
    """Run Evidently drift detection between reference and current data"""
    if not EVIDENTLY_AVAILABLE:
        return {"drift_detected": False, "error": "Evidently is not available"}
    try:
        import os
        import io

        # Load reference data
        if str(reference_data_path).startswith("s3://") or not os.path.exists(str(reference_data_path)):
            ref_data = pd.read_parquet(io.BytesIO(download_from_s3(reference_data_path)))
        else:
            ref_data = pd.read_parquet(reference_data_path)
        
        # Load current data
        if str(current_data_path).startswith("s3://") or not os.path.exists(str(current_data_path)):
            curr_data = pd.read_parquet(io.BytesIO(download_from_s3(current_data_path)))
        else:
            curr_data = pd.read_parquet(current_data_path)
        
        # Create report
        metrics = [
            DatasetDriftMetric(),
        ]
        
        for col in feature_columns:
            if col in ref_data.columns and col in curr_data.columns:
                metrics.append(ColumnDriftMetric(column_name=col))
        
        if target_column and target_column in ref_data.columns and target_column in curr_data.columns:
            metrics.append(ColumnDriftMetric(column_name=target_column))
        
        report = Report(metrics=metrics)
        report.run(reference_data=ref_data, current_data=curr_data)
        
        result = report.as_dict()
        
        # Extract drift score
        drift_score = result["metrics"][0]["result"]["dataset_drift"]
        
        return {
            "drift_detected": drift_score,
            "drift_score": drift_score,
            "details": result,
            "timestamp": pd.Timestamp.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Drift check failed: {e}")
        return {"drift_detected": False, "error": str(e)}

def save_reference_dataset(data_path: str, feature_columns: list, target_column: str, job_id: str) -> str:
    """Save test set statistics as Evidently ReferenceDataset"""
    # This would save the reference data for drift monitoring
    # Implementation depends on Evidently version
    return f"s3://{settings.S3_BUCKET_NAME}/drift_references/{job_id}/reference.parquet"