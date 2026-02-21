"""
Database schema introspection tool.
"""
from typing import Dict, Any, Optional, List
from core.tool import BaseTool
from databases.base import IDatabaseAdapter
from utils.logger import get_logger
from utils.exceptions import ToolExecutionError

logger = get_logger(__name__)


class SchemaIntrospectorTool(BaseTool):
    """Tool for introspecting database schema and listing available tables."""
    
    def __init__(self, db_adapter: IDatabaseAdapter):
        """
        Initialize schema introspector.
        
        Args:
            db_adapter: Database adapter instance
        """
        self.db_adapter = db_adapter
        super().__init__(
            name="get_schema",
            description="Get schema information for tables. Use this to discover what tables exist and their structure before writing queries.",
            parameter_schema={
                "tables": {
                    "type": "list",
                    "required": False,
                    "description": "List of table names to get schema for. If not provided, returns schema for all allowed tables."
                }
            }
        )
    
    def _execute_impl(self, args: Dict[str, Any], trace_id: Optional[str] = None) -> str:
        """Get schema information."""
        log = logger.bind(trace_id=trace_id)
        
        try:
            tables = args.get("tables")
            if not tables:
                # Get all allowed tables
                tables = self.db_adapter.get_allowed_tables()
                if not tables:
                    return "No tables are configured for this agent. Please check the agent configuration."
            
            if not isinstance(tables, list):
                tables = [tables] if tables else []
            
            log.info("schema_introspection_requested", tables=tables)
            
            # Get schema for requested tables
            schema_info = self.db_adapter.get_schema(tables, trace_id)
            
            if not schema_info or "Error:" in schema_info:
                # Try to list available tables
                available_tables = self.db_adapter.get_allowed_tables()
                if available_tables:
                    return f"Schema retrieval failed. Available tables: {', '.join(available_tables)}. Please use one of these table names."
                else:
                    return "Schema retrieval failed. No tables are available. Please check your database connection and configuration."
            
            # Add table list at the beginning
            result = f"Available tables: {', '.join(tables) if tables else 'None configured'}\n\n"
            result += "Schema information:\n"
            result += schema_info
            
            return result
            
        except Exception as e:
            log.error("schema_introspection_failed", error=str(e), exc_info=True)
            available_tables = self.db_adapter.get_allowed_tables()
            error_msg = f"Failed to get schema: {e}"
            if available_tables:
                error_msg += f"\nAvailable tables: {', '.join(available_tables)}"
            raise ToolExecutionError(error_msg, "get_schema") from e


class ListTablesTool(BaseTool):
    """Tool for listing available tables in the database."""
    
    def __init__(self, db_adapter: IDatabaseAdapter):
        """
        Initialize table lister.
        
        Args:
            db_adapter: Database adapter instance
        """
        self.db_adapter = db_adapter
        super().__init__(
            name="list_tables",
            description="List all available tables that can be queried. Use this to discover what tables exist before writing queries.",
            parameter_schema={}
        )
    
    def _execute_impl(self, args: Dict[str, Any], trace_id: Optional[str] = None) -> str:
        """List available tables."""
        log = logger.bind(trace_id=trace_id)
        
        try:
            tables = self.db_adapter.get_allowed_tables()
            
            if not tables:
                return "No tables are configured for this agent. Please check the agent configuration."
            
            result = f"Available tables ({len(tables)}):\n"
            for i, table in enumerate(tables, 1):
                result += f"  {i}. {table}\n"
            
            result += "\nUse the 'get_schema' tool to get detailed schema information for any table."
            
            log.info("tables_listed", table_count=len(tables))
            return result
            
        except Exception as e:
            log.error("list_tables_failed", error=str(e), exc_info=True)
            return f"Failed to list tables: {e}"

