"""
Base database adapter interface.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)


class IDatabaseAdapter(ABC):
    """
    Interface for all database adapters.
    Provides a unified interface for different database systems.
    """
    
    @abstractmethod
    def execute_query(self, query: str, trace_id: Optional[str] = None) -> pd.DataFrame:
        """
        Execute a read-only query and return results as DataFrame.
        
        Args:
            query: SQL query string
            trace_id: Optional trace ID for logging
            
        Returns:
            Query results as pandas DataFrame
            
        Raises:
            DatabaseError: If query execution fails
        """
        pass
    
    @abstractmethod
    def get_schema(self, tables: List[str], trace_id: Optional[str] = None) -> str:
        """
        Get schema information for specified tables.
        
        Args:
            tables: List of table names
            trace_id: Optional trace ID for logging
            
        Returns:
            Schema information as string (e.g., CREATE TABLE statements)
        """
        pass
    
    @abstractmethod
    def validate_connection(self) -> bool:
        """
        Validate that the database connection is working.
        
        Returns:
            True if connection is valid
        """
        pass
    
    @abstractmethod
    def get_database_type(self) -> str:
        """
        Get the database type identifier.
        
        Returns:
            Database type (e.g., "clickhouse", "postgresql", "mysql")
        """
        pass
    
    @abstractmethod
    def get_allowed_tables(self) -> List[str]:
        """
        Get the list of tables this adapter is allowed to access.
        
        Returns:
            List of allowed table names
        """
        pass

