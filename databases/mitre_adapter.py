"""
MITRE database adapter (generic SQL adapter).
This adapter can work with any SQL database that supports standard SQL.
"""
import pandas as pd
from typing import List, Optional, Dict, Any
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import text
from utils.logger import get_logger
from utils.exceptions import DatabaseError
from .base import IDatabaseAdapter

logger = get_logger(__name__)


class MITREAdapter(IDatabaseAdapter):
    """
    Generic SQL database adapter for MITRE or other SQL databases.
    Uses SQLAlchemy for database connectivity.
    """
    
    # SQLAlchemy dialect mappings
    DIALECT_MAP = {
        "postgresql": "postgresql",
        "postgres": "postgresql",
        "mysql": "mysql+pymysql",
        "mariadb": "mysql+pymysql",
        "sqlite": "sqlite",
        "mssql": "mssql+pyodbc",
        "oracle": "oracle",
    }
    
    def __init__(
        self,
        connection_string: Optional[str] = None,
        dialect: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        allowed_tables: Optional[List[str]] = None,
        **kwargs
    ):
        """
        Initialize MITRE/generic SQL adapter.
        
        Args:
            connection_string: Full SQLAlchemy connection string (takes precedence)
            dialect: Database dialect (postgresql, mysql, etc.)
            host: Database host
            port: Database port
            username: Database username
            password: Database password
            database: Database name
            allowed_tables: List of allowed table names
            **kwargs: Additional connection parameters
        """
        self.allowed_tables = set((allowed_tables or []))
        self._engine = None
        
        if connection_string:
            self.connection_string = connection_string
        else:
            # Build connection string from components
            if not all([dialect, host, database]):
                raise DatabaseError(
                    "Either connection_string or (dialect, host, database) must be provided",
                    "mitre"
                )
            
            # Map dialect to SQLAlchemy dialect
            sqlalchemy_dialect = self.DIALECT_MAP.get(dialect.lower(), dialect)
            
            if username and password:
                auth = f"{username}:{password}@"
            elif username:
                auth = f"{username}@"
            else:
                auth = ""
            
            port_str = f":{port}" if port else ""
            self.connection_string = f"{sqlalchemy_dialect}://{auth}{host}{port_str}/{database}"
        
        # Add any additional kwargs as query parameters
        if kwargs:
            params = "&".join([f"{k}={v}" for k, v in kwargs.items()])
            self.connection_string += f"?{params}"
        
        self._connect()
    
    def _connect(self):
        """Establish database connection."""
        try:
            self._engine = create_engine(self.connection_string)
            # Test connection
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("mitre_connection_success", connection_string=self._mask_connection_string())
        except Exception as e:
            logger.error("mitre_connection_failed", error=str(e), exc_info=True)
            raise DatabaseError(f"Failed to connect to database: {e}", "mitre") from e
    
    def _mask_connection_string(self) -> str:
        """Mask password in connection string for logging."""
        import re
        return re.sub(r':([^:@]+)@', ':****@', self.connection_string)
    
    def execute_query(self, query: str, trace_id: Optional[str] = None) -> pd.DataFrame:
        """Execute a read-only query and return results as DataFrame."""
        log = logger.bind(trace_id=trace_id)
        
        if not self._engine:
            raise DatabaseError("Not connected to database", "mitre")
        
        try:
            log.info("executing_sql_query", sql_query=query)
            with self._engine.connect() as conn:
                result_df = pd.read_sql(text(query), conn)
            log.info("sql_query_success", rows_returned=len(result_df))
            return result_df
        except Exception as e:
            log.error("sql_query_failed", sql_query=query, error=str(e), exc_info=True)
            raise DatabaseError(f"Database query failed: {e}", "mitre") from e
    
    def get_schema(self, tables: List[str], trace_id: Optional[str] = None) -> str:
        """Get schema information for specified tables."""
        log = logger.bind(trace_id=trace_id)
        log.info("getting_database_schema", tables=tables)
        
        schema_str = ""
        inspector = sqlalchemy.inspect(self._engine)
        
        for table in tables:
            # Check if table is allowed
            if self.allowed_tables and table.lower() not in {t.lower() for t in self.allowed_tables}:
                log.warning("table_not_allowed", table=table)
                continue
            
            try:
                # Get column information
                columns = inspector.get_columns(table)
                pk_constraint = inspector.get_pk_constraint(table)
                foreign_keys = inspector.get_foreign_keys(table)
                
                # Build CREATE TABLE-like statement
                col_defs = []
                for col in columns:
                    col_def = f"  {col['name']} {str(col['type'])}"
                    if col.get('nullable') is False:
                        col_def += " NOT NULL"
                    if col.get('default') is not None:
                        col_def += f" DEFAULT {col['default']}"
                    col_defs.append(col_def)
                
                schema_str += f"CREATE TABLE {table} (\n"
                schema_str += ",\n".join(col_defs)
                schema_str += "\n);\n\n"
                
            except Exception as e:
                log.error("get_schema_failed_for_table", table=table, error=str(e))
        
        if not schema_str:
            log.warning("get_schema_empty", tables=tables)
            return "Error: Could not retrieve schema for any tables."
        
        return schema_str
    
    def validate_connection(self) -> bool:
        """Validate that the connection is working."""
        try:
            if self._engine:
                with self._engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                return True
            return False
        except Exception:
            return False
    
    def get_database_type(self) -> str:
        """Get database type identifier."""
        return "mitre"
    
    def get_allowed_tables(self) -> List[str]:
        """Get list of allowed tables."""
        return list(self.allowed_tables) if self.allowed_tables else []

