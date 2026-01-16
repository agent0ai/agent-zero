"""Database initialization module."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager
import os
from typing import Generator, Any

Base = declarative_base()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agent_zero.db")

# Create engine with proper SQLite configuration
engine_kwargs: dict[str, Any] = {
    "echo": False,
    "future": True,
}

# Add SQLite-specific configuration
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    engine_kwargs["pool_pre_ping"] = True
else:
    # PostgreSQL/MySQL configuration
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_pre_ping"] = True

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db() -> Generator:
    """Get database session with automatic cleanup."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
