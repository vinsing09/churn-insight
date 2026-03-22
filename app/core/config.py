from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "sqlite:///./data/churn.db"

    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    TYPEFORM_CLIENT_ID: str = ""
    TYPEFORM_CLIENT_SECRET: str = ""
    TYPEFORM_REDIRECT_URI: str = "http://localhost:8000/api/v1/integrations/typeform/callback"

    DELIGHTED_API_KEY: str = ""

    JWT_SECRET_KEY: str = "changeme"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    ENCRYPTION_KEY: str = ""

    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    RESEND_API_KEY: str = ""

    FRONTEND_URL: str = "http://localhost:3000"

    ADMIN_SECRET: str = "change-me-in-production"


settings = Settings()
