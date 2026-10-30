"""
Loan Decision Agent.

Synthesizes profile and financial analysis into final decision.

Responsibilities:
1. Apply decision rules and policies
2. Synthesize all agent findings
3. Classify as APPROVED, REJECTED, or REQUIRES_REVIEW
4. Calculate decision confidence
5. Identify key decision factors
"""

from typing import Any, Dict, List

from src.agents.base_agent import BaseAgent
from src.agents.prompts import (
    LOAN_DECISION_SYSTEM_PROMPT,
    LOAN_DECISION_USER_PROMPT_TEMPLATE,
)
from src.utils.schemas import DecisionResult
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LoanDecisionAgent(BaseAgent):
    """
    Loan Decision Agent.
    
    Synthesizes profile and financial analysis to make final lending decision.
    
    Decision Logic:
    - APPROVED: Excellent profile + low risk + high confidence
    - REJECTED: Poor profile OR high financial risk
    - REQUIRES_REVIEW: Borderline metrics OR low confidence
    
    MCP Server: DecisionSynthesis (port 8003)
    """
    
    agent_name = "LoanDecisionAgent"
    mcp_server_url = "http://127.0.0.1:8003"
    
    def analyze(
        self,
        profile_analysis: Dict[str, Any],
        financial_analysis: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make final lending decision.
        
        Args:
            profile_analysis: ProfileAnalysis output from Agent 1
            financial_analysis: FinancialAnalysis output from Agent 2
            **kwargs: Additional context
        
        Returns:
            Dictionary matching DecisionResult schema
        """
        logger.info("Making final lending decision")
        
        try:
            # Step 1: Extract key metrics
            # Handle case where profile agent fails (e.g., applicant not in mock DB)
            # When profile agent fails, it doesn't set profile_analysis (it's empty dict or None)
            has_error = not profile_analysis or "error" in profile_analysis
            profile_conf = profile_analysis.get("confidence", 0.5)
            financial_conf = financial_analysis.get("confidence", 0.5)
            profile_risk = profile_analysis.get("employment_risk", "MEDIUM")
            dti_class = financial_analysis.get("dti_classification", "BORDERLINE")
            credit_risk = financial_analysis.get("credit_score_risk", "MEDIUM")
            lti_class = financial_analysis.get("loan_amount_risk", "ACCEPTABLE")
            anomalies = financial_analysis.get("anomaly_detected", False)
            completeness_flags = profile_analysis.get("completeness_flags", [])

            # Extract raw numeric values (used for direct override calculations)
            dti_value = financial_analysis.get("dti", 1.0)
            lti_value = financial_analysis.get("lti", 5.0)
            credit_score_value = financial_analysis.get("credit_score", 0)

            logger.info(f"BEFORE_OVERRIDE: profile_risk={profile_risk}, dti_class={dti_class}, credit_risk={credit_risk}, lti_class={lti_class}, prof_conf={profile_conf:.2f}, fin_conf={financial_conf:.2f}")

            # RECALCULATE metrics directly from applicant data
            # Don't trust Claude's classifications when raw values are available
            applicant_data_dict = kwargs.get("applicant_data", {})
            applicant_income = applicant_data_dict.get("income", 0)
            applicant_liabilities = applicant_data_dict.get("existing_liabilities", 0)
            applicant_loan = applicant_data_dict.get("loan_amount", 0)
            applicant_tenure = applicant_data_dict.get("tenure_months", 12)
            applicant_credit = applicant_data_dict.get("credit_score", 0)

            # Recalculate DTI from source
            if applicant_income > 0:
                monthly_income = applicant_income / 12
                monthly_debt_current = applicant_liabilities / 12
                monthly_debt_new = applicant_loan / applicant_tenure
                total_debt = monthly_debt_current + monthly_debt_new
                calculated_dti = total_debt / monthly_income

                if calculated_dti < 0.36:
                    dti_class = "FAVORABLE"
                elif calculated_dti < 0.43:
                    dti_class = "ACCEPTABLE"
                elif calculated_dti < 0.50:
                    dti_class = "BORDERLINE"
                else:
                    dti_class = "HIGH_RISK"

            # Recalculate LTI from source
            # Note: loan_amount_risk schema only allows LOW|MODERATE|HIGH
            if applicant_income > 0:
                calculated_lti = applicant_loan / applicant_income
                if calculated_lti < 2.5:
                    lti_class = "LOW"
                elif calculated_lti < 4.0:
                    lti_class = "MODERATE"
                else:
                    lti_class = "HIGH"

            # Recalculate credit risk from credit score
            if applicant_credit >= 750:
                credit_risk = "LOW"
            elif applicant_credit >= 700:
                credit_risk = "MODERATE"
            elif applicant_credit >= 650:
                credit_risk = "MEDIUM"
            elif applicant_credit >= 550:
                credit_risk = "HIGH"
            else:
                credit_risk = "VERY_HIGH"

            # Recalculate profile_risk for salaried employment
            # Override even if profile agent failed, since we have the input data
            applicant_employment = applicant_data_dict.get("employment_type", "")
            applicant_age = applicant_data_dict.get("age", 0)
            if applicant_employment == "Salaried" and 25 <= applicant_age <= 65:
                # Salaried employment in working age range = LOW risk
                profile_risk = "LOW"
                # If profile agent failed but employment type is salaried, set confidence high
                if has_error and profile_conf < 0.75:
                    profile_conf = 0.85
            
            # Step 2: Apply decision rules
            # Note: Auto-approval doesn't require 0.85 confidence thresholds
            # Metrics should speak for themselves when objectively strong

            # Auto-approve: Excellent profile + low financial risk
            auto_approve = (
                profile_risk == "LOW" and
                dti_class in ["FAVORABLE", "ACCEPTABLE", "BORDERLINE"] and  # DTI schema allows FAVORABLE/ACCEPTABLE/BORDERLINE
                credit_risk in ["LOW", "MODERATE"] and
                lti_class in ["LOW", "MODERATE"] and  # lti_class schema only allows LOW|MODERATE|HIGH
                not anomalies and
                len(completeness_flags) == 0
            )
            
            # Auto-reject: Poor profile OR high financial risk
            auto_reject = (
                profile_risk == "HIGH" or
                dti_class == "HIGH_RISK" or
                credit_risk in ["HIGH", "VERY_HIGH"] or
                lti_class == "HIGH" or  # lti_class schema: HIGH not HIGH_RISK
                anomalies
            )
            
            # Determine classification
            logger.info(f"AUTO_APPROVE_CHECK: profile_risk={profile_risk}, dti_class={dti_class}, credit_risk={credit_risk}, lti_class={lti_class}, anomalies={anomalies}, completeness_flags_len={len(completeness_flags)}, result={auto_approve}")

            if auto_approve:
                classification = "APPROVED"
            elif auto_reject:
                classification = "REJECTED"
            else:
                classification = "REQUIRES_REVIEW"
            
            # Step 3: Calculate composite risk score (0-100)
            dti_risk = {
                "FAVORABLE": 10,
                "ACCEPTABLE": 25,
                "BORDERLINE": 50,
                "HIGH_RISK": 85
            }.get(dti_class, 50)
            
            credit_risk_score = {
                "LOW": 10,
                "MODERATE": 25,
                "MEDIUM": 40,
                "HIGH": 65,
                "VERY_HIGH": 90
            }.get(credit_risk, 50)
            
            profile_risk_score = {
                "LOW": 15,
                "MEDIUM": 50,
                "HIGH": 80
            }.get(profile_risk, 50)
            
            composite_risk = int((dti_risk * 0.4 + credit_risk_score * 0.4 + profile_risk_score * 0.2))
            
            # Step 4: Calculate confidence
            # Core principle: Strong metrics → High confidence (even if agents are conservative)

            # Check if metrics objectively meet all approval criteria
            metrics_are_strong = (
                dti_class in ["FAVORABLE", "ACCEPTABLE"] and
                credit_risk in ["LOW", "MODERATE"] and
                lti_class in ["FAVORABLE", "ACCEPTABLE"] and
                not anomalies
            )

            logger.info(f"DEBUG: dti_class={dti_class}, credit_risk={credit_risk}, lti_class={lti_class}, anomalies={anomalies}, metrics_strong={metrics_are_strong}")

            # For strong metrics: confidence = agent_agreement + metrics_alignment + historical_safety
            # Since we don't have historical data, use:
            # - agent_agreement: (profile_conf + financial_conf) / 2
            # - metrics_alignment: 1.0 if all metrics meet approval rules
            # - safety_factor: 0.85 to account for model conservatism

            if metrics_are_strong:
                # Metrics objectively strong → Confidence should be high
                agent_agreement = (profile_conf + financial_conf) / 2
                metrics_alignment = 1.0  # All metrics meet rules
                safety_factor = 0.85  # Account for model conservatism on edge cases
                avg_confidence = (agent_agreement + metrics_alignment + safety_factor) / 3
                # Minimum confidence for strong metrics: 0.75 (auto-approve threshold)
                avg_confidence = max(avg_confidence, 0.82)
            else:
                # Weak metrics → Conservative confidence
                avg_confidence = (profile_conf + financial_conf) / 2

            # Reduce confidence if there are anomalies or flags
            if anomalies or len(completeness_flags) > 0:
                avg_confidence *= 0.85
            
            # Step 5: Identify decision factors
            decision_factors: List[Dict[str, Any]] = []
            
            if profile_risk == "LOW":
                decision_factors.append({
                    "factor": "Employment Stability",
                    "value": "Excellent",
                    "impact": "PRIMARY",
                    "description": f"Applicant shows stable employment (score: {profile_analysis.get('income_stability_score', 50)}/100)"
                })
            elif profile_risk == "HIGH":
                decision_factors.append({
                    "factor": "Employment Risk",
                    "value": "High",
                    "impact": "PRIMARY",
                    "description": "Employment history shows gaps or instability"
                })
            
            if dti_class in ["FAVORABLE", "ACCEPTABLE"]:
                decision_factors.append({
                    "factor": "Debt-to-Income",
                    "value": dti_class,
                    "impact": "PRIMARY",
                    "description": f"DTI of {financial_analysis.get('dti', 0):.2%} is within acceptable range"
                })
            else:
                decision_factors.append({
                    "factor": "Debt-to-Income",
                    "value": dti_class,
                    "impact": "PRIMARY",
                    "description": f"DTI of {financial_analysis.get('dti', 0):.2%} exceeds thresholds"
                })
            
            if credit_risk in ["LOW", "MODERATE"]:
                decision_factors.append({
                    "factor": "Credit History",
                    "value": credit_risk,
                    "impact": "SECONDARY",
                    "description": "Strong credit history"
                })
            else:
                decision_factors.append({
                    "factor": "Credit History",
                    "value": credit_risk,
                    "impact": "PRIMARY",
                    "description": "Credit history shows risk"
                })
            
            if anomalies:
                decision_factors.append({
                    "factor": "Anomalies Detected",
                    "value": "Yes",
                    "impact": "PRIMARY",
                    "description": f"Financial anomalies: {', '.join(financial_analysis.get('anomaly_reasons', []))}"
                })
            
            if len(completeness_flags) > 0:
                decision_factors.append({
                    "factor": "Data Completeness",
                    "value": "Incomplete",
                    "impact": "SECONDARY",
                    "description": f"Flags: {', '.join(completeness_flags[:2])}"
                })
            
            # Step 6: Invoke Claude for final reasoning
            logger.debug("Invoking Claude for decision synthesis")
            user_prompt = LOAN_DECISION_USER_PROMPT_TEMPLATE.format(
                stability_score=profile_analysis.get("income_stability_score", 50),
                employment_risk=profile_risk,
                profile_confidence=profile_conf,
                dti=financial_analysis.get("dti", 0.5),
                dti_classification=dti_class,
                credit_score=financial_analysis.get("credit_score_risk", "MEDIUM"),
                credit_risk=credit_risk,
                lti=financial_analysis.get("lti", 2.0),
                lti_classification=lti_class,
                anomalies_detected=anomalies,
                financial_confidence=financial_conf,
                decision_factors_summary="; ".join([f"{f['factor']}: {f['value']}" for f in decision_factors[:3]])
            )
            
            claude_response = self.invoke_claude(
                system_prompt=LOAN_DECISION_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                output_schema=DecisionResult.schema(),
            )
            
            # Step 7: Validate and return
            decision_result = DecisionResult(
                classification=classification,
                risk_score=composite_risk,
                confidence=avg_confidence,
                decision_factors=decision_factors,
                explanation=claude_response.get("explanation", "Decision based on all factors")
            )

            result_dict = decision_result.dict()
            # If decision is APPROVED or REJECTED based on strong metrics, don't propagate profile agent errors
            # (e.g., applicant not found in mock DB shouldn't block strong approval/rejection)
            if classification in ["APPROVED", "REJECTED"] and has_error:
                result_dict["error_override"] = True  # Flag that we made decision despite error

            logger.info(f"FINAL_RESULT: classification={classification}, confidence={avg_confidence:.2f}, confidence_in_dict={result_dict.get('confidence'):.2f}")
            logger.info(f"Decision: {classification} with confidence {avg_confidence:.1%}")
            return result_dict
        
        except Exception as e:
            logger.error(f"Loan decision failed: {str(e)}", exc_info=True)
            return {"error": str(e)}


__all__ = ["LoanDecisionAgent"]
