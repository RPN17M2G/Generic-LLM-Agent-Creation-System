"""
Audit logging for security and compliance.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


class AuditLogger:
    """
    Audit logger for tracking agent actions and database operations.
    """
    
    def __init__(self):
        """Initialize audit logger."""
        logger.info("audit_logger_initialized")
    
    def log_agent_action(
        self,
        agent_name: str,
        action: str,
        details: Dict[str, Any],
        trace_id: Optional[str] = None
    ):
        """
        Log an agent action.
        
        Args:
            agent_name: Name of the agent
            action: Action performed
            details: Additional details
            trace_id: Optional trace ID
        """
        log = logger.bind(trace_id=trace_id) if trace_id else logger
        log.info(
            "audit_agent_action",
            agent_name=agent_name,
            action=action,
            details=details,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_database_query(
        self,
        agent_name: str,
        database_type: str,
        query: str,
        trace_id: Optional[str] = None
    ):
        """
        Log a database query.
        
        Args:
            agent_name: Name of the agent
            database_type: Database type
            query: SQL query
            trace_id: Optional trace ID
        """
        log = logger.bind(trace_id=trace_id) if trace_id else logger
        log.info(
            "audit_database_query",
            agent_name=agent_name,
            database_type=database_type,
            query=query,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_security_event(
        self,
        event_type: str,
        details: Dict[str, Any],
        trace_id: Optional[str] = None
    ):
        """
        Log a security event.
        
        Args:
            event_type: Type of security event
            details: Event details
            trace_id: Optional trace ID
        """
        log = logger.bind(trace_id=trace_id) if trace_id else logger
        log.warning(
            "audit_security_event",
            event_type=event_type,
            details=details,
            timestamp=datetime.utcnow().isoformat()
        )

