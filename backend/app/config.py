"""
Central application configuration.

All values are read from environment variables (via a local .env file in
development). Never hardcode secrets here — see .env.example for the full
list of variables this app expects.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "SafeTrack"
    ENVIRONMENT: str = "development"
    FRONTEND_ORIGIN: str = "http://localhost:5500"

    # Database
    DATABASE_URL: str = "sqlite:///./safetrack.db"

    # JWT / sessions
    JWT_SECRET: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    OTP_SESSION_TOKEN_EXPIRE_MINUTES: int = 10

    # OTP
    OTP_EXPIRE_MINUTES: int = 5
    OTP_MAX_ATTEMPTS: int = 5
    OTP_LENGTH: int = 6

    # Email
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "SafeTrack <no-reply@safetrack.example>"
    EMAIL_USE_TLS: bool = True

    # WhatsApp
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = ""
    WHATSAPP_API_VERSION: str = "v20.0"
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = "safetrack_verify_token"

    # Rate limiting
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_OTP: str = "5/minute"
    RATE_LIMIT_SOS: str = "3/minute"


settings = Settings()
