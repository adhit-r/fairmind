"""
Database connection management for FairMind (PostgreSQL only)
"""

import os
import logging
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.schema import AddConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

from config.migration_integrity import bind_postgresql_engine_search_path
from config.settings import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


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
            or settings.database_url
        )
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

        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all database tables defined via ORM models."""
        try:
            # Import all model modules so Base.metadata is populated
            import database.governance_models as governance_models  # noqa: F401
            import database.risk_taxonomy_models as risk_taxonomy_models  # noqa: F401
            import database.models as user_models

            # The package is reachable as both "database" and
            # "src.infrastructure.db.database", and Python may load this module
            # once under each name, each with its own Base. Create tables from
            # every metadata the model modules actually registered against.
            metadatas = {id(m): m for m in (Base.metadata, user_models.Base.metadata, governance_models.Base.metadata)}
            created, failed, new_tables = 0, [], []
            existing = set(inspect(self.engine).get_table_names())
            for metadata in metadatas.values():
                # Table by table: one failing definition must not roll back
                # the users table.
                for table in metadata.sorted_tables:
                    try:
                        table.create(bind=self.engine, checkfirst=True)
                        created += 1
                        if table.name not in existing:
                            new_tables.append(table)
                    except Exception as table_error:
                        failed.append(table.name)
                        logger.warning(f"Could not create table {table.name}: {table_error}")
            # Foreign keys in a cycle (users <-> organizations) are left out of CREATE TABLE
            # (use_alter) and added here, only on tables created just now: an existing
            # database is never altered.
            for table in new_tables:
                for fk in table.foreign_key_constraints:
                    if fk.use_alter:
                        try:
                            with self.engine.begin() as conn:
                                conn.execute(AddConstraint(fk))
                        except Exception as fk_error:
                            logger.warning(f"Could not add foreign key {fk.name or fk.column_keys} on {table.name}: {fk_error}")
            logger.info(f"Database tables ready: {created} checked, {len(failed)} failed{': ' + ', '.join(failed) if failed else ''}")
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
