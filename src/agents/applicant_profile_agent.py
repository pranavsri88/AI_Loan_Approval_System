"""
Applicant Profile Agent.

Analyzes applicant's personal and employment profile.

Responsibilities:
1. Query ApplicantDB MCP server for applicant history
2. Fetch employment data and credit inquiries
3. Invoke Claude for stability assessment
4. Return ProfileAnalysis schema
"""

from typing import Any, Dict
import json

from src.agents.base_agent import BaseAgent
from src.agents.prompts import (
    APPLICANT_PROFILE_SYSTEM_PROMPT,
    APPLICANT_PROFILE_USER_PROMPT_TEMPLATE,
)
from src.utils.schemas import ProfileAnalysis
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ApplicantProfileAgent(BaseAgent):
    """
    Applicant Profile Analysis Agent.
    
    Analyzes applicant's personal and employment profile to assess:
    - Income stability and consistency
    - Employment risk and tenure
    - Credit history summary
    - Profile completeness and anomalies
    
    MCP Server: ApplicantDB (port 8001)
    """
    
    agent_name = "ApplicantProfileAgent"
    mcp_server_url = "http://127.0.0.1:8001"
    
    def analyze(self, applicant_id: str, **kwargs) -> Dict[str, Any]:
        """
        Analyze applicant profile.
        
        Args:
            applicant_id: Unique applicant identifier
            **kwargs: Additional context (typically passed from orchestrator)
        
        Returns:
            Dictionary matching ProfileAnalysis schema
        """
        logger.info(f"Analyzing profile for applicant {applicant_id}")
        
        try:
            # Step 1: Fetch applicant data from MCP server
            logger.debug(f"Fetching applicant history from MCP")
            app_history = self._fetch_applicant_history(applicant_id)
            
            if "error" in app_history:
                logger.error(f"Failed to fetch applicant: {app_history['error']}")
                return {"error": app_history["error"]}
            
            # Step 2: Fetch employment data
            logger.debug(f"Fetching employment data from MCP")
            emp_data = self._fetch_employment_data(applicant_id)
            
            # Step 3: Fetch credit inquiries
            logger.debug(f"Fetching credit inquiries from MCP")
            credit_data = self._fetch_credit_inquiries(applicant_id)
            
            # Step 4: Prepare context for Claude
            employment_history_text = self._format_employment_history(emp_data)
            credit_inquiries_text = self._format_credit_inquiries(credit_data)
            
            # Step 5: Invoke Claude for analysis
            logger.debug("Invoking Claude Sonnet for profile analysis")
            user_prompt = APPLICANT_PROFILE_USER_PROMPT_TEMPLATE.format(
                age=app_history["applicant"]["age"],
                income=app_history["applicant"]["income"],
                employment_type=app_history["applicant"]["employment_type"],
                credit_score=app_history["applicant"]["credit_score"],
                liabilities=app_history["applicant"].get("liabilities", 0),
                location=app_history["applicant"]["location"],
                employment_history=employment_history_text,
                credit_inquiries=credit_inquiries_text,
            )
            
            claude_response = self.invoke_claude(
                system_prompt=APPLICANT_PROFILE_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                output_schema=ProfileAnalysis.schema(),
            )
            
            # Step 6: Validate against ProfileAnalysis schema
            logger.debug("Validating response against ProfileAnalysis schema")
            profile_analysis = ProfileAnalysis(
                income_stability_score=claude_response.get("income_stability_score", 50),
                employment_risk=claude_response.get("employment_risk", "MEDIUM"),
                credit_summary=claude_response.get("credit_summary", "No history available"),
                completeness_flags=claude_response.get("completeness_flags", []),
                confidence=claude_response.get("confidence", 0.5),
                reasoning=claude_response.get("reasoning", ""),
            )
            
            logger.info(f"Profile analysis complete: {profile_analysis.employment_risk} risk")
            return profile_analysis.dict()
        
        except Exception as e:
            logger.error(f"Profile analysis failed: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    def _fetch_applicant_history(self, applicant_id: str) -> Dict[str, Any]:
        """Fetch applicant history from ApplicantDB MCP server."""
        from src.mcp_servers.applicant_db import get_applicant_history
        return get_applicant_history(applicant_id)
    
    def _fetch_employment_data(self, applicant_id: str) -> Dict[str, Any]:
        """Fetch employment data from ApplicantDB MCP server."""
        from src.mcp_servers.applicant_db import get_employment_data
        return get_employment_data(applicant_id)
    
    def _fetch_credit_inquiries(self, applicant_id: str) -> Dict[str, Any]:
        """Fetch credit inquiries from ApplicantDB MCP server."""
        from src.mcp_servers.applicant_db import get_credit_inquiries
        return get_credit_inquiries(applicant_id)
    
    def _format_employment_history(self, emp_data: Dict[str, Any]) -> str:
        """Format employment data for Claude prompt."""
        if "error" in emp_data:
            return "No employment history available"
        
        jobs = emp_data.get("jobs", [])
        if not jobs:
            return "No employment history available"
        
        lines = []
        for job in jobs:
            line = f"- {job['title']} at {job['company']}: {job['duration_months']} months"
            lines.append(line)
        
        return "\n".join(lines)
    
    def _format_credit_inquiries(self, credit_data: Dict[str, Any]) -> str:
        """Format credit inquiry data for Claude prompt."""
        if "error" in credit_data:
            return "No credit inquiries on record"
        
        inquiries = credit_data.get("inquiries", [])
        if not inquiries:
            return "No recent credit inquiries"
        
        recent = credit_data.get("recent_inquiries_3m", 0)
        return f"Total inquiries: {len(inquiries)}, Last 3 months: {recent}"


__all__ = ["ApplicantProfileAgent"]
