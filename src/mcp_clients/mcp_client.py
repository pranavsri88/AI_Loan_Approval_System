"""
MCP Client - Centralized communication with Model Context Protocol servers.

Provides:
- Connection management for all MCP servers
- Try-catch wrappers for graceful fallback
- Shared session reuse
- Helper methods for each MCP server
"""

from typing import Dict, Any, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

from src.utils.logger import get_logger

logger = get_logger(__name__)


class MCPClient:
    """
    Centralized MCP server client with fallback logic.

    Connects to:
    - RiskRulesDB (port 8002) - Risk rules and thresholds
    - DecisionSynthesis (port 8003) - Decision logic
    - NotificationSystem (port 8004) - Audit logging
    - ApplicantDB (port 8001) - Applicant data (already in use)
    """

    def __init__(self):
        """Initialize MCP client with retry strategy."""
        self.base_url_risk = "http://127.0.0.1:8002"
        self.base_url_decision = "http://127.0.0.1:8003"
        self.base_url_notification = "http://127.0.0.1:8004"
        self.base_url_applicant = "http://127.0.0.1:8001"

        # Setup retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _call_mcp_tool(self, base_url: str, tool_name: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Call an MCP server tool with fallback.

        Args:
            base_url: Base URL of MCP server
            tool_name: Name of the tool to call
            **kwargs: Tool arguments

        Returns:
            Tool response dict or None if failed
        """
        try:
            url = f"{base_url}/call/{tool_name}"
            response = self.session.post(url, json=kwargs, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"MCP tool call failed ({tool_name}): {str(e)}")
            return None

    # ==================== RiskRulesDB MCP ====================

    def get_risk_thresholds(self) -> Optional[Dict[str, Any]]:
        """
        Fetch risk thresholds from RiskRulesDB MCP.

        Returns:
            Dict with DTI, credit score, and LTI thresholds, or None if failed
        """
        return self._call_mcp_tool(self.base_url_risk, "get_risk_thresholds")

    def get_anomaly_rules(self) -> Optional[Dict[str, Any]]:
        """
        Fetch anomaly detection rules from RiskRulesDB MCP.

        Returns:
            Dict with anomaly rules, or None if failed
        """
        return self._call_mcp_tool(self.base_url_risk, "get_anomaly_rules")

    def classify_by_rules(self, dti: float, credit_score: int, lti: float) -> Optional[Dict[str, Any]]:
        """
        Classify applicant metrics using RiskRulesDB MCP.

        Args:
            dti: Debt-to-income ratio
            credit_score: Credit score
            lti: Loan-to-income ratio

        Returns:
            Classification dict with risk levels, or None if failed
        """
        return self._call_mcp_tool(
            self.base_url_risk,
            "classify_by_rules",
            dti=dti,
            credit_score=credit_score,
            lti=lti
        )

    # ==================== DecisionSynthesis MCP ====================

    def get_decision_policy(self) -> Optional[Dict[str, Any]]:
        """
        Fetch decision policy from DecisionSynthesis MCP.

        Returns:
            Dict with APPROVED/REJECTED/REQUIRES_REVIEW criteria, or None if failed
        """
        return self._call_mcp_tool(self.base_url_decision, "get_decision_policy")

    def score_applicant(
        self,
        credit_score: int,
        dti: float,
        lti: float,
        income_stability: float = 0.5,
        employment_risk: str = "MEDIUM",
        anomaly_score: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Score applicant using DecisionSynthesis MCP.

        Args:
            credit_score: Credit score
            dti: Debt-to-income ratio
            lti: Loan-to-income ratio
            income_stability: Income stability score (0-1)
            employment_risk: Employment risk level
            anomaly_score: Anomaly score (0-100)

        Returns:
            Risk score dict, or None if failed
        """
        return self._call_mcp_tool(
            self.base_url_decision,
            "score_applicant",
            credit_score=credit_score,
            dti=dti,
            lti=lti,
            income_stability=income_stability,
            employment_risk=employment_risk,
            anomaly_score=anomaly_score
        )

    # ==================== NotificationSystem MCP ====================

    def create_case(
        self,
        trace_id: str,
        applicant_id: str,
        decision: str,
        action_taken: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Create a case record in NotificationSystem MCP.

        Args:
            trace_id: Workflow trace ID
            applicant_id: Applicant ID
            decision: Decision (APPROVED/REJECTED/REQUIRES_REVIEW)
            action_taken: Action taken

        Returns:
            Case creation result with case_id, or None if failed
        """
        return self._call_mcp_tool(
            self.base_url_notification,
            "create_case",
            trace_id=trace_id,
            applicant_id=applicant_id,
            decision=decision,
            action_taken=action_taken
        )

    def write_audit_log(
        self,
        trace_id: str,
        case_id: str,
        applicant_id: str,
        decision: str,
        risk_score: int,
        confidence: float,
        explanation: str,
        agents_run: list,
        decision_factors: list
    ) -> Optional[Dict[str, Any]]:
        """
        Write audit log to NotificationSystem MCP.

        Args:
            trace_id: Workflow trace ID
            case_id: Case ID
            applicant_id: Applicant ID
            decision: Final decision
            risk_score: Risk score (0-100)
            confidence: Confidence (0-1)
            explanation: Decision explanation
            agents_run: List of agents that ran
            decision_factors: Decision factors

        Returns:
            Audit log result, or None if failed
        """
        return self._call_mcp_tool(
            self.base_url_notification,
            "write_audit_log",
            trace_id=trace_id,
            case_id=case_id,
            applicant_id=applicant_id,
            decision=decision,
            risk_score=risk_score,
            confidence=confidence,
            explanation=explanation,
            agents_run=agents_run,
            decision_factors=decision_factors
        )

    def send_notification(
        self,
        applicant_id: str,
        case_id: str,
        notification_type: str,
        message: str
    ) -> Optional[Dict[str, Any]]:
        """
        Send notification via NotificationSystem MCP.

        Args:
            applicant_id: Applicant ID
            case_id: Case ID
            notification_type: Type (email, sms, letter)
            message: Message to send

        Returns:
            Notification result, or None if failed
        """
        return self._call_mcp_tool(
            self.base_url_notification,
            "send_notification",
            applicant_id=applicant_id,
            case_id=case_id,
            notification_type=notification_type,
            message=message
        )

    # ==================== ApplicantDB MCP ====================

    def get_applicant_history(self, applicant_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch applicant history from ApplicantDB MCP.

        Args:
            applicant_id: Applicant ID

        Returns:
            Applicant history dict, or None if failed
        """
        return self._call_mcp_tool(
            self.base_url_applicant,
            "get_applicant_history",
            applicant_id=applicant_id
        )

    def get_employment_data(self, applicant_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch employment data from ApplicantDB MCP.

        Args:
            applicant_id: Applicant ID

        Returns:
            Employment data dict, or None if failed
        """
        return self._call_mcp_tool(
            self.base_url_applicant,
            "get_employment_data",
            applicant_id=applicant_id
        )

    def get_credit_inquiries(self, applicant_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch credit inquiries from ApplicantDB MCP.

        Args:
            applicant_id: Applicant ID

        Returns:
            Credit inquiries dict, or None if failed
        """
        return self._call_mcp_tool(
            self.base_url_applicant,
            "get_credit_inquiries",
            applicant_id=applicant_id
        )


# Global singleton instance
_mcp_client_instance: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """Get or create the global MCP client instance."""
    global _mcp_client_instance
    if _mcp_client_instance is None:
        _mcp_client_instance = MCPClient()
    return _mcp_client_instance


__all__ = ["MCPClient", "get_mcp_client"]
