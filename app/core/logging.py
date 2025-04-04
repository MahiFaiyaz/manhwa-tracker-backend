import logging
import sys
from typing import Dict, Any

# Configure logging format
logging_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=logging_format,
    handlers=[logging.StreamHandler(sys.stdout)],
)


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    return logging.getLogger(name)


def log_request(logger: logging.Logger, request_info: Dict[str, Any]) -> None:
    """Log incoming request information."""
    logger.info(
        f"Request: {request_info.get('method')} {request_info.get('url')} - "
        f"Client: {request_info.get('client')}"
    )


def log_response(
    logger: logging.Logger, status_code: int, processing_time: float
) -> None:
    """Log response information."""
    logger.info(f"Response: Status {status_code} - Processed in {processing_time:.4f}s")


def log_error(logger: logging.Logger, error_msg: str, exc_info: bool = False) -> None:
    """Log error information."""
    logger.error(error_msg, exc_info=exc_info)
