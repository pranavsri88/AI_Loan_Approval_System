"""LangGraph workflow node implementations."""

from datetime import datetime
from src.orchestration.state import ApplicationState
from src.agents.applicant_profile_agent import ApplicantProfileAgent
from src.agents.financial_risk_agent import FinancialRiskAgent
from src.agents.loan_decision_agent import LoanDecisionAgent
from src.agents.compliance_agent import ComplianceAgent
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize agents as singletons
profile_agent = ApplicantProfileAgent()
financial_agent = FinancialRiskAgent()
decision_agent = LoanDecisionAgent()
compliance_agent = ComplianceAgent()


def validate_input_node(state: ApplicationState) -> ApplicationState:
    """Validate input application data."""
    logger.info(f"[VALIDATE] Starting for trace {state['trace_id']}")
    start = datetime.utcnow()
    
    # Pydantic validation already happened in API layer
    # Just pass through and mark as complete
    state["timestamps"]["validate"] = start
    return state


def applicant_profile_node(state: ApplicationState) -> ApplicationState:
    """Execute Applicant Profile Agent."""
    logger.info(f"[PROFILE] Starting for trace {state['trace_id']}")
    start = datetime.utcnow()
    
    try:
        applicant_id = state["applicant_data"].get("applicant_id")
        profile = profile_agent.analyze(applicant_id=applicant_id)
        
        state["profile_analysis"] = profile
        state["agents_run"].append("applicant_profile")
        state["timestamps"]["profile"] = start
        logger.info(f"[PROFILE] Complete: {profile.get('employment_risk', 'UNKNOWN')} risk")
    except Exception as e:
        logger.error(f"[PROFILE] Failed: {str(e)}")
        state["error_state"] = {"error": str(e), "node": "profile"}
    
    return state


def financial_risk_node(state: ApplicationState) -> ApplicationState:
    """Execute Financial Risk Agent."""
    logger.info(f"[FINANCIAL] Starting for trace {state['trace_id']}")
    start = datetime.utcnow()
    
    try:
        applicant_data = state["applicant_data"]
        financial = financial_agent.analyze(applicant_data=applicant_data)
        
        state["financial_analysis"] = financial
        state["agents_run"].append("financial_risk")
        state["timestamps"]["financial"] = start
        logger.info(f"[FINANCIAL] Complete: DTI {financial.get('dti', 0):.2f}")
    except Exception as e:
        logger.error(f"[FINANCIAL] Failed: {str(e)}")
        state["error_state"] = {"error": str(e), "node": "financial"}
    
    return state


def loan_decision_node(state: ApplicationState) -> ApplicationState:
    """Execute Loan Decision Agent."""
    logger.info(f"[DECISION] Starting for trace {state['trace_id']}")
    start = datetime.utcnow()
    
    try:
        decision = decision_agent.make_decision(
            profile=state.get("profile_analysis"),
            financial=state.get("financial_analysis"),
            trace_id=state["trace_id"]
        )
        
        state["decision_result"] = decision
        state["agents_run"].append("loan_decision")
        state["timestamps"]["decision"] = start
        logger.info(f"[DECISION] Complete: {decision.get('classification', 'UNKNOWN')}")
    except Exception as e:
        logger.error(f"[DECISION] Failed: {str(e)}")
        state["error_state"] = {"error": str(e), "node": "decision"}
    
    return state


def compliance_node(state: ApplicationState) -> ApplicationState:
    """Execute Compliance & Action Agent."""
    logger.info(f"[COMPLIANCE] Starting for trace {state['trace_id']}")
    start = datetime.utcnow()
    
    try:
        applicant_id = state["applicant_data"].get("applicant_id")
        compliance = compliance_agent.execute(
            decision=state.get("decision_result"),
            applicant_id=applicant_id,
            trace_id=state["trace_id"]
        )
        
        state["compliance_action"] = compliance
        state["agents_run"].append("compliance")
        state["timestamps"]["compliance"] = start
        
        # Set final outputs
        state["final_decision"] = state["decision_result"].get("classification")
        state["final_confidence"] = state["decision_result"].get("confidence")
        state["final_explanation"] = state["decision_result"].get("explanation")
        state["case_id"] = compliance.get("case_id")
        
        logger.info(f"[COMPLIANCE] Complete: Case {state['case_id']}")
    except Exception as e:
        logger.error(f"[COMPLIANCE] Failed: {str(e)}")
        state["error_state"] = {"error": str(e), "node": "compliance"}
    
    return state


def error_handler_node(state: ApplicationState) -> ApplicationState:
    """Handle errors and route to manual review."""
    logger.error(f"[ERROR] Handler triggered for trace {state['trace_id']}")
    
    state["final_decision"] = "REQUIRES_REVIEW"
    state["final_confidence"] = 0.0
    state["final_explanation"] = f"Application encountered errors: {state['error_state'].get('error', 'Unknown error')}"
    
    return state


__all__ = [
    "validate_input_node",
    "applicant_profile_node",
    "financial_risk_node",
    "loan_decision_node",
    "compliance_node",
    "error_handler_node",
]
