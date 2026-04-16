from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str

    # JWT
    secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    jwt_refresh_expire_days: int = 30

    # Google OAuth
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Frontend
    frontend_url: str = "http://localhost:5173"

    # Gemini
    gemini_api_key: str

    # Admin
    admin_email: str


settings = Settings()
