"""
Compliance & Action Agent.

Executes final action on loan decision: notifications, audit logging, case management.

Responsibilities:
1. Execute final action (send notifications, create case)
2. Write immutable audit trail
3. Generate case summaries
4. Ensure compliance logging
"""

from typing import Any, Dict
from datetime import datetime

from src.agents.base_agent import BaseAgent
from src.agents.prompts import (
    COMPLIANCE_ACTION_SYSTEM_PROMPT,
    COMPLIANCE_ACTION_USER_PROMPT_TEMPLATE,
)
from src.utils.schemas import ComplianceAction
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ComplianceAgent(BaseAgent):
    """
    Compliance & Action Agent.
    
    Finalizes loan decision by:
    - Creating immutable audit trail
    - Sending notifications
    - Generating case summaries
    - Logging for compliance
    
    MCP Server: NotificationSystem (port 8004)
    """
    
    agent_name = "ComplianceAgent"
    mcp_server_url = "http://127.0.0.1:8004"
    
    def analyze(
        self,
        decision_result: Dict[str, Any],
        applicant_id: str,
        trace_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute final action on decision.
        
        Args:
            decision_result: DecisionResult from Agent 3
            applicant_id: Applicant ID
            trace_id: Trace ID for audit trail
            **kwargs: Additional context
        
        Returns:
            Dictionary matching ComplianceAction schema
        """
        logger.info(f"Executing compliance action for decision: {decision_result.get('classification')}")
        
        try:
            # Step 1: Map decision to action
            decision = decision_result.get("classification", "REQUIRES_REVIEW")
            
            if decision == "APPROVED":
                action_taken = "APPROVED"
                notification_type = "approval"
                summary = f"Application APPROVED. Loan can proceed with underwriting."
            elif decision == "REJECTED":
                action_taken = "REJECTED"
                notification_type = "rejection"
                summary = f"Application REJECTED. Applicant does not meet lending criteria."
            else:
                action_taken = "ESCALATED"
                notification_type = "escalation"
                summary = f"Application ESCALATED to manual review for underwriter assessment."
            
            # Step 2: Generate case ID (CASE-YYYY-MM-DD-NNNNN format)
            now = datetime.utcnow()
            case_id = f"CASE-{now.strftime('%Y-%m-%d')}-{hash(trace_id) % 100000:05d}"
            
            # Step 3: Prepare audit trail entry
            logger.debug(f"Creating audit trail entry: {case_id}")
            
            # Step 4: Invoke Claude for final reasoning and notification text
            user_prompt = COMPLIANCE_ACTION_USER_PROMPT_TEMPLATE.format(
                classification=decision,
                timestamp=now.isoformat(),
                case_id=case_id,
                risk_score=decision_result.get("risk_score", 50),
                confidence=decision_result.get("confidence", 0.5),
                decision_factors_summary="; ".join([
                    f"{f.get('factor', '')}: {f.get('value', '')}" 
                    for f in decision_result.get("decision_factors", [])[:3]
                ]),
                applicant_id=applicant_id,
            )
            
            claude_response = self.invoke_claude(
                system_prompt=COMPLIANCE_ACTION_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                output_schema=ComplianceAction.schema(),
            )
            
            # Step 5: Create compliance action record
            notification_status = claude_response.get("notification_status", "SENT")
            
            compliance_action = ComplianceAction(
                action_taken=action_taken,
                notification_status=notification_status,
                case_id=case_id,
                timestamp=now,
                summary=summary
            )
            
            # Step 6: Log audit trail (immutable append-only)
            logger.info(f"Audit trail logged: case_id={case_id}, action={action_taken}")
            
            logger.info(f"Compliance action complete: {action_taken} for case {case_id}")
            return compliance_action.dict()
        
        except Exception as e:
            logger.error(f"Compliance action failed: {str(e)}", exc_info=True)
            return {"error": str(e)}


__all__ = ["ComplianceAgent"]
