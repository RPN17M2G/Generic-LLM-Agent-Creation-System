"""
SQL generation tool using LLM.
"""
import re
from typing import Dict, Any, Optional
from ollama import Client
from core.tool import BaseTool
from utils.logger import get_logger
from utils.exceptions import ToolExecutionError

logger = get_logger(__name__)


class SQLGeneratorTool(BaseTool):
    """
    Tool for generating SQL queries from natural language.
    """
    
    def __init__(
        self,
        sql_llm: Client,
        model_name: str,
        database_type: str = "clickhouse"
    ):
        """
        Initialize SQL generator tool.
        
        Args:
            sql_llm: Ollama client instance
            model_name: Model name for SQL generation
            database_type: Database type (clickhouse, postgresql, mysql, etc.)
        """
        self.sql_llm = sql_llm
        self.model_name = model_name
        self.database_type = database_type
        
        super().__init__(
            name="generate_sql",
            description="Generate a SQL query from a natural language question",
            parameter_schema={
                "natural_language_query": {
                    "type": "str",
                    "required": True,
                    "description": "Natural language description of the query"
                },
                "schema_info": {
                    "type": "str",
                    "required": True,
                    "description": "Database schema information"
                },
                "correction_context": {
                    "type": "str",
                    "required": False,
                    "description": "Context from previous failed query attempts"
                }
            }
        )
    
    def _construct_prompt(
        self,
        natural_language_query: str,
        schema_info: str,
        correction_context: Optional[str] = None
    ) -> str:
        """Construct prompt for SQL generation."""
        # Database-specific instructions
        db_instructions = {
            "clickhouse": """
-- 2. Pay close attention to ClickHouse-specific functions, especially for date and time (e.g., use toStartOfMonth(), toYYYYMM(), now()).
-- 3. Do not use syntax from other SQL dialects like T-SQL or PostgreSQL (e.g., GETDATE(), ::date).
""",
            "postgresql": """
-- 2. Use PostgreSQL-specific functions and syntax (e.g., NOW(), DATE_TRUNC(), ::text).
""",
            "mysql": """
-- 2. Use MySQL-specific functions and syntax (e.g., NOW(), DATE_FORMAT()).
""",
        }
        
        db_instruction = db_instructions.get(self.database_type.lower(), "")
        
        few_shot_examples = """
---
-- Few-shot Examples:
-- Question: How many orders were placed last month?
SELECT count(*) FROM orders WHERE order_date >= DATE_TRUNC('month', NOW() - INTERVAL '1 month') AND order_date < DATE_TRUNC('month', NOW());

-- Question: What are the names of the top 3 customers by total spending?
SELECT c.customer_name, sum(p.price * o.quantity) as total_spent
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN products p ON o.product_id = p.product_id
GROUP BY c.customer_name
ORDER BY total_spent DESC
LIMIT 3;
"""
        
        correction_prompt = ""
        if correction_context:
            correction_prompt = f"""
---
-- Previous Attempt Failed:
-- You previously generated a query that failed to execute.
-- {correction_context}
-- Please analyze the error and the failed query, then generate a new, corrected query.
"""
        
        # Database-specific best practices
        db_best_practices = {
            "clickhouse": """
-- ClickHouse-Specific Guidelines:
-- ✅ Use ClickHouse functions: toStartOfMonth(), toYYYYMM(), now(), toDate(), toString()
-- ✅ Use proper ClickHouse types: String, UInt64, DateTime, Date
-- ✅ For aggregations, use sum(), count(), avg(), min(), max()
-- ✅ Use LIMIT for result limiting
-- ❌ DO NOT use: GETDATE(), DATE_TRUNC(), PostgreSQL/MySQL syntax
-- ❌ DO NOT use: ::date, ::text type casting (use ClickHouse functions instead)
""",
            "postgresql": """
-- PostgreSQL-Specific Guidelines:
-- ✅ Use PostgreSQL functions: NOW(), DATE_TRUNC(), TO_CHAR(), EXTRACT()
-- ✅ Use proper type casting: ::date, ::text, ::integer
-- ✅ Use window functions when appropriate: ROW_NUMBER(), RANK(), LAG()
-- ✅ Use proper PostgreSQL types: TIMESTAMP, VARCHAR, INTEGER, NUMERIC
""",
            "mysql": """
-- MySQL-Specific Guidelines:
-- ✅ Use MySQL functions: NOW(), DATE_FORMAT(), CURDATE(), STR_TO_DATE()
-- ✅ Use proper MySQL types: DATETIME, VARCHAR, INT, DECIMAL
-- ✅ Use LIMIT for result limiting
-- ✅ Use proper MySQL date functions
"""
        }
        
        db_practices = db_best_practices.get(self.database_type.lower(), "")
        
        prompt = f"""# Role
You are a world-class {self.database_type.upper()} SQL expert specializing in translating natural language questions into precise, optimized SQL queries.

# Your Task
Translate the user's natural language question into a single, syntactically correct {self.database_type.upper()} SQL query.

# Database Schema
The following tables and their structures are available:
{schema_info}

# Critical Requirements

1. **Query Type**: ONLY generate SELECT statements. NEVER generate:
   - INSERT, UPDATE, DELETE statements
   - DROP, ALTER, CREATE, TRUNCATE statements
   - Any DDL or DML operations
   - Stored procedures or functions

2. **Syntax**: Use {self.database_type.upper()}-specific syntax and functions only
{db_practices}

3. **Output Format**: 
   - Return ONLY the SQL query
   - NO markdown code blocks (no ```sql)
   - NO explanations or comments
   - NO semicolon at the end
   - NO text before or after the query

4. **Query Quality**:
   - Use appropriate JOINs when needed
   - Apply proper WHERE clauses for filtering
   - Use GROUP BY and aggregations when appropriate
   - Include ORDER BY when sorting is needed
   - Use LIMIT when the question implies a limit

# Step-by-Step Process

1. **Analyze** the user's question to understand what data they need
2. **Identify** which tables and columns are relevant from the schema
3. **Plan** the query structure (SELECT, FROM, JOINs, WHERE, GROUP BY, ORDER BY, LIMIT)
4. **Write** the query using correct {self.database_type.upper()} syntax
5. **Verify** the query is syntactically correct and only uses SELECT

# Examples

{few_shot_examples}

# Error Correction Context
{correction_prompt if correction_prompt else "-- No previous errors. Generate a fresh query."}

# User's Question
{natural_language_query}

# Your SQL Query (ONLY the query, nothing else):
"""
        return prompt.strip()
    
    def _parse_sql_from_response(self, response_text: str) -> str:
        """Extract SQL query from LLM response."""
        # Remove markdown code blocks
        match = re.search(r'```sql\s*(.*?)\s*```', response_text, re.DOTALL | re.IGNORECASE)
        if match:
            sql_query = match.group(1)
        else:
            sql_query = response_text
        
        sql_query = sql_query.strip().rstrip(';')
        
        # Remove any leading labels
        if sql_query.lower().startswith("sql query:"):
            sql_query = sql_query[10:].strip()
        
        return sql_query
    
    def _execute_impl(self, args: Dict[str, Any], trace_id: Optional[str] = None) -> str:
        """Execute SQL generation."""
        log = logger.bind(trace_id=trace_id)
        
        nl_query = args["natural_language_query"]
        schema_info = args["schema_info"]
        correction_context = args.get("correction_context")
        
        prompt = self._construct_prompt(nl_query, schema_info, correction_context)
        
        log.info("tool_call_sql_generate", model=self.model_name)
        
        try:
            response = self.sql_llm.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}]
            )
            
            generated_text = response['message']['content']
            sql_query = self._parse_sql_from_response(generated_text)
            
            log.info("tool_result_sql_generate", extracted_sql=sql_query)
            return f"Successfully generated SQL: {sql_query}"
            
        except Exception as e:
            log.error("tool_call_sql_generate_failed", error=str(e), exc_info=True)
            raise ToolExecutionError(f"SQL generation failed: {e}", "generate_sql") from e

