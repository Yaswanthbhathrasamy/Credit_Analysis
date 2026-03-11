from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    app_name: str = "Intelli-Credit"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    database_url: str = "postgresql://postgres:postgres@localhost:5432/intelli_credit"

    openai_api_key: str = ""
    serpapi_api_key: str = ""

    # LangSmith Monitoring
    langchain_tracing_v2: str = "true"
    langchain_api_key: str = ""
    langchain_project: str = "intelli-credit"
    langchain_endpoint: str = "https://api.smith.langchain.com"

    upload_dir: str = "uploads"
    reports_dir: str = "reports"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


def configure_langsmith():
    """Set LangSmith environment variables for LangChain tracing."""
    s = get_settings()
    if s.langchain_api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = s.langchain_tracing_v2
        os.environ["LANGCHAIN_API_KEY"] = s.langchain_api_key
        os.environ["LANGCHAIN_PROJECT"] = s.langchain_project
        os.environ["LANGCHAIN_ENDPOINT"] = s.langchain_endpoint
