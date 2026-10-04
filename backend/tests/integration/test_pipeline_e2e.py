import pytest
import pandas as pd
import numpy as np
import io
import uuid
from unittest.mock import patch, MagicMock

import backend.mlops.artifact_store as artifact_store
from backend.mlops.artifact_store import upload_to_s3
from backend.orchestrator.graph import build_pipeline_graph
from backend.orchestrator.state import PipelineState

mock_storage = {}

def mock_put_object(Bucket, Key, Body):
    if hasattr(Body, "read"):
        data = Body.read()
    elif isinstance(Body, str):
        data = Body.encode("utf-8")
    else:
        data = bytes(Body)
    mock_storage[(Bucket, Key)] = data

def mock_get_object(Bucket, Key):
    if (Bucket, Key) not in mock_storage:
        raise KeyError(f"Key not found in mock S3: {Bucket}/{Key}")
    return {"Body": io.BytesIO(mock_storage[(Bucket, Key)])}

def mock_upload_file(Filename, Bucket, Key):
    with open(Filename, "rb") as f:
        mock_storage[(Bucket, Key)] = f.read()

def mock_presigned_url(*args, **kwargs):
    return "https://mock-s3-presigned-url.com/download"


@pytest.fixture(autouse=True)
def setup_mocks(monkeypatch):
    """Ensure in-memory mock S3 and MLflow for integration testing."""
    mock_storage.clear()
    monkeypatch.setattr(artifact_store.s3_client, "put_object", mock_put_object)
    monkeypatch.setattr(artifact_store.s3_client, "get_object", mock_get_object)
    monkeypatch.setattr(artifact_store.s3_client, "upload_file", mock_upload_file)
    monkeypatch.setattr(artifact_store.s3_client, "generate_presigned_url", mock_presigned_url)
    
    # Mock MLflow
    monkeypatch.setattr("backend.mlops.mlflow_client.log_model_run", lambda **kwargs: None)
    monkeypatch.setattr("backend.mlops.mlflow_client.init_mlflow", lambda: None)
    yield
    mock_storage.clear()


def create_sample_classification_csv() -> bytes:
    """Create a sample classification dataset with mixed types and some noise."""
    np.random.seed(42)
    n = 120
    df = pd.DataFrame({
        "age": np.random.randint(18, 70, size=n),
        "income": np.random.normal(50000, 15000, size=n),
        "credit_score": np.random.randint(300, 850, size=n),
        "category": np.random.choice(["A", "B", "C"], size=n),
        "gender": np.random.choice(["male", "female"], size=n),
        "target": np.random.choice([0, 1], size=n, p=[0.6, 0.4]),
    })
    # Add a few NaNs to test cleaning
    df.loc[0, "income"] = np.nan
    df.loc[1, "category"] = np.nan
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")


def create_sample_regression_csv() -> bytes:
    """Create a sample regression dataset."""
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        "size_sqft": np.random.randint(500, 3500, size=n),
        "bedrooms": np.random.randint(1, 6, size=n),
        "neighborhood": np.random.choice(["Downtown", "Suburbs", "Rural"], size=n),
        "price": np.random.normal(300000, 80000, size=n),
    })
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")


