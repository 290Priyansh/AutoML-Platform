from prometheus_client import Histogram, Counter, Gauge

AGENT_DURATION = Histogram(
    "automl_agent_duration_seconds",
    "Time each agent takes",
    ["agent"],
)

AGENT_ERRORS = Counter(
    "automl_agent_errors_total",
    "Agent error count",
    ["agent"],
)

PIPELINE_DURATION = Histogram(
    "automl_pipeline_duration_seconds",
    "Total pipeline duration",
    buckets=[30, 60, 120, 300, 600, 1200, 1800],
)

ACTIVE_JOBS = Gauge(
    "automl_active_jobs",
    "Currently running pipeline jobs",
)

QUEUE_DEPTH = Gauge(
    "automl_celery_queue_depth",
    "Jobs waiting in Celery queue",
)

MODEL_TRAIN_DURATION = Histogram(
    "automl_model_train_seconds",
    "Per-model training time",
    ["model_name"],
)

LLM_CALL_DURATION = Histogram(
    "automl_llm_call_seconds",
    "LLM API call latency",
    ["agent", "provider"],
)

LLM_CALL_ERRORS = Counter(
    "automl_llm_call_errors_total",
    "LLM call failures",
    ["agent", "provider"],
)