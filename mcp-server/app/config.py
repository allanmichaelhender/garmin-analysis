import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str = os.getenv("DATABASE_URL", "")

    # Garmin Connect
    garmin_email: str = os.getenv("GARMIN_EMAIL", "")
    garmin_password: str = os.getenv("GARMIN_PASSWORD", "")

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
