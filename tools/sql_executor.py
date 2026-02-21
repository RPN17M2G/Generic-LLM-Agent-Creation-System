"""
SQL execution tool.
"""
from typing import Dict, Any, Optional, TYPE_CHECKING
import pandas as pd
from core.tool import BaseTool
from databases.base import IDatabaseAdapter
from utils.logger import get_logger
from utils.exceptions import ToolExecutionError

if TYPE_CHECKING:
    from security.pii_masker import PIIMasker
else:
    try:
        from security.pii_masker import PIIMasker
    except ImportError:
        PIIMasker = None

logger = get_logger(__name__)


class SQLExecutorTool(BaseTool):
    """
    Tool for executing SQL queries on a database.
    """
    
    def __init__(
        self,
        db_adapter: IDatabaseAdapter,
        pii_masker: Optional['PIIMasker'] = None
    ):
        """
        Initialize SQL executor tool.
        
        Args:
            db_adapter: Database adapter instance
            pii_masker: Optional PII masker for result sanitization
        """
        self.db_adapter = db_adapter
        self.pii_masker = pii_masker
        
        super().__init__(
            name="execute_sql",
            description="Execute a validated SQL query and return results",
            parameter_schema={
                "sql_query": {
                    "type": "str",
                    "required": True,
                    "description": "Valid SQL query to execute"
                }
            }
        )
    
    def _execute_impl(self, args: Dict[str, Any], trace_id: Optional[str] = None) -> str:
        """Execute SQL query."""
        log = logger.bind(trace_id=trace_id)
        sql_query = args["sql_query"]
        
        try:
            log.info("executing_sql_query", sql_query=sql_query)
            data_df = self.db_adapter.execute_query(sql_query, trace_id)
            
            if data_df.empty:
                return "Query executed successfully, but returned no results."
            
            data_markdown = data_df.to_markdown(index=False)
            
            # Mask PII if masker is available
            if self.pii_masker:
                masked_data = self.pii_masker.mask_text_result(data_markdown, trace_id)
                return f"Query executed successfully. Data:\n{masked_data}"
            else:
                return f"Query executed successfully. Data:\n{data_markdown}"
                
        except Exception as e:
            log.error("sql_execution_failed", error=str(e), exc_info=True)
            raise ToolExecutionError(f"SQL execution failed: {e}", "execute_sql") from e

