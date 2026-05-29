from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AETHER Backend API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "sqlite:///./aether.db"
    MODEL_DIR: str = "./ai_models"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()