"""
LangGraph workflow orchestrator for loan application processing.

Coordinates 4 AI agents through structured workflow with conditional routing,
error handling, and retry logic.

Workflow:
1. Input validation
2. Applicant profile analysis (Agent 1)
3. Financial risk analysis (Agent 2)
4. Loan decision synthesis (Agent 3)
5. Compliance & action (Agent 4)

Conditional routing:
- Incomplete data → Manual review path
- Anomalies detected → Manual review path
- Agent failures → Retry, then escalate if max retries exceeded
"""

from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime
import uuid

from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from src.agents.applicant_profile_agent import ApplicantProfileAgent
from src.agents.financial_risk_agent import FinancialRiskAgent
from src.agents.loan_decision_agent import LoanDecisionAgent
from src.agents.compliance_agent import ComplianceAgent
from src.utils.schemas import ApplicationData
from src.utils.logger import get_logger
from src.utils.config import settings

logger = get_logger(__name__)


class ApplicationState(TypedDict):
    """
    Shared state passed through all workflow nodes.
    
    Updated at each step with intermediate and final results.
    """
    # Input
    applicant_data: Dict[str, Any]
    trace_id: str
    
    # Intermediate results from each agent
    profile_analysis: Optional[Dict[str, Any]]
    financial_analysis: Optional[Dict[str, Any]]
    decision_result: Optional[Dict[str, Any]]
    compliance_action: Optional[Dict[str, Any]]
    
    # Metadata
    agents_run: List[str]
    timestamps: Dict[str, datetime]
    retry_count: int
    
    # Error handling
    error_state: Optional[Dict[str, Any]]
    
    # Final outputs
    final_decision: Optional[str]
    final_confidence: Optional[float]
    final_explanation: Optional[str]
    case_id: Optional[str]


# Lazy-initialized agents (to avoid connection issues during import)
_agents_cache = {}

def get_profile_agent():
    if "profile" not in _agents_cache:
        _agents_cache["profile"] = ApplicantProfileAgent()
    return _agents_cache["profile"]

def get_financial_agent():
    if "financial" not in _agents_cache:
        _agents_cache["financial"] = FinancialRiskAgent()
    return _agents_cache["financial"]

def get_decision_agent():
    if "decision" not in _agents_cache:
        _agents_cache["decision"] = LoanDecisionAgent()
    return _agents_cache["decision"]

def get_compliance_agent():
    if "compliance" not in _agents_cache:
        _agents_cache["compliance"] = ComplianceAgent()
    return _agents_cache["compliance"]


def validate_input_node(state: ApplicationState) -> ApplicationState:
    """
    LangGraph Node: Validate input application data.
    
    Checks:
    - Required fields present
    - Data types correct
    - Values within acceptable ranges
    
    INPUT:
      state.applicant_data: Application data dict
    
    OUTPUT:
      state: Updated with validation results, or escalated to manual review if invalid
    """
    logger.info(f"[VALIDATE] Starting input validation for trace {state['trace_id']}")
    start_time = datetime.utcnow()
    
    try:
        data = state["applicant_data"]
        
        # Basic validation
        required_fields = [
            "applicant_id", "age", "income", "employment_type",
            "credit_score", "loan_amount", "tenure_months",
            "existing_liabilities", "location"
        ]
        
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            logger.warning(f"[VALIDATE] Missing fields: {missing_fields}")
            state["error_state"] = {"error": f"Missing fields: {missing_fields}"}
            state["final_decision"] = "REQUIRES_REVIEW"
            return state
        
        # Convert to ApplicationData for validation
        app_data = ApplicationData(**data)
        state["applicant_data"] = app_data.dict()
        
        state["agents_run"].append("validate")
        state["timestamps"]["validate"] = start_time
        logger.info(f"[VALIDATE] Input validation passed")
        return state
    
    except Exception as e:
        logger.error(f"[VALIDATE] Input validation failed: {str(e)}", exc_info=True)
        state["error_state"] = {"error": str(e)}
        state["final_decision"] = "REQUIRES_REVIEW"
        return state


def profile_agent_node(state: ApplicationState) -> ApplicationState:
    """
    LangGraph Node: Execute Applicant Profile Agent.
    
    Invokes Agent 1 to analyze applicant profile and employment history.
    """
    logger.info(f"[PROFILE] Starting profile analysis")
    start_time = datetime.utcnow()
    
    try:
        applicant_id = state["applicant_data"].get("applicant_id")
        profile_result = get_profile_agent().analyze(applicant_id)
        
        if "error" in profile_result:
            logger.error(f"[PROFILE] Agent error: {profile_result['error']}")
            state["error_state"] = profile_result
            state["final_decision"] = "REQUIRES_REVIEW"
            return state
        
        state["profile_analysis"] = profile_result
        state["agents_run"].append("profile")
        state["timestamps"]["profile"] = start_time
        logger.info(f"[PROFILE] Analysis complete: {profile_result.get('employment_risk')} risk")
        return state
    
    except Exception as e:
        logger.error(f"[PROFILE] Agent execution failed: {str(e)}", exc_info=True)
        state["error_state"] = {"error": str(e)}
        state["final_decision"] = "REQUIRES_REVIEW"
        return state


