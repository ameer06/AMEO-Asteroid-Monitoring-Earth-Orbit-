import os
from functools import lru_cache
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic_settings import BaseSettings


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
        url, _ = self.sqlalchemy_database_config
        return url

    @property
    def sqlalchemy_connect_args(self) -> Dict[str, object]:
        _, connect_args = self.sqlalchemy_database_config
        return connect_args

    @property
    def sqlalchemy_database_config(self) -> Tuple[str, Dict[str, object]]:
        """
        Build asyncpg URL + connect_args.
        Neon URLs use ?sslmode=require — asyncpg needs ssl=True, not sslmode.
        """
        url = self.database_url or os.getenv("DATABASE_URL")
        if url:
            return _normalize_database_url(url)
        return (
            (
                f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            ),
            {},
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    class Config:
        env_file = ".env"


def _normalize_database_url(url: str) -> Tuple[str, Dict[str, object]]:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))

    sslmode = query.pop("sslmode", None)
    query.pop("channel_binding", None)

    use_ssl = sslmode in ("require", "verify-ca", "verify-full", "prefer")
    if not use_ssl and parsed.hostname and "neon" in parsed.hostname:
        use_ssl = True

    clean_query = urlencode(query)
    clean_url = urlunparse(parsed._replace(query=clean_query))

    connect_args: Dict[str, object] = {"ssl": True} if use_ssl else {}
    return clean_url, connect_args


@lru_cache()
def get_settings() -> Settings:
    return Settings()
