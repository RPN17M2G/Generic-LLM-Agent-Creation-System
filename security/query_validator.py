"""
Enhanced query validation with whitelisting.
"""
from typing import List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class QueryValidator:
    """
    Enhanced query validator with operation whitelisting.
    """
    
    def __init__(
        self,
        allowed_operations: Optional[List[str]] = None
    ):
        """
        Initialize query validator.
        
        Args:
            allowed_operations: List of allowed SQL operations (default: ["SELECT"])
        """
        self.allowed_operations = set((allowed_operations or ["SELECT"]))
        logger.info("query_validator_initialized", allowed_operations=list(self.allowed_operations))
    
    def validate_operation(self, query: str) -> tuple[bool, Optional[str]]:
        """
        Validate that query only uses allowed operations.
        
        Returns:
            (is_valid, error_message)
        """
        query_upper = query.upper().strip()
        
        for operation in self.allowed_operations:
            if query_upper.startswith(operation.upper()):
                return True, None
        
        error_msg = f"Query uses disallowed operation. Allowed operations: {list(self.allowed_operations)}"
        logger.warning("query_operation_not_allowed", query_preview=query[:100])
        return False, error_msg

