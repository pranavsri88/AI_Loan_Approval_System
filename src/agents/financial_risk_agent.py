"""
Financial Risk Agent.

Analyzes applicant's financial metrics and risk profile.

Responsibilities:
1. Calculate DTI (debt-to-income ratio) and LTI (loan-to-income ratio)
2. Classify credit risk
3. Detect financial anomalies
4. Score overall financial risk
"""

from typing import Any, Dict
from decimal import Decimal

from src.agents.base_agent import BaseAgent
from src.agents.prompts import (
    FINANCIAL_RISK_SYSTEM_PROMPT,
    FINANCIAL_RISK_USER_PROMPT_TEMPLATE,
)
from src.utils.schemas import FinancialAnalysis
from src.utils.logger import get_logger
from src.mcp_clients.mcp_client import get_mcp_client

logger = get_logger(__name__)


class FinancialRiskAgent(BaseAgent):
    """
    Financial Risk Analysis Agent.
    
    Analyzes financial metrics to assess:
    - Debt-to-income ratio (DTI)
    - Loan-to-income ratio (LTI)
    - Credit score risk classification
    - Anomaly detection (income spikes, unusual patterns)
    - Composite financial risk score
    
    MCP Server: RiskRulesDB (port 8002)
    """
    
    agent_name = "FinancialRiskAgent"
    mcp_server_url = "http://127.0.0.1:8002"
    
    def analyze(self, applicant_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Analyze financial risk profile.
        
        Args:
            applicant_data: ApplicationData dict with income, liabilities, loan_amount, tenure_months
            **kwargs: Additional context
        
        Returns:
            Dictionary matching FinancialAnalysis schema
        """
        logger.info(f"Analyzing financial risk")
        
        try:
            # Step 1: Calculate DTI (deterministically in code)
            income = float(applicant_data.get("income", 0))
            liabilities = float(applicant_data.get("existing_liabilities", 0))
            loan_amount = float(applicant_data.get("loan_amount", 0))
            tenure_months = int(applicant_data.get("tenure_months", 12))
            credit_score = int(applicant_data.get("credit_score", 600))
            
            # DTI calculation: (monthly_debt / monthly_income)
            monthly_income = income / 12
            monthly_debt_current = liabilities / 12
            monthly_debt_new = (loan_amount / tenure_months)
            total_monthly_debt = monthly_debt_current + monthly_debt_new
            dti = total_monthly_debt / monthly_income if monthly_income > 0 else 1.0

            # Step 2: Calculate LTI (loan-to-income ratio)
            lti = loan_amount / income if income > 0 else 0.0

            # Step 3: Try to fetch risk thresholds from RiskRulesDB MCP
            mcp_client = get_mcp_client()
            dti_classification = "BORDERLINE"  # Default
            lti_classification = "MODERATE"    # Default
            credit_risk = "MEDIUM"              # Default

            try:
                # Fetch and use MCP thresholds if available
                thresholds = mcp_client.get_risk_thresholds()
                if thresholds:
                    dti_favorable = thresholds.get("dti_favorable_max", 0.36)
                    dti_acceptable = thresholds.get("dti_acceptable_max", 0.43)
                    dti_borderline = thresholds.get("dti_borderline_max", 0.50)
                    lti_favorable = thresholds.get("lti_favorable_max", 2.5)
                    lti_acceptable = thresholds.get("lti_acceptable_max", 4.0)
                    credit_excellent = thresholds.get("credit_excellent_min", 750)
                    credit_good = thresholds.get("credit_good_min", 700)
                    credit_fair = thresholds.get("credit_fair_min", 650)
                    credit_poor = thresholds.get("credit_poor_min", 550)
                    logger.info("[MCP] Fetched risk thresholds from RiskRulesDB")
                else:
                    logger.warning("[MCP] No response from RiskRulesDB, using defaults")
                    dti_favorable, dti_acceptable, dti_borderline = 0.36, 0.43, 0.50
                    lti_favorable, lti_acceptable = 2.5, 4.0
                    credit_excellent, credit_good, credit_fair, credit_poor = 750, 700, 650, 550
            except Exception as e:
                logger.warning(f"[MCP] RiskRulesDB unavailable, using hardcoded thresholds: {e}")
                dti_favorable, dti_acceptable, dti_borderline = 0.36, 0.43, 0.50
                lti_favorable, lti_acceptable = 2.5, 4.0
                credit_excellent, credit_good, credit_fair, credit_poor = 750, 700, 650, 550

            # Classify DTI using thresholds
            if dti < dti_favorable:
                dti_classification = "FAVORABLE"
            elif dti < dti_acceptable:
                dti_classification = "ACCEPTABLE"
            elif dti < dti_borderline:
                dti_classification = "BORDERLINE"
            else:
                dti_classification = "HIGH_RISK"

            # Classify LTI using thresholds
            if lti < lti_favorable:
                lti_classification = "LOW"
            elif lti < lti_acceptable:
                lti_classification = "MODERATE"
            else:
                lti_classification = "HIGH"

            # Classify credit score risk using thresholds
            if credit_score >= credit_excellent:
                credit_risk = "LOW"
            elif credit_score >= credit_good:
                credit_risk = "MODERATE"
            elif credit_score >= credit_fair:
                credit_risk = "MEDIUM"
            elif credit_score >= credit_poor:
                credit_risk = "HIGH"
            else:
                credit_risk = "VERY_HIGH"
            
            # Step 6: Check for anomalies (using RiskRulesDB if available)
            anomalies = []
            if dti > 0.50:
                anomalies.append("DTI exceeds 50%")
            if lti > 4.0:
                anomalies.append("LTI exceeds 4.0x")
            if credit_score < 550:
                anomalies.append("Credit score below 550")
            
            # Step 7: Invoke Claude for reasoning and final assessment
            logger.debug("Invoking Claude for financial risk assessment")
            user_prompt = FINANCIAL_RISK_USER_PROMPT_TEMPLATE.format(
                dti=dti,
                credit_score=credit_score,
                credit_classification=credit_risk,
                lti=lti,
                income=income,
                monthly_debt=total_monthly_debt,
                loan_amount=loan_amount,
                tenure_months=tenure_months,
                stability_score=kwargs.get("stability_score", 50),
                employment_risk=kwargs.get("employment_risk", "MEDIUM"),
                anomalies_detected=len(anomalies) > 0,
            )
            
            claude_response = self.invoke_claude(
                system_prompt=FINANCIAL_RISK_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                output_schema=FinancialAnalysis.schema(),
            )
            
            # Step 8: Validate and return
            financial_analysis = FinancialAnalysis(
                dti=dti,
                dti_classification=dti_classification,
                credit_score_risk=credit_risk,
                lti=lti,
                loan_amount_risk=lti_classification,
                anomaly_detected=len(anomalies) > 0,
                anomaly_reasons=anomalies,
                risk_score=claude_response.get("risk_score", 50),
                confidence=claude_response.get("confidence", 0.5),
                reasoning=claude_response.get("reasoning", ""),
            )
            
            logger.info(f"Financial risk analysis complete: {dti_classification} DTI, {credit_risk} credit")
            return financial_analysis.dict()
        
        except Exception as e:
            logger.error(f"Financial risk analysis failed: {str(e)}", exc_info=True)
            return {"error": str(e)}


__all__ = ["FinancialRiskAgent"]
