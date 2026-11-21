import os


class Settings:
    database_url: str = os.getenv("DATABASE_URL", "postgresql://investwatch:investwatch-dev@localhost:5432/investwatch")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    # S3-compatible object storage for evidence (Garage, see garage/init.sh).
    s3_endpoint: str = os.getenv("S3_ENDPOINT", "http://localhost:3900")
    s3_access_key: str = os.getenv("S3_ACCESS_KEY", "GK0123456789abcdef01234567")
    s3_secret_key: str = os.getenv(
        "S3_SECRET_KEY", "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    )
    s3_bucket: str = os.getenv("S3_BUCKET", "investwatch-evidence")
    # Any OpenAI-compatible endpoint: OpenRouter, or Ollama via its /v1 API.
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "google/gemma-3-12b-it")
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 8
    searxng_url: str = os.getenv("SEARXNG_URL", "http://localhost:8888")
    proxy_urls: str = os.getenv("PROXY_URLS", "")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    retention_days_no_finding: int = int(os.getenv("RETENTION_DAYS_NO_FINDING", "30"))
    classifier_threshold_m1: float = float(os.getenv("CLASSIFIER_THRESHOLD_M1", "0.5"))
    classifier_threshold_m2: float = float(os.getenv("CLASSIFIER_THRESHOLD_M2", "0.5"))
    classifier_threshold_m3: float = float(os.getenv("CLASSIFIER_THRESHOLD_M3", "0.5"))


settings = Settings()