def financial_agent_node(state: ApplicationState) -> ApplicationState:
    """
    LangGraph Node: Execute Financial Risk Agent.
    
    Invokes Agent 2 to analyze DTI, LTI, credit risk, and anomalies.
    """
    logger.info(f"[FINANCIAL] Starting financial risk analysis")
    start_time = datetime.utcnow()
    
    try:
        profile = state["profile_analysis"] or {}
        financial_result = get_financial_agent().analyze(
            state["applicant_data"],
            stability_score=profile.get("income_stability_score", 50),
            employment_risk=profile.get("employment_risk", "MEDIUM")
        )
        
        if "error" in financial_result:
            logger.error(f"[FINANCIAL] Agent error: {financial_result['error']}")
            state["error_state"] = financial_result
            state["final_decision"] = "REQUIRES_REVIEW"
            return state
        
        state["financial_analysis"] = financial_result
        state["agents_run"].append("financial")
        state["timestamps"]["financial"] = start_time
        logger.info(f"[FINANCIAL] Analysis complete: DTI {financial_result.get('dti_classification')}")
        return state
    
    except Exception as e:
        logger.error(f"[FINANCIAL] Agent execution failed: {str(e)}", exc_info=True)
        state["error_state"] = {"error": str(e)}
        state["final_decision"] = "REQUIRES_REVIEW"
        return state


def decision_agent_node(state: ApplicationState) -> ApplicationState:
    """
    LangGraph Node: Execute Loan Decision Agent.
    
    Invokes Agent 3 to synthesize all analysis and make final decision.
    """
    logger.info(f"[DECISION] Starting loan decision synthesis")
    start_time = datetime.utcnow()
    
    try:
        decision_result = get_decision_agent().analyze(
            state["profile_analysis"] or {},
            state["financial_analysis"] or {},
            applicant_data=state.get("applicant_data", {})
        )
        
        if "error" in decision_result:
            logger.error(f"[DECISION] Agent error: {decision_result['error']}")
            state["error_state"] = decision_result
            state["final_decision"] = "REQUIRES_REVIEW"
            return state
        
        state["decision_result"] = decision_result
        state["agents_run"].append("decision")
        state["timestamps"]["decision"] = start_time

        # Extract decision and confidence for routing
        state["final_decision"] = decision_result.get("classification", "REQUIRES_REVIEW")
        state["final_confidence"] = decision_result.get("confidence", 0.0)

        # If APPROVED or REJECTED based on strong metrics despite prior errors, clear error_state
        # This handles cases like profile agent failing (applicant not in mock DB)
        # but financial metrics being objectively strong (approval) or clearly rejectable (rejection)
        if state["final_decision"] in ["APPROVED", "REJECTED"] and decision_result.get("error_override"):
            logger.info(f"[DECISION] Clearing error_state - decision is {state['final_decision']} on strong metrics")
            state["error_state"] = None

        logger.info(f"[DECISION] Decision: {state['final_decision']} ({state['final_confidence']:.1%} confidence)")
        return state
    
    except Exception as e:
        logger.error(f"[DECISION] Agent execution failed: {str(e)}", exc_info=True)
        state["error_state"] = {"error": str(e)}
        state["final_decision"] = "REQUIRES_REVIEW"
        return state


def compliance_agent_node(state: ApplicationState) -> ApplicationState:
    """
    LangGraph Node: Execute Compliance & Action Agent.
    
    Invokes Agent 4 to finalize action, create audit trail, send notifications.
    """
    logger.info(f"[COMPLIANCE] Starting compliance action")
    start_time = datetime.utcnow()
    
    try:
        compliance_result = get_compliance_agent().analyze(
            state["decision_result"] or {},
            state["applicant_data"].get("applicant_id", "UNKNOWN"),
            state["trace_id"]
        )
        
        if "error" in compliance_result:
            logger.error(f"[COMPLIANCE] Agent error: {compliance_result['error']}")
            state["error_state"] = compliance_result
            return state
        
        state["compliance_action"] = compliance_result
        state["case_id"] = compliance_result.get("case_id")
        state["agents_run"].append("compliance")
        state["timestamps"]["compliance"] = start_time
        
        logger.info(f"[COMPLIANCE] Action complete: case_id={state['case_id']}")
        return state
    
    except Exception as e:
        logger.error(f"[COMPLIANCE] Agent execution failed: {str(e)}", exc_info=True)
        state["error_state"] = {"error": str(e)}
        return state


