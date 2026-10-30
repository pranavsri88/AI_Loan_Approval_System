"""
FastAPI application initialization and setup.

Creates and configures the FastAPI app with:
- Request/response validation
- Error handling middleware
- CORS configuration
- Structured logging
- Health checks
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api import routes
from src.api.middleware import LoggingMiddleware
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Agentic AI Loan Approval System",
        description="Multi-agent AI system for automated loan approval decisions",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Middleware
    app.add_middleware(LoggingMiddleware)
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure per environment
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(routes.router, prefix="/api/v1", tags=["Applications"])
    
    # Startup/shutdown (using lifespan context manager for newer FastAPI versions)
    @app.get("/startup", include_in_schema=False)
    async def startup_log():
        logger.info(f"Application starting: {settings.app_env}")
        logger.info(f"Debug mode: {settings.debug}")
        return {"status": "started"}
    
    return app


# Create app instance
app = create_app()


# Health check endpoint (root)
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status with version and environment
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.app_env,
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Agentic AI Loan Approval System",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "api": "/api/v1",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info",
    )
