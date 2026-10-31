from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Faculty Workload Balancing API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Environment & Server
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Persistence Store (gist | local)
    STORE_BACKEND: str = "local"
    GIST_TOKEN: str = ""
    GIST_ID: str = ""
    LOCAL_DATA_DIR: str = "data/store"

    # Security & Auth
    JWT_SECRET: str = "super-secret-development-key-change-in-production-min32chars"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    OTP_DEV_MODE: bool = True
    OTP_CODE_TTL_MINUTES: int = 5

    # Email / SMTP
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@university.edu"
    SMTP_TLS: bool = True

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 180

    # CORS
    ALLOWED_ORIGINS: list[str] | str = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # ML / Forecasting (model | precomputed)
    FORECAST_MODE: str = "model"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v  # type: ignore[return-value]
        raise ValueError(v)

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )


settings = Settings()
