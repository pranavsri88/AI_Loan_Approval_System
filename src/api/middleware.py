"""
FastAPI middleware for logging, error handling, and request/response tracking.
"""

import time
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils.logger import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured logging of HTTP requests and responses.
    
    Logs:
    - Request method, path, and status
    - Response time (latency)
    - Client IP
    - Request/response body (when appropriate)
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log details.
        
        Args:
            request: HTTP request
            call_next: Next middleware/handler
        
        Returns:
            HTTP response
        """
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", "unknown")
        
        # Log request
        logger.info(
            f"{request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else "unknown",
            }
        )
        
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(
                f"Request failed: {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                },
                exc_info=True
            )
            raise
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        # Log response
        logger.info(
            f"{request.method} {request.url.path} → {response.status_code}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "latency_ms": latency_ms,
            }
        )
        
        # Add custom headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(latency_ms)
        
        return response


__all__ = ["LoggingMiddleware"]
