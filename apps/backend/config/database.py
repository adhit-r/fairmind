"""
Production-ready database configuration with connection pooling.
"""

import asyncio
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
import logging
from databases import Database
from databases.backends.sqlite import SQLitePool
from sqlalchemy import create_engine, MetaData, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import asyncpg

from .settings import settings
from .migration_integrity import (
    MigrationIntegrityError,
    bind_postgresql_engine_search_path,
    postgresql_runtime_search_path,
    verify_assurance_migration_integrity,
    verify_database_identities,
)

logger = logging.getLogger("fairmind.database")

_DATABASE_IMPLEMENTATION = Database

# SQLAlchemy setup
engine = None
SessionLocal = None
Base = declarative_base()
metadata = MetaData()

# Async database connection
database: Optional[Database] = None


def _get_repository_database_manager():
    """Resolve the manager used by the v2 route dependency at startup."""
    from database.connection import db_manager as repository_database_manager

    return repository_database_manager


def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys = ON")
    finally:
        cursor.close()


class _ForeignKeySQLitePool(SQLitePool):
    """Enable and verify foreign keys on every aiosqlite acquisition."""

    async def acquire(self):
        connection = await super().acquire()
        try:
            enable_cursor = await connection.execute("PRAGMA foreign_keys = ON")
            await enable_cursor.close()
            cursor = await connection.execute("PRAGMA foreign_keys")
            try:
                row = await cursor.fetchone()
            finally:
                await cursor.close()
            if row is None or int(row[0]) != 1:
                raise RuntimeError(
                    "SQLite foreign-key enforcement could not be enabled"
                )
        except Exception:
            await super().release(connection)
            raise
        return connection


def _install_async_sqlite_foreign_key_pool(database_instance) -> None:
    """Replace the per-query library pool before connect; fail on API drift."""
    if not isinstance(database_instance, _DATABASE_IMPLEMENTATION):
        # Unit-test doubles do not expose the third-party backend internals.
        return
    backend = getattr(database_instance, "_backend", None)
    current_pool = getattr(backend, "_pool", None)
    if not isinstance(current_pool, SQLitePool):
        raise RuntimeError("Unexpected databases SQLite backend implementation")
    memory_reference = getattr(current_pool, "_memref", None)
    if memory_reference is not None:
        memory_reference.close()
    backend._pool = _ForeignKeySQLitePool(
        database_instance.url,
        **database_instance.options,
    )


