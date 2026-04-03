import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"
DEFAULT_SQLITE_PATH = INSTANCE_DIR / "dealradar.db"


def normalize_database_url(value: str) -> str:
    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+psycopg://", 1)
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+psycopg://", 1)
    return value


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dealradar-dev-secret")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    APP_ENV = os.getenv("APP_ENV", "development")
    SQLALCHEMY_DATABASE_URI = normalize_database_url(
        os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH}")
    )


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(BaseConfig):
    DEBUG = False


CONFIG_BY_NAME = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
