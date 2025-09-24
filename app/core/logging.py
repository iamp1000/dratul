import logging
import sys
from typing import Dict, Any
import structlog
from pythonjsonlogger import jsonlogger

def setup_logging():
    """Modern structured logging setup"""
    
    # JSON formatter for production
    json_formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.ConsoleRenderer()  # Use JSON in production
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Setup root logger
    logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(json_formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    return structlog.get_logger()
