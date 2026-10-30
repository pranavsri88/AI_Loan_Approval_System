"""LangGraph workflow state definition."""

from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime

class ApplicationState(TypedDict):
    """
    Shared state passed through all LangGraph workflow nodes.
    
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


__all__ = ["ApplicationState"]
