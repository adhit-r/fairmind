"""
Production-ready database configuration with connection pooling.
"""

import asyncio
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
import logging
from databases import Database
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import asyncpg

from .settings import settings

logger = logging.getLogger("fairmind.database")

# SQLAlchemy setup
engine = None
SessionLocal = None
Base = declarative_base()
metadata = MetaData()

# Async database connection
database: Optional[Database] = None


class DatabaseManager:
    """Database connection manager with pooling."""
    
    def __init__(self):
        self.database: Optional[Database] = None
        self.engine = None
        self.SessionLocal = None
        self._pool = None
    
    async def initialize(self):
        """Initialize database connections and pool."""
        try:
            # Create async database connection with pooling
            if settings.database_url.startswith("postgresql"):
                # PostgreSQL with connection pooling
                self.database = Database(
                    settings.database_url,
                    min_size=5,  # Minimum connections in pool
                    max_size=settings.database_pool_size,  # Maximum connections
                    max_queries=50000,  # Max queries per connection
                    max_inactive_connection_lifetime=300,  # 5 minutes
                    timeout=20,  # Connection timeout
                    command_timeout=60,  # Command timeout
                )
                
                # Create asyncpg pool for direct access when needed
                self._pool = await asyncpg.create_pool(
                    settings.database_url,
                    min_size=5,
                    max_size=settings.database_pool_size,
                    max_queries=50000,
                    max_inactive_connection_lifetime=300,
                    timeout=20,
                    command_timeout=60,
                )
                
            else:
                # SQLite fallback (development)
                self.database = Database(settings.database_url)
            
            await self.database.connect()
            
            # Create sync engine for migrations and admin tasks
            if settings.database_url.startswith("postgresql"):
                self.engine = create_engine(
                    settings.database_url,
                    poolclass=QueuePool,
                    pool_size=settings.database_pool_size,
                    max_overflow=settings.database_max_overflow,
                    pool_pre_ping=True,
                    pool_recycle=3600,  # Recycle connections every hour
                    echo=settings.database_echo and not settings.is_production,
                )
            else:
                self.engine = create_engine(
                    settings.database_url,
                    echo=settings.database_echo and not settings.is_production,
                )
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info("Database connections initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def disconnect(self):
        """Close database connections."""
        try:
            if self.database:
                await self.database.disconnect()
            
            if self._pool:
                await self._pool.close()
            
            if self.engine:
                self.engine.dispose()
            
            logger.info("Database connections closed")
            
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")
    
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