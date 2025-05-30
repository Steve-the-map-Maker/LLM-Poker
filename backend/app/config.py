from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
