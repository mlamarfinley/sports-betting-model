"""Database connection pooling module for sports betting model."""
import os
import psycopg2
from psycopg2 import pool
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Singleton database manager with connection pooling.
    
    CRITICAL FIX #1: Database Connection Pooling
    Problem: Each pipeline creates new connections, exhausting pool
    Solution: Use psycopg2.pool.SimpleConnectionPool for connection reuse
    """
    _instance = None
    _connection_pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_pool()
        return cls._instance

    def _initialize_pool(self):
        """Initialize connection pool with proper configuration."""
        try:
            db_config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'database': os.getenv('DB_NAME', 'sports_betting'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD'),
                'port': int(os.getenv('DB_PORT', '5432'))
            }
            
            # Create connection pool (min 2, max 20 connections)
            self._connection_pool = pool.SimpleConnectionPool(
                minconn=2,
                maxconn=20,
                **db_config
            )
            logger.info(f"Database connection pool initialized (2-20 connections)")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise

    def get_connection(self):
        """Get a connection from the pool.
        
        Returns:
            psycopg2 connection object or None if pool is not initialized
        """
        try:
            if self._connection_pool is None:
                logger.error("Connection pool not initialized")
                return None
            return self._connection_pool.getconn()
        except Exception as e:
            logger.error(f"Failed to get connection from pool: {e}")
            return None

    def return_connection(self, conn):
        """Return a connection back to the pool.
        
        Args:
            conn: psycopg2 connection object
        """
        try:
            if self._connection_pool and conn:
                self._connection_pool.putconn(conn)
        except Exception as e:
            logger.error(f"Failed to return connection to pool: {e}")

    def close_all_connections(self):
        """Close all connections in the pool.
        
        Call this when shutting down the application.
        """
        try:
            if self._connection_pool:
                self._connection_pool.closeall()
                logger.info("All database connections closed")
        except Exception as e:
            logger.error(f"Error closing connections: {e}")

    def execute_query(self, query, params=None, fetch_one=False):
        """Execute a query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters (optional)
            fetch_one: If True, return one row; if False, return all rows
            
        Returns:
            Query results or None if error
        """
        conn = self.get_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            
            if fetch_one:
                result = cursor.fetchone()
            else:
                result = cursor.fetchall()
            
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            return None
        finally:
            self.return_connection(conn)


# Global instance for easy access
db_manager = DatabaseManager()
