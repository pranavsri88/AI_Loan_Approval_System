"""
Smart Rules-Based Decision Engine for Demo Mode

Implements intelligent loan decision logic based on financial metrics and thresholds.
Used when AI agents are unavailable (no valid API key).
"""

from decimal import Decimal
from typing import Dict, Tuple
from src.utils.logger import get_logger

logger = get_logger(__name__)


def calculate_monthly_income(annual_income: float) -> float:
    """Calculate monthly income from annual income."""
    return annual_income / 12


def calculate_monthly_debt(existing_liabilities: float, loan_amount: float, tenure_months: int) -> float:
    """Calculate monthly debt obligation including new loan."""
    # Existing monthly liability (assume spread over typical period)
    existing_monthly = existing_liabilities / 60  # Assume 5-year average

    # New loan monthly payment (assuming 5% interest)
    monthly_interest_rate = 0.05 / 12
    if tenure_months > 0:
        monthly_loan_payment = loan_amount * (monthly_interest_rate * (1 + monthly_interest_rate) ** tenure_months) / (
            (1 + monthly_interest_rate) ** tenure_months - 1
        )
    else:
        monthly_loan_payment = 0

    return existing_monthly + monthly_loan_payment


def calculate_dti(monthly_debt: float, monthly_income: float) -> float:
    """
    Calculate Debt-to-Income ratio.

    DTI = (Monthly Debt / Monthly Income) * 100

    Returns: DTI as percentage (0-100+)
    """
    if monthly_income <= 0:
        return 100.0

    dti = (monthly_debt / monthly_income) * 100
    return min(dti, 150.0)  # Cap at 150%


def calculate_lti(loan_amount: float, monthly_income: float) -> float:
    """
    Calculate Loan-to-Income ratio.

    LTI = Loan Amount / (Monthly Income * 12)

    Returns: LTI as ratio (e.g., 2.5 means loan is 2.5x annual income)
    """
    annual_income = monthly_income * 12
    if annual_income <= 0:
        return 100.0

    lti = loan_amount / annual_income
    return min(lti, 20.0)  # Cap at 20x


def classify_credit_risk(credit_score: int) -> Tuple[str, float]:
    """
    Classify credit risk based on credit score.

    Returns: (risk_level, confidence_adjustment)
        risk_level: "EXCELLENT", "GOOD", "FAIR", "POOR", "VERY_POOR"
        confidence_adjustment: multiplier for base confidence
    """
    if credit_score >= 750:
        return "EXCELLENT", 1.2
    elif credit_score >= 700:
        return "GOOD", 1.0
    elif credit_score >= 650:
        return "FAIR", 0.8
    elif credit_score >= 600:
        return "POOR", 0.5
    else:
        return "VERY_POOR", 0.2


def classify_dti_level(dti: float) -> Tuple[str, int]:
    """
    Classify DTI level and return risk score impact.

    Returns: (dti_level, risk_score_impact)
    """
    if dti < 36:
        return "FAVORABLE", 20
    elif dti < 43:
        return "ACCEPTABLE", 35
    elif dti < 50:
        return "BORDERLINE", 50
    else:
        return "HIGH_RISK", 75


def classify_lti_level(lti: float) -> Tuple[str, int]:
    """
    Classify LTI level and return risk score impact.

    Returns: (lti_level, risk_score_impact)
    """
    if lti <= 2.5:
        return "FAVORABLE", 15
    elif lti <= 4.0:
        return "ACCEPTABLE", 30
    elif lti <= 5.0:
        return "BORDERLINE", 50
    else:
        return "HIGH_RISK", 70


def evaluate_employment_stability(employment_type: str, age: int) -> Tuple[float, int]:
    """
    Evaluate employment stability.

    Returns: (confidence_adjustment, risk_score_impact)
    """
    # Employment type stability
    employment_multiplier = {
        "Salaried": 1.0,
        "Self-Employed": 0.8,
        "Retired": 0.9,
        "Unemployed": 0.0,
    }.get(employment_type, 0.5)

    # Age factor (mid-career is most stable)
    if 30 <= age <= 55:
        age_multiplier = 1.0
    elif 25 <= age < 30 or 55 < age <= 65:
        age_multiplier = 0.9
    else:
        age_multiplier = 0.7

    confidence_adj = employment_multiplier * age_multiplier
    risk_impact = int(30 * (1 - confidence_adj))

    return confidence_adj, risk_impact


