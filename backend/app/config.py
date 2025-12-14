"""Configuration management for the application."""
from pathlib import Path
from typing import Literal

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
    
    # LLM Provider Configuration
    llm_provider: Literal["openai", "vertex"] = "openai"
    
    # OpenAI Configuration
    openai_api_key: str = ""
    
    # Google Vertex AI Configuration
    google_application_credentials: str = ""
    vertex_project_id: str = ""
    vertex_location: str = "us-central1"
    
    # Chroma Configuration
    chroma_persist_dir: str = "./chroma_db"
    
    # Embedding Model Configuration
    embedding_model: str = "text-embedding-3-small"  # OpenAI default
    vertex_embedding_model: str = "textembedding-gecko@003"  # Vertex default
    
    # LLM Model Configuration
    openai_model: str = "gpt-4"
    vertex_model: str = "gemini-1.5-pro"
    
    @field_validator("chroma_persist_dir")
    @classmethod
    def ensure_chroma_dir_exists(cls, v: str) -> str:
        """Ensure Chroma directory exists."""
        Path(v).mkdir(parents=True, exist_ok=True)
        return v
    
    @model_validator(mode="after")
    def validate_provider_settings(self) -> "Settings":
        """Validate provider-specific settings."""
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when using OpenAI provider")
        
        if self.llm_provider == "vertex":
            if not self.google_application_credentials:
                raise ValueError("GOOGLE_APPLICATION_CREDENTIALS is required when using Vertex provider")
            if not self.vertex_project_id:
                raise ValueError("VERTEX_PROJECT_ID is required when using Vertex provider")
        
        return self


# Global settings instance
settings = Settings()

