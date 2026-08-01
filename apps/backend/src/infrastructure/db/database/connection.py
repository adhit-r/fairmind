"""
Database connection management for FairMind
Supports both PostgreSQL (Supabase) and SQLite for development
"""

import os
import logging
from pathlib import Path
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from config.migration_integrity import bind_postgresql_engine_search_path
from config.settings import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys = ON")
    finally:
        cursor.close()


class DatabaseManager:
    """Database connection manager with support for multiple databases"""
    
    def __init__(
        self,
        database_url: str | None = None,
        trusted_schema: str | None = None,
    ):
        self.engine = None
        self.SessionLocal = None
        self._database_url = database_url
        self._trusted_schema = trusted_schema
        self._setup_connection()
    
    def _setup_connection(self):
        """Setup database connection based on environment"""
        database_url = (
            self._database_url
            or os.getenv("DATABASE_URL")
        )
        if not database_url:
            if settings.assurance_v2_enabled:
                database_url = settings.database_url
            else:
                # V2 is opt-in. Preserve the repository manager's historical
                # dedicated SQLite identity until the enabled startup path
                # verifies both database authorities are equivalent.
                database_url = f"sqlite:///{Path(__file__).parent.parent / 'fairmind.db'}"
        
        if database_url.startswith("postgresql"):
            # PostgreSQL/Supabase connection
            self.engine = create_engine(
                database_url,
                pool_pre_ping=True,
                pool_recycle=300,
                echo=os.getenv("DEBUG", "false").lower() == "true"
            )
            if settings.assurance_v2_enabled:
                bind_postgresql_engine_search_path(
                    self.engine,
                    self._trusted_schema
                    or settings.assurance_migration_schema
                    or "",
                )
            logger.info("Connected to PostgreSQL database")
        else:
            # SQLite for development; identity is checked against config startup.
            self.engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=os.getenv("DEBUG", "false").lower() == "true"
            )
            event.listen(self.engine, "connect", _enable_sqlite_foreign_keys)
            logger.info("Connected to SQLite database")
        
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all database tables defined via ORM models."""
        try:
            # Import all model modules so Base.metadata is populated
            import database.governance_models  # noqa: F401

            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Session:
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

# Global database manager instance
db_manager = DatabaseManager()

def get_db():
    """Dependency for FastAPI to get database session"""
    with db_manager.get_session() as session:
        yield session
