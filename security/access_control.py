"""
Access control for database operations.
"""
from typing import List, Dict, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class AccessControl:
    """
    Access control manager for agents and databases.
    """
    
    def __init__(self):
        """Initialize access control."""
        self._agent_permissions: Dict[str, Dict[str, List[str]]] = {}
        logger.info("access_control_initialized")
    
    def grant_access(
        self,
        agent_name: str,
        database_type: str,
        allowed_tables: List[str]
    ):
        """
        Grant access to an agent for specific tables.
        
        Args:
            agent_name: Name of the agent
            database_type: Database type
            allowed_tables: List of allowed table names
        """
        if agent_name not in self._agent_permissions:
            self._agent_permissions[agent_name] = {}
        
        self._agent_permissions[agent_name][database_type] = allowed_tables
        logger.info("access_granted", agent_name=agent_name, database_type=database_type, tables=allowed_tables)
    
    def check_access(
        self,
        agent_name: str,
        database_type: str,
        table_name: str
    ) -> bool:
        """
        Check if agent has access to a table.
        
        Args:
            agent_name: Name of the agent
            database_type: Database type
            table_name: Table name to check
            
        Returns:
            True if access is granted
        """
        if agent_name not in self._agent_permissions:
            return False
        
        if database_type not in self._agent_permissions[agent_name]:
            return False
        
        allowed_tables = self._agent_permissions[agent_name][database_type]
        return table_name.lower() in {t.lower() for t in allowed_tables}
    
    def get_allowed_tables(
        self,
        agent_name: str,
        database_type: str
    ) -> List[str]:
        """Get list of allowed tables for an agent."""
        if agent_name not in self._agent_permissions:
            return []
        
        if database_type not in self._agent_permissions[agent_name]:
            return []
        
        return self._agent_permissions[agent_name][database_type].copy()

