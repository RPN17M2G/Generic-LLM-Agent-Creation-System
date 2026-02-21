import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

class Config:
    """
    Singleton class to hold application configuration.
    Loads settings from environment variables.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """Loads all configuration from environment variables."""
        
        # Ollama
        self.OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.ORCHESTRATOR_MODEL = os.getenv("ORCHESTRATOR_MODEL", "phi4-reasoning:plus")
        self.SQL_MODEL = os.getenv("SQL_MODEL", "HridaAI/hrida-t2sql")

        # ClickHouse
        self.CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
        self.CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", 8123))
        self.CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
        self.CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")
        self.CLICKHOUSE_DB = os.getenv("CLICKHOUSE_DB", "default")

        # Agent
        tables_str = os.getenv("AGENT_RELEVANT_TABLES", "")
        self.AGENT_RELEVANT_TABLES = [table.strip() for table in tables_str.split(',') if table.strip()]
        self.MAX_AGENT_ITERATIONS = int(os.getenv("MAX_AGENT_ITERATIONS", 5))

config = Config()
