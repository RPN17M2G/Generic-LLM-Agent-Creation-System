"""
Base agent interface and ReAct implementation.
"""
import uuid
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional, TYPE_CHECKING

try:
    from ollama import Client
except ImportError:
    Client = None  # type: ignore

if TYPE_CHECKING:
    from core.tool import ITool

from utils.logger import get_logger
from core.response_parser import ResponseParser
from core.tool_executor import ToolExecutor
from core.error_handler import ErrorHandler

logger = get_logger(__name__)

ToolCall = Dict[str, Any]
Observation = str
IntermediateStep = Tuple[ToolCall, Observation]


class IAgent(ABC):
    """
    Interface for all agents in the framework.
    Agents must implement the run method to process user queries.
    """
    
    @abstractmethod
    def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute the agent on a user query.
        
        Args:
            query: The user's query or request
            context: Optional context dictionary for additional information
            
        Returns:
            The agent's response as a string
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the agent's name."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Return the agent's description."""
        pass


class ReActAgent(IAgent):
    """
    ReAct (Reasoning and Acting) agent implementation.
    Implements the ReAct loop: Reason -> Act -> Observe -> Repeat.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        orchestrator_llm: Client,
        orchestrator_model_name: str,
        tools: List['ITool'],
        system_prompt_template: str,
        max_iterations: int = 5,
        enable_self_correction: bool = True,
        response_format: str = "json"
    ):
        """
        Initialize the ReAct agent.
        
        Args:
            name: Agent name
            description: Agent description
            orchestrator_llm: Ollama client instance
            orchestrator_model_name: Model name for the orchestrator
            tools: List of tools available to the agent
            system_prompt_template: System prompt template (can include {tools}, {context}, etc.)
            max_iterations: Maximum number of reasoning iterations
            enable_self_correction: Whether to enable self-correction on errors
            response_format: Expected response format from LLM ("json" or "text")
        """
        self.name = name
        self.description = description
        self.orchestrator_llm = orchestrator_llm
        self.orchestrator_model_name = orchestrator_model_name
        self.tools = {tool.get_name(): tool for tool in tools}
        self.system_prompt_template = system_prompt_template
        self.max_iterations = max_iterations
        self.enable_self_correction = enable_self_correction
        self.response_format = response_format
        self.conversation_history: List[Dict[str, str]] = []
        
        # Initialize helper classes (Dependency Injection for testability)
        self.response_parser = ResponseParser(response_format=response_format)
        self.tool_executor = ToolExecutor(tools={tool.get_name(): tool for tool in tools})
        self.error_handler = ErrorHandler()
        
    def get_name(self) -> str:
        return self.name
    
    def get_description(self) -> str:
        return self.description
    
    def _build_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Build the system prompt from template, injecting tools and context.
        """
        # The system_prompt_template from agent_factory is already fully formatted
        # We don't need to format it again. Just return it as-is.
        # If we need to inject context or regenerate tools, we would do it here,
        # but for now the template is complete from the factory.
        return self.system_prompt_template
    
    def _format_tools_description(self) -> str:
        """Format available tools for the system prompt."""
        if not self.tools:
            return "No tools available."
        
        tool_descriptions = []
        for tool_name, tool in self.tools.items():
            desc = tool.get_description()
            params = tool.get_parameter_schema()
            
            # Format parameters more clearly
            param_list = []
            for param_name, param_info in params.items():
                required = param_info.get("required", False)
                param_type = param_info.get("type", "str")
                param_desc = param_info.get("description", "")
                req_marker = "REQUIRED" if required else "optional"
                param_list.append(f"    - {param_name} ({param_type}, {req_marker}): {param_desc}")
            
            params_str = "\n".join(param_list) if param_list else "    - No parameters"
            
            tool_descriptions.append(
                f"- **{tool_name}**: {desc}\n"
                f"  Parameters:\n{params_str}"
            )
        
        return "\n".join(tool_descriptions)
    
    def _format_intermediate_steps(self, steps: List[IntermediateStep]) -> List[Dict[str, str]]:
        """
        Convert intermediate steps to message format for LLM.
        """
        messages = []
        for tool_call, observation in steps:
            messages.append({
                "role": "assistant",
                "content": json.dumps({"tool_call": tool_call})
            })
            messages.append({
                "role": "user",
                "content": f"Observation:\n{observation}"
            })
        return messages
    
    def _run_tool(self, tool_call: ToolCall, trace_id: str) -> Observation:
        """
        Execute a tool call and return the observation.
        Delegates to ToolExecutor for clean separation of concerns.
        """
        return self.tool_executor.execute(tool_call, trace_id)
    
    def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute the ReAct loop on a user query.
        """
        trace_id = str(uuid.uuid4())
        log = logger.bind(trace_id=trace_id, agent_name=self.name)
        log.info("agent_start", user_query=query)
        
        try:
            system_prompt = self._build_system_prompt(context)
            
            # Initialize conversation history
            history = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
            
            intermediate_steps: List[IntermediateStep] = []
            last_observation = None
            iteration_count = 0  # Only count actual iterations (errors/retries)
            step_count = 0  # Count successful tool execution steps
            
            # Main execution loop - continue until finish or max iterations
            # Note: Tool calls are steps, not iterations. Iterations only count for errors/retries.
            while iteration_count < self.max_iterations:
                
                # Construct messages with history and intermediate steps
                messages = history + self._format_intermediate_steps(intermediate_steps)
                
                try:
                    # REASON: Get LLM response
                    options = {"temperature": 0.0}
                    if self.response_format == "json":
                        options["format"] = "json"
                    
                    response = self.orchestrator_llm.chat(
                        model=self.orchestrator_model_name,
                        messages=messages,
                        options=options
                    )
                    
                    response_text = response['message']['content']
                    
                    # Log raw response for debugging
                    log.debug("agent_llm_raw_response", 
                             response_length=len(response_text),
                             response_preview=response_text[:500],
                             full_response=response_text)
                    
                    # Parse response using ResponseParser
                    response_json, thought, tool_call, parse_error = self.response_parser.parse(response_text)
                    
                    if parse_error:
                        iteration_count += 1
                        log.error("agent_llm_response_parse_failed", 
                                 error=parse_error,
                                 response_preview=response_text[:500],
                                 full_response=response_text,
                                 iteration=iteration_count)
                        
                        observation = self.error_handler.handle_parsing_error(
                            response_text, parse_error, response_json
                        )
                        intermediate_steps.append(
                            ({"name": "error", "args": {"response": response_text[:500], "error": parse_error}}, observation)
                        )
                        continue
                    
                    if not tool_call:
                        iteration_count += 1
                        log.error("agent_missing_tool_call",
                                 thought=thought,
                                 iteration=iteration_count)
                        
                        observation = self.error_handler.handle_missing_field("tool_call", response_json)
                        intermediate_steps.append(
                            ({"name": "error", "args": {"error": "missing_tool_call"}}, observation)
                        )
                        continue
                    
                    # Validate tool_call structure
                    if not isinstance(tool_call, dict):
                        iteration_count += 1
                        error_msg = f"tool_call must be a dictionary, got {type(tool_call).__name__}"
                        log.error("agent_tool_call_invalid_type", error=error_msg, iteration=iteration_count)
                        observation = self.error_handler.handle_validation_error(
                            "tool_call", "dictionary", type(tool_call).__name__
                        )
                        intermediate_steps.append(
                            ({"name": "error", "args": {"error": error_msg}}, observation)
                        )
                        continue
                    
                    if "name" not in tool_call:
                        iteration_count += 1
                        log.warning("agent_tool_call_missing_name", tool_call=tool_call, iteration=iteration_count)
                        observation = self.error_handler.handle_validation_error(
                            "tool_call.name", "string", "missing"
                        )
                        intermediate_steps.append(
                            ({"name": "error", "args": {"error": "missing_name"}}, observation)
                        )
                        continue
                    
                    log.info("agent_llm_parsed", 
                             has_thought=bool(thought),
                             thought_preview=thought[:200] if thought else None,
                             has_tool_call=bool(tool_call),
                             tool_call_name=tool_call.get("name") if tool_call else None)
                    
                    log.info("agent_reasoning_step", 
                             thought=thought[:200] if thought else None,
                             tool_call=tool_call,
                             has_tool_call=bool(tool_call))
                    
                    # ACT: Execute tool
                    if tool_call["name"] == "finish":
                        final_answer = tool_call.get("args", {}).get("answer", "I have finished processing.")
                        log.info("agent_finish", 
                                final_answer=final_answer, 
                                total_steps=step_count,
                                total_iterations=iteration_count)
                        return final_answer
                    
                    # Execute tool - this is a step, not an iteration
                    step_count += 1
                    log.info("agent_step_execution", step=step_count, tool_name=tool_call["name"])
                    
                    observation = self._run_tool(tool_call, trace_id)
                    last_observation = observation
                    
                    # OBSERVE: Store step
                    intermediate_steps.append((tool_call, observation))
                    
                    # Check if tool execution failed - if so, this counts as an iteration (retry)
                    if observation.startswith("Error:") or observation.startswith("Tool Execution Failed:"):
                        iteration_count += 1
                        log.info("agent_iteration_retry", 
                                iteration=iteration_count, 
                                reason="tool_execution_failed",
                                tool_name=tool_call["name"])
                    # Otherwise, successful step - continue without incrementing iteration
                    
                except Exception as e:
                    iteration_count += 1
                    log.error("agent_loop_error", error=str(e), exc_info=True, iteration=iteration_count)
                    observation = f"An unexpected error occurred: {e}. Please try again."
                    intermediate_steps.append(
                        ({"name": "error", "args": {}}, observation)
                    )
            
            log.warning("agent_finish_max_iterations", 
                       total_iterations=iteration_count,
                       total_steps=step_count,
                       max_iterations=self.max_iterations)
            return "Sorry, I was unable to answer your question after several attempts. Please try rephrasing your question."
            
        except Exception as e:
            log.error("agent_execution_failed", error=str(e), exc_info=True)
            return f"Agent execution failed: {e}"
    
    def _parse_tool_call_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Attempt to parse a tool call from text format (fallback for non-JSON responses).
        This is a simple implementation; can be enhanced with regex or NLP.
        """
        # Try to find JSON in the text
        import re
        json_match = re.search(r'\{[^{}]*"tool_call"[^{}]*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0)).get("tool_call")
            except:
                pass
        return None

