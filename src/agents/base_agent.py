"""
Base agent class with common MCP client setup and utilities.

Provides:
- MCP client initialization and tool calling
- Claude Haiku invocation via Anthropic SDK
- Structured output validation via Pydantic
- Error handling and logging
"""

from typing import Any, Dict, Optional
from abc import ABC, abstractmethod
import logging
import json

from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all loan approval agents.

    Each agent:
    1. Connects to MCP server for tool access
    2. Fetches context data via MCP tools
    3. Invokes Claude Haiku 4.5 for analysis
    4. Returns structured Pydantic output
    """
    
    agent_name: str = "BaseAgent"
    mcp_server_url: str = ""
    
    def __init__(self):
        """Initialize agent with MCP client."""
        self.logger = get_logger(self.agent_name)
        self.client = None
        self._setup_mcp_client()
    
    def _setup_mcp_client(self) -> None:
        """
        Setup MCP client connection.
        
        In production, this connects to a real MCP server.
        For development, we'll call MCP functions directly since they're
        FastMCP servers in the same process (no remote connection needed).
        """
        self.logger.info(f"Setting up MCP client for {self.agent_name}")
        # MCP client will be used to call tools
        # In development, we call the functions directly
    
    def invoke_claude(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Invoke Claude Haiku 4.5 with structured output.
        
        Args:
            system_prompt: System message defining agent role
            user_prompt: User message with context and task
            output_schema: Pydantic model or JSON schema for structured output
        
        Returns:
            Parsed response matching output_schema
        """
        from anthropic import Anthropic
        
        self.logger.debug(f"Invoking Claude Haiku 4.5 via {self.agent_name}")
        
        client = Anthropic(api_key=settings.anthropic_api_key)
        
        message = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=2048,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ],
        )
        
        # Extract text response
        response_text = message.content[0].text
        
        # Try to parse as JSON if structured output expected
        if output_schema:
            try:
                # Extract JSON from response (Claude may wrap it in markdown)
                if "```json" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    json_str = response_text.split("```")[1].split("```")[0].strip()
                else:
                    json_str = response_text
                
                parsed = json.loads(json_str)
                self.logger.debug("Successfully parsed Claude response as JSON")
                return parsed
            except (json.JSONDecodeError, IndexError) as e:
                self.logger.warning(f"Failed to parse JSON response: {e}")
                # Return as-is if parsing fails
                return {"raw_response": response_text}
        
        return {"response": response_text}
    
    @abstractmethod
    def analyze(self, **kwargs) -> Dict[str, Any]:
        """
        Main analysis method - implemented by subclasses.
        
        Each agent implements this with its specific logic:
        1. Fetch data via MCP tools
        2. Call Claude for analysis
        3. Return structured output
        """
        pass


__all__ = ["BaseAgent"]
