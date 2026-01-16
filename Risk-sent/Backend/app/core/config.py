from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "RiskSent AI"
    API_V1_STR: str = "/api/v1"
    
    # AI Config
    # Validate that the token is a string and is required
    HUGGING_FACE_API_KEY: str = Field(..., env="HUGGING_FACE_API_KEY")
    GROK_API_KEY: str = Field(..., env="GROK_API_KEY")
    MONGO_DB_CONNECTION_STRING : str = Field(... , env="MONGO_DB_CONNECTION_STRING")
    MONGO_DB_NAME : str = Field(... , env="MONGO_DB_NAME")
    ACCESS_TOKEN_EXPIRE_MINUTES : float = Field(... , env="ACCESS_TOKEN_EXPIRE_MINUTES")
    SECRET_KEY : str = Field(... ,env="SECRET_KEY")
    ALGORITHM : str = Field(... , env="ALGORITHM")
    SYSTEM_ENV : str = Field(..., env="SYSTEM_ENV")
    REDIS_SERVER_URL : str = Field(... , env="REDIS_SERVER_URL")
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    LLM_REPO_ID: str = "mistralai/Mistral-7B-Instruct-v0.3"
    
    # Storage
    UPLOAD_DIR: str = "data/uploads"
    VECTOR_STORE_DIR: str = "data/vector_store"

    # Load from .env file
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Global settings object to be imported by other modules
settings = Settings()
