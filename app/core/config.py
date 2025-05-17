from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # For Vertex AI, project and location are often needed.
    # These can be set in the environment or passed when initializing ChatVertexAI.
    google_cloud_project: str | None = None
    google_cloud_location: str | None = None # e.g., "us-central1"

    gemini_api_key: str | None = None
    langsmith_tracing: bool = False
    langsmith_endpoint: str | None = None
    langsmith_api_key: str | None = None
    langsmith_project: str | None = None

    # Example of another API key if your tools need it
    # any_other_api_key: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings() 