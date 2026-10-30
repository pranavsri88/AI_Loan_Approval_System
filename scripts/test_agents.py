#!/usr/bin/env python3
"""Manual end-to-end test of loan application workflow."""

from decimal import Decimal
from datetime import datetime
import uuid

from src.utils.schemas import ApplicationData
from src.orchestration.langgraph_workflow import create_workflow
from src.utils.logger import get_logger

logger = get_logger(__name__)


def test_loan_approval_workflow():
    """Test complete workflow with sample application."""
    logger.info("=" * 80)
    logger.info("END-TO-END WORKFLOW TEST")
    logger.info("=" * 80)
    
    # Create sample application data
    app_data = ApplicationData(
        applicant_id="APP-TEST-" + str(uuid.uuid4())[:8].upper(),
        age=35,
        income=Decimal("85000"),
        employment_type="Salaried",
        credit_score=760,
        loan_amount=Decimal("150000"),
        tenure_months=180,
        existing_liabilities=Decimal("12000"),
        location="US",
    )
    
    logger.info(f"Test Application: {app_data.applicant_id}")
    logger.info(f"  • Age: {app_data.age}")
    logger.info(f"  • Income: ${app_data.income:,.2f}")
    logger.info(f"  • Credit Score: {app_data.credit_score}")
    logger.info(f"  • Loan Amount: ${app_data.loan_amount:,.2f}")
    logger.info("")
    
    # Create workflow
    logger.info("Creating LangGraph workflow...")
    workflow = create_workflow()
    logger.info("✅ Workflow created")
    logger.info("")
    
    # Initialize state
    trace_id = f"trace-test-{str(uuid.uuid4())[:8]}"
    initial_state = {
        "applicant_data": app_data.dict(),
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
    
    # Execute workflow
    logger.info("Executing workflow...")
    logger.info("-" * 80)
    
    try:
        result = workflow.invoke(initial_state)
        
        logger.info("-" * 80)
        logger.info("")
        logger.info("🎉 WORKFLOW COMPLETE")
        logger.info("=" * 80)
        logger.info("RESULTS:")
        logger.info(f"  Trace ID: {result['trace_id']}")
        logger.info(f"  Case ID: {result['case_id']}")
        logger.info(f"  Decision: {result['final_decision']}")
        logger.info(f"  Confidence: {result['final_confidence']:.1%}")
        logger.info(f"  Risk Score: {result['decision_result'].get('risk_score', 'N/A')} / 100")
        logger.info(f"  Agents Executed: {' → '.join(result['agents_run'])}")
        logger.info("")
        logger.info("EXPLANATION:")
        logger.info(f"  {result['final_explanation']}")
        logger.info("=" * 80)
        logger.info("")
        
        # Print decision factors if available
        if result.get("decision_result"):
            factors = result["decision_result"].get("decision_factors", [])
            if factors:
                logger.info("DECISION FACTORS (ranked by impact):")
                for i, factor in enumerate(factors, 1):
                    logger.info(f"  {i}. {factor.get('factor', 'Unknown')}")
        
        logger.info("")
        logger.info("✅ TEST PASSED - Workflow executed successfully")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ TEST FAILED: {str(e)}", exc_info=True)
        logger.error("=" * 80)


if __name__ == "__main__":
    test_loan_approval_workflow()
