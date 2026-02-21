"""
SQL validation tool.
"""
import sqlglot
import sqlparse
from typing import Dict, Any, Optional, List, Tuple, Set
from core.tool import BaseTool
from utils.logger import get_logger
from utils.exceptions import ToolExecutionError

logger = get_logger(__name__)

PII_COLUMN_PATTERNS = [
    r'ssn', r'social_security', r'credit_card', r'cc_num',
    r'phone', r'email', r'address', r'dob', r'date_of_birth'
]

DIALECTS_TO_TRY = ["tsql", "postgres", "mysql"]


class SQLValidatorTool(BaseTool):
    """
    Tool for validating SQL queries.
    """
    
    def __init__(
        self,
        allowed_tables: List[str],
        database_type: str = "clickhouse",
        pii_patterns: Optional[List[str]] = None
    ):
        """
        Initialize SQL validator tool.
        
        Args:
            allowed_tables: List of allowed table names
            database_type: Database type for parsing
            pii_patterns: Optional custom PII column patterns
        """
        import re
        self.allowed_tables = {table.lower() for table in allowed_tables}
        self.database_type = database_type
        self.pii_patterns = [re.compile(p, re.IGNORECASE) for p in (pii_patterns or PII_COLUMN_PATTERNS)]
        
        super().__init__(
            name="validate_sql",
            description="Validate a SQL query for security and correctness",
            parameter_schema={
                "sql_query": {
                    "type": "str",
                    "required": True,
                    "description": "SQL query to validate"
                }
            }
        )
    
    def _get_all_queried_tables(self, parsed_statement: sqlglot.exp.Expression) -> Set[str]:
        """Find all tables in the query."""
        return {
            table.name.lower()
            for table in parsed_statement.find_all(sqlglot.exp.Table)
        }
    
    def _get_all_selected_columns(self, parsed_statement: sqlglot.exp.Expression) -> Set[str]:
        """Find all columns being selected."""
        return {
            col.name.lower()
            for col in parsed_statement.find_all(sqlglot.exp.Column)
        }
    
    def _validate_internal(
        self,
        sql_query: str,
        log,
        is_correction: bool = False
    ) -> Tuple[bool, str, Optional[sqlglot.exp.Expression]]:
        """Internal validation logic."""
        try:
            parsed_statement = sqlglot.parse_one(sql_query, read=self.database_type)
        except sqlglot.errors.ParseError as e:
            if is_correction:
                return False, f"Corrected query still fails to parse: {e}", None
            log.warning("sql_parse_failed_trying_correction", error=str(e))
            return False, f"Initial parse failed: {e}", None
        except Exception as e:
            msg = f"Unexpected parsing error: {e}"
            log.warning("sql_validation_failed", reason=msg, error=str(e))
            return False, msg, None
        
        if not isinstance(parsed_statement, sqlglot.exp.Select):
            msg = "Validation Failed: Only SELECT statements are allowed."
            log.warning("sql_validation_failed", reason=msg)
            return False, msg, None
        
        queried_tables = self._get_all_queried_tables(parsed_statement)
        if queried_tables and not queried_tables.issubset(self.allowed_tables):
            disallowed_tables = queried_tables - self.allowed_tables
            msg = f"Validation Failed: Access to unauthorized tables is forbidden: {disallowed_tables}."
            log.warning("sql_validation_failed", reason=msg, disallowed_tables=list(disallowed_tables))
            return False, msg, None
        
        selected_columns = self._get_all_selected_columns(parsed_statement)
        for col_name in selected_columns:
            for pattern in self.pii_patterns:
                if pattern.search(col_name):
                    msg = f"Validation Failed: Query appears to be selecting PII column: '{col_name}'."
                    log.warning("sql_validation_failed", reason=msg, pii_column=col_name)
                    return False, msg, None
        
        return True, "", parsed_statement
    
    def _execute_impl(self, args: Dict[str, Any], trace_id: Optional[str] = None) -> str:
        """Execute SQL validation."""
        log = logger.bind(trace_id=trace_id)
        sql_query = args["sql_query"]
        
        # Check for multiple statements
        try:
            statements = sqlparse.split(sql_query)
            if len(statements) > 1:
                msg = "Validation Failed: Multiple SQL statements are not allowed."
                log.warning("sql_validation_failed", reason=msg)
                return f"Error: {msg}"
        except Exception as e:
            msg = f"Validation Failed: SQL parsing error (sqlparse): {e}"
            log.warning("sql_validation_failed", reason=msg, error=str(e))
            return f"Error: {msg}"
        
        is_valid, error_msg, parsed_statement = self._validate_internal(sql_query, log)
        
        if is_valid:
            log.info("sql_validation_success")
            return "SQL query is valid."
        
        # Try auto-correction
        if "Initial parse failed" in error_msg:
            for dialect in DIALECTS_TO_TRY:
                try:
                    corrected_query = sqlglot.transpile(sql_query, read=dialect, write=self.database_type)[0]
                    log.info("sql_correction_attempt", source_dialect=dialect, corrected_query=corrected_query)
                    
                    is_valid_corrected, error_msg_corrected, _ = self._validate_internal(
                        corrected_query, log, is_correction=True
                    )
                    
                    if is_valid_corrected:
                        log.info("sql_correction_success", source_dialect=dialect)
                        return f"SQL query corrected and validated. Corrected query: {corrected_query}"
                except Exception as e:
                    log.info("sql_correction_dialect_failed", dialect=dialect, error=str(e))
                    continue
        
        log.warning("sql_validation_failed_final", reason=error_msg)
        return f"Error: {error_msg}"

