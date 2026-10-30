"""
Integration tests for LangGraph workflow.

Tests complete end-to-end application processing with all 4 agents.
Uses mocked agent responses for deterministic testing.
"""

import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import datetime

from src.orchestration.langgraph_workflow import (
    run_application,
    ApplicationState,
)
from src.utils.schemas import ApplicationData


@pytest.fixture
def sample_clear_approve():
    """Fixture: Clear approval case."""
    return {
        "applicant_id": "APP-CLEAR-APPROVE-1",
        "age": 45,
        "income": Decimal("120000"),
        "employment_type": "Salaried",
        "credit_score": 780,
        "loan_amount": Decimal("200000"),
        "tenure_months": 240,
        "existing_liabilities": Decimal("15000"),
        "location": "US",
    }


@pytest.fixture
def sample_clear_reject():
    """Fixture: Clear rejection case."""
    return {
        "applicant_id": "APP-CLEAR-REJECT-1",
        "age": 35,
        "income": Decimal("45000"),
        "employment_type": "Salaried",
        "credit_score": 520,
        "loan_amount": Decimal("250000"),
        "tenure_months": 360,
        "existing_liabilities": Decimal("40000"),
        "location": "US",
    }


@pytest.fixture
def sample_borderline():
    """Fixture: Borderline case requiring manual review."""
    return {
        "applicant_id": "APP-BORDERLINE-1",
        "age": 32,
        "income": Decimal("72000"),
        "employment_type": "Salaried",
        "credit_score": 710,
        "loan_amount": Decimal("150000"),
        "tenure_months": 180,
        "existing_liabilities": Decimal("18000"),
        "location": "US",
    }


@pytest.fixture
def sample_recent_job_change():
    """Fixture: Recent job change case."""
    return {
        "applicant_id": "APP-NEW-JOB-1",
        "age": 28,
        "income": Decimal("65000"),
        "employment_type": "Salaried",
        "credit_score": 720,
        "loan_amount": Decimal("120000"),
        "tenure_months": 120,
        "existing_liabilities": Decimal("8000"),
        "location": "US",
    }


@pytest.fixture
def sample_high_debt():
    """Fixture: High debt case."""
    return {
        "applicant_id": "APP-HIGH-DEBT-1",
        "age": 42,
        "income": Decimal("55000"),
        "employment_type": "Salaried",
        "credit_score": 650,
        "loan_amount": Decimal("200000"),
        "tenure_months": 240,
        "existing_liabilities": Decimal("35000"),
        "location": "US",
    }


def mock_profile_response_excellent():
    """Mock excellent profile response."""
    return {
        "income_stability_score": 90,
        "employment_risk": "LOW",
        "credit_summary": "Excellent employment history, 15+ years at current employer",
        "completeness_flags": [],
        "confidence": 0.95,
        "reasoning": "Very stable employment profile"
    }


def mock_profile_response_poor():
    """Mock poor profile response."""
    return {
        "income_stability_score": 30,
        "employment_risk": "HIGH",
        "credit_summary": "Unstable employment with recent gaps",
        "completeness_flags": ["Recent unemployment"],
        "confidence": 0.70,
        "reasoning": "Employment history shows significant instability"
    }


def mock_financial_response_low_risk():
    """Mock low financial risk response."""
    return {
        "dti": 0.28,
        "dti_classification": "FAVORABLE",
        "credit_score_risk": "LOW",
        "lti": 1.67,
        "loan_amount_risk": "FAVORABLE",
        "anomaly_detected": False,
        "anomaly_reasons": [],
        "risk_score": 18,
        "confidence": 0.93,
        "reasoning": "Strong financial metrics with excellent DTI and credit"
    }


def mock_financial_response_high_risk():
    """Mock high financial risk response."""
    return {
        "dti": 0.68,
        "dti_classification": "HIGH_RISK",
        "credit_score_risk": "VERY_HIGH",
        "lti": 4.44,
        "loan_amount_risk": "HIGH_RISK",
        "anomaly_detected": True,
        "anomaly_reasons": ["DTI exceeds 50%", "Credit score below 550"],
        "risk_score": 85,
        "confidence": 0.88,
        "reasoning": "Poor financial metrics indicate high risk"
    }


