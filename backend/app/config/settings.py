from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    PROJECT_NAME: str = "FloodGuard AI"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    SECRET_KEY: str = "floodguard-development-secret-key-change-in-prod"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Firebase
    FIREBASE_CREDENTIALS_PATH: str = ""
    FIREBASE_DATABASE_URL: str = "https://floodguard-ai-default-rtdb.firebaseio.com"
    FIREBASE_STORAGE_BUCKET: str = "floodguard-ai.appspot.com"
    FIREBASE_MOCK_MODE: bool = True

    # External APIs
    OPENWEATHER_API_KEY: str = ""
    MAPBOX_ACCESS_TOKEN: str = ""

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

settings = Settings()
