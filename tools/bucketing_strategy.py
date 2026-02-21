"""
Domain-aware bucketing strategy tools.
"""
import json
from typing import Dict, Any, Optional, List
from ollama import Client
import pandas as pd
from core.tool import BaseTool
from utils.logger import get_logger
from utils.exceptions import ToolExecutionError

logger = get_logger(__name__)


class FieldAnalyzerTool(BaseTool):
    """Tool for analyzing field distribution."""
    
    def __init__(self):
        super().__init__(
            name="analyze_field",
            description="Analyze field distribution and statistics",
            parameter_schema={
                "field_data": {
                    "type": "str",
                    "required": True,
                    "description": "Field data (CSV or JSON)"
                },
                "field_name": {
                    "type": "str",
                    "required": True,
                    "description": "Name of the field to analyze"
                }
            }
        )
    
    def _execute_impl(self, args: Dict[str, Any], trace_id: Optional[str] = None) -> str:
        """Analyze field distribution."""
        field_data = args["field_data"]
        field_name = args["field_name"]
        
        try:
            # Try to parse as CSV or JSON
            if field_data.startswith("["):
                data = json.loads(field_data)
                df = pd.DataFrame(data)
            else:
                # Assume CSV-like format
                lines = field_data.split("\n")
                df = pd.DataFrame([line.split(",") for line in lines if line.strip()])
            
            if field_name in df.columns:
                field_values = df[field_name]
                stats = {
                    "count": len(field_values),
                    "unique": field_values.nunique(),
                    "min": float(field_values.min()) if pd.api.types.is_numeric_dtype(field_values) else None,
                    "max": float(field_values.max()) if pd.api.types.is_numeric_dtype(field_values) else None,
                    "mean": float(field_values.mean()) if pd.api.types.is_numeric_dtype(field_values) else None,
                    "sample_values": field_values.head(10).tolist()
                }
                return json.dumps(stats, indent=2)
            else:
                return json.dumps({"error": f"Field '{field_name}' not found"})
        except Exception as e:
            return json.dumps({"error": str(e)})


class BucketStrategyGeneratorTool(BaseTool):
    """Tool for generating domain-aware bucketing strategy using LLM."""
    
    def __init__(self, llm: Client, model_name: str):
        """
        Initialize bucket strategy generator.
        
        Args:
            llm: Ollama client
            model_name: Model name
        """
        self.llm = llm
        self.model_name = model_name
        super().__init__(
            name="generate_bucketing_strategy",
            description="Generate domain-aware bucketing strategy for a field using LLM",
            parameter_schema={
                "field_analysis": {
                    "type": "str",
                    "required": True,
                    "description": "Field analysis results (JSON)"
                },
                "field_name": {
                    "type": "str",
                    "required": True,
                    "description": "Name of the field"
                },
                "domain": {
                    "type": "str",
                    "required": False,
                    "default": "general",
                    "description": "Domain context (e.g., financial, time, categorical)"
                }
            }
        )
    
    def _execute_impl(self, args: Dict[str, Any], trace_id: Optional[str] = None) -> str:
        """Generate bucketing strategy."""
        log = logger.bind(trace_id=trace_id)
        field_analysis = args["field_analysis"]
        field_name = args["field_name"]
        domain = args.get("domain", "general")
        
        prompt = f"""# Role
You are an expert data scientist and statistician specializing in creating optimal bucketing strategies for data analysis, feature engineering, and business intelligence.

# Your Task
Analyze the provided field statistics and generate a domain-aware bucketing strategy that creates meaningful, actionable segments for analysis.

# Context
Field Name: {field_name}
Domain: {domain}
Field Statistics:
{field_analysis}

# Bucketing Strategy Design Principles

## 1. Domain Awareness
- Consider domain-specific thresholds, ranges, and meaningful breakpoints
- Use industry-standard categorizations when applicable
- Align buckets with business logic and analytical needs

## 2. Statistical Soundness
- Ensure buckets have sufficient data points (avoid empty or near-empty buckets)
- Consider data distribution (normal, skewed, uniform, etc.)
- Balance granularity with practicality

## 3. Analytical Value
- Create buckets that enable meaningful comparisons
- Ensure buckets are mutually exclusive and collectively exhaustive
- Design for interpretability and actionability

## 4. Strategy Selection
Choose the most appropriate strategy type:
- **equal_width**: When you want uniform ranges (good for uniform distributions)
- **equal_frequency**: When you want similar counts per bucket (good for skewed distributions)
- **domain_specific**: When domain knowledge suggests specific thresholds (e.g., age groups, income brackets)
- **quantile_based**: When you want percentiles (25th, 50th, 75th, etc.)
- **custom**: When a hybrid or custom approach is best

# Analysis Process

1. **Examine Statistics**: Review min, max, mean, distribution, sample values
2. **Identify Patterns**: Look for natural breakpoints, clusters, or thresholds
3. **Consider Domain**: Apply domain knowledge to identify meaningful ranges
4. **Design Buckets**: Create 3-10 buckets (optimal is usually 5-7)
5. **Validate**: Ensure buckets are logical, non-overlapping, and cover the full range

# Output Format

Return a comprehensive JSON object:
{{
    "strategy_type": "equal_width|equal_frequency|domain_specific|quantile_based|custom",
    "strategy_rationale": "Detailed explanation of why this strategy type was chosen for this field and domain",
    "buckets": [
        {{
            "name": "descriptive_bucket_name",
            "min": minimum_value_inclusive,
            "max": maximum_value_exclusive,
            "description": "what this bucket represents and when to use it",
            "expected_frequency": "high|medium|low (estimated)"
        }}
    ],
    "implementation_notes": "Any special considerations for implementing this bucketing strategy",
    "alternatives_considered": "Brief note about other strategies considered and why they were rejected"
}}

# Quality Checklist

✅ Buckets cover the entire value range (min to max)
✅ Buckets are non-overlapping
✅ Bucket boundaries are clear and unambiguous
✅ Strategy is appropriate for the domain
✅ Buckets enable meaningful analysis
✅ Number of buckets is optimal (not too few, not too many)

# Your Bucketing Strategy (JSON only, no other text):
"""
        
        try:
            response = self.llm.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}],
                options={"format": "json"}
            )
            return response['message']['content']
        except Exception as e:
            log.error("bucket_strategy_generation_failed", error=str(e))
            raise ToolExecutionError(f"Bucket strategy generation failed: {e}", "generate_bucketing_strategy") from e


