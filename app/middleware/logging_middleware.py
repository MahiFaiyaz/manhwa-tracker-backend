import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import get_logger, log_request, log_response

logger = get_logger("api")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Log request
        request_info = {
            "method": request.method,
            "url": request.url.path,
            "client": request.client.host if request.client else "unknown",
        }
        log_request(logger, request_info)

        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log response
            log_response(logger, response.status_code, process_time)

            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Request failed: {str(e)}")
            raise e
