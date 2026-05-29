from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
import json
import sys


class Settings(BaseSettings):
    # App
    app_name: str = "OpenCLAW"
    app_version: str = "V2.2"
    debug: bool = True

    # PostgreSQL
    postgres_user: str = "openclaw"
    postgres_password: str = ""
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

    # NATS — 补全缺失的字段定义
    nats_host: str = "localhost"
    nats_port: int = 4222

    @property
    def nats_url(self) -> str:
        return f"nats://{self.nats_host}:{self.nats_port}"

    # MinIO
    minio_host: str = "localhost"
    minio_port: int = 9000
    minio_access_key: str = "openclaw"  # 用户名，默认值不敏感
    minio_secret_key: str = ""  # 必须通过环境变量配置

    @property
    def minio_endpoint(self) -> str:
        return f"http://{self.minio_host}:{self.minio_port}"

    # JWT
    jwt_secret_key: str = ""  # 必须通过环境变量配置
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours

    # CORS — 从环境变量读取 JSON 数组格式
    # 开发环境默认 ["*"]，生产环境通过 CORS_ORIGINS 环境变量设置
    cors_origins: list[str] = ["*"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Pydantic v2 不会自动解析 JSON 数组格式的环境变量，
        需要手动将字符串转为 list。"""
        if isinstance(v, str):
            return json.loads(v)
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()

    # 🚫 启动时强制检查：关键凭据未配置则退出
    required_secrets = {
        "postgres_password": settings.postgres_password,
        "jwt_secret_key": settings.jwt_secret_key,
        "minio_secret_key": settings.minio_secret_key,
    }
    missing = [name for name, val in required_secrets.items() if not val]
    if missing:
        print(f"[FATAL] 缺少必要配置项（请在 .env 中设置）：{', '.join(missing)}")
        sys.exit(1)

    return settings
