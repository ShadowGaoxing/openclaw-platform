from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # App
    app_name: str = "OpenCLAW"
    app_version: str = "V2.2"
    debug: bool = True

    # PostgreSQL
    postgres_user: str = "openclaw"
    postgres_password: str = "openclaw_dev_2026"
    postgres_db: str = "openclaw"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def database_url_sync(self) -> str:
        return f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}"

    # NATS
    nats_host: str = "localhost"
    nats_port: int = 4222
    nats_ws_port: int = 9222

    @property
    def nats_url(self) -> str:
        return f"nats://{self.nats_host}:{self.nats_port}"

    # MinIO
    minio_host: str = "localhost"
    minio_port: int = 9000
    minio_access_key: str = "openclaw"
    minio_secret_key: str = "openclaw_dev_2026"

    @property
    def minio_endpoint(self) -> str:
        return f"http://{self.minio_host}:{self.minio_port}"

    # JWT
    jwt_secret_key: str = "openclaw-jwt-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
