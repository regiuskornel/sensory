"""Configuration settings for the Sensor Data API application."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


@lru_cache
def get_settings():
    """Get the cached settings instance."""
    return Settings()

class Settings(BaseSettings):
    """
    Application configuration settings loaded from environment variables.
    """

    timescale_db_connection: str = "postgresql+psycopg2://sensory:sensory@localhost:5432/sensory"
    openai_model_id: str = "gpt-4o-mini"
    openai_api_key: str = (
        "Invalid"  # Must be set via environment variable for security.
    )
    # Read config from the .env file.
    model_config = SettingsConfigDict(env_file=".env", str_strip_whitespace=True, extra='ignore' )
