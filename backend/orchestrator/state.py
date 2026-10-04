from typing import TypedDict, Optional, Any, List, Dict
import pandas as pd


class PipelineState(TypedDict):
    # Job metadata
    job_id: str
    user_id: str
    created_at: str
    status: str                          # queued | running | completed | failed
    current_agent: str
    progress_pct: int
    error: Optional[str]

    # Input
    raw_data_path: str                   # S3 path to uploaded file
    data_source_type: str                # csv | pdf | url
    url: Optional[str]                   # URL if data_source_type == 'url'
    user_model_preference: Optional[str] # None = auto-select

    # Phase 1 outputs
    dataframe_path: str                  # S3 path to parquet after ingestion
    schema: Dict[str, str]               # {col_name: dtype, ...}
    row_count: int
    col_count: int
    eda_report: Dict[str, Any]           # full ydata-profiling JSON
    problem_type: str                    # classification | regression | clustering | timeseries
    target_column: str
    feature_columns: List[str]
    data_quality_score: float            # 0.0 - 1.0
    data_quality_flags: List[str]        # human-readable warnings
    train_path: str                      # S3 path to train parquet
    val_path: str
    test_path: str
    split_strategy: str                  # stratified | timeseries | group

    # Phase 2 outputs
    cleaned_train_path: str
    cleaned_val_path: str
    cleaned_test_path: str
    encoded_train_path: Optional[str]
    encoded_val_path: Optional[str]
    encoded_test_path: Optional[str]
    scaled_train_path: Optional[str]
    scaled_val_path: Optional[str]
    scaled_test_path: Optional[str]
    engineered_train_path: Optional[str]
    engineered_val_path: Optional[str]
    engineered_test_path: Optional[str]
    selected_train_path: Optional[str]
    selected_val_path: Optional[str]
    selected_test_path: Optional[str]
    resampled_train_path: Optional[str]
    text_columns: List[str]              # detected text columns
    embedding_columns: List[str]         # columns converted to embeddings
    encoding_map: Dict[str, str]         # {col: encoding_strategy}
    scaler_type: str
    engineered_features: List[str]       # new feature names added
    selected_features: List[str]         # final feature set after selection
    imbalance_strategy: str              # smote | adasyn | undersample | weights | none
    preprocessor_path: str              # S3 path to fitted sklearn Pipeline joblib

    # Phase 3 outputs
    label_encoder_path: Optional[str]
    trained_models: Dict[str, Dict[str, Any]]                 # {model_name: {"path": s3_path, "params": {}}}
    hpo_results: Dict[str, Dict[str, Any]]                    # {model_name: best_params}
    evaluation_results: Dict[str, Dict[str, float]]           # {model_name: {metric: value}}
    cv_strategy: str
    ranked_models: List[Dict[str, Any]]                       # sorted by composite score, top 3
    ranking_rationale: Optional[str]                          # LLM rationale for top model
    ensemble_model_path: Optional[str]

    # Phase 4 outputs
    shap_plots_path: Dict[str, str]                # {model_name: s3_path_to_plots}
    lime_explanations_path: Dict[str, str]
    feature_importance: Dict[str, Dict[str, float]]             # {model_name: {feature: importance}}
    bias_report: Dict[str, Any]
    final_report_md: str                 # LLM-written markdown report
    report_md_path: Optional[str]        # S3 path to markdown report
    report_pdf_path: Optional[str]       # S3 path to PDF report
    packaged_models: Dict[str, Dict[str, Any]]                # {model_name: {joblib_path, onnx_path, registry_version}}
    inference_endpoints: Dict[str, str]                # {model_name: https://...}
    drift_monitor_config: Dict[str, Any]