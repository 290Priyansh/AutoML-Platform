# AutoML Platform

> **AutoML-as-a-Service** backend. Upload a dataset (CSV, PDF, or URL), and the system autonomously runs the entire ML pipeline — ingestion → EDA → preprocessing → feature engineering → training → hyperparameter tuning → evaluation → explainability → reporting — returning top 3 ranked models with a live inference endpoint.

## Architecture

```
User Upload → FastAPI → Celery Queue → LangGraph Pipeline (23 Agents) → MLflow + S3 → Live Endpoint
                                    ↓
                              WebSocket Progress
```

Every pipeline step is a **specialized AI agent** node in a **LangGraph state machine**. Training jobs run asynchronously via **Celery + Redis**. The system deploys on **Docker + Kubernetes (AWS EKS)**.

## Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- AWS credentials (for S3, EKS)
- LLM API keys (Anthropic, OpenAI) or Ollama for local

### Local Development

```bash
# Clone and navigate
cd automl-platform

# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Start infrastructure
docker-compose -f infra/docker-compose.yml up -d

# Run API
cd backend
uvicorn main:app --reload

# Run worker (separate terminal)
celery -A workers.celery_app worker --loglevel=info --concurrency=4 -Q training

# API available at http://localhost:8000
# Health check: curl http://localhost:8000/health
# Docs: http://localhost:8000/docs
```

### Submit a Training Job

```bash
curl -X POST "http://localhost:8000/api/v1/jobs" \
  -F "file=@data.csv" \
  -F "model=auto" \
  -F "target_col=target"
```

### Monitor Progress (WebSocket)

```javascript
const ws = new WebSocket("ws://localhost:8000/api/v1/ws/{job_id}");
ws.onmessage = (event) => console.log(JSON.parse(event.data));
```

## Project Structure

```
automl-platform/
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Pydantic settings
│   ├── api/                    # REST + WebSocket routes
│   ├── agents/                 # 23 specialized agents
│   │   ├── phase1_understanding/   # Ingestion, EDA, Classification, Quality, Split
│   │   ├── phase2_preprocessing/   # Cleaning, NLP, Encoding, Scaling, FeatEng, Selection, Imbalance
│   │   ├── phase3_modeling/        # CV Strategy, Training, HPO, Evaluation, Ranking, Ensemble
│   │   └── phase4_output/          # Explainability, Bias, Report, Packaging, Deployment, Drift
│   ├── orchestrator/           # LangGraph state machine
│   ├── workers/                # Celery tasks
│   ├── mlops/                  # MLflow, DVC, S3
│   ├── llm/                    # LLM router, prompts, guardrails
│   └── monitoring/             # Prometheus, Evidently
├── infra/
│   ├── docker/                 # 4 Dockerfiles
│   ├── docker-compose.yml      # Local dev stack
│   └── k8s/                    # K8s manifests + KEDA
├── .github/workflows/          # CI/CD
└── pyproject.toml              # Dependencies
```

## Pipeline Agents

| Phase | Agent | Purpose |
|-------|-------|---------|
| 1 | `ingestion` | Load CSV/PDF/URL → Parquet |
| 1 | `eda` | ydata-profiling report |
| 1 | `problem_classifier` | Identify target + task type (LLM) |
| 1 | `data_quality` | Composite quality score |
| 1 | `split` | Stratified/TimeSeries/Group splits |
| 2 | `cleaning` | Impute, cap outliers, dedupe |
| 2 | `nlp` | TF-IDF / Embeddings for text |
| 2 | `encoding` | OneHot/Target/Binary/Ordinal |
| 2 | `scaling` | Standard/MinMax/Robust/None |
| 2 | `feature_engineering` | Datetime, interactions, ratios, cyclical |
| 2 | `feature_selection` | MI + RFECV + LASSO + Corr + VIF voting |
| 2 | `imbalance_handler` | SMOTE/ADASYN/SMOTETomek/ClassWeight |
| 3 | `cv_strategy` | StratifiedKFold/TimeSeriesSplit/GroupKFold |
| 3 | `training` | 8 models from scratch |
| 3 | `hpo` | Optuna (50 trials, MedianPruner) |
| 3 | `evaluation` | Test set: all metrics + plots |
| 3 | `ranking` | Composite score (LLM rationale) |
| 3 | `ensemble` | Voting + Stacking + Blending |
| 4 | `explainability` | SHAP + LIME |
| 4 | `bias_fairness` | Fairlearn + LLM narrative |
| 4 | `report` | Full markdown + PDF (LLM) |
| 4 | `packaging` | Joblib + ONNX + MLflow Registry |
| 4 | `deployment` | FastAPI → Docker → EKS |
| 4 | `drift_monitor` | Evidently + Celery periodic |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/jobs` | Submit training job |
| GET | `/api/v1/jobs/{id}` | Job status + progress |
| GET | `/api/v1/jobs/{id}/results` | Full results |
| GET | `/api/v1/jobs/{id}/report` | Download markdown/PDF |
| GET | `/api/v1/jobs/{id}/models` | Top 3 models + download links |
| GET | `/api/v1/jobs/{id}/plots` | S3 signed URLs for all plots |
| POST | `/api/v1/jobs/{id}/deploy` | Deploy specific model |
| WS | `/api/v1/ws/{id}` | Real-time progress |
| GET | `/api/v1/models/available` | Supported model types |
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/metrics` | Prometheus metrics |

## Monitoring

- **Prometheus metrics**: `/metrics` endpoint
- **Grafana dashboards**: Pipeline Overview, Agent Performance, LLM Usage, Model Drift, Infrastructure
- **LangFuse**: LLM call tracing
- **MLflow**: Experiment tracking + Model Registry

## Deployment

### AWS EKS (Production)

```bash
# Infrastructure
cd infra/terraform
terraform init && terraform apply

# Deploy via GitHub Actions (on merge to main)
# Or manually:
kubectl apply -f infra/k8s/
```

### KEDA Autoscaling

Workers scale 1→20 based on Redis queue depth (`automl:training` queue length > 1 → add worker).

## Testing

```bash
# Unit tests
pytest backend/tests/unit/ -v

# Integration tests
pytest backend/tests/integration/ -v

# Lint
ruff check backend/

# Type check
mypy backend/
```

## Configuration

All settings via environment variables (see `.env.example`):

- **LLM Routing**: `PRIMARY_LLM_PROVIDER` (anthropic/openai/ollama)
- **Pipeline**: `MAX_TRAINING_TIME_SECONDS=1800`, `TOP_N_MODELS=3`
- **Optuna**: `OPTUNA_N_TRIALS=50`, `OPTUNA_TIMEOUT_SECONDS=300`
- **Security**: JWT auth, rate limiting, pre-signed S3 URLs

## License

Proprietary — Internal use only.