"""
ClickHouse database adapter.
"""
import pandas as pd
import clickhouse_connect
from typing import List, Optional
from utils.logger import get_logger
from utils.exceptions import DatabaseError
from .base import IDatabaseAdapter

logger = get_logger(__name__)


class ClickHouseAdapter(IDatabaseAdapter):
    """
    ClickHouse database adapter implementing IDatabaseAdapter.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8123,
        username: str = "default",
        password: str = "",
        database: str = "default",
        allowed_tables: Optional[List[str]] = None
    ):
        """
        Initialize ClickHouse adapter.
        
        Args:
            host: ClickHouse host
            port: ClickHouse port
            username: Database username
            password: Database password
            database: Database name
            allowed_tables: List of allowed table names (None = all tables)
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.allowed_tables = set((allowed_tables or []))
        self._client = None
        self._connect()
    
    def _connect(self):
        """Establish ClickHouse connection."""
        try:
            self._client = clickhouse_connect.get_client(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                database=self.database,
            )
            self._client.ping()
            logger.info(
                "clickhouse_connection_success",
                host=self.host,
                database=self.database
            )
        except Exception as e:
            logger.error("clickhouse_connection_failed", error=str(e), exc_info=True)
            raise DatabaseError(f"Failed to connect to ClickHouse: {e}", "clickhouse") from e
    
    def execute_query(self, query: str, trace_id: Optional[str] = None) -> pd.DataFrame:
        """Execute a read-only query and return results as DataFrame."""
        log = logger.bind(trace_id=trace_id)
        
        if not self._client:
            raise DatabaseError("Not connected to ClickHouse", "clickhouse")
        
        try:
            log.info("executing_sql_query", sql_query=query)
            result_df = self._client.query_df(query)
            log.info("sql_query_success", rows_returned=len(result_df))
            return result_df
        except Exception as e:
            log.error("sql_query_failed", sql_query=query, error=str(e), exc_info=True)
            raise DatabaseError(f"ClickHouse query failed: {e}", "clickhouse") from e
    
    def get_schema(self, tables: List[str], trace_id: Optional[str] = None) -> str:
        """Get schema information for specified tables."""
        log = logger.bind(trace_id=trace_id)
        log.info("getting_database_schema", tables=tables)
        
        schema_str = ""
        for table in tables:
            # Check if table is allowed
            if self.allowed_tables and table.lower() not in {t.lower() for t in self.allowed_tables}:
                log.warning("table_not_allowed", table=table)
                continue
            
            try:
                create_table_statement = self._client.command(f'SHOW CREATE TABLE {table}')
                schema_str += create_table_statement + "\n\n"
            except Exception as e:
                log.error("get_schema_failed_for_table", table=table, error=str(e))
        
        if not schema_str:
            log.warning("get_schema_empty", tables=tables)
            return "Error: Could not retrieve schema for any tables."
        
        return schema_str
    
    def validate_connection(self) -> bool:
        """Validate that the connection is working."""
        try:
            if self._client:
                self._client.ping()
                return True
            return False
        except Exception:
            return False
    
    def get_database_type(self) -> str:
        """Get database type identifier."""
        return "clickhouse"
    
    def get_allowed_tables(self) -> List[str]:
        """Get list of allowed tables."""
        return list(self.allowed_tables) if self.allowed_tables else []

