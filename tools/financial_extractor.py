"""
Financial field extraction tools.
"""
import re
import json
from typing import Dict, Any, Optional, List
from ollama import Client
from core.tool import BaseTool
from utils.logger import get_logger
from utils.exceptions import ToolExecutionError

logger = get_logger(__name__)


class MessageParserTool(BaseTool):
    """Tool for parsing messages from database."""
    
    def __init__(self):
        super().__init__(
            name="parse_messages",
            description="Parse messages from database results",
            parameter_schema={
                "message_data": {
                    "type": "str",
                    "required": True,
                    "description": "Message data from database"
                }
            }
        )
    
    def _execute_impl(self, args: Dict[str, Any], trace_id: Optional[str] = None) -> str:
        """Parse message data."""
        message_data = args["message_data"]
        # Simple parsing - can be enhanced
        return message_data


class FinancialExtractorTool(BaseTool):
    """Tool for extracting financial numeric fields from messages using LLM."""
    
    def __init__(self, llm: Client, model_name: str):
        """
        Initialize financial extractor.
        
        Args:
            llm: Ollama client
            model_name: Model name for extraction
        """
        self.llm = llm
        self.model_name = model_name
        super().__init__(
            name="extract_financial_fields",
            description="Extract financial numeric fields (amounts, currencies, dates) from messages",
            parameter_schema={
                "message": {
                    "type": "str",
                    "required": True,
                    "description": "Message text to extract from"
                }
            }
        )
    
    def _execute_impl(self, args: Dict[str, Any], trace_id: Optional[str] = None) -> str:
        """Extract financial fields from message."""
        log = logger.bind(trace_id=trace_id)
        message = args["message"]
        
        prompt = f"""# Role
You are a financial data extraction expert specializing in identifying and extracting financial information from unstructured text, with expertise in accounting, finance, banking, and trading systems.

# Your Task
Extract all financial and numeric fields from the provided message. Focus on fields that are relevant to financial analysis, accounting, trading, or business transactions.

# Extraction Targets

Extract the following types of financial data:

## Monetary Amounts
- Currency amounts (with or without currency symbols: $, €, £, ¥, etc.)
- Decimal values representing money
- Percentages related to financial metrics
- Ratios and rates (interest rates, exchange rates, etc.)

## Currency Information
- Currency codes (USD, EUR, GBP, JPY, etc.)
- Currency symbols and their corresponding amounts

## Temporal Financial Data
- Transaction dates
- Payment due dates
- Settlement dates
- Fiscal periods
- Time-sensitive financial events

## Identifiers
- Account numbers (bank accounts, credit cards, etc.)
- Transaction IDs and reference numbers
- Order IDs, invoice numbers
- Routing numbers, SWIFT codes

## Other Financial Metrics
- Stock prices, volumes, market caps
- Interest rates, yields
- Financial ratios (P/E, debt-to-equity, etc.)
- Performance metrics (ROI, profit margins, etc.)

# Extraction Guidelines

1. **Be Thorough**: Extract all financial data, not just the most obvious
2. **Be Precise**: Capture exact values, don't round or approximate
3. **Be Contextual**: Include context about where each value appears
4. **Be Categorized**: Group similar types of data together
5. **Be Validated**: Ensure extracted values are actually financial (not random numbers)

# Output Format

Return a comprehensive JSON object:
{{
    "amounts": [
        {{
            "value": 1234.56,
            "currency": "USD|EUR|etc_or_null",
            "context": "description of where this amount appears in the message",
            "type": "payment|price|fee|refund|etc"
        }}
    ],
    "dates": [
        {{
            "value": "2024-01-15",
            "type": "transaction_date|due_date|settlement_date|etc",
            "context": "description of the date's significance"
        }}
    ],
    "account_numbers": [
        {{
            "value": "account_number_or_id",
            "type": "bank_account|credit_card|account_id|etc",
            "context": "description of the account"
        }}
    ],
    "transaction_ids": [
        {{
            "value": "transaction_id",
            "type": "transaction_ref|order_id|invoice_number|etc",
            "context": "description of the transaction"
        }}
    ],
    "other_numeric_fields": [
        {{
            "name": "descriptive_name",
            "value": 123.45,
            "type": "percentage|rate|ratio|price|volume|etc",
            "unit": "unit_if_applicable",
            "context": "description of the field"
        }}
    ],
    "extraction_summary": {{
        "total_fields_extracted": number,
        "has_currency_info": boolean,
        "has_temporal_info": boolean,
        "confidence": "high|medium|low"
    }}
}}

# Input Message

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
            log.error("financial_extraction_failed", error=str(e))
            raise ToolExecutionError(f"Financial extraction failed: {e}", "extract_financial_fields") from e


class FieldValidatorTool(BaseTool):
    """Tool for validating extracted financial fields."""
    
    def __init__(self):
        super().__init__(
            name="validate_financial_fields",
            description="Validate extracted financial fields",
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
            
            # Validate amounts
            if "amounts" in fields:
                for amount in fields["amounts"]:
                    if "value" in amount and isinstance(amount["value"], (int, float)):
                        validation_results.append(f"Valid amount: {amount}")
                    else:
                        validation_results.append(f"Invalid amount: {amount}")
            
            return json.dumps({
                "valid": len(validation_results) > 0,
                "validation_results": validation_results,
                "fields": fields
            }, indent=2)
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON in extracted fields: {e}"

