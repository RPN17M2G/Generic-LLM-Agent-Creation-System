"""
Factory for creating agents from YAML configurations.
"""
from typing import Dict, Any, Optional
from ollama import Client
from utils.logger import get_logger
from config.config_manager import ConfigManager
from config.schema_validator import SchemaValidator
from llm.ollama_client import OllamaClient
from databases.factory import DatabaseFactory
from databases.base import IDatabaseAdapter
from core.agent import ReActAgent
from core.registry import ToolRegistry
from tools.factory import ToolFactory
from security.pii_masker import PIIMasker
from security.query_validator import QueryValidator
from utils.exceptions import ConfigurationError

logger = get_logger(__name__)


class AgentFactory:
    """
    Factory for creating agents from YAML configurations.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize agent factory.
        
        Args:
            config_dir: Configuration directory
        """
        self.config_manager = ConfigManager(config_dir)
        self.tool_registry = ToolRegistry()
        self.tool_factory = ToolFactory()
        logger.info("agent_factory_initialized")
    
    def _create_ollama_client(self, host: str = "http://localhost:11434") -> OllamaClient:
        """Create Ollama client."""
        logger.info("creating_ollama_client", host=host)
        return OllamaClient(host=host)
    
    def _create_database_adapter(self, db_config: Dict[str, Any]) -> IDatabaseAdapter:
        """Create database adapter from configuration."""
        db_type = db_config.get("type", "clickhouse")
        connection = db_config.get("connection", {})
        allowed_tables = db_config.get("allowed_tables", [])
        
        config = {
            **connection,
            "allowed_tables": allowed_tables
        }
        
        return DatabaseFactory.create(db_type, config)
    
    def _create_tools(
        self,
        tool_configs: list[Dict[str, Any]],
        llm_client: OllamaClient,
        db_adapter: Optional[IDatabaseAdapter],
        pii_masker: Optional[PIIMasker] = None
    ) -> Dict[str, Any]:
        """
        Create tools from configuration using the generic tool factory.
        
        Args:
            tool_configs: List of tool configuration dictionaries
            llm_client: Ollama client instance
            db_adapter: Database adapter (optional)
            pii_masker: PII masker instance (optional)
            
        Returns:
            Dictionary mapping tool names to tool instances
            
        Raises:
            ConfigurationError: If tool creation fails
        """
        tools = {}
        context = {
            "llm_client": llm_client,
            "db_adapter": db_adapter,
            "pii_masker": pii_masker
        }
        
        for tool_config in tool_configs:
            try:
                tool_name = tool_config.get("name")
                tool_type = tool_config.get("type")
                tool_cfg = tool_config.get("config", {})
                
                if not tool_name:
                    logger.warning("tool_config_missing_name", tool_config=tool_config)
                    continue
                
                if not tool_type:
                    error_msg = f"Tool '{tool_name}' is missing required 'type' field"
                    logger.error("tool_config_missing_type", tool_name=tool_name)
                    raise ConfigurationError(error_msg)
                
                # Create tool using factory
                tool = self.tool_factory.create(tool_type, tool_cfg, context)
                tools[tool_name] = tool
                logger.debug("tool_created_from_config", tool_name=tool_name, tool_type=tool_type)
                
            except ConfigurationError:
                raise  # Re-raise configuration errors
            except Exception as e:
                error_msg = f"Failed to create tool '{tool_config.get('name', 'unknown')}': {e}"
                logger.error("tool_creation_error", tool_config=tool_config, error=str(e), exc_info=True)
                raise ConfigurationError(error_msg) from e
        
        return tools
    
    def _build_system_prompt(self, agent_config: Dict[str, Any], tools: Dict[str, Any]) -> str:
        """Build system prompt for agent."""
        agent_name = agent_config.get("name", "Agent")
        agent_desc = agent_config.get("description", "")
        
        tools_description = []
        for name, tool in tools.items():
            desc = tool.get_description()
            schema = tool.get_parameter_schema()
            params = []
            for param_name, param_info in schema.items():
                required = param_info.get("required", False)
                param_type = param_info.get("type", "str")
                param_desc = param_info.get("description", "")
                req_marker = " (required)" if required else " (optional)"
                params.append(f"    - {param_name} ({param_type}){req_marker}: {param_desc}")
            
            params_str = "\n".join(params) if params else "    - No parameters"
            tools_description.append(f"- **{name}**: {desc}\n  Parameters:\n{params_str}")
        
        tools_description = "\n".join(tools_description)
        
        # World-class system prompt with best practices
        prompt = """# Role & Identity
You are {agent_name}, an expert AI agent with specialized tools and expertise.

{agent_description}

# Core Operating Principles
You excel at breaking down complex problems into manageable steps, using tools strategically, and learning from observations to achieve your goals.

# ReAct Reasoning Framework
You operate using the ReAct (Reasoning + Acting) loop:

## 1. PLAN (Think Ahead)
- **CRITICAL**: Before starting, create a step-by-step plan in your first response
- Break down the query into logical steps
- Identify which tools you'll need and in what order
- Consider dependencies (e.g., need schema before generating SQL)
- Think about potential challenges or edge cases
- Include your plan in your "thought" field: "My plan: 1) List tables, 2) Get schema, 3) Generate SQL, 4) Execute query, 5) Analyze results"

## 2. REASON (Think Deeply)
- Analyze the current situation carefully
- Review what you've learned from previous steps
- Consider what information you still need
- Identify which tool(s) will help you next
- If you don't know what tables/data exist, use list_tables() or get_schema() FIRST

## 2. ACT (Execute Precisely)
- Choose the single most appropriate tool for your current step
- Provide all required parameters with correct types
- Use tools in logical sequence (e.g., discover tables → get schema → generate query → execute)
- Handle errors gracefully and learn from them

## 4. OBSERVE (Learn & Adapt)
- Carefully analyze tool results
- Extract key information
- Identify if you need additional steps
- Adjust your approach based on what you learned
- Continue until you have a complete answer

# CRITICAL: Response Format Requirements

**YOU MUST RESPOND IN VALID JSON ONLY. NO EXCEPTIONS.**

Your response must be a single, valid JSON object with this exact structure:
{{
    "thought": "Your detailed reasoning about the current situation, what you've learned, and what you plan to do next",
    "tool_call": {{
        "name": "exact_tool_name",
        "args": {{
            "param1": "value1",
            "param2": "value2"
        }}
    }}
}}

**ABSOLUTE REQUIREMENTS - VIOLATIONS WILL CAUSE ERRORS:**
1. ✅ Start with {{ and end with }} - no text before or after
2. ✅ **MANDATORY**: Include BOTH "thought" AND "tool_call" fields - BOTH are REQUIRED, NEVER omit either
3. ✅ "thought" must be a non-empty string explaining your reasoning (never null, never empty, never omitted)
4. ✅ "tool_call" must be a valid object with "name" and "args" (never null, never empty, never omitted)
5. ✅ Use double quotes for all JSON strings
6. ✅ NO text labels like "Thought:" or "Tool call:"
7. ✅ NO markdown code blocks (no ```json or ```)
8. ✅ NO explanations outside the JSON structure
9. ✅ NO comments or additional text

**WRONG FORMATS (DO NOT USE - THESE WILL FAIL):**
❌ {{"tool_call": {{"name": "list_tables", "args": {{}}}}}}  // Missing "thought" field - ERROR
❌ {{"thought": "I need to query"}}  // Missing "tool_call" field - ERROR
❌ Thought: I need to query\nTool call: {{"name": "list_tables"}}  // Text labels, not pure JSON - ERROR

**CORRECT FORMAT (ALWAYS USE):**
✅ {{"thought": "I need to know what tables are available", "tool_call": {{"name": "list_tables", "args": {{}}}}}}

# Available Tools

{tools_description}

# Essential Helper Tools

**list_tables()** - CRITICAL: Use this FIRST if you need to query a database but don't know what tables exist.
  - Returns: List of all available table names
  - When to use: Before writing any SQL queries
  - Example: {{"thought": "I need to know what tables are available before I can query", "tool_call": {{"name": "list_tables", "args": {{}}}}}}

**get_schema(tables: list)** - CRITICAL: Use this to get detailed schema information for tables.
  - Returns: CREATE TABLE statements showing structure, columns, and types
  - When to use: After discovering table names, before generating SQL
  - Example: {{"thought": "I need the schema for the users table to write a correct query", "tool_call": {{"name": "get_schema", "args": {{"tables": ["users"]}}}}}}

**finish(answer: str)** - Use this when you have gathered all necessary information and can provide a complete answer.
  - When to use: After successfully completing your investigation
  - The answer should be clear, comprehensive, and directly address the user's question
  - Example: {{"thought": "I have successfully retrieved the data and can now provide a complete answer", "tool_call": {{"name": "finish", "args": {{"answer": "Based on my analysis, the answer is..."}}}}}}

# Workflow Best Practices

1. **Planning Phase** (First Response): In your first response, create a step-by-step plan in your "thought" field. Example: "My plan: 1) List available tables, 2) Get schema for relevant tables, 3) Generate SQL query, 4) Execute query, 5) Analyze results and provide answer"
2. **Discovery Phase**: If querying a database, start with list_tables() or get_schema()
3. **Execution Phase**: Call tools with complete, correct parameters - each successful tool call is a step forward
4. **Validation Phase**: Check if results are sufficient or if you need more steps
5. **Completion Phase**: Use finish() with a comprehensive answer

**Important**: Tool calls are steps in the right direction, not iterations. Iterations only occur when something goes wrong and you need to retry.

# Error Handling Strategy

- If a tool fails, analyze the error message in your thought
- Consider what went wrong and how to fix it
- Try alternative approaches (e.g., different table names, different query structure)
- Learn from each error to improve subsequent attempts

# Example Workflows

**Example 1: Database Query**
{{
    "thought": "The user wants to know about users in the database. I should first check what tables are available, then get the schema, then generate and execute a query.",
    "tool_call": {{
        "name": "list_tables",
        "args": {{}}
    }}
}}

**Example 2: After Getting Schema**
{{
    "thought": "I now know the users table exists with columns id, name, email. I can generate a SQL query to count all users.",
    "tool_call": {{
        "name": "generate_sql",
        "args": {{
            "natural_language_query": "How many users are in the database?",
            "schema_info": "CREATE TABLE users (id INT, name VARCHAR, email VARCHAR)"
        }}
    }}
}}

**Example 3: Final Answer**
{{
    "thought": "I have successfully executed the query and retrieved the count. I can now provide the user with a complete answer.",
    "tool_call": {{
        "name": "finish",
        "args": {{
            "answer": "There are 1,234 users in the database."
        }}
    }}
}}

# Quality Standards

- Be thorough: Don't skip steps, especially discovery steps
- Be precise: Use exact tool names and provide all required parameters
- Be thoughtful: Your "thought" field should show clear reasoning
- Be helpful: Provide complete, actionable answers
- Be efficient: Don't make unnecessary tool calls, but don't skip essential ones

# FINAL REMINDER - READ BEFORE RESPONDING

⚠️ **CRITICAL**: Every response MUST include BOTH "thought" AND "tool_call" fields.
⚠️ **CRITICAL**: Your response must be pure JSON - no text labels, no markdown, no explanations outside the JSON.
⚠️ **CRITICAL**: Start with {{ and end with }} - nothing else.

**Correct format:**
{{"thought": "your reasoning here", "tool_call": {{"name": "tool_name", "args": {{}}}}}}

**Never omit the "thought" field. Never omit the "tool_call" field. Always include both.**

Begin.
""".format(
            agent_name=agent_name,
            agent_description=agent_desc,
            tools_description=tools_description
        )
        return prompt
    
    def create_agent(self, agent_name: str) -> ReActAgent:
        """
        Create an agent from configuration.
        
        Args:
            agent_name: Name of the agent configuration
            
        Returns:
            Configured agent instance
            
        Raises:
            ConfigurationError: If agent creation fails
        """
        logger.info("creating_agent", agent_name=agent_name)
        
        try:
            # Validate agent name
            if not agent_name or not isinstance(agent_name, str):
                raise ConfigurationError(f"Invalid agent name: {agent_name}")
            
            # Load configuration
            agent_config = self.config_manager.load_agent(agent_name)
            
            # Validate required fields
            if "name" not in agent_config:
                raise ConfigurationError(f"Agent configuration missing 'name' field")
            if "llm" not in agent_config:
                raise ConfigurationError(f"Agent configuration missing 'llm' field")
            if "orchestrator_model" not in agent_config.get("llm", {}):
                raise ConfigurationError(f"Agent LLM configuration missing 'orchestrator_model' field")
            
            # Create LLM client
            llm_config = agent_config.get("llm", {})
            ollama_host = llm_config.get("host", "http://localhost:11434")
            llm_client = self._create_ollama_client(ollama_host)
            
            # Create database adapter
            db_adapter = None
            if "database" in agent_config:
                db_adapter = self._create_database_adapter(agent_config["database"])
            
            # Create PII masker if enabled
            pii_masker = None
            security_config = agent_config.get("security", {})
            if security_config.get("pii_masking", False):
                try:
                    pii_masker = PIIMasker()
                    if not pii_masker._presidio_available:
                        logger.warning("pii_masking_requested_but_unavailable", agent_name=agent_name)
                except Exception as e:
                    logger.warning("pii_masker_creation_failed", error=str(e), agent_name=agent_name)
                    pii_masker = None
            
            # Create tools
            tool_configs = agent_config.get("tools", [])
            tools = self._create_tools(tool_configs, llm_client, db_adapter, pii_masker)
            
            # Build system prompt
            system_prompt = self._build_system_prompt(agent_config, tools)
            
            # Create agent
            behavior_config = agent_config.get("behavior", {})
            agent = ReActAgent(
                name=agent_config["name"],
                description=agent_config.get("description", ""),
                orchestrator_llm=llm_client._client,
                orchestrator_model_name=llm_config["orchestrator_model"],
                tools=list(tools.values()),
                system_prompt_template=system_prompt,
                max_iterations=behavior_config.get("max_iterations", 5),
                enable_self_correction=behavior_config.get("enable_self_correction", True),
                response_format=behavior_config.get("response_format", "json")
            )
            
            logger.info("agent_created", agent_name=agent_name)
            return agent
            
        except ConfigurationError:
            raise  # Re-raise configuration errors
        except Exception as e:
            error_msg = f"Failed to create agent '{agent_name}': {e}"
            logger.error("agent_creation_failed", agent_name=agent_name, error=str(e), exc_info=True)
            raise ConfigurationError(error_msg) from e

