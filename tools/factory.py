"""
Generic factory for creating tools dynamically from configuration.
"""
from typing import Dict, Any, Optional, Callable, Type
from abc import ABC, abstractmethod
from utils.logger import get_logger
from core.tool import ITool
from utils.exceptions import ConfigurationError

logger = get_logger(__name__)


class IToolFactory(ABC):
    """Interface for tool factories."""
    
    @abstractmethod
    def can_create(self, tool_type: str) -> bool:
        """Check if this factory can create a tool of the given type."""
        pass
    
    @abstractmethod
    def create(self, tool_type: str, config: Dict[str, Any], context: Dict[str, Any]) -> ITool:
        """Create a tool instance."""
        pass


class ToolFactory:
    """
    Generic factory for creating tools from configuration.
    Uses a registry of tool creators for extensibility.
    """
    
    def __init__(self):
        """Initialize the tool factory."""
        self._creators: Dict[str, Callable[[Dict[str, Any], Dict[str, Any]], ITool]] = {}
        self._register_default_tools()
        logger.info("tool_factory_initialized", registered_tools=list(self._creators.keys()))
    
    def register(
        self,
        tool_type: str,
        creator: Callable[[Dict[str, Any], Dict[str, Any]], ITool]
    ):
        """
        Register a tool creator function.
        
        Args:
            tool_type: Type identifier for the tool
            creator: Function that takes (config, context) and returns an ITool instance
        """
        if tool_type in self._creators:
            logger.warning("tool_creator_already_registered", tool_type=tool_type)
        self._creators[tool_type] = creator
        logger.info("tool_creator_registered", tool_type=tool_type)
    
    def create(
        self,
        tool_type: str,
        tool_config: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ITool:
        """
        Create a tool instance.
        
        Args:
            tool_type: Type of tool to create
            tool_config: Tool-specific configuration
            context: Shared context (LLM client, DB adapter, etc.)
            
        Returns:
            Tool instance
            
        Raises:
            ConfigurationError: If tool type is not registered or creation fails
        """
        if tool_type not in self._creators:
            available = list(self._creators.keys())
            error_msg = f"Unknown tool type '{tool_type}'. Available types: {available}"
            logger.error("unknown_tool_type", tool_type=tool_type, available_types=available)
            raise ConfigurationError(error_msg)
        
        try:
            creator = self._creators[tool_type]
            tool = creator(tool_config, context)
            logger.debug("tool_created", tool_type=tool_type, tool_name=tool.get_name())
            return tool
        except Exception as e:
            error_msg = f"Failed to create tool '{tool_type}': {e}"
            logger.error("tool_creation_failed", tool_type=tool_type, error=str(e), exc_info=True)
            raise ConfigurationError(error_msg) from e
    
    def _register_default_tools(self):
        """Register default tool creators."""
        # Lazy imports to avoid circular dependencies
        def _register_sql_tools():
            from tools.sql_generator import SQLGeneratorTool
            from tools.sql_validator import SQLValidatorTool
            from tools.sql_executor import SQLExecutorTool
            from tools.schema_introspector import SchemaIntrospectorTool, ListTablesTool
            
            def create_sql_generator(config: Dict[str, Any], context: Dict[str, Any]) -> ITool:
                llm_client = context.get("llm_client")
                db_adapter = context.get("db_adapter")
                if not llm_client:
                    raise ConfigurationError("llm_client required for sql_generator")
                return SQLGeneratorTool(
                    sql_llm=llm_client._client,
                    model_name=config.get("model", "HridaAI/hrida-t2sql"),
                    database_type=db_adapter.get_database_type() if db_adapter else "clickhouse"
                )
            
            def create_sql_validator(config: Dict[str, Any], context: Dict[str, Any]) -> ITool:
                db_adapter = context.get("db_adapter")
                if not db_adapter:
                    raise ConfigurationError("db_adapter required for sql_validator")
                return SQLValidatorTool(
                    allowed_tables=db_adapter.get_allowed_tables(),
                    database_type=db_adapter.get_database_type()
                )
            
            def create_sql_executor(config: Dict[str, Any], context: Dict[str, Any]) -> ITool:
                db_adapter = context.get("db_adapter")
                if not db_adapter:
                    raise ConfigurationError("db_adapter required for sql_executor")
                return SQLExecutorTool(
                    db_adapter=db_adapter,
                    pii_masker=context.get("pii_masker")
                )
            
            def create_schema_introspector(config: Dict[str, Any], context: Dict[str, Any]) -> ITool:
                db_adapter = context.get("db_adapter")
                if not db_adapter:
                    raise ConfigurationError("db_adapter required for schema_introspector")
                return SchemaIntrospectorTool(db_adapter=db_adapter)
            
            def create_list_tables(config: Dict[str, Any], context: Dict[str, Any]) -> ITool:
                db_adapter = context.get("db_adapter")
                if not db_adapter:
                    raise ConfigurationError("db_adapter required for list_tables")
                return ListTablesTool(db_adapter=db_adapter)
            
            self.register("sql_generator", create_sql_generator)
            self.register("sql_validator", create_sql_validator)
            self.register("sql_executor", create_sql_executor)
            self.register("schema_introspector", create_schema_introspector)
            self.register("list_tables", create_list_tables)
        
        def _register_log_tools():
            from tools.log_analyzer import LogAnalyzerTool
            
            def create_log_analyzer(config: Dict[str, Any], context: Dict[str, Any]) -> ITool:
                llm_client = context.get("llm_client")
                if not llm_client:
                    raise ConfigurationError("llm_client required for log_analyzer")
                return LogAnalyzerTool(
                    llm=llm_client._client,
                    model_name=config.get("model", "llama3.2"),
                    log_format=config.get("log_format", "json")
                )
            
            self.register("log_analyzer", create_log_analyzer)
        
        def _register_financial_tools():
            from tools.financial_extractor import FinancialExtractorTool, MessageParserTool
            
            def create_financial_extractor(config: Dict[str, Any], context: Dict[str, Any]) -> ITool:
                llm_client = context.get("llm_client")
                if not llm_client:
                    raise ConfigurationError("llm_client required for financial_extractor")
                return FinancialExtractorTool(
                    llm=llm_client._client,
                    model_name=config.get("model", "llama3.2")
                )
            
            def create_message_parser(config: Dict[str, Any], context: Dict[str, Any]) -> ITool:
                return MessageParserTool()
            
            self.register("financial_extractor", create_financial_extractor)
            self.register("message_parser", create_message_parser)
        
        def _register_generic_field_tools():
            from tools.field_extractor import GenericFieldExtractorTool, FieldValidatorTool
            
            def create_field_extractor(config: Dict[str, Any], context: Dict[str, Any]) -> ITool:
                llm_client = context.get("llm_client")
                if not llm_client:
                    raise ConfigurationError("llm_client required for field_extractor")
                field_types = config.get("field_types")
                if isinstance(field_types, str):
                    field_types = [t.strip() for t in field_types.split(",")]
                return GenericFieldExtractorTool(
                    llm=llm_client._client,
                    model_name=config.get("model", "llama3.2"),
                    field_types=field_types
                )
            
            def create_field_validator(config: Dict[str, Any], context: Dict[str, Any]) -> ITool:
                return FieldValidatorTool()
            
            self.register("field_extractor", create_field_extractor)
            self.register("validate_fields", create_field_validator)
        
        def _register_bucketing_tools():
            from tools.bucketing_strategy import (
                FieldAnalyzerTool,
                BucketStrategyGeneratorTool,
                BucketValidatorTool
            )
            
            def create_field_analyzer(config: Dict[str, Any], context: Dict[str, Any]) -> ITool:
                return FieldAnalyzerTool()
            
            def create_bucket_strategy_generator(config: Dict[str, Any], context: Dict[str, Any]) -> ITool:
                llm_client = context.get("llm_client")
                if not llm_client:
                    raise ConfigurationError("llm_client required for bucket_strategy_generator")
                return BucketStrategyGeneratorTool(
                    llm=llm_client._client,
                    model_name=config.get("model", "llama3.2")
                )
            
            def create_bucket_validator(config: Dict[str, Any], context: Dict[str, Any]) -> ITool:
                return BucketValidatorTool()
            
            self.register("field_analyzer", create_field_analyzer)
            self.register("bucket_strategy_generator", create_bucket_strategy_generator)
            self.register("bucket_validator", create_bucket_validator)
        
        # Register all default tools
        _register_sql_tools()
        _register_log_tools()
        _register_financial_tools()
        _register_generic_field_tools()
        _register_bucketing_tools()

