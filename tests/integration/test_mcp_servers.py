"""
Integration tests for MCP servers.

Tests each MCP server's tools by calling them with test data.
Requires database to be seeded with test data first.

Run: pytest tests/integration/test_mcp_servers.py -v
"""

import pytest
from decimal import Decimal
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Applicant, EmploymentHistory, CreditHistory, create_tables
from src.utils.config import settings
from src.mcp_servers.applicant_db import (
    get_applicant_history,
    get_employment_data,
    get_credit_inquiries,
)
from src.mcp_servers.risk_rules_db import (
    get_risk_thresholds,
    get_anomaly_rules,
    classify_by_rules,
)
from src.mcp_servers.decision_synthesis import (
    get_decision_policy,
    score_applicant,
)
from src.mcp_servers.notification_system import (
    send_notification,
    create_case,
    write_audit_log,
)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Setup test database."""
    # Use in-memory SQLite for testing
    test_db_url = "sqlite:///:memory:"
    
    # Create tables
    engine = create_engine(test_db_url)
    from src.database.models import Base
    Base.metadata.create_all(engine)
    
    # Seed test data
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # Create test applicant
    app = Applicant(
        id="APP-TEST-001",
        age=35,
        income=Decimal("85000"),
        employment_type="Salaried",
        credit_score=745,
        existing_liabilities=Decimal("12000"),
        location="US",
    )
    session.add(app)
    
    # Add employment
    emp = EmploymentHistory(
        applicant_id="APP-TEST-001",
        job_title="Software Engineer",
        company="Tech Corp",
        start_date=datetime.utcnow().replace(year=datetime.utcnow().year - 5),
        tenure_months=60,
    )
    session.add(emp)
    
    # Add credit inquiries
    credit = CreditHistory(
        applicant_id="APP-TEST-001",
        inquiry_date=datetime.utcnow(),
        inquiry_type="Soft",
        notes="Auto loan inquiry",
    )
    session.add(credit)
    
    session.commit()
    session.close()
    
    yield test_db_url
    
    # Cleanup
    engine.dispose()


class TestApplicantDBServer:
    """Test ApplicantDB MCP server tools."""
    
    def test_get_applicant_history(self):
        """Test getting applicant history."""
        result = get_applicant_history("APP-TEST-001")
        
        assert "applicant" in result
        assert result["applicant"]["id"] == "APP-TEST-001"
        assert result["applicant"]["credit_score"] == 745
        assert "employment_history" in result
        assert result["tenure_years"] == 5.0
    
    def test_get_employment_data(self):
        """Test getting employment data."""
        result = get_employment_data("APP-TEST-001")
        
        assert result["applicant_id"] == "APP-TEST-001"
        assert result["current_tenure_months"] == 60
        assert result["total_jobs"] == 1
        assert result["stability_score"] >= 100  # Max out at 100
        assert result["status"] == "STABLE"
    
    def test_get_credit_inquiries(self):
        """Test getting credit inquiries."""
        result = get_credit_inquiries("APP-TEST-001")
        
        assert result["applicant_id"] == "APP-TEST-001"
        assert len(result["inquiries"]) >= 1
        assert "Soft" in result["inquiry_types"]
    
    def test_nonexistent_applicant(self):
        """Test with nonexistent applicant."""
        result = get_applicant_history("NONEXISTENT")
        assert "error" in result


class TestRiskRulesDBServer:
    """Test RiskRulesDB MCP server tools."""
    
    def test_get_risk_thresholds(self):
        """Test getting risk thresholds."""
        result = get_risk_thresholds()
        
        assert "dti_favorable_max" in result
        assert "credit_excellent_min" in result
        assert "lti_favorable_max" in result
        assert result["dti_favorable_max"] == settings.dti_favorable_max
        assert result["credit_excellent_min"] == settings.credit_excellent_min
    
    def test_get_anomaly_rules(self):
        """Test getting anomaly rules."""
        result = get_anomaly_rules()
        
        assert "income_spike_threshold" in result
        assert "employment_gap_months_threshold" in result
        assert "credit_inquiries_3m_threshold" in result
        assert "rules" in result
        assert len(result["rules"]) > 0
    
    def test_classify_by_rules_excellent(self):
        """Test classifying excellent credit applicant."""
        result = classify_by_rules(
            dti=0.30,
            credit_score=780,
            lti=1.8,
        )
        
        assert result["dti"]["classification"] == "FAVORABLE"
        assert result["credit_score"]["classification"] == "EXCELLENT"
        assert result["credit_score"]["risk_level"] == "LOW"
        assert result["lti"]["classification"] == "FAVORABLE"
    
    def test_classify_by_rules_poor(self):
        """Test classifying poor credit applicant."""
        result = classify_by_rules(
            dti=0.65,
            credit_score=520,
            lti=5.0,
        )
        
        assert result["dti"]["classification"] == "HIGH_RISK"
        assert result["credit_score"]["classification"] == "VERY_POOR"
        assert result["credit_score"]["risk_level"] == "VERY_HIGH"
        assert result["lti"]["classification"] == "HIGH_RISK"


class TestDecisionSynthesisServer:
    """Test DecisionSynthesis MCP server tools."""
    
    def test_get_decision_policy(self):
        """Test getting decision policy."""
        result = get_decision_policy()
        
        assert "approval_criteria" in result
        assert "rejection_criteria" in result
        assert "manual_review_criteria" in result
        
        # Check structure
        assert "all_required" in result["approval_criteria"]
        assert "any_trigger" in result["rejection_criteria"]
        assert "any_trigger" in result["manual_review_criteria"]
    
    def test_score_applicant_low_risk(self):
        """Test scoring low-risk applicant."""
        result = score_applicant(
            credit_score=780,
            dti=0.30,
            lti=1.8,
            income_stability=90,
            employment_risk="LOW",
            anomaly_score=0.1,
        )
        
        assert "risk_score" in result
        assert result["risk_score"] <= 30  # Should be low risk
        assert "components" in result
        assert "weights" in result
        assert "interpretation" in result
    
    def test_score_applicant_high_risk(self):
        """Test scoring high-risk applicant."""
        result = score_applicant(
            credit_score=520,
            dti=0.65,
            lti=5.0,
            income_stability=20,
            employment_risk="HIGH",
            anomaly_score=0.8,
        )
        
        assert "risk_score" in result
        assert result["risk_score"] >= 80  # Should be high risk


class TestNotificationSystemServer:
    """Test NotificationSystem MCP server tools."""
    
    def test_create_case(self):
        """Test creating a case."""
        result = create_case(
            trace_id="trace-test-001",
            applicant_id="APP-TEST-001",
            decision="APPROVED",
        )
        
        assert "case_id" in result
        assert result["applicant_id"] == "APP-TEST-001"
        assert result["decision"] == "APPROVED"
        assert "created_at" in result
    
    def test_send_notification(self):
        """Test sending notification."""
        # Create case first
        case_result = create_case(
            trace_id="trace-test-002",
            applicant_id="APP-TEST-001",
            decision="APPROVED",
        )
        
        result = send_notification(
            applicant_id="APP-TEST-001",
            case_id=case_result["case_id"],
            notification_type="email",
            message="Your application has been approved.",
        )
        
        assert "status" in result
        assert "notification_id" in result
        assert result["applicant_id"] == "APP-TEST-001"
    
    def test_write_audit_log(self):
        """Test writing audit log."""
        # Create case first
        case_result = create_case(
            trace_id="trace-test-003",
            applicant_id="APP-TEST-001",
            decision="APPROVED",
        )
        
        result = write_audit_log(
            trace_id="trace-test-003",
            applicant_id="APP-TEST-001",
            case_id=case_result["case_id"],
            decision="APPROVED",
            risk_score=25,
            confidence=0.95,
            explanation="Excellent credit and low DTI.",
            agents_run='["profile_agent", "financial_agent", "decision_agent"]',
            decision_factors='[{"factor": "credit_score", "value": 780}]',
        )
        
        assert "audit_id" in result
        assert "status" in result
        assert result["status"] == "LOGGED"
        assert result["case_id"] == case_result["case_id"]


class TestMCPServerIntegration:
    """Integration tests with multiple servers."""
    
    def test_end_to_end_decision_flow(self):
        """Test complete flow: query -> assess risk -> score -> log."""
        # 1. Get applicant data
        app_history = get_applicant_history("APP-TEST-001")
        assert app_history["applicant"]["credit_score"] == 745
        
        # 2. Get thresholds
        thresholds = get_risk_thresholds()
        assert thresholds["dti_favorable_max"] == 0.36
        
        # 3. Classify by rules
        classification = classify_by_rules(
            dti=0.30,
            credit_score=745,
            lti=1.76,
        )
        assert classification["dti"]["classification"] == "FAVORABLE"
        
        # 4. Get decision policy
        policy = get_decision_policy()
        assert "approval_criteria" in policy
        
        # 5. Score applicant
        score = score_applicant(
            credit_score=745,
            dti=0.30,
            lti=1.76,
            income_stability=85,
            employment_risk="LOW",
            anomaly_score=0.1,
        )
        assert score["risk_score"] < 40
        
        # 6. Create case and log
        case = create_case(
            trace_id="trace-integration-001",
            applicant_id="APP-TEST-001",
            decision="APPROVED",
        )
        assert case["case_id"].startswith("CASE-")
        
        # 7. Send notification
        notif = send_notification(
            applicant_id="APP-TEST-001",
            case_id=case["case_id"],
            notification_type="email",
            message="You have been approved.",
        )
        assert notif["status"] in ["SENT", "PENDING"]
        
        # 8. Write audit log
        audit = write_audit_log(
            trace_id="trace-integration-001",
            applicant_id="APP-TEST-001",
            case_id=case["case_id"],
            decision="APPROVED",
            risk_score=int(score["risk_score"]),
            confidence=0.95,
            explanation="Strong profile.",
        )
        assert audit["status"] == "LOGGED"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