def test_workflow_clear_approval(sample_clear_approve):
    """Test workflow approves excellent applicant."""
    with patch("src.agents.applicant_profile_agent.ApplicantProfileAgent.analyze",
               return_value=mock_profile_response_excellent()):
        with patch("src.agents.financial_risk_agent.FinancialRiskAgent.analyze",
                   return_value=mock_financial_response_low_risk()):
            with patch("src.agents.loan_decision_agent.LoanDecisionAgent.analyze",
                       return_value={
                           "classification": "APPROVED",
                           "risk_score": 20,
                           "confidence": 0.92,
                           "decision_factors": [
                               {"factor": "Employment", "value": "Excellent", "impact": "PRIMARY"},
                               {"factor": "DTI", "value": "FAVORABLE", "impact": "PRIMARY"}
                           ],
                           "explanation": "Strong applicant with excellent metrics"
                       }):
                with patch("src.agents.compliance_agent.ComplianceAgent.analyze",
                           return_value={
                               "action_taken": "APPROVED",
                               "notification_status": "SENT",
                               "case_id": "CASE-2026-10-29-12345",
                               "timestamp": datetime.utcnow(),
                               "summary": "Application APPROVED"
                           }):
                    
                    result = run_application(sample_clear_approve)
    
    assert result["decision"] == "APPROVED"
    assert result["confidence"] >= 0.85
    assert result["risk_score"] <= 25
    assert "profile" in result["agents_run"]
    assert "financial" in result["agents_run"]
    assert "decision" in result["agents_run"]
    assert "compliance" in result["agents_run"]


def test_workflow_clear_rejection(sample_clear_reject):
    """Test workflow rejects poor applicant."""
    with patch("src.agents.applicant_profile_agent.ApplicantProfileAgent.analyze",
               return_value=mock_profile_response_poor()):
        with patch("src.agents.financial_risk_agent.FinancialRiskAgent.analyze",
                   return_value=mock_financial_response_high_risk()):
            with patch("src.agents.loan_decision_agent.LoanDecisionAgent.analyze",
                       return_value={
                           "classification": "REJECTED",
                           "risk_score": 82,
                           "confidence": 0.91,
                           "decision_factors": [
                               {"factor": "Credit Score", "value": "VERY_HIGH", "impact": "PRIMARY"},
                               {"factor": "DTI", "value": "HIGH_RISK", "impact": "PRIMARY"}
                           ],
                           "explanation": "Applicant does not meet lending criteria"
                       }):
                with patch("src.agents.compliance_agent.ComplianceAgent.analyze",
                           return_value={
                               "action_taken": "REJECTED",
                               "notification_status": "SENT",
                               "case_id": "CASE-2026-10-29-54321",
                               "timestamp": datetime.utcnow(),
                               "summary": "Application REJECTED"
                           }):
                    
                    result = run_application(sample_clear_reject)
    
    assert result["decision"] == "REJECTED"
    assert result["risk_score"] >= 75


def test_workflow_borderline_manual_review(sample_borderline):
    """Test workflow escalates borderline case to manual review."""
    with patch("src.agents.applicant_profile_agent.ApplicantProfileAgent.analyze",
               return_value={
                   "income_stability_score": 65,
                   "employment_risk": "MEDIUM",
                   "credit_summary": "Fair employment history",
                   "completeness_flags": [],
                   "confidence": 0.72,
                   "reasoning": "Moderate stability"
               }):
        with patch("src.agents.financial_risk_agent.FinancialRiskAgent.analyze",
                   return_value={
                       "dti": 0.38,
                       "dti_classification": "BORDERLINE",
                       "credit_score_risk": "MODERATE",
                       "lti": 2.08,
                       "loan_amount_risk": "ACCEPTABLE",
                       "anomaly_detected": False,
                       "anomaly_reasons": [],
                       "risk_score": 42,
                       "confidence": 0.74,
                       "reasoning": "Borderline metrics"
                   }):
            with patch("src.agents.loan_decision_agent.LoanDecisionAgent.analyze",
                       return_value={
                           "classification": "REQUIRES_REVIEW",
                           "risk_score": 45,
                           "confidence": 0.71,
                           "decision_factors": [
                               {"factor": "DTI", "value": "BORDERLINE", "impact": "PRIMARY"}
                           ],
                           "explanation": "Metrics are borderline"
                       }):
                
                result = run_application(sample_borderline)
    
    assert result["decision"] == "REQUIRES_REVIEW"
    assert result["confidence"] < 0.75
    assert "manual_review" in result["agents_run"]


