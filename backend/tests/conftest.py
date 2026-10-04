import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock external dependencies
import os
os.environ["POSTGRES_URL"] = "postgresql+asyncpg://user:pass@localhost:5432/automl_db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["MLFLOW_TRACKING_URI"] = "http://localhost:5000"
os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://localhost:9000"
os.environ["S3_BUCKET_NAME"] = "automl-artifacts"
os.environ["S3_DATA_BUCKET"] = "automl-datasets"
os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
os.environ["AWS_REGION"] = "us-east-1"
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
os.environ["PRIMARY_LLM_PROVIDER"] = "ollama"
os.environ["FALLBACK_LLM_PROVIDER"] = "ollama"

# Pytest fixtures
@pytest.fixture
def mock_state():
    """Create a mock pipeline state for testing"""
    return {
        "job_id": "test-job-123",
        "user_id": "test-user",
        "created_at": "2024-01-01T00:00:00Z",
        "status": "running",
        "current_agent": "test",
        "progress_pct": 0,
        "error": None,
        "raw_data_path": "s3://bucket/test.csv",
        "data_source_type": "csv",
        "user_model_preference": None,
        "dataframe_path": "",
        "schema": {},
        "row_count": 0,
        "col_count": 0,
        "eda_report": {},
        "problem_type": "",
        "target_column": "",
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

@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe for testing"""
    import pandas as pd
    import numpy as np
    
    np.random.seed(42)
    n = 1000
    
    df = pd.DataFrame({
        'feature1': np.random.randn(n),
        'feature2': np.random.randn(n),
        'feature3': np.random.choice(['A', 'B', 'C'], n),
        'feature4': np.random.randint(1, 10, n),
        'target': np.random.choice([0, 1], n),
    })
    
    return df

@pytest.fixture
def sample_regression_dataframe():
    """Create a sample regression dataframe for testing"""
    import pandas as pd
    import numpy as np
    
    np.random.seed(42)
    n = 1000
    
    df = pd.DataFrame({
        'feature1': np.random.randn(n),
        'feature2': np.random.randn(n),
        'feature3': np.random.choice(['A', 'B', 'C'], n),
        'feature4': np.random.randint(1, 10, n),
        'target': np.random.randn(n) * 100 + 50,
    })
    
    return df