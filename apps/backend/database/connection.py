"""
Database connection management for FairMind
Supports both PostgreSQL (Supabase) and SQLite for development
"""

import os
import logging
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

logger = logging.getLogger(__name__)

Base = declarative_base()

class DatabaseManager:
    """Database connection manager with support for multiple databases"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._setup_connection()
    
    def _setup_connection(self):
        """Setup database connection based on environment"""
        database_url = os.getenv("DATABASE_URL")
        
        if database_url and database_url.startswith("postgresql"):
            # PostgreSQL/Supabase connection
            self.engine = create_engine(
                database_url,
                pool_pre_ping=True,
                pool_recycle=300,
                echo=os.getenv("DEBUG", "false").lower() == "true"
            )
            logger.info("Connected to PostgreSQL database")
        else:
            # SQLite for development
            sqlite_url = database_url or "sqlite:///./fairmind.db"
            self.engine = create_engine(
                sqlite_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=os.getenv("DEBUG", "false").lower() == "true"
            )
            logger.info("Connected to SQLite database")
        
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all database tables"""
        try:
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


