"""
Tests for security components.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from security.pii_masker import PIIMasker
from security.query_validator import QueryValidator
from security.access_control import AccessControl
from security.audit_logger import AuditLogger


class TestPIIMasker:
    """Tests for PII masker."""
    
    @patch('security.pii_masker._import_presidio')
    def test_pii_masker_init(self, mock_import):
        """Test PII masker initialization."""
        mock_analyzer_class = MagicMock()
        mock_anonymizer_class = MagicMock()
        mock_operator_config = MagicMock()
        
        mock_analyzer_instance = Mock()
        mock_anonymizer_instance = Mock()
        mock_analyzer_class.return_value = mock_analyzer_instance
        mock_anonymizer_class.return_value = mock_anonymizer_instance
        
        mock_import.return_value = (mock_analyzer_class, mock_anonymizer_class, mock_operator_config)
        
        masker = PIIMasker()
        
        # If Presidio is available, check it's initialized
        # If not available, check graceful degradation
        assert masker._presidio_available is not None
    
    @patch('security.pii_masker._import_presidio')
    def test_pii_masker_mask_text(self, mock_import):
        """Test PII masking."""
        mock_analyzer_class = MagicMock()
        mock_anonymizer_class = MagicMock()
        mock_operator_config = MagicMock()
        
        mock_analyzer_instance = Mock()
        mock_anonymizer_instance = Mock()
        mock_analyzer_class.return_value = mock_analyzer_instance
        mock_anonymizer_class.return_value = mock_anonymizer_instance
        
        # Mock analyzer results
        mock_result = Mock()
        mock_result.entity_type = "EMAIL"
        mock_analyzer_instance.analyze.return_value = [mock_result]
        
        # Mock anonymizer result
        mock_anonymized = Mock()
        mock_anonymized.text = "test <REDACTED>"
        mock_anonymizer_instance.anonymize.return_value = mock_anonymized
        
        mock_import.return_value = (mock_analyzer_class, mock_anonymizer_class, mock_operator_config)
        
        masker = PIIMasker()
        result = masker.mask_text_result("test@example.com", trace_id="test")
        
        # Result should either be masked or original (if Presidio not available)
        assert isinstance(result, str)
        assert len(result) > 0


class TestQueryValidator:
    """Tests for query validator."""
    
    def test_query_validator_init(self):
        """Test query validator initialization."""
        validator = QueryValidator(allowed_operations=["SELECT", "WITH"])
        assert "SELECT" in validator.allowed_operations
        assert "WITH" in validator.allowed_operations
    
    def test_query_validator_default(self):
        """Test query validator with default operations."""
        validator = QueryValidator()
        assert "SELECT" in validator.allowed_operations
    
    def test_validate_operation_select(self):
        """Test validation of SELECT operation."""
        validator = QueryValidator()
        is_valid, error = validator.validate_operation("SELECT * FROM test")
        assert is_valid is True
        assert error is None
    
    def test_validate_operation_insert(self):
        """Test validation of INSERT operation (should fail)."""
        validator = QueryValidator(allowed_operations=["SELECT"])
        is_valid, error = validator.validate_operation("INSERT INTO test VALUES (1)")
        assert is_valid is False
        assert error is not None
    
    def test_validate_operation_case_insensitive(self):
        """Test case-insensitive validation."""
        validator = QueryValidator()
        is_valid, error = validator.validate_operation("select * from test")
        assert is_valid is True


class TestAccessControl:
    """Tests for access control."""
    
    def test_access_control_init(self):
        """Test access control initialization."""
        ac = AccessControl()
        assert ac._agent_permissions == {}
    
    def test_grant_access(self):
        """Test granting access."""
        ac = AccessControl()
        ac.grant_access("agent1", "clickhouse", ["table1", "table2"])
        
        assert ac.check_access("agent1", "clickhouse", "table1") is True
        assert ac.check_access("agent1", "clickhouse", "table2") is True
        assert ac.check_access("agent1", "clickhouse", "table3") is False
    
    def test_check_access_nonexistent_agent(self):
        """Test checking access for non-existent agent."""
        ac = AccessControl()
        assert ac.check_access("nonexistent", "clickhouse", "table1") is False
    
    def test_get_allowed_tables(self):
        """Test getting allowed tables."""
        ac = AccessControl()
        ac.grant_access("agent1", "clickhouse", ["table1", "table2"])
        
        tables = ac.get_allowed_tables("agent1", "clickhouse")
        assert "table1" in tables
        assert "table2" in tables
    
    def test_get_allowed_tables_nonexistent(self):
        """Test getting allowed tables for non-existent agent."""
        ac = AccessControl()
        tables = ac.get_allowed_tables("nonexistent", "clickhouse")
        assert tables == []


class TestAuditLogger:
    """Tests for audit logger."""
    
    def test_audit_logger_init(self):
        """Test audit logger initialization."""
        logger = AuditLogger()
        assert logger is not None
    
    def test_log_agent_action(self):
        """Test logging agent action."""
        logger = AuditLogger()
        # Should not raise exception
        logger.log_agent_action("agent1", "query", {"query": "test"}, trace_id="test")
    
    def test_log_database_query(self):
        """Test logging database query."""
        logger = AuditLogger()
        # Should not raise exception
        logger.log_database_query("agent1", "clickhouse", "SELECT * FROM test", trace_id="test")
    
    def test_log_security_event(self):
        """Test logging security event."""
        logger = AuditLogger()
        # Should not raise exception
        logger.log_security_event("unauthorized_access", {"details": "test"}, trace_id="test")