class TestAutoMLPipelineE2E:

    @patch("backend.llm.router.get_llm")
    def test_classification_pipeline_e2e(self, mock_get_llm):
        """Run full 23-agent pipeline end-to-end on classification data."""
        # Mock LLM response to return valid structure when called
        mock_llm_instance = MagicMock()
        mock_resp = MagicMock()
        mock_resp.content = '{"cleaned_text": "text", "rationale": "Top model chosen based on metrics", "narrative": "No significant bias detected", "recommendations": []}'
        mock_llm_instance.invoke.return_value = mock_resp
        mock_get_llm.return_value = mock_llm_instance

        job_id = f"test-classif-{uuid.uuid4().hex[:8]}"
        raw_csv_bytes = create_sample_classification_csv()
        raw_key = f"users/test/jobs/{job_id}/raw_data.csv"
        upload_to_s3(raw_csv_bytes, raw_key)

        initial_state: PipelineState = {
            "job_id": job_id,
            "user_id": "test_user",
            "created_at": "2026-09-21T00:00:00",
            "status": "queued",
            "current_agent": "ingestion",
            "progress_pct": 0,
            "error": None,
            "raw_data_path": raw_key,
            "data_source_type": "csv",
            "user_model_preference": None,
            "dataframe_path": "",
            "schema": {},
            "row_count": 0,
            "col_count": 0,
            "eda_report": {},
            "problem_type": "",
            "target_column": "target",
            "feature_columns": [],
            "data_quality_score": 0.0,
            "data_quality_flags": [],
            "train_path": "",
            "val_path": "",
            "test_path": "",
            "split_strategy": "",
            "cleaned_train_path": "",
            "cleaned_val_path": "",
            "cleaned_test_path": "",
            "text_columns": [],
            "embedding_columns": [],
            "encoding_map": {},
            "scaler_type": "",
            "engineered_features": [],
            "selected_features": [],
            "imbalance_strategy": "",
            "preprocessor_path": "",
            "trained_models": {},
            "hpo_results": {},
            "evaluation_results": {},
            "cv_strategy": "",
            "ranked_models": [],
            "ensemble_model_path": None,
            "shap_plots_path": {},
            "lime_explanations_path": {},
            "feature_importance": {},
            "bias_report": {},
            "final_report_md": "",
            "packaged_models": {},
            "inference_endpoints": {},
            "drift_monitor_config": {},
        }

        # Build graph and run
        graph = build_pipeline_graph()
        config = {"configurable": {"thread_id": job_id}}

        final_state = None
        for event in graph.stream(initial_state, config=config):
            agent_name = list(event.keys())[0]
            final_state = event[agent_name]
            assert final_state.get("status") != "failed", f"Failed at {agent_name}: {final_state.get('error')}"

        assert final_state is not None
        # Verify downstream artifacts
        assert final_state.get("progress_pct") == 100

    @patch("backend.llm.router.get_llm")
    def test_regression_pipeline_e2e(self, mock_get_llm):
        """Run full 23-agent pipeline end-to-end on regression data."""
        mock_llm_instance = MagicMock()
        mock_resp = MagicMock()
        mock_resp.content = '{"cleaned_text": "text", "rationale": "Top model chosen", "narrative": "Fairness report", "recommendations": []}'
        mock_llm_instance.invoke.return_value = mock_resp
        mock_get_llm.return_value = mock_llm_instance

        job_id = f"test-reg-{uuid.uuid4().hex[:8]}"
        raw_csv_bytes = create_sample_regression_csv()
        raw_key = f"users/test/jobs/{job_id}/raw_data.csv"
        upload_to_s3(raw_csv_bytes, raw_key)

        initial_state: PipelineState = {
            "job_id": job_id,
            "user_id": "test_user",
            "created_at": "2026-09-21T00:00:00",
            "status": "queued",
            "current_agent": "ingestion",
            "progress_pct": 0,
            "error": None,
            "raw_data_path": raw_key,
            "data_source_type": "csv",
            "user_model_preference": None,
            "dataframe_path": "",
            "schema": {},
            "row_count": 0,
            "col_count": 0,
            "eda_report": {},
            "problem_type": "regression",
            "target_column": "price",
            "feature_columns": [],
            "data_quality_score": 0.0,
            "data_quality_flags": [],
            "train_path": "",
            "val_path": "",
            "test_path": "",
            "split_strategy": "",
            "cleaned_train_path": "",
            "cleaned_val_path": "",
            "cleaned_test_path": "",
            "text_columns": [],
            "embedding_columns": [],
            "encoding_map": {},
            "scaler_type": "",
            "engineered_features": [],
            "selected_features": [],
            "imbalance_strategy": "",
            "preprocessor_path": "",
            "trained_models": {},
            "hpo_results": {},
            "evaluation_results": {},
            "cv_strategy": "",
            "ranked_models": [],
            "ensemble_model_path": None,
            "shap_plots_path": {},
            "lime_explanations_path": {},
            "feature_importance": {},
            "bias_report": {},
            "final_report_md": "",
            "packaged_models": {},
            "inference_endpoints": {},
            "drift_monitor_config": {},
        }

        graph = build_pipeline_graph()
        config = {"configurable": {"thread_id": job_id}}

        final_state = None
        for event in graph.stream(initial_state, config=config):
            agent_name = list(event.keys())[0]
            final_state = event[agent_name]
            assert final_state.get("status") != "failed", f"Failed at {agent_name}: {final_state.get('error')}"

        assert final_state is not None
        assert final_state.get("progress_pct") == 100
