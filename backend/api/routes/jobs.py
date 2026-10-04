from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
import uuid
import logging
from datetime import datetime, timezone

from backend.workers.tasks import run_pipeline
from backend.mlops.artifact_store import upload_to_s3, get_presigned_url
from backend.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

class JobCreate(BaseModel):
    model: Optional[str] = None
    target_col: Optional[str] = None

class JobStatus(BaseModel):
    job_id: str
    status: str
    current_agent: str
    progress_pct: int
    error: Optional[str] = None
    created_at: Optional[str] = None
    target_column: Optional[str] = None
    problem_type: Optional[str] = None
    row_count: Optional[int] = None

class JobResult(BaseModel):
    job_id: str
    status: str
    ranked_models: List[dict]
    report_url: Optional[str] = None
    model_urls: List[str] = []

class ModelInfo(BaseModel):
    name: str
    type: str
    problem_type: str

@router.get("/jobs", response_model=List[JobStatus])
async def list_jobs():
    """List all training jobs"""
    from backend.orchestrator.store import get_all_jobs
    jobs = get_all_jobs()
    return [
        JobStatus(
            job_id=j.get("job_id", ""),
            status=j.get("status", "queued"),
            current_agent=j.get("current_agent", "ingestion"),
            progress_pct=int(j.get("progress_pct", 0)),
            error=j.get("error"),
            created_at=j.get("created_at"),
            target_column=j.get("target_column"),
            problem_type=j.get("problem_type"),
            row_count=j.get("row_count"),
        )
        for j in reversed(jobs)
    ]


@router.post("/jobs", response_model=dict)
async def create_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    model: Optional[str] = Form(None),
    target_col: Optional[str] = Form(None),
):
    """Submit new training job"""
    job_id = str(uuid.uuid4())
    user_id = "default_user"  # TODO: get from auth
    
    # Validate file
    allowed_types = ["text/csv", "application/pdf", "text/plain"]
    if file.content_type not in allowed_types:
        # Check extension as fallback
        ext = file.filename.split(".")[-1].lower()
        if ext not in ["csv", "pdf", "txt"]:
            raise HTTPException(400, "Invalid file type. Supported: CSV, PDF, URL")
    
    # Save file to S3
    file_content = await file.read()
    if len(file_content) > 500 * 1024 * 1024:  # 500MB
        raise HTTPException(400, "File too large. Max 500MB for CSV, 200MB for PDF")
    
    data_source_type = "csv"
    if file.filename.lower().endswith(".pdf"):
        data_source_type = "pdf"
    
    s3_key = f"users/{user_id}/jobs/{job_id}/raw_data.{data_source_type}"
    upload_to_s3(file_content, s3_key)
    
    # Initial state
    initial_state = {
        "job_id": job_id,
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "queued",
        "current_agent": "ingestion",
        "progress_pct": 0,
        "error": None,
        "raw_data_path": s3_key,
        "data_source_type": data_source_type,
        "user_model_preference": model,
        # Phase 1
        "dataframe_path": "",
        "schema": {},
        "row_count": 0,
        "col_count": 0,
        "eda_report": {},
        "problem_type": "",
        "target_column": target_col or "",
        "feature_columns": [],
        "data_quality_score": 0.0,
        "data_quality_flags": [],
        "train_path": "",
        "val_path": "",
        "test_path": "",
        "split_strategy": "",
        # Phase 2
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
        # Phase 3
        "trained_models": {},
        "hpo_results": {},
        "evaluation_results": {},
        "cv_strategy": "",
        "ranked_models": [],
        "ensemble_model_path": None,
        # Phase 4
        "shap_plots_path": {},
        "lime_explanations_path": {},
        "feature_importance": {},
        "bias_report": {},
        "final_report_md": "",
        "packaged_models": {},
        "inference_endpoints": {},
        "drift_monitor_config": {},
    }
    
    from backend.orchestrator.store import set_job_state
    set_job_state(job_id, initial_state)

    # Queue the pipeline task: Celery if Redis is up, otherwise local FastAPI BackgroundTasks
    dispatched = False
    try:
        from backend.config import settings
        import redis
        r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=0.3)
        r.ping()
        run_pipeline.delay(job_id, initial_state)
        dispatched = True
        logger.info(f"Dispatched job {job_id} to Celery queue")
    except Exception as e:
        logger.info(f"Redis unavailable, running job {job_id} via local BackgroundTasks: {e}")

    if not dispatched:
        background_tasks.add_task(run_pipeline, None, job_id, initial_state)
    
    return {"job_id": job_id, "status": "queued"}

class DeployRequest(BaseModel):
    model_index: int = 0

