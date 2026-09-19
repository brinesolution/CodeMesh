from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import Settings


def build_engine(settings: Settings):
    if settings.database_url.startswith("sqlite:///"):
        database_path = settings.database_url.removeprefix("sqlite:///")
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        return create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False},
        )
    return create_engine(settings.database_url)


def build_session_factory(settings: Settings):
    return sessionmaker(bind=build_engine(settings), autoflush=False, autocommit=False)