class DatabaseManager:
    """Database connection manager with pooling."""
    
    def __init__(self):
        self.database: Optional[Database] = None
        self.engine = None
        self.SessionLocal = None
        self._pool = None

    async def _close_resources(self) -> list[Exception]:
        """Best-effort close of every initialized resource in reverse order."""
        errors: list[Exception] = []
        engine_to_close, self.engine = self.engine, None
        database_to_close, self.database = self.database, None
        pool_to_close, self._pool = self._pool, None
        self.SessionLocal = None

        if engine_to_close is not None:
            try:
                engine_to_close.dispose()
            except Exception as error:
                errors.append(error)
        if database_to_close is not None:
            try:
                await database_to_close.disconnect()
            except Exception as error:
                errors.append(error)
        if pool_to_close is not None:
            try:
                await pool_to_close.close()
            except Exception as error:
                errors.append(error)
        return errors
    
    async def initialize(self):
        """Initialize database connections and pool."""
        try:
            is_postgresql = settings.database_url.startswith("postgresql")
            assurance_enabled = settings.assurance_v2_enabled
            trusted_schema = settings.assurance_migration_schema or ""
            runtime_search_path = None
            if is_postgresql and assurance_enabled:
                runtime_search_path = postgresql_runtime_search_path(trusted_schema)

            # Create async database connection with pooling
            if is_postgresql:
                # PostgreSQL with connection pooling
                database_options = {
                    "min_size": 5,
                    "max_size": settings.database_pool_size,
                    "max_queries": 50000,
                    "max_inactive_connection_lifetime": 300,
                    "timeout": 20,
                    "command_timeout": 60,
                }
                if runtime_search_path is not None:
                    database_options["server_settings"] = {
                        "search_path": runtime_search_path
                    }
                self.database = Database(settings.database_url, **database_options)
                
                # Create asyncpg pool for direct access when needed
                pool_options = {
                    "min_size": 5,
                    "max_size": settings.database_pool_size,
                    "max_queries": 50000,
                    "max_inactive_connection_lifetime": 300,
                    "timeout": 20,
                    "command_timeout": 60,
                }
                if runtime_search_path is not None:
                    pool_options["server_settings"] = {
                        "search_path": runtime_search_path
                    }
                self._pool = await asyncpg.create_pool(
                    settings.database_url,
                    **pool_options,
                )
                
            else:
                # SQLite fallback (development)
                self.database = Database(settings.database_url)
                _install_async_sqlite_foreign_key_pool(self.database)
            
            await self.database.connect()
            if not is_postgresql:
                await self.database.execute("PRAGMA foreign_keys = ON")
            
            # Create sync engine for migrations and admin tasks
            if is_postgresql:
                self.engine = create_engine(
                    settings.database_url,
                    poolclass=QueuePool,
                    pool_size=settings.database_pool_size,
                    max_overflow=settings.database_max_overflow,
                    pool_pre_ping=True,
                    pool_recycle=3600,  # Recycle connections every hour
                    echo=settings.database_echo and not settings.is_production,
                )
                if assurance_enabled:
                    bind_postgresql_engine_search_path(self.engine, trusted_schema)
            else:
                self.engine = create_engine(
                    settings.database_url,
                    echo=settings.database_echo and not settings.is_production,
                )
                event.listen(self.engine, "connect", _enable_sqlite_foreign_keys)

            repository_engine = None
            if assurance_enabled:
                repository_database_manager = _get_repository_database_manager()
                repository_engine = getattr(repository_database_manager, "engine", None)
                if repository_engine is None:
                    raise RuntimeError("Repository database engine is unavailable")
                if is_postgresql:
                    bind_postgresql_engine_search_path(
                        repository_engine, trusted_schema
                    )
                verify_database_identities(self.engine, repository_engine)

            verify_assurance_migration_integrity(
                self.engine,
                enabled=assurance_enabled,
                postgresql_schema=settings.assurance_migration_schema,
            )
            if repository_engine is not None:
                verify_assurance_migration_integrity(
                    repository_engine,
                    enabled=assurance_enabled,
                    postgresql_schema=settings.assurance_migration_schema,
                )
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )

            # Create all tables defined in models
            try:
                from src.infrastructure.db.database.models import Base
                Base.metadata.create_all(bind=self.engine)
                logger.info("Database tables created successfully")
            except Exception as error:
                logger.warning(
                    "Database table creation failed (%s)",
                    type(error).__name__,
                )

            logger.info("Database connections initialized successfully")

        except Exception as error:
            logger.error(
                "Failed to initialize database (%s)",
                type(error).__name__,
            )
            for cleanup_error in await self._close_resources():
                logger.error(
                    "Failed to clean up database resource after initialization "
                    "error (%s)",
                    type(cleanup_error).__name__,
                )
            if isinstance(error, MigrationIntegrityError):
                raise
            raise RuntimeError("Database initialization failed") from None
    
    async def disconnect(self):
        """Close database connections."""
        errors = await self._close_resources()
        if not errors:
            logger.info("Database connections closed")
            return
        for error in errors:
            logger.error(
                "Error closing database connection (%s)", type(error).__name__
            )
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection from the pool."""
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.connection() as connection:
            yield connection
    
    @asynccontextmanager
    async def get_transaction(self):
        """Get a database transaction."""
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.transaction():
            yield self.database
    
    async def execute_query(self, query: str, values: dict = None):
        """Execute a single query."""
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        return await self.database.fetch_all(query, values)
    
    async def execute_one(self, query: str, values: dict = None):
        """Execute a query and return one result."""
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        return await self.database.fetch_one(query, values)
    
    async def execute(self, query: str, values: dict = None):
        """Execute a query without returning results."""
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        return await self.database.execute(query, values)
    
    def get_sync_session(self):
        """Get a synchronous database session."""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")
        
        return self.SessionLocal()
    
    async def health_check(self) -> bool:
        """Check database health."""
        try:
            if not self.database:
                return False
            
            await self.database.fetch_one("SELECT 1")
            return True
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def get_pool_status(self) -> dict:
        """Get connection pool status."""
        if not self._pool:
            return {"status": "no_pool"}
        
        return {
            "size": self._pool.get_size(),
            "max_size": self._pool.get_max_size(),
            "min_size": self._pool.get_min_size(),
            "idle_connections": self._pool.get_idle_size(),
            "used_connections": self._pool.get_size() - self._pool.get_idle_size(),
        }


# Global database manager instance
db_manager = DatabaseManager()


# Dependency for FastAPI
async def get_database() -> Database:
    """FastAPI dependency to get database connection."""
    if not db_manager.database:
        raise RuntimeError("Database not initialized")
    return db_manager.database


@asynccontextmanager
async def get_db_connection():
    """Context manager for database connections."""
    async with db_manager.get_connection() as connection:
        yield connection


@asynccontextmanager
async def get_db_transaction():
    """Context manager for database transactions."""
    async with db_manager.get_transaction() as transaction:
        yield transaction


# Initialize database on import (will be called from main.py)
async def init_database():
    """Initialize database connections."""
    await db_manager.initialize()


async def close_database():
    """Close database connections."""
    await db_manager.disconnect()
