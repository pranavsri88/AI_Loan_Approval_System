"""
DecisionSynthesis MCP Server.

Provides tools for decision logic and scoring helpers.

Tools:
- get_decision_policy() -> Decision rules (approval, rejection, review criteria)
- score_applicant(metrics_dict) -> Score risk based on combined metrics
"""

from typing import Any, Dict
from fastmcp import FastMCP

from src.utils.config import settings


# Initialize MCP server
mcp = FastMCP("decision_synthesis")


@mcp.tool
def get_decision_policy() -> Dict[str, Any]:
    """
    Get the decision policy and rules.
    
    Returns:
    {
        "approval_criteria": [...],
        "rejection_criteria": [...],
        "manual_review_criteria": [...]
    }
    """
    return {
        "approval_criteria": {
            "all_required": [
                f"credit_score >= {settings.credit_excellent_min}",
                f"dti < {settings.dti_favorable_max}",
                f"lti < {settings.lti_favorable_max}",
                "employment_risk == LOW",
                "anomaly_detected == false",
            ],
            "description": "All criteria must be true to auto-approve",
        },
        "rejection_criteria": {
            "any_trigger": [
                f"credit_score < 550",
                f"dti > {settings.dti_high_risk_min}",
                f"lti > {settings.lti_high_risk_min}",
                "employment_type == Unemployed AND income_stability < 50",
            ],
            "description": "Any criterion triggers auto-reject",
        },
        "manual_review_criteria": {
            "any_trigger": [
                f"confidence < {settings.confidence_threshold}",
                f"dti in range ({settings.dti_acceptable_max}, {settings.dti_borderline_max})",
                f"anomaly_score > {settings.anomaly_score_threshold}",
                "age < 21 OR age > 70 WITH strong_other_factors",
                "recent_employment_gap > 6",
            ],
            "description": "Any criterion routes to manual review",
        },
    }


@mcp.tool
def score_applicant(
    credit_score: int,
    dti: float,
    lti: float,
    income_stability: int,
    employment_risk: str,
    anomaly_score: float,
) -> Dict[str, Any]:
    """
    Calculate risk score for applicant based on combined metrics.
    
    Returns risk score (0=safest, 100=riskiest) and factors.
    """
    
    # Score each component (0-100 scale)
    # Credit score: lower score = higher risk
    if credit_score >= settings.credit_excellent_min:
        credit_component = 10
    elif credit_score >= settings.credit_good_min:
        credit_component = 25
    elif credit_score >= settings.credit_fair_min:
        credit_component = 50
    elif credit_score >= settings.credit_poor_min:
        credit_component = 75
    else:
        credit_component = 95
    
    # DTI: higher ratio = higher risk
    if dti < settings.dti_favorable_max:
        dti_component = 10
    elif dti < settings.dti_acceptable_max:
        dti_component = 30
    elif dti < settings.dti_borderline_max:
        dti_component = 60
    else:
        dti_component = 90
    
    # LTI: higher ratio = higher risk
    if lti < settings.lti_favorable_max:
        lti_component = 15
    elif lti < settings.lti_acceptable_max:
        lti_component = 40
    else:
        lti_component = 85
    
    # Income stability: lower = higher risk
    income_component = max(0, 100 - income_stability)
    
    # Employment risk
    employment_component = {
        "LOW": 10,
        "MEDIUM": 50,
        "HIGH": 85,
    }.get(employment_risk, 50)
    
    # Anomalies: higher anomaly score = higher risk
    anomaly_component = anomaly_score * 100
    
    # Weighted average
    weights = {
        "credit": 0.35,
        "dti": 0.25,
        "lti": 0.15,
        "income_stability": 0.10,
        "employment": 0.10,
        "anomaly": 0.05,
    }
    
    risk_score = int(
        weights["credit"] * credit_component
        + weights["dti"] * dti_component
        + weights["lti"] * lti_component
        + weights["income_stability"] * income_component
        + weights["employment"] * employment_component
        + weights["anomaly"] * anomaly_component
    )
    
    return {
        "risk_score": max(0, min(100, risk_score)),
        "components": {
            "credit_score": credit_component,
            "dti": dti_component,
            "lti": lti_component,
            "income_stability": income_component,
            "employment_risk": employment_component,
            "anomaly": anomaly_component,
        },
        "weights": weights,
        "interpretation": {
            0: "Very Low Risk",
            25: "Low Risk",
            50: "Medium Risk",
            75: "High Risk",
            100: "Very High Risk",
        }[min(100, (risk_score // 25) * 25)],
    }


def run_server(host: str = "127.0.0.1", port: int = 8003):
    """Run the DecisionSynthesis MCP server."""
    import uvicorn
    uvicorn.run("src.mcp_servers.decision_synthesis:mcp", host=host, port=port, reload=True)


if __name__ == "__main__":
    run_server()
