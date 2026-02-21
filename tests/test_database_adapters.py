"""
Tests for database adapters.
"""
import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from databases.base import IDatabaseAdapter
from databases.clickhouse_adapter import ClickHouseAdapter
from databases.mitre_adapter import MITREAdapter
from databases.factory import DatabaseFactory
from utils.exceptions import DatabaseError


class TestClickHouseAdapter:
    """Tests for ClickHouse adapter."""
    
    @patch('databases.clickhouse_adapter.clickhouse_connect')
    def test_clickhouse_adapter_init(self, mock_clickhouse):
        """Test ClickHouse adapter initialization."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_clickhouse.get_client.return_value = mock_client
        
        adapter = ClickHouseAdapter(
            host="localhost",
            port=8123,
            username="test",
            password="test",
            database="test",
            allowed_tables=["table1", "table2"]
        )
        
        assert adapter.get_database_type() == "clickhouse"
        # Order may vary, so check set equality
        assert set(adapter.get_allowed_tables()) == {"table1", "table2"}
        assert adapter.validate_connection() is True
    
    @patch('databases.clickhouse_adapter.clickhouse_connect')
    def test_clickhouse_execute_query(self, mock_clickhouse):
        """Test query execution."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.query_df.return_value = pd.DataFrame({"col1": [1, 2, 3]})
        mock_clickhouse.get_client.return_value = mock_client
        
        adapter = ClickHouseAdapter(host="localhost")
        result = adapter.execute_query("SELECT * FROM test", trace_id="test")
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        mock_client.query_df.assert_called_once_with("SELECT * FROM test")
    
    @patch('databases.clickhouse_adapter.clickhouse_connect')
    def test_clickhouse_get_schema(self, mock_clickhouse):
        """Test schema retrieval."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.command.return_value = "CREATE TABLE test (id Int32)"
        mock_clickhouse.get_client.return_value = mock_client
        
        adapter = ClickHouseAdapter(
            host="localhost",
            allowed_tables=["test"]
        )
        schema = adapter.get_schema(["test"], trace_id="test")
        
        assert "CREATE TABLE test" in schema
        mock_client.command.assert_called_once_with("SHOW CREATE TABLE test")


class TestMITREAdapter:
    """Tests for MITRE adapter."""
    
    @patch('databases.mitre_adapter.create_engine')
    def test_mitre_adapter_init(self, mock_create_engine):
        """Test MITRE adapter initialization."""
        mock_engine = Mock()
        mock_conn = Mock()
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        mock_conn.execute.return_value = None
        mock_engine.connect.return_value = mock_conn
        mock_create_engine.return_value = mock_engine
        
        adapter = MITREAdapter(
            dialect="postgresql",
            host="localhost",
            port=5432,
            username="test",
            password="test",
            database="test",
            allowed_tables=["table1"]
        )
        
        assert adapter.get_database_type() == "mitre"
        assert adapter.get_allowed_tables() == ["table1"]
    
    @patch('databases.mitre_adapter.create_engine')
    @patch('databases.mitre_adapter.pd.read_sql')
    def test_mitre_execute_query(self, mock_read_sql, mock_create_engine):
        """Test query execution."""
        mock_engine = Mock()
        mock_conn = Mock()
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        mock_conn.execute.return_value = None
        mock_engine.connect.return_value = mock_conn
        mock_create_engine.return_value = mock_engine
        
        mock_read_sql.return_value = pd.DataFrame({"col1": [1, 2]})
        
        adapter = MITREAdapter(
            dialect="postgresql",
            host="localhost",
            database="test"
        )
        result = adapter.execute_query("SELECT * FROM test", trace_id="test")
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2


class TestDatabaseFactory:
    """Tests for database factory."""
    
    def test_factory_registration(self):
        """Test database adapter registration."""
        original_count = len(DatabaseFactory.list_supported_types())
        
        class TestAdapter(IDatabaseAdapter):
            def execute_query(self, query, trace_id=None):
                return pd.DataFrame()
            
            def get_schema(self, tables, trace_id=None):
                return ""
            
            def validate_connection(self):
                return True
            
            def get_database_type(self):
                return "test"
            
            def get_allowed_tables(self):
                return []
        
        DatabaseFactory.register("test_db", TestAdapter)
        
        assert "test_db" in DatabaseFactory.list_supported_types()
        assert len(DatabaseFactory.list_supported_types()) == original_count + 1
    
    def test_factory_create_unsupported(self):
        """Test factory with unsupported database type."""
        with pytest.raises(DatabaseError):
            DatabaseFactory.create("unsupported_db", {})
    
    @patch('databases.clickhouse_adapter.clickhouse_connect')
    def test_factory_create_clickhouse(self, mock_clickhouse):
        """Test factory creating ClickHouse adapter."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_clickhouse.get_client.return_value = mock_client
        
        adapter = DatabaseFactory.create("clickhouse", {
            "host": "localhost",
            "port": 8123,
            "username": "test",
            "password": "test",
            "database": "test"
        })
        
        assert isinstance(adapter, ClickHouseAdapter)
        assert adapter.get_database_type() == "clickhouse"

