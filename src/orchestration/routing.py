"""LangGraph conditional routing functions."""

from src.orchestration.state import ApplicationState
from src.utils.logger import get_logger

logger = get_logger(__name__)


def route_after_validation(state: ApplicationState) -> str:
    """Route after validation node."""
    if state.get("error_state"):
        return "error_node"
    return "profile_node"


def route_after_profile(state: ApplicationState) -> str:
    """Route after profile analysis."""
    if state.get("error_state"):
        logger.warning(f"Profile analysis error, escalating to manual review")
        return "error_node"
    
    profile = state.get("profile_analysis")
    if profile and profile.get("confidence", 0) < 0.5:
        logger.warning(f"Low profile confidence ({profile.get('confidence')}), escalating")
        return "error_node"
    
    return "financial_node"


def route_after_financial(state: ApplicationState) -> str:
    """Route after financial risk analysis."""
    if state.get("error_state"):
        logger.warning(f"Financial analysis error, escalating to manual review")
        return "error_node"
    
    financial = state.get("financial_analysis")
    if financial and financial.get("anomaly_detected"):
        logger.warning(f"Anomalies detected, escalating to manual review")
        return "error_node"
    
    if financial and financial.get("confidence", 0) < 0.5:
        logger.warning(f"Low financial confidence, escalating")
        return "error_node"
    
    return "decision_node"


def route_after_decision(state: ApplicationState) -> str:
    """Route after loan decision."""
    if state.get("error_state"):
        logger.warning(f"Decision error, escalating to manual review")
        return "error_node"
    
    decision = state.get("decision_result")
    if decision and decision.get("confidence", 0) < 0.75:
        logger.info(f"Decision confidence {decision.get('confidence')}, escalating to manual review")
        return "error_node"
    
    return "compliance_node"


__all__ = [
    "route_after_validation",
    "route_after_profile",
    "route_after_financial",
    "route_after_decision",
]