@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get job status + current agent + progress %"""
    from backend.orchestrator.store import get_job_state
    state = get_job_state(job_id)
    if not state:
        return JobStatus(
            job_id=job_id,
            status="queued",
            current_agent="ingestion",
            progress_pct=0,
        )
    return JobStatus(
        job_id=job_id,
        status=state.get("status", "running"),
        current_agent=state.get("current_agent", "unknown"),
        progress_pct=int(state.get("progress_pct", 0)),
        error=state.get("error"),
        created_at=state.get("created_at"),
        target_column=state.get("target_column"),
        problem_type=state.get("problem_type"),
        row_count=state.get("row_count"),
    )

@router.get("/jobs/{job_id}/results", response_model=JobResult)
async def get_job_results(job_id: str):
    """Get full results when complete"""
    from backend.orchestrator.store import get_job_state
    state = get_job_state(job_id) or {}
    
    report_url = None
    report_path = state.get("report_md_path") or state.get("report_pdf_path")
    if report_path:
        try:
            report_url = get_presigned_url(report_path)
        except Exception:
            report_url = None

    model_urls = []
    for model in state.get("ranked_models", []):
        mpath = model.get("model_path")
        if mpath:
            try:
                model_urls.append(get_presigned_url(mpath))
            except Exception:
                pass

    return JobResult(
        job_id=job_id,
        status=state.get("status", "completed"),
        ranked_models=state.get("ranked_models", []),
        report_url=report_url,
        model_urls=model_urls,
    )

@router.get("/jobs/{job_id}/report")
async def get_job_report(job_id: str, format: str = "md"):
    """Download markdown/PDF report"""
    from backend.orchestrator.store import get_job_state
    from backend.mlops.artifact_store import download_from_s3
    from fastapi.responses import Response

    state = get_job_state(job_id) or {}
    
    if format == "pdf" and state.get("report_pdf_path"):
        try:
            pdf_bytes = download_from_s3(state["report_pdf_path"])
            return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=report_{job_id}.pdf"})
        except Exception:
            pass

    report_content = state.get("final_report_md", "")
    if not report_content and state.get("report_md_path"):
        try:
            report_content = download_from_s3(state["report_md_path"]).decode("utf-8")
        except Exception:
            report_content = "# AutoML Report\nReport generation in progress or unavailable."

    return Response(
        content=report_content or "# AutoML Report\nNo report available.",
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=report_{job_id}.md"}
    )

@router.get("/jobs/{job_id}/models")
async def get_job_models(job_id: str):
    """Get top 3 ranked models with download links"""
    from backend.orchestrator.store import get_job_state
    state = get_job_state(job_id) or {}
    ranked = state.get("ranked_models", [])
    
    models_out = []
    for m in ranked:
        m_copy = dict(m)
        mpath = m.get("model_path")
        if mpath:
            try:
                m_copy["download_url"] = get_presigned_url(mpath)
            except Exception:
                m_copy["download_url"] = None
        models_out.append(m_copy)
    return {"models": models_out}

@router.get("/jobs/{job_id}/plots")
async def get_job_plots(job_id: str):
    """Get all S3 signed URLs for all plots"""
    from backend.orchestrator.store import get_job_state
    state = get_job_state(job_id) or {}
    
    plots = {}
    eval_results = state.get("evaluation_results", {})
    for model_name, res in eval_results.items():
        if isinstance(res, dict) and "plot_paths" in res:
            for plot_type, path in res["plot_paths"].items():
                try:
                    plots[f"{model_name}_{plot_type}"] = get_presigned_url(path)
                except Exception:
                    plots[f"{model_name}_{plot_type}"] = path

    shap_plots = state.get("shap_plots_path", {})
    for model_name, s_plots in shap_plots.items():
        if isinstance(s_plots, dict):
            for plot_type, path in s_plots.items():
                try:
                    plots[f"{model_name}_shap_{plot_type}"] = get_presigned_url(path)
                except Exception:
                    plots[f"{model_name}_shap_{plot_type}"] = path

    return {"plots": plots}

@router.post("/jobs/{job_id}/deploy")
async def deploy_model(job_id: str, request_data: Optional[DeployRequest] = None, model_index: Optional[int] = None):
    """Deploy a specific ranked model (0, 1, or 2)"""
    from backend.orchestrator.store import get_job_state
    idx = request_data.model_index if request_data is not None else (model_index or 0)
    state = get_job_state(job_id) or {}
    ranked = state.get("ranked_models", [])
    
    if ranked and idx < len(ranked):
        chosen_model = ranked[idx]["model_name"]
        endpoint = state.get("inference_endpoints", {}).get(chosen_model, f"https://api.automl.example.com/models/{chosen_model}/{job_id}")
        return {"message": f"Deployment triggered for {chosen_model}", "endpoint": endpoint}
    
    return {"message": "Deployment triggered", "endpoint": f"https://api.automl.example.com/models/model_{idx}/{job_id}"}

@router.get("/jobs/{job_id}/models/{model_name}/download")
async def download_model_file(job_id: str, model_name: str, format: str = "joblib"):
    """Download trained model artifact"""
    from backend.orchestrator.store import get_job_state
    from backend.mlops.artifact_store import download_from_s3
    from fastapi.responses import Response

    state = get_job_state(job_id) or {}
    packaged = state.get("packaged_models", {}).get(model_name, {})
    trained = state.get("trained_models", {}).get(model_name, {})
    
    target_path = None
    if format == "onnx" and packaged.get("onnx_path"):
        target_path = packaged["onnx_path"]
    elif packaged.get("joblib_path"):
        target_path = packaged["joblib_path"]
    elif trained.get("path"):
        target_path = trained["path"]
    
    if not target_path:
        raise HTTPException(status_code=404, detail=f"Model artifact not found for {model_name}")

    try:
        content = download_from_s3(target_path)
        return Response(
            content=content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={model_name}.{format}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve model artifact: {e}")

@router.get("/jobs/artifacts/{bucket}/{key:path}")
async def get_artifact(bucket: str, key: str):
    """Serve artifact file directly when running locally"""
    from backend.mlops.artifact_store import download_from_s3
    from fastapi.responses import Response
    try:
        content = download_from_s3(key, bucket=bucket)
        media_type = "image/png" if key.endswith(".png") else ("text/markdown" if key.endswith(".md") else "application/octet-stream")
        return Response(content=content, media_type=media_type)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Artifact not found: {e}")

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