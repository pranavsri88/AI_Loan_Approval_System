"""
RiskRulesDB MCP Server.

Provides tools for querying risk rules, thresholds, and anomaly detection rules.

Tools:
- get_risk_thresholds() -> DTI, credit score, LTI bands
- get_anomaly_rules() -> Rules for detecting anomalies
- classify_by_rules(metrics_dict) -> Score applicant by rules
"""

from typing import Any, Dict
from fastmcp import FastMCP
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import RiskRule
from src.utils.config import settings


# Initialize MCP server
mcp = FastMCP("risk_rules_db")


def get_session():
    """Get database session."""
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


@mcp.tool
def get_risk_thresholds() -> Dict[str, Any]:
    """
    Get current risk thresholds for DTI, credit score, LTI.
    
    Returns:
    {
        "dti": {...},
        "credit_score": {...},
        "lti": {...}
    }
    """
    session = get_session()
    try:
        # Query all threshold rules
        rules = session.query(RiskRule).filter(
            RiskRule.rule_type.in_(["dti", "credit_score", "lti"])
        ).all()
        
        thresholds = {}
        for rule in rules:
            rule_type = rule.rule_type
            if rule_type not in thresholds:
                thresholds[rule_type] = {}
            
            thresholds[rule_type][rule.rule_name] = {
                "value": rule.float_value or rule.int_value,
                "description": rule.description,
            }
        
        return {
            "dti_favorable_max": settings.dti_favorable_max,
            "dti_acceptable_max": settings.dti_acceptable_max,
            "dti_borderline_max": settings.dti_borderline_max,
            "credit_excellent_min": settings.credit_excellent_min,
            "credit_good_min": settings.credit_good_min,
            "credit_fair_min": settings.credit_fair_min,
            "credit_poor_min": settings.credit_poor_min,
            "lti_favorable_max": settings.lti_favorable_max,
            "lti_acceptable_max": settings.lti_acceptable_max,
            "lti_high_risk_min": settings.lti_high_risk_min,
        }
    finally:
        session.close()


@mcp.tool
def get_anomaly_rules() -> Dict[str, Any]:
    """
    Get rules for anomaly detection.
    
    Returns thresholds for:
    - Income spike detection
    - Employment gap detection
    - Credit inquiry frequency
    - Liability changes
    """
    return {
        "income_spike_threshold": 1.5,  # 150% increase = anomaly
        "employment_gap_months_threshold": 6,  # > 6 months = anomaly
        "credit_inquiries_3m_threshold": 3,  # > 3 in 90 days = anomaly
        "liabilities_spike_threshold": 1.3,  # 130% increase = anomaly
        "rules": [
            {
                "name": "income_spike",
                "description": "Income increased >150% year-over-year",
                "action": "FLAG",
                "severity": "MEDIUM",
            },
            {
                "name": "employment_gap",
                "description": "Employment gap > 6 months",
                "action": "FLAG",
                "severity": "MEDIUM",
            },
            {
                "name": "credit_inquiries",
                "description": "More than 3 credit inquiries in past 3 months",
                "action": "FLAG",
                "severity": "LOW",
            },
            {
                "name": "liabilities_spike",
                "description": "Liabilities increased >130%",
                "action": "FLAG",
                "severity": "HIGH",
            },
        ],
    }


@mcp.tool
def classify_by_rules(dti: float, credit_score: int, lti: float) -> Dict[str, Any]:
    """
    Classify applicant metrics against current rules.
    
    Input:
    - dti: Debt-to-income ratio (0.0-1.0)
    - credit_score: Credit score (300-850)
    - lti: Loan-to-income ratio (0.0+)
    
    Returns classifications for each metric.
    """
    # DTI Classification
    if dti < settings.dti_favorable_max:
        dti_class = "FAVORABLE"
    elif dti < settings.dti_acceptable_max:
        dti_class = "ACCEPTABLE"
    elif dti < settings.dti_borderline_max:
        dti_class = "BORDERLINE"
    else:
        dti_class = "HIGH_RISK"
    
    # Credit Score Classification
    if credit_score >= settings.credit_excellent_min:
        credit_class = "EXCELLENT"
        credit_risk = "LOW"
    elif credit_score >= settings.credit_good_min:
        credit_class = "GOOD"
        credit_risk = "MODERATE"
    elif credit_score >= settings.credit_fair_min:
        credit_class = "FAIR"
        credit_risk = "MEDIUM"
    elif credit_score >= settings.credit_poor_min:
        credit_class = "POOR"
        credit_risk = "HIGH"
    else:
        credit_class = "VERY_POOR"
        credit_risk = "VERY_HIGH"
    
    # LTI Classification
    if lti < settings.lti_favorable_max:
        lti_class = "FAVORABLE"
    elif lti < settings.lti_acceptable_max:
        lti_class = "ACCEPTABLE"
    else:
        lti_class = "HIGH_RISK"
    
    return {
        "dti": {
            "value": dti,
            "classification": dti_class,
        },
        "credit_score": {
            "value": credit_score,
            "classification": credit_class,
            "risk_level": credit_risk,
        },
        "lti": {
            "value": lti,
            "classification": lti_class,
        },
    }


def run_server(host: str = "127.0.0.1", port: int = 8002):
    """Run the RiskRulesDB MCP server."""
    import uvicorn
    uvicorn.run("src.mcp_servers.risk_rules_db:mcp", host=host, port=port, reload=True)


if __name__ == "__main__":
    run_server()