def test_workflow_with_anomaly_detection(sample_high_debt):
    """Test workflow detects and escalates anomalies."""
    with patch("src.agents.applicant_profile_agent.ApplicantProfileAgent.analyze",
               return_value={
                   "income_stability_score": 50,
                   "employment_risk": "MEDIUM",
                   "credit_summary": "Moderate employment history",
                   "completeness_flags": [],
                   "confidence": 0.75,
                   "reasoning": "Normal profile"
               }):
        with patch("src.agents.financial_risk_agent.FinancialRiskAgent.analyze",
                   return_value={
                       "dti": 0.55,
                       "dti_classification": "HIGH_RISK",
                       "credit_score_risk": "HIGH",
                       "lti": 3.64,
                       "loan_amount_risk": "HIGH_RISK",
                       "anomaly_detected": True,
                       "anomaly_reasons": ["DTI exceeds 50%"],
                       "risk_score": 72,
                       "confidence": 0.82,
                       "reasoning": "Anomaly detected"
                   }):
            
            result = run_application(sample_high_debt)
    
    assert result["decision"] == "REQUIRES_REVIEW"
    assert "manual_review" in result["agents_run"]


def test_workflow_all_agents_run():
    """Test that all agents are invoked in normal flow."""
    app_data = {
        "applicant_id": "APP-ALL-AGENTS-1",
        "age": 38,
        "income": Decimal("95000"),
        "employment_type": "Salaried",
        "credit_score": 740,
        "loan_amount": Decimal("180000"),
        "tenure_months": 240,
        "existing_liabilities": Decimal("20000"),
        "location": "US",
    }
    
    with patch("src.agents.applicant_profile_agent.ApplicantProfileAgent.analyze",
               return_value=mock_profile_response_excellent()):
        with patch("src.agents.financial_risk_agent.FinancialRiskAgent.analyze",
                   return_value=mock_financial_response_low_risk()):
            with patch("src.agents.loan_decision_agent.LoanDecisionAgent.analyze",
                       return_value={
                           "classification": "APPROVED",
                           "risk_score": 25,
                           "confidence": 0.91,
                           "decision_factors": [],
                           "explanation": "Good fit"
                       }):
                with patch("src.agents.compliance_agent.ComplianceAgent.analyze",
                           return_value={
                               "action_taken": "APPROVED",
                               "notification_status": "SENT",
                               "case_id": "CASE-2026-10-29-99999",
                               "timestamp": datetime.utcnow(),
                               "summary": "Approved"
                           }):
                    
                    result = run_application(app_data)
    
    # Verify all agents ran
    assert "validate" in result["agents_run"]
    assert "profile" in result["agents_run"]
    assert "financial" in result["agents_run"]
    assert "decision" in result["agents_run"]
    assert "compliance" in result["agents_run"]
    
    # Verify result structure
    assert "trace_id" in result
    assert "decision" in result
    assert "confidence" in result
    assert "case_id" in result


def test_workflow_error_handling():
    """Test workflow handles agent errors gracefully."""
    app_data = {
        "applicant_id": "APP-ERROR-1",
        "age": 35,
        "income": Decimal("75000"),
        "employment_type": "Salaried",
        "credit_score": 700,
        "loan_amount": Decimal("150000"),
        "tenure_months": 180,
        "existing_liabilities": Decimal("15000"),
        "location": "US",
    }
    
    with patch("src.agents.applicant_profile_agent.ApplicantProfileAgent.analyze",
               return_value={"error": "MCP server unavailable"}):
        
        result = run_application(app_data)
    
    assert result["decision"] == "REQUIRES_REVIEW"
    assert "error" in result or result["decision"] == "REQUIRES_REVIEW"


def test_workflow_invalid_input():
    """Test workflow handles invalid input."""
    invalid_data = {
        "applicant_id": "APP-INVALID",
        # Missing required fields
    }
    
    result = run_application(invalid_data)
    
    # Should escalate to manual review
    assert result["decision"] == "REQUIRES_REVIEW"


__all__ = [
    "test_workflow_clear_approval",
    "test_workflow_clear_rejection",
    "test_workflow_borderline_manual_review",
    "test_workflow_with_anomaly_detection",
    "test_workflow_all_agents_run",
    "test_workflow_error_handling",
    "test_workflow_invalid_input",
]
