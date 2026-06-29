from pydantic import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    MINHA_API_KEY: str
    SERPAPI_KEY: str | None = None
    OPENROUTER_KEY: str | None = None
    DB_PATH: str = os.getenv("DB_PATH", "./facilita_ai.db")
    SERP_LL: str = os.getenv("SERP_LL", "São Paulo, Brazil")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-r1-0528:free")
    RATE_LIMIT: str = "30/minute"

    class Config:
        env_file = ".env"

settings = Settings()
