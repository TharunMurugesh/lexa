"""
LEXA Configuration Management using Pydantic BaseSettings.
All configuration from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    """Main application settings."""

    # ===== API Configuration =====
    API_TITLE: str = "LEXA API"
    API_DESCRIPTION: str = "Multi-agent legal reasoning system"
    API_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # ===== Server Configuration =====
    HOST: str = "localhost"
    PORT: int = 8000
    RELOAD: bool = True

    # ===== CORS Configuration =====
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # ===== LLM Configuration (Ollama) =====
    MODEL_NAME: str = "llama3.1:8b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_TEMPERATURE_REASONING: float = 0.1
    LLM_TEMPERATURE_CREATIVE: float = 0.7
    LLM_MAX_TOKENS: int = 2048
    LLM_TIMEOUT: int = 60

    # ===== Embedding Configuration =====
    EMBEDDING_MODEL: str = "sentence-transformers/bge-large-en-v1.5"
    EMBEDDING_DIM: int = 1024
    EMBEDDING_BATCH_SIZE: int = 32

    # ===== Retrieval Configuration =====
    FAISS_INDEX_PATH: str = "models/faiss_indices/v1/index.bin"
    FAISS_METADATA_PATH: str = "models/faiss_indices/v1/metadata.pkl"
    ELASTICSEARCH_HOST: str = "localhost"
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_INDEX_NAME: str = "legal_corpus"
    RETRIEVAL_TOP_K_SPARSE: int = 20
    RETRIEVAL_TOP_K_DENSE: int = 20
    RETRIEVAL_TOP_K_RERANKED: int = 5
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-12-v2"

    # ===== NLI Configuration =====
    NLI_MODEL: str = "cross-encoder/nli-deberta-v3-large"
    CONTRADICTION_THRESHOLD: float = 0.7

    # ===== Document Processing =====
    MAX_DOCUMENT_SIZE_MB: int = 50
    CHUNK_SIZE_TOKENS: int = 512
    CHUNK_OVERLAP_TOKENS: int = 128
    MIN_CHUNK_SIZE_TOKENS: int = 100

    # ===== Debate Configuration =====
    MAX_DEBATE_ROUNDS: int = 3
    CONFIDENCE_THRESHOLD: float = 0.6
    CONTRADICTION_SEVERITY_THRESHOLD: float = 0.7

    # ===== Async Task Configuration =====
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    CELERY_TASK_TIMEOUT: int = 300

    # ===== MLflow Configuration =====
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    MLFLOW_EXPERIMENT_NAME: str = "lexa_experiments"
    MLFLOW_REGISTRY_URI: Optional[str] = None

    # ===== DVC Configuration =====
    DVC_REMOTE_URL: str = "./dvc-storage"  # Local for development

    # ===== Paths =====
    DATA_DIR: str = "data"
    CORPUS_DIR: str = "data/corpus"
    TRAINING_DIR: str = "data/training"
    EVAL_DIR: str = "data/evaluation"
    MODELS_DIR: str = "models"
    LOGS_DIR: str = "logs"
    PROMPTS_DIR: str = "backend/config/prompts"

    # ===== Evaluation Configuration =====
    EVAL_SET_SIZE: int = 100
    EVAL_SAMPLE_SIZE: int = 20

    # ===== Security =====
    API_KEY_OPTIONAL: bool = True  # For development; set to False in production
    AUDIT_LOG_ENABLED: bool = True
    AUDIT_LOG_PATH: str = "logs/audit.log"

    # ===== GPU/Hardware Configuration =====
    GPU_MEMORY_FRACTION: float = 0.85
    USE_GPU: bool = True
    DEVICE: str = "cuda"  # cuda or cpu

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton settings instance
settings = Settings()
