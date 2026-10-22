from collections.abc import Generator

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")
    database_url: str = "postgresql+psycopg://insightflow:insightflow@localhost:5432/insightflow"


engine = create_engine(DatabaseSettings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
