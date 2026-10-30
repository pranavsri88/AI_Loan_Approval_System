"""
Base MCP Server Class.

Abstract base class for all MCP servers. Defines common patterns for:
- Tool registration and invocation
- Error handling with logging
- Database session management
- Response formatting

All MCP servers (ApplicantDB, RiskRulesDB, DecisionSynthesis, NotificationSystem)
inherit from this base to ensure consistent behavior and error handling.

DESIGN:
  - BaseMCPServer: Abstract base with common infrastructure
  - Subclasses: Implement specific tools for their domain
  - Error handling: Logs failures but doesn't crash the server
  - Response format: Consistent Dict[str, Any] for all tools
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Callable, Optional
import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastmcp import FastMCP

from src.utils.logger import get_logger
from src.utils.config import settings

logger = get_logger(__name__)


class BaseMCPServer(ABC):
    """
    Abstract base class for all MCP servers.

    RESPONSIBILITY:
      - Manage FastMCP instance and tool registration
      - Provide common error handling and logging
      - Manage database sessions and connection pooling
      - Format responses consistently

    SUBCLASS CONTRACT:
      Subclasses must:
      1. Set self.mcp_name in __init__
      2. Call self.register_tools() with tool functions
      3. Implement each tool as a @staticmethod that returns Dict[str, Any]

    USAGE:
      class ApplicantDBServer(BaseMCPServer):
          def __init__(self):
              super().__init__()
              self.mcp_name = "applicant_db"
              self.register_tools([
                  ("get_applicant_history", self.get_applicant_history),
                  ("get_employment_data", self.get_employment_data),
              ])

          @staticmethod
          def get_applicant_history(applicant_id: str) -> Dict[str, Any]:
              # Implement tool logic
              ...
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize base MCP server.

        Args:
            database_url: SQLite connection string. Defaults to settings.database_url
        """
        self.mcp_name = "base_mcp_server"
        self.mcp = FastMCP(self.mcp_name)
        self.database_url = database_url or settings.database_url

        # Connection pool for database sessions
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

        logger.info(
            f"BaseMCPServer initialized",
            extra={"server_name": self.mcp_name, "database_url": self.database_url}
        )

    def get_session(self) -> Session:
        """
        Get a new database session from the pool.

        Returns:
            SQLAlchemy Session for database queries

        Usage:
            session = self.get_session()
            try:
                result = session.query(Applicant).first()
            finally:
                session.close()
        """
        return self.SessionLocal()

    def register_tools(self, tools: list[tuple[str, Callable]]) -> None:
        """
        Register tools with the MCP server.

        Args:
            tools: List of (tool_name, tool_function) tuples

        DESIGN:
          - Each tool is wrapped with error handling
          - Failures are logged but don't crash the server
          - Response format is consistent across all tools

        Usage:
            self.register_tools([
                ("get_applicant_history", self.get_applicant_history),
                ("get_employment_data", self.get_employment_data),
            ])
        """
        for tool_name, tool_func in tools:
            # Wrap tool function with error handling
            wrapped_func = self._wrap_tool(tool_name, tool_func)

            # Register with FastMCP
            self.mcp.tool(wrapped_func)

            logger.debug(
                f"Tool registered: {tool_name}",
                extra={"server_name": self.mcp_name, "tool_name": tool_name}
            )

    def _wrap_tool(self, tool_name: str, tool_func: Callable) -> Callable:
        """
        Wrap a tool function with error handling and logging.

        DESIGN:
          - Catch all exceptions to prevent server crash
          - Log errors with trace info
          - Return error response in consistent format
          - Preserve function metadata for FastMCP introspection

        Args:
            tool_name: Name of the tool for logging
            tool_func: The actual tool implementation

        Returns:
            Wrapped function with error handling
        """
        def wrapper(*args, **kwargs) -> Dict[str, Any]:
            try:
                logger.debug(
                    f"Tool called: {tool_name}",
                    extra={
                        "server_name": self.mcp_name,
                        "tool_name": tool_name,
                        "args": str(args)[:100],
                        "kwargs": str(kwargs)[:100],
                    }
                )

                # Execute tool
                result = tool_func(*args, **kwargs)

                logger.debug(
                    f"Tool succeeded: {tool_name}",
                    extra={
                        "server_name": self.mcp_name,
                        "tool_name": tool_name,
                        "result_keys": list(result.keys()) if isinstance(result, dict) else None,
                    }
                )

                return result

            except Exception as e:
                logger.error(
                    f"Tool failed: {tool_name}",
                    extra={
                        "server_name": self.mcp_name,
                        "tool_name": tool_name,
                        "error": str(e),
                    },
                    exc_info=True
                )

                return {
                    "error": f"Tool {tool_name} failed: {str(e)}",
                    "error_type": type(e).__name__,
                    "timestamp": datetime.utcnow().isoformat(),
                }

        # Preserve function metadata for FastMCP introspection
        wrapper.__name__ = tool_func.__name__
        wrapper.__doc__ = tool_func.__doc__

        return wrapper

    def format_response(
        self,
        data: Any,
        status: str = "success",
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format a consistent response structure for all tool returns.

        Args:
            data: The response data
            status: "success" or "error"
            error: Error message if status is "error"

        Returns:
            Formatted response dict

        DESIGN:
          - All responses follow same structure
          - Status and timestamp always included
          - Errors provide actionable information
          - Data is always present (empty dict if error)
        """
        response = {
            "status": status,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat(),
        }

        if error:
            response["error"] = error

        return response

    def run_server(
        self,
        host: str = "127.0.0.1",
        port: int = 8000
    ) -> None:
        """
        Start the FastMCP server.

        Args:
            host: Server host (default: localhost)
            port: Server port (default: 8000)

        Usage:
            server = ApplicantDBServer()
            server.run_server(port=8001)
        """
        import uvicorn

        logger.info(
            f"Starting MCP server: {self.mcp_name}",
            extra={"host": host, "port": port}
        )

        uvicorn.run(
            self.mcp,
            host=host,
            port=port,
            log_level="info"
        )

    def health_check(self) -> Dict[str, Any]:
        """
        Check server and database health.

        Returns:
            Health status dict with timestamp

        USAGE:
          Used by orchestration layer to detect server failures.
        """
        try:
            session = self.get_session()
            session.execute("SELECT 1")
            session.close()

            return {
                "status": "healthy",
                "server": self.mcp_name,
                "database": "connected",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(
                f"Health check failed for {self.mcp_name}",
                extra={"error": str(e)},
                exc_info=True
            )

            return {
                "status": "unhealthy",
                "server": self.mcp_name,
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def close(self) -> None:
        """Close database connection pool."""
        self.engine.dispose()
        logger.info(f"MCP server closed: {self.mcp_name}")


__all__ = ["BaseMCPServer"]
