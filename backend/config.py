from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    # FastAPI
    APP_ENV: str = Field(default="development", validation_alias="APP_ENV")
    SECRET_KEY: str = Field(default="changeme", validation_alias="SECRET_KEY")
    ALLOWED_ORIGINS: str = Field(default="http://localhost:3003", validation_alias="ALLOWED_ORIGINS")

    # Database
    POSTGRES_URL: str = Field(default="postgresql+asyncpg://postgres:postgres@localhost:5432/automl_db", validation_alias="POSTGRES_URL")

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")

    # AWS
    AWS_REGION: str = Field(default="us-east-1", validation_alias="AWS_REGION")
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, validation_alias="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, validation_alias="AWS_SECRET_ACCESS_KEY")
    S3_BUCKET_NAME: str = Field(default="automl-artifacts", validation_alias="S3_BUCKET_NAME")
    S3_DATA_BUCKET: str = Field(default="automl-datasets", validation_alias="S3_DATA_BUCKET")

    # MLflow
    MLFLOW_TRACKING_URI: str = Field(default="http://mlflow:5000", validation_alias="MLFLOW_TRACKING_URI")
    MLFLOW_S3_ENDPOINT_URL: str = Field(default="https://s3.amazonaws.com", validation_alias="MLFLOW_S3_ENDPOINT_URL")

    # LLM API keys
    GROQ_API_KEY: Optional[str] = Field(default=None, validation_alias="GROQ_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    OPENAI_API_KEY: Optional[str] = Field(default=None, validation_alias="OPENAI_API_KEY")
    LANGSMITH_API_KEY: Optional[str] = Field(default=None, validation_alias="LANGSMITH_API_KEY")
    LANGFUSE_PUBLIC_KEY: Optional[str] = Field(default=None, validation_alias="LANGFUSE_PUBLIC_KEY")
    LANGFUSE_SECRET_KEY: Optional[str] = Field(default=None, validation_alias="LANGFUSE_SECRET_KEY")
    LANGFUSE_HOST: str = Field(default="https://cloud.langfuse.com", validation_alias="LANGFUSE_HOST")

    # Ollama (local fallback)
    OLLAMA_BASE_URL: str = Field(default="http://ollama:11434", validation_alias="OLLAMA_BASE_URL")
    OLLAMA_MODEL: str = Field(default="llama3.1:8b", validation_alias="OLLAMA_MODEL")

    # LLM routing
    PRIMARY_LLM_PROVIDER: str = Field(default="groq", validation_alias="PRIMARY_LLM_PROVIDER")
    FALLBACK_LLM_PROVIDER: str = Field(default="anthropic", validation_alias="FALLBACK_LLM_PROVIDER")
    LLM_MAX_TOKENS: int = Field(default=8192, validation_alias="LLM_MAX_TOKENS")
    LLM_TOKEN_BUDGET_PER_AGENT: int = Field(default=2000, validation_alias="LLM_TOKEN_BUDGET_PER_AGENT")

    # Optuna
    OPTUNA_N_TRIALS: int = Field(default=50, validation_alias="OPTUNA_N_TRIALS")
    OPTUNA_TIMEOUT_SECONDS: int = Field(default=300, validation_alias="OPTUNA_TIMEOUT_SECONDS")

    # Pipeline
    MAX_TRAINING_TIME_SECONDS: int = Field(default=1800, validation_alias="MAX_TRAINING_TIME_SECONDS")
    MIN_MODELS_TO_TRAIN: int = Field(default=5, validation_alias="MIN_MODELS_TO_TRAIN")
    TOP_N_MODELS: int = Field(default=3, validation_alias="TOP_N_MODELS")

    # Vector DB
    QDRANT_URL: str = Field(default="http://qdrant:6333", validation_alias="QDRANT_URL")
    CHROMA_PATH: str = Field(default="./chroma_db", validation_alias="CHROMA_PATH")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


settings = Settings()