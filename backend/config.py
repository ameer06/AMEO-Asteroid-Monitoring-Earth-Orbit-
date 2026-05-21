import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Optional


class Settings(BaseSettings):
    nasa_api_key: str = "DEMO_KEY"

    # Render/Heroku-style single URL (overrides postgres_* when set)
    database_url: Optional[str] = None

    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_db: str = "neodb"
    postgres_user: str = "neouser"
    postgres_password: str = "neopassword"

    redis_host: str = "redis"
    redis_port: int = 6379

    poll_interval_minutes: int = 15
    alert_threshold_ld: float = 5.0
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def sqlalchemy_database_url(self) -> str:
        url = self.database_url or os.getenv("DATABASE_URL")
        if url:
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
