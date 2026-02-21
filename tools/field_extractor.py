"""
Generic field extraction tools for extracting interesting numerical and categorical fields.
"""
import json
from typing import Dict, Any, Optional, List
from ollama import Client
from core.tool import BaseTool
from utils.logger import get_logger
from utils.exceptions import ToolExecutionError

logger = get_logger(__name__)


class GenericFieldExtractorTool(BaseTool):
    """Generic tool for extracting interesting fields from messages using LLM."""
    
    def __init__(self, llm: Client, model_name: str, field_types: Optional[List[str]] = None):
        """
        Initialize generic field extractor.
        
        Args:
            llm: Ollama client
            model_name: Model name for extraction
            field_types: Optional list of field types to focus on (e.g., ["numeric", "financial", "temporal"])
                        If None, extracts all interesting fields
        """
        self.llm = llm
        self.model_name = model_name
        self.field_types = field_types or ["numeric", "categorical", "temporal", "identifiers"]
        
        field_types_desc = ", ".join(self.field_types) if self.field_types else "all types"
        super().__init__(
            name="extract_fields",
            description=f"Extract interesting fields ({field_types_desc}) from messages/logs. Can extract numeric values, categorical data, dates, IDs, and other structured information.",
            parameter_schema={
                "message": {
                    "type": "str",
                    "required": True,
                    "description": "Message or log text to extract fields from"
                },
                "field_types": {
                    "type": "str",
                    "required": False,
                    "description": "Comma-separated list of field types to extract (numeric, categorical, temporal, identifiers, financial). If not specified, extracts all interesting fields."
                },
                "domain": {
                    "type": "str",
                    "required": False,
                    "description": "Domain context (e.g., financial, technical, general) to guide extraction"
                }
            }
        )
    
    def _execute_impl(self, args: Dict[str, Any], trace_id: Optional[str] = None) -> str:
        """Extract fields from message."""
        log = logger.bind(trace_id=trace_id)
        message = args["message"]
        requested_field_types = args.get("field_types", "").split(",") if args.get("field_types") else self.field_types
        domain = args.get("domain", "general")
        
        # Build extraction instructions based on field types
        extraction_instructions = []
        if "numeric" in requested_field_types or "all" in requested_field_types:
            extraction_instructions.append("- Numeric values (integers, floats, percentages, ratios)")
        if "financial" in requested_field_types or "all" in requested_field_types:
            extraction_instructions.append("- Financial amounts (with or without currency symbols)")
            extraction_instructions.append("- Currency codes")
            extraction_instructions.append("- Stock prices, volumes, market data")
        if "temporal" in requested_field_types or "all" in requested_field_types:
            extraction_instructions.append("- Dates and timestamps")
            extraction_instructions.append("- Time durations")
        if "categorical" in requested_field_types or "all" in requested_field_types:
            extraction_instructions.append("- Categorical values (status codes, types, categories)")
        if "identifiers" in requested_field_types or "all" in requested_field_types:
            extraction_instructions.append("- IDs (account numbers, transaction IDs, user IDs)")
            extraction_instructions.append("- Reference numbers")
        
        field_types_list = ", ".join(requested_field_types) if requested_field_types else "all types"
        
        prompt = f"""# Role
You are an expert data extraction specialist with deep knowledge of structured data extraction, field identification, and domain-specific patterns.

# Your Task
Extract all interesting, relevant, and analyzable fields from the provided message/log text. Focus on fields that would be valuable for data analysis, bucketing strategies, statistical processing, or business intelligence.

# Domain Context
Domain: {domain}
This context should guide your extraction - understand what types of fields are most relevant in this domain.

# Field Types to Extract
Target field types: {field_types_list}

# Extraction Guidelines

{chr(10).join(extraction_instructions)}

# Extraction Strategy

1. **Scan** the entire message/log systematically
2. **Identify** all potential fields matching the target types
3. **Categorize** each field into the appropriate category
4. **Extract** the value, name, and relevant metadata
5. **Validate** that extracted values are meaningful and useful
6. **Contextualize** each field with surrounding context

# Quality Criteria

Extract fields that are:
- ✅ Numerically meaningful (not just random numbers)
- ✅ Structurally significant (IDs, codes, references)
- ✅ Temporally relevant (dates, times, durations)
- ✅ Categorically distinct (statuses, types, classifications)
- ✅ Financially relevant (amounts, prices, values)
- ✅ Useful for analysis or bucketing

# Output Format

Return a JSON object with this exact structure:
{{
    "numeric_fields": [
        {{
            "name": "descriptive_field_name",
            "value": 123.45,
            "unit": "unit_if_applicable",
            "context": "surrounding context explaining where this value appears"
        }}
    ],
    "financial_fields": [
        {{
            "name": "descriptive_field_name",
            "value": 1234.56,
            "currency": "USD|EUR|etc_or_null",
            "context": "surrounding context"
        }}
    ],
    "temporal_fields": [
        {{
            "name": "descriptive_field_name",
            "value": "2024-01-15",
            "type": "date|time|duration",
            "context": "surrounding context"
        }}
    ],
    "categorical_fields": [
        {{
            "name": "descriptive_field_name",
            "value": "category_value",
            "context": "surrounding context"
        }}
    ],
    "identifiers": [
        {{
            "name": "descriptive_field_name",
            "value": "ID12345",
            "type": "id|reference|code",
            "context": "surrounding context"
        }}
    ],
    "other_fields": [
        {{
            "name": "descriptive_field_name",
            "value": "any_value",
            "type": "field_type_description",
            "context": "surrounding context"
        }}
    ]
}}

# Input Message/Log

{message}

# Your Extraction (JSON only, no other text):
"""
        
        try:
            response = self.llm.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}],
                options={"format": "json"}
            )
            return response['message']['content']
        except Exception as e:
            log.error("field_extraction_failed", error=str(e), domain=domain)
            raise ToolExecutionError(f"Field extraction failed: {e}", "extract_fields") from e


class FieldValidatorTool(BaseTool):
    """Tool for validating extracted fields."""
    
    def __init__(self):
        super().__init__(
            name="validate_fields",
            description="Validate extracted fields for correctness and completeness",
            parameter_schema={
                "extracted_fields": {
                    "type": "str",
                    "required": True,
                    "description": "JSON string of extracted fields"
                }
            }
        )
    
    def _execute_impl(self, args: Dict[str, Any], trace_id: Optional[str] = None) -> str:
        """Validate extracted fields."""
        extracted_fields = args["extracted_fields"]
        
        try:
            fields = json.loads(extracted_fields)
            validation_results = []
            field_count = 0
            
            # Validate all field types
            field_categories = ["numeric_fields", "financial_fields", "temporal_fields", 
                             "categorical_fields", "identifiers", "other_fields"]
            
            for category in field_categories:
                if category in fields and isinstance(fields[category], list):
                    for field in fields[category]:
                        field_count += 1
                        if isinstance(field, dict) and "name" in field and "value" in field:
                            validation_results.append(f"Valid {category[:-1]}: {field.get('name')} = {field.get('value')}")
                        else:
                            validation_results.append(f"Invalid {category[:-1]}: missing name or value")
            
            return json.dumps({
                "valid": field_count > 0,
                "field_count": field_count,
                "validation_results": validation_results,
                "fields": fields
            }, indent=2)
        except json.JSONDecodeError as e:
            return json.dumps({
                "valid": False,
                "error": f"Invalid JSON in extracted fields: {e}",
                "raw_data": extracted_fields[:500]
            }, indent=2)

