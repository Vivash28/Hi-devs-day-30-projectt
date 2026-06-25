from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


def make_engine(database_url: str):
    # SQLite needs check_same_thread=False for multithreaded FastAPI usage
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args, future=True)


def make_session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def session_scope(session_factory) -> Session:
    """
    FastAPI dependency style: yields a session and ensures close.
    (Implemented as a generator function for use with Depends.)
    """
    db = session_factory()
    try:
        yield db
    finally:
        db.close()