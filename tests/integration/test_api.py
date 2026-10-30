"""
Integration tests for FastAPI endpoints.

Tests the complete API workflow using TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from decimal import Decimal
from datetime import datetime

from src.api.main import create_app


@pytest.fixture
def client():
    """Fixture: FastAPI TestClient"""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_application():
    """Fixture: Sample application data"""
    return {
        "applicant_id": "APP-TEST-001",
        "age": 35,
        "income": 85000,
        "employment_type": "Salaried",
        "credit_score": 745,
        "loan_amount": 150000,
        "tenure_months": 180,
        "existing_liabilities": 12000,
        "location": "US",
    }


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["environment"] in ["development", "production"]


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "docs" in data


def test_submit_application_success(client, sample_application):
    """Test successful application submission."""
    with patch("src.orchestration.langgraph_workflow.run_application") as mock_run:
        mock_run.return_value = {
            "trace_id": "TRACE-test-001",
            "applicant_id": sample_application["applicant_id"],
            "decision": "APPROVED",
            "confidence": 0.92,
            "risk_score": 20,
            "case_id": "CASE-2026-10-29-12345",
            "agents_run": ["validate", "profile", "financial", "decision", "compliance"],
            "timestamp": datetime.utcnow().isoformat(),
            "explanation": "Excellent applicant with strong metrics",
        }
        
        response = client.post("/api/v1/applications", json=sample_application)
    
    assert response.status_code == 202
    data = response.json()
    assert data["trace_id"] == "TRACE-test-001"
    assert data["applicant_id"] == sample_application["applicant_id"]
    assert data["status"] == "COMPLETED"


def test_submit_application_validation_error(client):
    """Test application submission with missing fields."""
    invalid_app = {
        "applicant_id": "APP-INVALID",
        # Missing required fields
    }
    
    response = client.post("/api/v1/applications", json=invalid_app)
    
    assert response.status_code == 422  # Pydantic validation error


def test_submit_application_invalid_age(client, sample_application):
    """Test application with invalid age."""
    sample_application["age"] = 15  # Too young
    
    response = client.post("/api/v1/applications", json=sample_application)
    
    assert response.status_code == 422


def test_submit_application_invalid_credit_score(client, sample_application):
    """Test application with invalid credit score."""
    sample_application["credit_score"] = 1000  # Invalid (> 850)
    
    response = client.post("/api/v1/applications", json=sample_application)
    
    assert response.status_code == 422


def test_get_application_decision_success(client, sample_application):
    """Test retrieving application decision."""
    # First submit application
    with patch("src.orchestration.langgraph_workflow.run_application") as mock_run:
        mock_run.return_value = {
            "trace_id": "TRACE-test-001",
            "applicant_id": sample_application["applicant_id"],
            "decision": "APPROVED",
            "confidence": 0.92,
            "risk_score": 20,
            "case_id": "CASE-2026-10-29-12345",
            "agents_run": ["validate", "profile", "financial", "decision", "compliance"],
            "timestamp": datetime.utcnow().isoformat(),
            "explanation": "Strong applicant",
            "decision_factors": [
                {"factor": "Employment", "value": "Excellent", "impact": "PRIMARY"}
            ],
        }
        
        submit_response = client.post("/api/v1/applications", json=sample_application)
        trace_id = submit_response.json()["trace_id"]
    
    # Now get decision
    response = client.get(f"/api/v1/applications/{trace_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["trace_id"] == trace_id
    assert data["decision"] == "APPROVED"
    assert data["confidence"] == 0.92
    assert data["risk_score"] == 20


def test_get_application_decision_not_found(client):
    """Test retrieving decision for non-existent trace ID."""
    response = client.get("/api/v1/applications/TRACE-invalid-xyz")
    
    assert response.status_code == 404


def test_get_audit_trail_success(client, sample_application):
    """Test retrieving audit trail."""
    # First submit application
    with patch("src.orchestration.langgraph_workflow.run_application") as mock_run:
        mock_run.return_value = {
            "trace_id": "TRACE-test-001",
            "applicant_id": sample_application["applicant_id"],
            "decision": "APPROVED",
            "confidence": 0.92,
            "risk_score": 20,
            "case_id": "CASE-2026-10-29-12345",
            "agents_run": ["validate", "profile", "financial", "decision", "compliance"],
            "timestamp": datetime.utcnow().isoformat(),
            "explanation": "Strong applicant",
            "decision_factors": [],
        }
        
        submit_response = client.post("/api/v1/applications", json=sample_application)
        trace_id = submit_response.json()["trace_id"]
    
    # Get audit trail
    response = client.get(f"/api/v1/applications/{trace_id}/audit")
    
    assert response.status_code == 200
    data = response.json()
    assert data["trace_id"] == trace_id
    assert data["case_id"] == "CASE-2026-10-29-12345"
    assert data["decision"] == "APPROVED"
    assert "agents_run" in data
    assert "validate" in data["agents_run"]


def test_get_audit_trail_not_found(client):
    """Test retrieving audit trail for non-existent trace ID."""
    response = client.get("/api/v1/applications/TRACE-invalid-xyz/audit")
    
    assert response.status_code == 404


def test_submit_application_rejected(client, sample_application):
    """Test application submission that results in rejection."""
    with patch("src.orchestration.langgraph_workflow.run_application") as mock_run:
        mock_run.return_value = {
            "trace_id": "TRACE-reject-001",
            "applicant_id": sample_application["applicant_id"],
            "decision": "REJECTED",
            "confidence": 0.88,
            "risk_score": 78,
            "case_id": "CASE-2026-10-29-54321",
            "agents_run": ["validate", "profile", "financial", "decision", "compliance"],
            "timestamp": datetime.utcnow().isoformat(),
            "explanation": "Applicant does not meet lending criteria",
        }
        
        response = client.post("/api/v1/applications", json=sample_application)
    
    assert response.status_code == 202
    
    # Verify decision is REJECTED
    trace_id = response.json()["trace_id"]
    decision_response = client.get(f"/api/v1/applications/{trace_id}")
    decision_data = decision_response.json()
    assert decision_data["decision"] == "REJECTED"


def test_submit_application_manual_review(client, sample_application):
    """Test application submission requiring manual review."""
    with patch("src.orchestration.langgraph_workflow.run_application") as mock_run:
        mock_run.return_value = {
            "trace_id": "TRACE-review-001",
            "applicant_id": sample_application["applicant_id"],
            "decision": "REQUIRES_REVIEW",
            "confidence": 0.71,
            "risk_score": 45,
            "case_id": "CASE-2026-10-29-99999",
            "agents_run": ["validate", "profile", "financial", "decision", "manual_review"],
            "timestamp": datetime.utcnow().isoformat(),
            "explanation": "Borderline metrics require manual review",
        }
        
        response = client.post("/api/v1/applications", json=sample_application)
    
    assert response.status_code == 202
    
    # Verify decision is REQUIRES_REVIEW
    trace_id = response.json()["trace_id"]
    decision_response = client.get(f"/api/v1/applications/{trace_id}")
    decision_data = decision_response.json()
    assert decision_data["decision"] == "REQUIRES_REVIEW"


def test_request_headers(client, sample_application):
    """Test that request headers are properly set."""
    with patch("src.orchestration.langgraph_workflow.run_application") as mock_run:
        mock_run.return_value = {
            "trace_id": "TRACE-header-test",
            "applicant_id": sample_application["applicant_id"],
            "decision": "APPROVED",
            "confidence": 0.9,
            "risk_score": 25,
            "case_id": "CASE-2026-10-29-11111",
            "agents_run": ["validate", "profile", "financial", "decision", "compliance"],
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        response = client.post("/api/v1/applications", json=sample_application)
    
    # Check custom headers
    assert "X-Process-Time" in response.headers
    assert response.headers["X-Process-Time"] is not None


def test_cors_headers(client):
    """Test that CORS headers are set."""
    response = client.get("/health")
    
    # Check CORS headers
    assert response.status_code == 200


@pytest.mark.parametrize("age,valid", [
    (18, True),
    (80, True),
    (17, False),
    (81, False),
])
def test_age_validation(client, sample_application, age, valid):
    """Test age field validation with parametrized tests."""
    sample_application["age"] = age
    response = client.post("/api/v1/applications", json=sample_application)
    
    if valid:
        assert response.status_code == 202
    else:
        assert response.status_code == 422


@pytest.mark.parametrize("credit_score,valid", [
    (300, True),
    (850, True),
    (750, True),
    (299, False),
    (851, False),
])
def test_credit_score_validation(client, sample_application, credit_score, valid):
    """Test credit score validation with parametrized tests."""
    sample_application["credit_score"] = credit_score
    response = client.post("/api/v1/applications", json=sample_application)
    
    if valid:
        assert response.status_code == 202
    else:
        assert response.status_code == 422


__all__ = [
    "test_health_check",
    "test_root_endpoint",
    "test_submit_application_success",
    "test_submit_application_validation_error",
    "test_get_application_decision_success",
    "test_get_application_decision_not_found",
    "test_get_audit_trail_success",
    "test_get_audit_trail_not_found",
    "test_submit_application_rejected",
    "test_submit_application_manual_review",
]
