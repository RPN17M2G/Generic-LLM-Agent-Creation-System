# Multi-Agent LLM Framework

A generic, extensible framework for dynamically creating and managing agentic LLMs with tools, specializations, and capabilities. Supports multiple databases, YAML-based configuration, and follows SOLID principles.

## Features

- **Dynamic Agent Creation**: Create agents from YAML configurations
- **Multi-Database Support**: ClickHouse, MITRE (and extensible for others)
- **Four Core Capabilities**:
  1. SQL Query Generation and Execution (ClickHouse and generic SQL)
  2. Log Analysis from Databases
  3. Financial Field Extraction from Messages
  4. Domain-Aware Bucketing Strategies
- **YAML Configuration**: Easy agent and capability definition
- **Ollama Integration**: Full support for Ollama LLM models
- **Security**: Multi-layer security with PII masking, query validation, and access control
- **SOLID Architecture**: Clean, extensible, maintainable codebase

## Architecture

### Core Components

- **Core Framework** (`core/`): Base interfaces and ReAct agent implementation
- **Database Adapters** (`databases/`): Database abstraction layer
- **Tools** (`tools/`): Reusable tools for agents
- **Capabilities** (`capabilities/`): Higher-level abstractions combining tools
- **LLM Integration** (`llm/`): Ollama client wrapper and model management
- **Configuration** (`config/`): YAML loader and schema validation
- **Security** (`security/`): PII masking, query validation, access control

### Design Principles

- **SOLID Compliance**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- **Plugin Architecture**: All extensions are plugins
- **YAML-First**: Agents defined in YAML for easy creation/modification
- **Composition over Inheritance**: Capabilities compose tools, agents compose capabilities
- **Interface-Based**: All components communicate via interfaces

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure Ollama is running:
```bash
ollama serve
```

3. Pull required models:
```bash
ollama pull phi4-reasoning:plus
ollama pull HridaAI/hrida-t2sql
ollama pull llama3.2
```

## Configuration

### Agent Configuration

Create agent YAML files in `config/agents/`. Example:

```yaml
agent:
  name: "clickhouse_analyst"
  description: "Specialized agent for ClickHouse database queries"
  
  llm:
    provider: "ollama"
    orchestrator_model: "phi4-reasoning:plus"
    temperature: 0.0
  
  database:
    type: "clickhouse"
    connection:
      host: "${CLICKHOUSE_HOST:localhost}"
      port: 8123
      database: "${CLICKHOUSE_DB:default}"
      username: "${CLICKHOUSE_USER:default}"
      password: "${CLICKHOUSE_PASSWORD:}"
    allowed_tables:
      - "users"
      - "orders"
  
  tools:
    - name: "generate_sql"
      type: "sql_generator"
      config:
        model: "HridaAI/hrida-t2sql"
    - name: "execute_sql"
      type: "sql_executor"
    - name: "validate_sql"
      type: "sql_validator"
  
  security:
    pii_masking: true
    query_validation: true
    allowed_operations:
      - "SELECT"
  
  behavior:
    max_iterations: 5
    enable_self_correction: true
    response_format: "json"
```

### Environment Variables

Use environment variables in YAML with `${VAR_NAME}` or `${VAR_NAME:default_value}` syntax.

## Usage

### Running the Framework

```bash
python main_new.py
```

### Programmatic Usage

```python
from agent_factory import AgentFactory
from core.orchestrator import AgentOrchestrator

# Create factory
factory = AgentFactory()

# Create agent from configuration
agent = factory.create_agent("clickhouse_analyst")

# Use agent
response = agent.run("How many users are in the database?")
print(response)
```

## Extending the Framework

### Adding a New Database

1. Implement `IDatabaseAdapter` interface
2. Register in `DatabaseFactory`:
```python
from databases.factory import DatabaseFactory
from databases.my_adapter import MyAdapter

DatabaseFactory.register("my_database", MyAdapter)
```

### Adding a New Tool

1. Create class inheriting `BaseTool`
2. Implement `_execute_impl()` method
3. Register in tool registry or reference in agent YAML

### Adding a New Capability

1. Create class inheriting `BaseCapability`
2. Define required tools
3. Implement `_execute_impl()` method
4. Reference in agent/capability YAML

## Project Structure

```
.
├── core/                 # Core framework components
│   ├── agent.py         # ReAct agent implementation
│   ├── tool.py          # Tool interface and base
│   ├── capability.py    # Capability interface and base
│   └── registry.py      # Tool and capability registries
├── databases/            # Database adapters
│   ├── base.py          # Database adapter interface
│   ├── clickhouse_adapter.py
│   ├── mitre_adapter.py
│   └── factory.py       # Database factory
├── tools/                # Reusable tools
│   ├── sql_generator.py
│   ├── sql_validator.py
│   ├── sql_executor.py
│   ├── log_analyzer.py
│   ├── financial_extractor.py
│   └── bucketing_strategy.py
├── capabilities/        # High-level capabilities
│   ├── sql_query.py
│   ├── log_analysis.py
│   ├── financial_extraction.py
│   └── domain_bucketing.py
├── llm/                 # LLM integration
│   ├── ollama_client.py
│   ├── model_registry.py
│   └── prompt_builder.py
├── config/              # Configuration management
│   ├── yaml_loader.py
│   ├── schema_validator.py
│   └── config_manager.py
├── security/            # Security components
│   ├── pii_masker.py
│   ├── query_validator.py
│   ├── access_control.py
│   └── audit_logger.py
├── utils/               # Utilities
│   ├── logger.py
│   ├── exceptions.py
│   ├── retry.py
│   └── cache.py
├── config/              # Configuration files
│   ├── agents/          # Agent YAML files
│   └── capabilities/   # Capability YAML files
├── agent_factory.py     # Agent factory
└── main_new.py          # Main entry point
```

## Security

The framework implements multi-layer security:

1. **LLM Prompt Engineering**: Instructions to prevent dangerous operations
2. **SQL Validation**: Query structure validation, table whitelisting, PII column detection
3. **Database Permissions**: Read-only connections, table-level access control
4. **PII Masking**: Result sanitization using Presidio
5. **Audit Logging**: All agent actions and database queries logged

## Performance

- **Connection Pooling**: Database and LLM client connection pools
- **Caching**: Schema information and query result caching
- **Retry Logic**: Exponential backoff for transient failures
- **Async Support**: Ready for async operations (structure in place)

