import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from backend.main import app
from backend.orchestrator.store import set_job_state


@pytest.fixture
def client():
    with patch("backend.mlops.mlflow_client.init_mlflow", return_value=None):
        with TestClient(app) as test_client:
            yield test_client


def test_health_endpoints(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data


def test_available_models_endpoint(client):
    res = client.get("/api/v1/models/available")
    assert res.status_code == 200
    models = res.json()
    assert len(models) >= 10
    names = [m["name"] for m in models]
    assert "RandomForestClassifier" in names
    assert "LinearRegression" in names


def test_job_status_and_results_flow(client):
    job_id = "test-job-flow-123"
    set_job_state(job_id, {
        "job_id": job_id,
        "status": "completed",
        "current_agent": "complete",
        "progress_pct": 100,
        "ranked_models": [
            {"model_name": "RandomForestClassifier", "composite_score": 0.95, "model_path": "models/rf.joblib"}
        ],
        "final_report_md": "# Test Report\nEverything passed successfully."
    })

    # Test status endpoint
    res = client.get(f"/api/v1/jobs/{job_id}")
    assert res.status_code == 200
    assert res.json()["status"] == "completed"
    assert res.json()["progress_pct"] == 100

    # Test results endpoint
    res = client.get(f"/api/v1/jobs/{job_id}/results")
    assert res.status_code == 200
    assert len(res.json()["ranked_models"]) == 1

    # Test models endpoint
    res = client.get(f"/api/v1/jobs/{job_id}/models")
    assert res.status_code == 200
    assert len(res.json()["models"]) == 1

    # Test report endpoint
    res = client.get(f"/api/v1/jobs/{job_id}/report")
    assert res.status_code == 200
    assert "Test Report" in res.text

    # Test deploy endpoint
    res = client.post(f"/api/v1/jobs/{job_id}/deploy", json={"model_index": 0})
    assert res.status_code == 200
    assert "endpoint" in res.json()
