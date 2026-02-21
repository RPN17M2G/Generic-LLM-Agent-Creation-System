"""
Database adapter factory for creating database adapters dynamically.
"""
from typing import Dict, Any, Optional, Type
from utils.logger import get_logger
from utils.exceptions import DatabaseError
from .base import IDatabaseAdapter

logger = get_logger(__name__)


class DatabaseFactory:
    """
    Factory for creating database adapters based on configuration.
    """
    _adapters: Dict[str, Type[IDatabaseAdapter]] = {}
    
    @classmethod
    def register(cls, database_type: str, adapter_class: Type[IDatabaseAdapter]):
        """
        Register a database adapter class.
        
        Args:
            database_type: Database type identifier (e.g., "clickhouse")
            adapter_class: Adapter class implementing IDatabaseAdapter
        """
        cls._adapters[database_type] = adapter_class
        logger.info("database_adapter_registered", database_type=database_type)
    
    @classmethod
    def create(cls, database_type: str, config: Dict[str, Any]) -> IDatabaseAdapter:
        """
        Create a database adapter instance.
        
        Args:
            database_type: Database type identifier
            config: Configuration dictionary for the adapter
            
        Returns:
            Database adapter instance
            
        Raises:
            DatabaseError: If database type is not supported
        """
        adapter_class = cls._adapters.get(database_type.lower())
        
        if adapter_class is None:
            supported_types = list(cls._adapters.keys())
            raise DatabaseError(
                f"Unsupported database type: {database_type}. Supported types: {supported_types}",
                database_type
            )
        
        try:
            adapter = adapter_class(**config)
            logger.info("database_adapter_created", database_type=database_type)
            return adapter
        except Exception as e:
            logger.error("database_adapter_creation_failed", database_type=database_type, error=str(e))
            raise DatabaseError(
                f"Failed to create database adapter for {database_type}: {e}",
                database_type
            ) from e
    
    @classmethod
    def list_supported_types(cls) -> list[str]:
        """List all supported database types."""
        return list(cls._adapters.keys())


# Register default adapters
from .clickhouse_adapter import ClickHouseAdapter
from .mitre_adapter import MITREAdapter

DatabaseFactory.register("clickhouse", ClickHouseAdapter)
DatabaseFactory.register("mitre", MITREAdapter)
