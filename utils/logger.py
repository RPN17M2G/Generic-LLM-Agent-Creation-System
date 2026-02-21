import sys
import structlog

def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Configures and returns a structured logger.
    
    This setup is done once and provides JSON-formatted logs
    for production-ready observability, as described in the blueprint.
    """
    if not structlog.is_configured():
        structlog.configure(
            processors=[
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        handler = logging.StreamHandler(sys.stdout)
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)

    return structlog.get_logger(name)

import logging
