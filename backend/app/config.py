"""Configuration management for the application."""
from pathlib import Path

from pydantic import field_validator, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

# Get the backend directory (parent of app directory)
BACKEND_DIR = Path(__file__).parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        case_sensitive=False,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Customize settings sources to prioritize .env file over environment variables."""
        return (
            init_settings,      # 1. Arguments passed to Settings() (highest priority)
            dotenv_settings,    # 2. .env file (now higher priority than env vars)
            env_settings,       # 3. Environment variables (now lower priority)
            file_secret_settings,  # 4. Secrets directory (lowest priority)
        )

    # OpenAI Configuration
    openai_api_key: str = ""

    # Model used to answer questions
    openai_model: str = "gpt-4o"
    # Cheaper model used to rewrite follow-up questions into standalone search queries
    condense_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    # Retrieval configuration
    retrieval_k: int = 8

    # Chroma Configuration
    chroma_persist_dir: str = "./chroma_db"

    # Comma-separated list of allowed CORS origins for the frontend
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    @field_validator("chroma_persist_dir")
    @classmethod
    def ensure_chroma_dir_exists(cls, v: str) -> str:
        """Ensure Chroma directory exists."""
        Path(v).mkdir(parents=True, exist_ok=True)
        return v

    @model_validator(mode="after")
    def validate_api_key(self) -> "Settings":
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


# Global settings instance
settings = Settings()
