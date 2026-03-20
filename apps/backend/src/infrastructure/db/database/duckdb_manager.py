"""
DuckDB Manager
Handles connections and query execution for analytical workloads using DuckDB.
"""

import duckdb
import logging
from typing import Optional, List, Dict, Any
import pandas as pd
from core.container import service, ServiceLifetime
from core.base_service import BaseService
from core.interfaces import ILogger

@service(lifetime=ServiceLifetime.SINGLETON)
class DuckDBManager(BaseService):
    def __init__(self, logger: Optional[ILogger] = None):
        super().__init__(logger)
        self.db_path = "apps/backend/fairmind_analytics.duckdb"
        self.conn = None
        
    def get_connection(self):
        """Get a connection to the DuckDB database."""
        if self.conn is None:
            try:
                self.conn = duckdb.connect(self.db_path)
                self.logger.info(f"Connected to DuckDB at {self.db_path}")
            except Exception as e:
                self.logger.error(f"Failed to connect to DuckDB: {e}")
                raise
        return self.conn

    def execute_query(self, query: str, params: Optional[List[Any]] = None) -> List[Any]:
        """Execute a query and return results."""
        conn = self.get_connection()
        try:
            if params:
                return conn.execute(query, params).fetchall()
            return conn.execute(query).fetchall()
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            raise

    def query_df(self, query: str, params: Optional[List[Any]] = None) -> pd.DataFrame:
        """Execute a query and return result as a Pandas DataFrame."""
        conn = self.get_connection()
        try:
            if params:
                return conn.execute(query, params).df()
            return conn.execute(query).df()
        except Exception as e:
            self.logger.error(f"DataFrame query failed: {e}")
            raise
            
    def register_file(self, table_name: str, file_path: str):
        """Register a CSV/Parquet file as a table view."""
        conn = self.get_connection()
        try:
            # Auto-detect file type
            if file_path.endswith('.csv'):
                conn.execute(f"CREATE OR REPLACE VIEW {table_name} AS SELECT * FROM read_csv_auto('{file_path}')")
            elif file_path.endswith('.parquet'):
                conn.execute(f"CREATE OR REPLACE VIEW {table_name} AS SELECT * FROM read_parquet('{file_path}')")
            else:
                raise ValueError(f"Unsupported file type for {file_path}")
                
            self.logger.info(f"Registered file {file_path} as view {table_name}")
        except Exception as e:
            self.logger.error(f"Failed to register file: {e}")
            raise
