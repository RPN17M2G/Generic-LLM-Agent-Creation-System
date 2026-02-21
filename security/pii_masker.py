"""
PII masking using Presidio.
"""
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)

# Lazy import to avoid issues with Python 3.14 compatibility
_analyzer_engine = None
_anonymizer_engine = None
_operator_config = None


def _import_presidio():
    """Lazy import of Presidio components."""
    global _analyzer_engine, _anonymizer_engine, _operator_config
    if _analyzer_engine is None:
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine
            from presidio_anonymizer.entities import OperatorConfig
            _analyzer_engine = AnalyzerEngine
            _anonymizer_engine = AnonymizerEngine
            _operator_config = OperatorConfig
        except ImportError as e:
            logger.warning("presidio_not_available", error=str(e))
            raise ImportError(f"Presidio is not available or incompatible: {e}") from e
    return _analyzer_engine, _anonymizer_engine, _operator_config


class PIIMasker:
    """
    PII masking using Microsoft Presidio.
    Falls back to no-op if Presidio is not available.
    """
    
    def __init__(self):
        """Initialize Presidio engines."""
        self.analyzer = None
        self.anonymizer = None
        self._presidio_available = False
        
        try:
            AnalyzerEngine, AnonymizerEngine, OperatorConfig = _import_presidio()
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
            self._operator_config = OperatorConfig
            self._presidio_available = True
            logger.info("presidio_engines_initialized")
        except (ImportError, Exception) as e:
            logger.warning("presidio_init_failed", error=str(e))
            logger.info("pii_masking_disabled", reason="Presidio not available, PII masking will be disabled")
            self._presidio_available = False
    
    def mask_text_result(self, text_data: str, trace_id: str = None) -> str:
        """
        Mask PII in text data.
        
        Args:
            text_data: Text to mask
            trace_id: Optional trace ID for logging
            
        Returns:
            Masked text (or original if Presidio not available)
        """
        log = logger.bind(trace_id=trace_id) if trace_id else logger
        if not text_data:
            return ""
        
        # If Presidio is not available, return original text
        if not self._presidio_available:
            log.debug("pii_masking_skipped", reason="Presidio not available")
            return text_data
        
        try:
            analyzer_results = self.analyzer.analyze(
                text=text_data,
                language='en'
            )
            
            anonymized_result = self.anonymizer.anonymize(
                text=text_data,
                analyzer_results=analyzer_results,
                operators={"DEFAULT": self._operator_config("replace", {"new_value": "<REDACTED>"})}
            )
            
            if analyzer_results:
                log.info(
                    "pii_scan_result",
                    entities_found=[res.entity_type for res in analyzer_results]
                )
            
            return anonymized_result.text
        
        except Exception as e:
            log.error("pii_masking_failed", error=str(e), exc_info=True)
            return "[PII masking failed. Data redacted.]"

