"""
Log analysis tools.
"""
import json
from typing import Dict, Any, Optional, List
from ollama import Client
from core.tool import BaseTool
from utils.logger import get_logger
from utils.exceptions import ToolExecutionError

logger = get_logger(__name__)


class LogParserTool(BaseTool):
    """Tool for parsing log entries from various formats."""
    
    def __init__(self, log_format: str = "json"):
        """
        Initialize log parser.
        
        Args:
            log_format: Log format (json, csv, text)
        """
        self.log_format = log_format
        super().__init__(
            name="parse_logs",
            description="Parse log entries from database results",
            parameter_schema={
                "log_data": {
                    "type": "str",
                    "required": True,
                    "description": "Raw log data to parse"
                }
            }
        )
    
    def _execute_impl(self, args: Dict[str, Any], trace_id: Optional[str] = None) -> str:
        """Parse log data."""
        log_data = args["log_data"]
        
        try:
            if self.log_format == "json":
                # Try to parse as JSON
                parsed = json.loads(log_data)
                return json.dumps(parsed, indent=2)
            elif self.log_format == "csv":
                # Parse CSV (simplified)
                lines = log_data.split("\n")
                return f"Parsed {len(lines)} log entries"
            else:
                # Text format - return as is
                return log_data
        except Exception as e:
            return f"Error parsing logs: {e}"


class PatternDetectorTool(BaseTool):
    """Tool for detecting patterns in logs using LLM."""
    
    def __init__(self, llm: Client, model_name: str):
        """
        Initialize pattern detector.
        
        Args:
            llm: Ollama client
            model_name: Model name for pattern detection
        """
        self.llm = llm
        self.model_name = model_name
        super().__init__(
            name="detect_patterns",
            description="Detect patterns and anomalies in log data using LLM",
            parameter_schema={
                "log_data": {
                    "type": "str",
                    "required": True,
                    "description": "Parsed log data"
                },
                "pattern_type": {
                    "type": "str",
                    "required": False,
                    "default": "errors",
                    "description": "Type of patterns to detect (errors, anomalies, trends)"
                }
            }
        )
    
    def _execute_impl(self, args: Dict[str, Any], trace_id: Optional[str] = None) -> str:
        """Detect patterns in logs."""
        log = logger.bind(trace_id=trace_id)
        log_data = args["log_data"]
        pattern_type = args.get("pattern_type", "errors")
        
        prompt = f"""# Role
You are an expert log analysis specialist with deep expertise in log parsing, pattern recognition, anomaly detection, and system diagnostics.

# Your Task
Analyze the provided log data and perform a comprehensive {pattern_type} analysis. Your goal is to identify meaningful patterns, anomalies, trends, or issues that would be valuable for system monitoring, debugging, or optimization.

# Analysis Type
Focus on: {pattern_type}

# Analysis Framework

## 1. Data Understanding
- Examine log structure, format, and content
- Identify log levels, timestamps, sources, and message types
- Understand the context and domain of the logs

## 2. Pattern Identification
- Look for recurring patterns, sequences, or behaviors
- Identify anomalies, outliers, or unexpected events
- Detect trends, spikes, or gradual changes
- Find correlations between different log entries

## 3. Categorization
- Group similar log entries
- Classify by severity, type, source, or impact
- Identify root causes or contributing factors

## 4. Insight Generation
- Extract actionable insights
- Identify potential issues or risks
- Suggest improvements or optimizations

# Output Requirements

Provide a comprehensive JSON analysis with this structure:
{{
    "summary": {{
        "total_log_entries": number,
        "analysis_type": "{pattern_type}",
        "key_findings": "High-level summary of the most important findings",
        "severity_assessment": "critical|high|medium|low|info"
    }},
    "patterns": [
        {{
            "pattern_name": "descriptive_name",
            "description": "what this pattern represents",
            "frequency": "how often it occurs",
            "examples": ["example1", "example2"],
            "significance": "why this pattern matters"
        }}
    ],
    "anomalies": [
        {{
            "anomaly_type": "error|spike|unusual_behavior|etc",
            "description": "what makes this anomalous",
            "occurrence": "when/where it happened",
            "potential_impact": "what this could mean"
        }}
    ],
    "recommendations": [
        {{
            "priority": "high|medium|low",
            "recommendation": "specific actionable recommendation",
            "rationale": "why this recommendation is important"
        }}
    ],
    "statistics": {{
        "error_count": number,
        "warning_count": number,
        "info_count": number,
        "unique_sources": number,
        "time_span": "time range covered"
    }}
}}

# Log Data

{log_data}

# Your Analysis (JSON only, no other text):
"""
        
        try:
            response = self.llm.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}]
            )
            return response['message']['content']
        except Exception as e:
            log.error("pattern_detection_failed", error=str(e))
            raise ToolExecutionError(f"Pattern detection failed: {e}", "detect_patterns") from e


class LogAnalyzerTool(BaseTool):
    """Combined log analysis tool."""
    
    def __init__(self, llm: Client, model_name: str, log_format: str = "json"):
        """
        Initialize log analyzer.
        
        Args:
            llm: Ollama client
            model_name: Model name
            log_format: Log format
        """
        self.llm = llm
        self.model_name = model_name
        self.log_format = log_format
        super().__init__(
            name="analyze_logs",
            description="Analyze logs from database and identify patterns, errors, and anomalies",
            parameter_schema={
                "log_data": {
                    "type": "str",
                    "required": True,
                    "description": "Log data to analyze"
                },
                "analysis_type": {
                    "type": "str",
                    "required": False,
                    "default": "comprehensive",
                    "description": "Type of analysis (comprehensive, errors, anomalies, trends)"
                }
            }
        )
    
    def _execute_impl(self, args: Dict[str, Any], trace_id: Optional[str] = None) -> str:
        """Analyze logs."""
        log = logger.bind(trace_id=trace_id)
        log_data = args["log_data"]
        analysis_type = args.get("analysis_type", "comprehensive")
        
        # Parse logs first
        parser = LogParserTool(self.log_format)
        parsed_logs = parser.execute({"log_data": log_data}, trace_id)
        
        # Detect patterns
        detector = PatternDetectorTool(self.llm, self.model_name)
        patterns = detector.execute({
            "log_data": parsed_logs,
            "pattern_type": analysis_type
        }, trace_id)
        
        return f"Log Analysis Results:\n{patterns}"

