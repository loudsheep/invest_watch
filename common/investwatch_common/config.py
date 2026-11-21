import os


def _csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings:
    """Runtime configuration from the environment. Secrets have no defaults: they come
    only from `.env` (see `.env.example`)."""

    database_url: str = os.getenv("DATABASE_URL", "postgresql://investwatch@localhost:5432/investwatch")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    # S3-compatible object storage for evidence (Garage, see garage/init.sh).
    s3_endpoint: str = os.getenv("S3_ENDPOINT", "http://localhost:3900")
    s3_access_key: str = os.getenv("S3_ACCESS_KEY", "")
    s3_secret_key: str = os.getenv("S3_SECRET_KEY", "")
    s3_region: str = os.getenv("S3_REGION", "auto")
    s3_bucket: str = os.getenv("S3_BUCKET", "investwatch-evidence")
    # Any OpenAI-compatible endpoint; the default is a local Ollama.
    llm_base_url: str = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "gemma3:4b")
    jwt_secret: str = os.getenv("JWT_SECRET", "")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 8
    cors_origins: list[str] = _csv(os.getenv("CORS_ORIGINS", "http://localhost:47173,http://localhost:5173"))
    searxng_url: str = os.getenv("SEARXNG_URL", "http://localhost:8888")
    proxy_urls: str = os.getenv("PROXY_URLS", "")
    # Hosts on private networks the crawler may still fetch (the demo-sites sandbox).
    fetch_allowed_private_hosts: list[str] = _csv(
        os.getenv("FETCH_ALLOWED_PRIVATE_HOSTS", "demo-sites,nordik-brokr-demo.local")
    )
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    retention_days_no_finding: int = int(os.getenv("RETENTION_DAYS_NO_FINDING", "30"))
    classifier_threshold_m1: float = float(os.getenv("CLASSIFIER_THRESHOLD_M1", "0.5"))
    classifier_threshold_m2: float = float(os.getenv("CLASSIFIER_THRESHOLD_M2", "0.5"))
    classifier_threshold_m3: float = float(os.getenv("CLASSIFIER_THRESHOLD_M3", "0.5"))


settings = Settings()