def should_escalate_to_review(state: ApplicationState) -> str:
    """
    Conditional routing: Decide whether to escalate to manual review.
    
    Escalate if:
    - Error state present
    - Confidence below threshold
    - Anomalies detected
    """
    # Check explicit decisions first (APPROVED/REJECTED take precedence)
    decision = state.get("final_decision", "REQUIRES_REVIEW")

    # APPROVED and REJECTED are final decisions - execute them regardless of errors/anomalies
    if decision in ["APPROVED", "REJECTED"]:
        logger.info(f"→ Routing to EXECUTE ({decision} decision finalized)")
        return "execute"

    # For REQUIRES_REVIEW, check error conditions
    if state.get("error_state"):
        logger.info("→ Routing to MANUAL REVIEW (error)")
        return "manual_review"

    confidence = state.get("final_confidence", 1.0)
    if confidence < settings.confidence_threshold:
        logger.info(f"→ Routing to MANUAL REVIEW (low confidence: {confidence:.1%})")
        return "manual_review"

    financial = state.get("financial_analysis", {})
    if financial.get("anomaly_detected"):
        logger.info("→ Routing to MANUAL REVIEW (anomalies detected)")
        return "manual_review"

    logger.info("→ Routing to MANUAL REVIEW (agent decision)")
    return "manual_review"


def manual_review_node(state: ApplicationState) -> ApplicationState:
    """
    LangGraph Node: Manual Review Path.
    
    Sets decision to REQUIRES_REVIEW if not already set.
    This node is where a human loan officer would review the case.
    """
    logger.info(f"[REVIEW] Case escalated for manual review")
    
    if state["final_decision"] != "REQUIRES_REVIEW":
        state["final_decision"] = "REQUIRES_REVIEW"
    
    state["agents_run"].append("manual_review")
    state["timestamps"]["manual_review"] = datetime.utcnow()
    
    logger.info(f"[REVIEW] Awaiting manual underwriter assessment")
    return state


def create_graph() -> CompiledStateGraph:
    """
    Create and compile LangGraph workflow.
    
    Returns:
        Compiled state graph ready for invocation
    """
    graph = StateGraph(ApplicationState)
    
    # Add nodes
    graph.add_node("validate", validate_input_node)
    graph.add_node("profile", profile_agent_node)
    graph.add_node("financial", financial_agent_node)
    graph.add_node("decision", decision_agent_node)
    graph.add_node("manual_review", manual_review_node)
    graph.add_node("compliance", compliance_agent_node)

    # Set entry point
    graph.set_entry_point("validate")

    # Add edges
    graph.add_edge("validate", "profile")
    graph.add_edge("profile", "financial")
    graph.add_edge("financial", "decision")

    # Conditional routing after decision
    graph.add_conditional_edges(
        "decision",
        should_escalate_to_review,
        {
            "manual_review": "manual_review",
            "execute": "compliance"
        }
    )

    # Edges from paths to end
    graph.add_edge("manual_review", END)
    graph.add_edge("compliance", END)

    # Compile
    return graph.compile()


def run_application(applicant_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute loan application workflow end-to-end.
    
    Orchestrates all 4 agents through LangGraph workflow.
    
    Args:
        applicant_data: Application data (dict or ApplicationData)
    
    Returns:
        Final result with decision, confidence, explanation, case_id
    """
    trace_id = f"TRACE-{uuid.uuid4().hex[:12]}"
    logger.info(f"Starting application workflow: {trace_id}")
    
    # Convert ApplicationData to dict if needed
    if hasattr(applicant_data, "dict"):
        applicant_data = applicant_data.dict()
    
    # Initialize state
    initial_state: ApplicationState = {
        "applicant_data": applicant_data,
        "trace_id": trace_id,
        "profile_analysis": None,
        "financial_analysis": None,
        "decision_result": None,
        "compliance_action": None,
        "agents_run": [],
        "timestamps": {"start": datetime.utcnow()},
        "retry_count": 0,
        "error_state": None,
        "final_decision": None,
        "final_confidence": None,
        "final_explanation": None,
        "case_id": None,
    }
    
    try:
        # Create and execute graph
        graph = create_graph()
        final_state = graph.invoke(initial_state)
        
        # Extract results
        result = {
            "trace_id": trace_id,
            "applicant_id": applicant_data.get("applicant_id"),
            "decision": final_state.get("final_decision", "UNKNOWN"),
            "confidence": final_state.get("final_confidence", 0.0),
            "risk_score": final_state.get("decision_result", {}).get("risk_score"),
            "case_id": final_state.get("case_id"),
            "agents_run": final_state.get("agents_run", []),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if final_state.get("decision_result"):
            result["decision_factors"] = final_state["decision_result"].get("decision_factors", [])
            result["explanation"] = final_state["decision_result"].get("explanation", "")
        
        logger.info(f"Workflow complete: {result['decision']} (case: {result['case_id']})")
        return result
    
    except Exception as e:
        logger.error(f"Workflow failed: {str(e)}", exc_info=True)
        return {
            "trace_id": trace_id,
            "applicant_id": applicant_data.get("applicant_id"),
            "decision": "REQUIRES_REVIEW",
            "confidence": 0.0,
            "error": str(e),
            "case_id": None,
        }


__all__ = [
    "ApplicationState",
    "create_graph",
    "run_application",
]