class BucketValidatorTool(BaseTool):
    """Tool for validating bucketing strategy."""
    
    def __init__(self):
        super().__init__(
            name="validate_bucketing_strategy",
            description="Validate a bucketing strategy",
            parameter_schema={
                "strategy": {
                    "type": "str",
                    "required": True,
                    "description": "Bucketing strategy (JSON)"
                },
                "field_analysis": {
                    "type": "str",
                    "required": True,
                    "description": "Field analysis for validation"
                }
            }
        )
    
    def _execute_impl(self, args: Dict[str, Any], trace_id: Optional[str] = None) -> str:
        """Validate bucketing strategy."""
        strategy = args["strategy"]
        field_analysis = args["field_analysis"]
        
        try:
            strategy_json = json.loads(strategy)
            analysis_json = json.loads(field_analysis)
            
            # Basic validation
            if "buckets" not in strategy_json:
                return json.dumps({"valid": False, "error": "Missing 'buckets' in strategy"})
            
            buckets = strategy_json["buckets"]
            if not isinstance(buckets, list) or len(buckets) == 0:
                return json.dumps({"valid": False, "error": "Buckets must be a non-empty list"})
            
            # Check if buckets cover the data range
            if "min" in analysis_json and "max" in analysis_json:
                data_min = analysis_json["min"]
                data_max = analysis_json["max"]
                
                bucket_mins = [b.get("min") for b in buckets if "min" in b]
                bucket_maxs = [b.get("max") for b in buckets if "max" in b]
                
                if bucket_mins and min(bucket_mins) > data_min:
                    return json.dumps({"valid": False, "error": "Buckets don't cover minimum value"})
                if bucket_maxs and max(bucket_maxs) < data_max:
                    return json.dumps({"valid": False, "error": "Buckets don't cover maximum value"})
            
            return json.dumps({
                "valid": True,
                "strategy": strategy_json,
                "bucket_count": len(buckets)
            }, indent=2)
        except json.JSONDecodeError as e:
            return json.dumps({"valid": False, "error": f"Invalid JSON: {e}"})

