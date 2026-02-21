"""
Agent orchestrator for managing agent lifecycle and execution.
"""
from typing import Dict, Any, Optional, List
from utils.logger import get_logger
from .agent import IAgent

logger = get_logger(__name__)


class AgentOrchestrator:
    """
    Orchestrator for managing multiple agents.
    """
    
    def __init__(self):
        """Initialize orchestrator."""
        self._agents: Dict[str, IAgent] = {}
        logger.info("agent_orchestrator_initialized")
    
    def register_agent(self, agent: IAgent):
        """
        Register an agent.
        
        Args:
            agent: Agent instance
        """
        agent_name = agent.get_name()
        self._agents[agent_name] = agent
        logger.info("agent_registered", agent_name=agent_name)
    
    def get_agent(self, agent_name: str) -> Optional[IAgent]:
        """
        Get an agent by name.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent instance or None
        """
        return self._agents.get(agent_name)
    
    def list_agents(self) -> List[str]:
        """
        List all registered agent names.
        
        Returns:
            List of agent names
        """
        return list(self._agents.keys())
    
    def execute(
        self,
        agent_name: str,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Execute a query on a specific agent.
        
        Args:
            agent_name: Name of the agent
            query: User query
            context: Optional context
            
        Returns:
            Agent response
            
        Raises:
            ValueError: If agent not found
        """
        agent = self.get_agent(agent_name)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found")
        
        logger.info("orchestrator_execute", agent_name=agent_name, query=query)
        return agent.run(query, context)

