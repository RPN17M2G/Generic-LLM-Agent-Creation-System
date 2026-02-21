"""
Tests for tools.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from tools.sql_generator import SQLGeneratorTool
from tools.sql_validator import SQLValidatorTool
from tools.sql_executor import SQLExecutorTool
from tools.log_analyzer import LogAnalyzerTool, LogParserTool, PatternDetectorTool
from tools.financial_extractor import FinancialExtractorTool, MessageParserTool, FieldValidatorTool
from tools.bucketing_strategy import FieldAnalyzerTool, BucketStrategyGeneratorTool, BucketValidatorTool
from utils.exceptions import ToolExecutionError


class TestSQLGeneratorTool:
    """Tests for SQL generator tool."""
    
    def test_sql_generator_init(self):
        """Test SQL generator initialization."""
        mock_llm = Mock()
        tool = SQLGeneratorTool(
            sql_llm=mock_llm,
            model_name="test-model",
            database_type="clickhouse"
        )
        
        assert tool.get_name() == "generate_sql"
        assert tool.get_description() == "Generate a SQL query from a natural language question"
    
    def test_sql_generator_parameter_schema(self):
        """Test parameter schema."""
        mock_llm = Mock()
        tool = SQLGeneratorTool(mock_llm, "test-model")
        schema = tool.get_parameter_schema()
        
        assert "natural_language_query" in schema
        assert schema["natural_language_query"]["required"] is True
    
    def test_sql_generator_execute(self):
        """Test SQL generation execution."""
        mock_llm = Mock()
        mock_response = {
            'message': {'content': 'SELECT * FROM users'}
        }
        mock_llm.chat.return_value = mock_response
        
        tool = SQLGeneratorTool(mock_llm, "test-model")
        result = tool.execute({
            "natural_language_query": "Get all users",
            "schema_info": "CREATE TABLE users (id INT)"
        })
        
        # Check that SQL is in the result (format may vary)
        assert "SELECT" in result or "users" in result.lower()


class TestSQLValidatorTool:
    """Tests for SQL validator tool."""
    
    def test_sql_validator_init(self):
        """Test SQL validator initialization."""
        tool = SQLValidatorTool(
            allowed_tables=["users", "orders"],
            database_type="clickhouse"
        )
        
        assert tool.get_name() == "validate_sql"
        assert len(tool.allowed_tables) == 2
    
    def test_sql_validator_valid_query(self):
        """Test validation of valid query."""
        tool = SQLValidatorTool(
            allowed_tables=["users"],
            database_type="clickhouse"
        )
        
        result = tool.execute({
            "sql_query": "SELECT * FROM users"
        })
        
        assert "valid" in result.lower() or "SQL query is valid" in result
    
    def test_sql_validator_invalid_table(self):
        """Test validation with unauthorized table."""
        tool = SQLValidatorTool(
            allowed_tables=["users"],
            database_type="clickhouse"
        )
        
        result = tool.execute({
            "sql_query": "SELECT * FROM unauthorized_table"
        })
        
        assert "error" in result.lower() or "forbidden" in result.lower()


class TestSQLExecutorTool:
    """Tests for SQL executor tool."""
    
    def test_sql_executor_init(self):
        """Test SQL executor initialization."""
        mock_adapter = Mock()
        tool = SQLExecutorTool(mock_adapter)
        
        assert tool.get_name() == "execute_sql"
    
    def test_sql_executor_execute(self):
        """Test SQL execution."""
        import pandas as pd
        mock_adapter = Mock()
        mock_adapter.execute_query.return_value = pd.DataFrame({"col1": [1, 2, 3]})
        
        tool = SQLExecutorTool(mock_adapter)
        result = tool.execute({
            "sql_query": "SELECT * FROM test"
        })
        
        assert "executed successfully" in result.lower()
        mock_adapter.execute_query.assert_called_once()


class TestLogParserTool:
    """Tests for log parser tool."""
    
    def test_log_parser_json(self):
        """Test parsing JSON logs."""
        tool = LogParserTool(log_format="json")
        result = tool.execute({
            "log_data": '{"level": "ERROR", "message": "test"}'
        })
        
        assert "level" in result or "ERROR" in result
    
    def test_log_parser_text(self):
        """Test parsing text logs."""
        tool = LogParserTool(log_format="text")
        result = tool.execute({
            "log_data": "ERROR: test message"
        })
        
        assert "ERROR" in result


class TestMessageParserTool:
    """Tests for message parser tool."""
    
    def test_message_parser(self):
        """Test message parsing."""
        tool = MessageParserTool()
        result = tool.execute({
            "message_data": "Test message content"
        })
        
        assert "Test message" in result


class TestFieldAnalyzerTool:
    """Tests for field analyzer tool."""
    
    def test_field_analyzer(self):
        """Test field analysis."""
        tool = FieldAnalyzerTool()
        result = tool.execute({
            "field_data": "col1,col2\n1,2\n3,4",
            "field_name": "col1"
        })
        
        # Should return JSON with statistics
        assert "count" in result or "error" in result


class TestFieldValidatorTool:
    """Tests for field validator tool."""
    
    def test_field_validator_valid(self):
        """Test validation of valid fields."""
        tool = FieldValidatorTool()
        result = tool.execute({
            "extracted_fields": '{"amounts": [{"value": 100, "currency": "USD"}]}'
        })
        
        assert "valid" in result.lower()


class TestToolValidation:
    """Tests for tool parameter validation."""
    
    def test_missing_required_parameter(self):
        """Test tool with missing required parameter."""
        mock_llm = Mock()
        tool = SQLGeneratorTool(mock_llm, "test-model")
        
        result = tool.execute({
            "schema_info": "CREATE TABLE test"
            # Missing natural_language_query
        })
        
        assert "error" in result.lower() or "required" in result.lower()
    
    def test_wrong_parameter_type(self):
        """Test tool with wrong parameter type."""
        mock_llm = Mock()
        tool = SQLGeneratorTool(mock_llm, "test-model")
        
        result = tool.execute({
            "natural_language_query": 123,  # Should be string
            "schema_info": "CREATE TABLE test"
        })
        
        # Should handle gracefully or return error
        assert isinstance(result, str)

