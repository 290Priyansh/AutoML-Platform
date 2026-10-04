export interface JobCreate {
  file: File;
  model?: string;
  targetCol?: string;
}


export interface JobStatus {
  job_id: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  current_agent: string;
  progress_pct: number;
  error?: string;
  created_at: string;
}

export interface RankedModel {
  rank: number;
  model_name: string;
  composite_score: number;
  metrics: Record<string, number>;
  training_time: number;
  model_path: string;
  onnx_path?: string;
}

export interface JobResult {
  job_id: string;
  status: string;
  ranked_models: RankedModel[];
  report_url?: string;
  model_urls: string[];
  row_count?: number;
  col_count?: number;
  problem_type?: string;
  data_quality_score?: number;
  ensemble_model_path?: string;
  inference_endpoints?: Record<string, string>;
}

export interface ModelInfo {
  name: string;
  type: string;
  problem_type: string;
  description?: string;
}

export interface WebSocketMessage {
  job_id: string;
  current_agent: string;
  progress_pct: number;
  message: string;
  status: string;
  timestamp: string;
}

export interface AgentProgress {
  name: string;
  label: string;
  phase: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  startTime?: Date;
  endTime?: Date;
  error?: string;
}

export type ProblemType = 'classification' | 'regression' | 'clustering' | 'timeseries';

export interface EvaluationResult {
  [modelName: string]: {
    accuracy?: number;
    precision_macro?: number;
    precision_weighted?: number;
    recall_macro?: number;
    recall_weighted?: number;
    f1_macro?: number;
    f1_weighted?: number;
    roc_auc?: number;
    roc_auc_ovr?: number;
    pr_auc?: number;
    cohen_kappa?: number;
    matthews_corrcoef?: number;
    rmse?: number;
    mae?: number;
    mse?: number;
    r2?: number;
    adjusted_r2?: number;
    mape?: number;
    plot_paths?: Record<string, string>;
    error?: string;
  };
}

export interface FeatureImportance {
  [modelName: string]: Record<string, number>;
}

export interface BiasReport {
  sensitive_columns_found: boolean;
  sensitive_columns?: string[];
  fairness_metrics?: Record<string, any>;
  recommendations?: string[];
  narrative?: string;
  message?: string;
}

export interface DriftMonitorConfig {
  [modelName: string]: {
    reference_data_path: string;
    feature_columns: string[];
    target_column: string;
    drift_threshold: number;
    check_interval_hours: number;
    alert_threshold_consecutive_days: number;
    model_path: string;
  };
}

export interface PackagedModel {
  joblib_path: string;
  onnx_path: string;
  registry_version: string;
  rank: number;
  composite_score: number;
  model_card_path?: string;
}

export interface InferenceEndpoint {
  [modelName: string]: string;
}