def make_intelligent_decision(applicant_data: Dict) -> Dict:
    """
    Make intelligent loan decision based on financial metrics.

    Args:
        applicant_data: Dictionary with applicant information

    Returns:
        Dictionary with decision, confidence, risk_score, explanation, factors
    """
    try:
        # Extract data
        age = applicant_data.get("age", 35)
        annual_income = applicant_data.get("income", 50000)
        credit_score = applicant_data.get("credit_score", 650)
        loan_amount = applicant_data.get("loan_amount", 150000)
        existing_liabilities = applicant_data.get("existing_liabilities", 20000)
        tenure_months = applicant_data.get("tenure_months", 180)
        employment_type = applicant_data.get("employment_type", "Salaried")

        logger.info(f"[RULES] Evaluating: income=${annual_income}, credit={credit_score}, loan=${loan_amount}")

        # Calculate metrics
        monthly_income = calculate_monthly_income(annual_income)
        monthly_debt = calculate_monthly_debt(existing_liabilities, loan_amount, tenure_months)
        dti = calculate_dti(monthly_debt, monthly_income)
        lti = calculate_lti(loan_amount, monthly_income)

        logger.info(f"[RULES] DTI={dti:.1f}%, LTI={lti:.2f}")

        # Classify factors
        credit_risk, credit_confidence = classify_credit_risk(credit_score)
        dti_level, dti_risk = classify_dti_level(dti)
        lti_level, lti_risk = classify_lti_level(lti)
        employment_conf, employment_risk = evaluate_employment_stability(employment_type, age)

        # Calculate base risk score
        risk_score = (dti_risk + lti_risk + employment_risk) // 3

        # Adjust based on credit score
        if credit_score >= 750:
            risk_score = max(0, risk_score - 15)  # Excellent credit reduces risk
        elif credit_score < 600:
            risk_score = min(100, risk_score + 20)  # Poor credit increases risk

        # Calculate confidence
        base_confidence = 0.7
        confidence = base_confidence * credit_confidence * employment_conf

        # Clamp confidence to 0.0-1.0
        confidence = min(1.0, max(0.0, confidence))

        # Make decision based on metrics
        decision = "REQUIRES_REVIEW"  # Default to safe choice

        # Strong APPROVAL: Good credit + Low DTI + Reasonable LTI + Low risk
        if (credit_score >= 700 and dti < 43 and lti <= 4.0 and risk_score < 40):
            decision = "APPROVED"
            confidence = min(1.0, confidence + 0.15)
            logger.info(f"[RULES] APPROVED: Strong financial profile")

        # Strong REJECTION: Bad credit + High DTI + High LTI + High risk
        elif (credit_score < 600 and dti > 50 and lti > 5.0) or (credit_score < 550):
            decision = "REJECTED"
            confidence = min(1.0, confidence + 0.10)
            risk_score = min(100, risk_score + 15)
            logger.info(f"[RULES] REJECTED: Poor financial profile")

        # REJECTION: Unemployed with high loan request
        elif employment_type == "Unemployed" and loan_amount > annual_income * 3:
            decision = "REJECTED"
            confidence = 0.9
            risk_score = 85
            logger.info(f"[RULES] REJECTED: Unemployed with excessive loan")

        # REQUIRES REVIEW: Borderline cases
        else:
            decision = "REQUIRES_REVIEW"
            logger.info(f"[RULES] REQUIRES_REVIEW: Borderline financial profile")

        # Prepare decision factors
        decision_factors = [
            {
                "factor": "Credit Score",
                "value": f"{credit_score} ({credit_risk})",
                "impact": f"Confidence adjustment: {credit_confidence:.0%}"
            },
            {
                "factor": "Debt-to-Income",
                "value": f"{dti:.1f}% ({dti_level})",
                "impact": f"Risk impact: +{dti_risk}"
            },
            {
                "factor": "Loan-to-Income",
                "value": f"{lti:.2f}x ({lti_level})",
                "impact": f"Risk impact: +{lti_risk}"
            },
            {
                "factor": "Employment",
                "value": f"{employment_type}",
                "impact": f"Stability: {employment_conf:.0%}"
            }
        ]

        # Prepare explanation
        if decision == "APPROVED":
            explanation = f"Strong financial profile: {credit_risk} credit ({credit_score}), favorable DTI ({dti:.1f}%), reasonable loan-to-income ratio ({lti:.2f}x). Applicant demonstrates strong ability to repay."
        elif decision == "REJECTED":
            explanation = f"Financial profile does not meet lending criteria: {credit_risk} credit ({credit_score}), high DTI ({dti:.1f}%), high loan-to-income ratio ({lti:.2f}x). Risk assessment indicates significant default risk."
        else:
            explanation = f"Application requires manual review: {credit_risk} credit ({credit_score}), DTI at {dti:.1f}%, LTI at {lti:.2f}x. Profile falls within borderline parameters."

        result = {
            "classification": decision,
            "decision": decision,
            "confidence": round(confidence, 2),
            "risk_score": min(100, max(0, risk_score)),
            "decision_factors": decision_factors,
            "explanation": explanation,
            "metrics": {
                "dti": round(dti, 1),
                "lti": round(lti, 2),
                "credit_score": credit_score,
                "employment_type": employment_type
            }
        }

        logger.info(f"[RULES] Decision: {decision} | Confidence: {confidence:.0%} | Risk: {risk_score}")
        return result

    except Exception as e:
        logger.error(f"[RULES] Decision logic failed: {str(e)}", exc_info=True)
        # Fallback to safe decision
        return {
            "classification": "REQUIRES_REVIEW",
            "decision": "REQUIRES_REVIEW",
            "confidence": 0.5,
            "risk_score": 60,
            "decision_factors": [{"factor": "Error", "value": "Logic evaluation error", "impact": "Manual review required"}],
            "explanation": "Application requires manual review due to system evaluation.",
        }


__all__ = [
    "calculate_dti",
    "calculate_lti",
    "classify_credit_risk",
    "make_intelligent_decision",
]
