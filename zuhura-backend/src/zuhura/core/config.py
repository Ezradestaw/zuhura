import logging
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# zuhura-backend/src/zuhura/core/config.py -> repository root
_REPO_ROOT = Path(__file__).resolve().parents[4]
_DEFAULT_DATA_ROOT = _REPO_ROOT / "zuhura-data"
_DEV_DATABASE_PASSWORDS = ("zuhura_secure_password", "zuhura_dev_only_change_me")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "zuhura-backend/.env"), extra="ignore")

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Service
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Database & Cache
    DATABASE_URL: str = "postgresql+asyncpg://zuhura_user:zuhura_secure_password@postgres:5432/zuhura"
    REDIS_URL: str = "redis://redis:6379/0"
    # Immediate peers allowed to supply X-Forwarded-For. Empty means the header is ignored.
    TRUSTED_PROXY_CIDRS: List[str] = []

    # Storage. Defaults follow the repository layout; Docker overrides them.
    MINIO_PUBLIC_URL: str = "http://localhost:9000"
    REPO_ROOT: str = str(_REPO_ROOT)
    DATA_REPO_ROOT: str = str(_DEFAULT_DATA_ROOT)
    TILES_CACHE_DIR: str = str(_DEFAULT_DATA_ROOT / "data" / "tiles")
    MARS_DATA_ROOT: str = str(_REPO_ROOT / "data" / "mars")

    # Mars Geodetic Constants (IAU/IAG 2015 WGCCRE)
    MARS_SEMI_MAJOR_RADIUS_M: float = Field(default=3396190.0, description="Equatorial semi-major radius A in meters")
    MARS_SEMI_MINOR_RADIUS_M: float = Field(default=3376200.0, description="Polar semi-minor radius C in meters")
    MARS_ELEVATION_DATUM: str = "Mars Areoid (MOLA GMM-2B)"

    # AI Configuration (Mars AI Scientist - Gemini Integration)
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")
    GEMINI_MODEL: str = Field(default="gemini-3.5-flash-lite", description="Gemini model identifier (e.g. gemini-3.5-flash-lite, gemini-1.5-pro)")
    GEMINI_ENABLED: bool = Field(default=True, description="Enable Gemini AI scientific provider")
    AI_PROVIDER: str = Field(default="gemini", description="AI provider: gemini or mock_fallback")
    AI_MODEL_NAME: str = Field(default="gemini-3.5-flash-lite", description="Legacy alias for AI model name")
    AI_API_KEY: str = Field(default="", description="Legacy alias for API key")
    AI_MAX_OUTPUT_TOKENS: int = Field(default=4096, description="Maximum output tokens for AI scientist responses")
    AI_REQUEST_TIMEOUT: float = Field(default=30.0, description="Timeout in seconds for AI provider requests")
    AI_RATE_LIMIT: int = Field(default=60, description="Max AI requests per minute per IP")
    AI_TEMPERATURE: float = Field(default=0.2, description="Sampling temperature for scientific accuracy")


settings = Settings()


def log_runtime_configuration_warnings() -> None:
    """Warn when a production process is still carrying development secrets or open CORS."""
    if settings.ENVIRONMENT.lower() != "production":
        return
    logger = logging.getLogger("zuhura.config")
    if any(password in settings.DATABASE_URL for password in _DEV_DATABASE_PASSWORDS):
        logger.warning(
            "Production is using a development database password. "
            "Set POSTGRES_PASSWORD and DATABASE_URL before exposing this service."
        )
    if not settings.REDIS_URL or settings.REDIS_URL in {"redis://redis:6379/0", "redis://localhost:6379/0"}:
        logger.warning(
            "Production Redis URL has no password. Set REDIS_PASSWORD and REDIS_URL before deployment."
        )
    if "*" in settings.CORS_ORIGINS:
        logger.warning(
            "Production CORS_ORIGINS contains '*'. Replace it with an explicit origin list."
        )
    if not settings.TRUSTED_PROXY_CIDRS:
        logger.warning(
            "TRUSTED_PROXY_CIDRS is empty, so X-Forwarded-For is ignored for rate limiting."
        )
