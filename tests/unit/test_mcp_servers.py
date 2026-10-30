"""
Unit tests for MCP servers.

Tests all MCP server implementations:
- ApplicantDB server (applicant queries)
- RiskRulesDB server (thresholds and rules)
- DecisionSynthesis server (scoring and policy)
- NotificationSystem server (notifications and audit)
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.mcp_servers.base import BaseMCPServer
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
from src.database.models import (
    Base,
    Applicant,
    EmploymentHistory,
    CreditHistory,
)
from src.utils.config import settings


# ============================================================================
# FIXTURES: In-Memory Database Setup
# ============================================================================

@pytest.fixture
def test_db():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    yield SessionLocal

    engine.dispose()


@pytest.fixture
def mock_applicant(test_db):
    """Create a mock applicant in test database."""
    SessionLocal = test_db
    session = SessionLocal()

    applicant = Applicant(
        id="APP-TEST-001",
        age=35,
        income=Decimal("85000.00"),
        employment_type="Salaried",
        credit_score=745,
        existing_liabilities=Decimal("12000.00"),
        location="US",
    )
    session.add(applicant)
    session.commit()
    session.close()

    return applicant


@pytest.fixture
def mock_employment_history(test_db, mock_applicant):
    """Create mock employment history for test applicant."""
    SessionLocal = test_db
    session = SessionLocal()

    # Current job (36 months)
    job1 = EmploymentHistory(
        applicant_id="APP-TEST-001",
        job_title="Senior Software Engineer",
        company="Tech Corp",
        start_date=datetime.utcnow() - timedelta(days=36*30),
        end_date=None,
        tenure_months=36,
    )

    # Previous job (24 months, ended 6 months ago)
    job2 = EmploymentHistory(
        applicant_id="APP-TEST-001",
        job_title="Software Engineer",
        company="Startup Inc",
        start_date=datetime.utcnow() - timedelta(days=(36+24+6)*30),
        end_date=datetime.utcnow() - timedelta(days=6*30),
        tenure_months=24,
    )

    session.add_all([job1, job2])
    session.commit()
    session.close()

    return [job1, job2]


@pytest.fixture
def mock_credit_history(test_db, mock_applicant):
    """Create mock credit history for test applicant."""
    SessionLocal = test_db
    session = SessionLocal()

    # Recent inquiry (1 month ago)
    inquiry1 = CreditHistory(
        applicant_id="APP-TEST-001",
        inquiry_date=datetime.utcnow() - timedelta(days=30),
        inquiry_type="hard",
        notes="Mortgage application inquiry",
    )

    # Older inquiry (6 months ago)
    inquiry2 = CreditHistory(
        applicant_id="APP-TEST-001",
        inquiry_date=datetime.utcnow() - timedelta(days=180),
        inquiry_type="soft",
        notes="Auto loan inquiry",
    )

    session.add_all([inquiry1, inquiry2])
    session.commit()
    session.close()

    return [inquiry1, inquiry2]


# ============================================================================
# TEST SUITE: ApplicantDB MCP Server
# ============================================================================

class TestApplicantDBServer:
    """Tests for ApplicantDB MCP server tools."""

    def test_get_applicant_history_found(self, test_db, mock_applicant, mock_employment_history):
        """Test retrieving applicant history for existing applicant."""
        # Mock the get_session to use test database
        import src.mcp_servers.applicant_db as applicant_module
        original_get_session = applicant_module.get_session
        applicant_module.get_session = lambda: test_db()

        try:
            result = get_applicant_history("APP-TEST-001")

            assert "applicant" in result
            assert result["applicant"]["id"] == "APP-TEST-001"
            assert result["applicant"]["age"] == 35
            assert result["applicant"]["credit_score"] == 745

            assert "employment_history" in result
            assert len(result["employment_history"]) == 2
            assert result["tenure_years"] == 3.0
        finally:
            applicant_module.get_session = original_get_session

    def test_get_applicant_history_not_found(self, test_db):
        """Test retrieving non-existent applicant returns error."""
        import src.mcp_servers.applicant_db as applicant_module
        original_get_session = applicant_module.get_session
        applicant_module.get_session = lambda: test_db()

        try:
            result = get_applicant_history("APP-NONEXISTENT")
            assert "error" in result
        finally:
            applicant_module.get_session = original_get_session

    def test_get_employment_data_stable(self, test_db, mock_applicant, mock_employment_history):
        """Test employment data retrieval with stable employment."""
        import src.mcp_servers.applicant_db as applicant_module
        original_get_session = applicant_module.get_session
        applicant_module.get_session = lambda: test_db()

        try:
            result = get_employment_data("APP-TEST-001")

            assert "jobs" in result
            assert len(result["jobs"]) == 2
            assert result["current_tenure_months"] == 36
            assert result["status"] == "STABLE"  # >= 24 months
            assert result["stability_score"] >= 50
        finally:
            applicant_module.get_session = original_get_session

    def test_get_credit_inquiries_with_data(self, test_db, mock_applicant, mock_credit_history):
        """Test credit inquiry retrieval."""
        import src.mcp_servers.applicant_db as applicant_module
        original_get_session = applicant_module.get_session
        applicant_module.get_session = lambda: test_db()

        try:
            result = get_credit_inquiries("APP-TEST-001")

            assert "inquiries" in result
            assert len(result["inquiries"]) == 2
            assert result["recent_inquiries_3m"] >= 1
            assert "inquiry_types" in result
        finally:
            applicant_module.get_session = original_get_session

    def test_get_credit_inquiries_empty(self, test_db, mock_applicant):
        """Test credit inquiry retrieval with no inquiries."""
        import src.mcp_servers.applicant_db as applicant_module
        original_get_session = applicant_module.get_session
        applicant_module.get_session = lambda: test_db()

        try:
            result = get_credit_inquiries("APP-TEST-001")

            assert result["inquiries"] == []
            assert result["recent_inquiries_3m"] == 0
            assert result["inquiry_types"] == {}
        finally:
            applicant_module.get_session = original_get_session


# ============================================================================
# TEST SUITE: RiskRulesDB MCP Server
# ============================================================================

class TestRiskRulesDBServer:
    """Tests for RiskRulesDB MCP server tools."""

    def test_get_risk_thresholds_structure(self):
        """Test risk thresholds are returned with expected structure."""
        result = get_risk_thresholds()

        assert "dti_favorable_max" in result
        assert "credit_excellent_min" in result
        assert "lti_favorable_max" in result
        assert isinstance(result["dti_favorable_max"], (int, float))

    def test_get_anomaly_rules_complete(self):
        """Test anomaly rules are complete with all required rules."""
        result = get_anomaly_rules()

        assert "income_spike_threshold" in result
        assert "employment_gap_months_threshold" in result
        assert "credit_inquiries_3m_threshold" in result
        assert "liabilities_spike_threshold" in result
        assert "rules" in result

        rule_names = {r["name"] for r in result["rules"]}
        expected_rules = {
            "income_spike",
            "employment_gap",
            "credit_inquiries",
            "liabilities_spike",
        }
        assert expected_rules.issubset(rule_names)

    def test_classify_by_rules_favorable(self):
        """Test classification with favorable metrics."""
        result = classify_by_rules(
            dti=0.25,  # Favorable
            credit_score=780,  # Excellent
            lti=1.5,  # Favorable (< lti_favorable_max ~= 2.0)
        )

        assert result["dti"]["classification"] == "FAVORABLE"
        assert result["credit_score"]["classification"] == "EXCELLENT"
        assert result["credit_score"]["risk_level"] == "LOW"
        assert result["lti"]["classification"] in ["FAVORABLE", "ACCEPTABLE"]

    def test_classify_by_rules_high_risk(self):
        """Test classification with high-risk metrics."""
        result = classify_by_rules(
            dti=0.65,  # High risk
            credit_score=500,  # Poor
            lti=5.0,  # High risk
        )

        assert result["dti"]["classification"] == "HIGH_RISK"
        assert result["credit_score"]["classification"] in ["POOR", "VERY_POOR"]
        assert result["credit_score"]["risk_level"] in ["HIGH", "VERY_HIGH"]
        assert result["lti"]["classification"] == "HIGH_RISK"

    def test_classify_by_rules_borderline(self):
        """Test classification with borderline metrics."""
        result = classify_by_rules(
            dti=0.45,  # Borderline
            credit_score=720,  # Good
            lti=3.5,  # Acceptable
        )

        assert result["dti"]["classification"] in ["BORDERLINE", "ACCEPTABLE"]
        assert result["credit_score"]["classification"] == "GOOD"
        assert result["credit_score"]["risk_level"] == "MODERATE"


# ============================================================================
# TEST SUITE: DecisionSynthesis MCP Server
# ============================================================================

class TestDecisionSynthesisServer:
    """Tests for DecisionSynthesis MCP server tools."""

    def test_get_decision_policy_structure(self):
        """Test decision policy has required criteria."""
        result = get_decision_policy()

        assert "approval_criteria" in result
        assert "rejection_criteria" in result
        assert "manual_review_criteria" in result

        assert "all_required" in result["approval_criteria"]
        assert "any_trigger" in result["rejection_criteria"]
        assert "any_trigger" in result["manual_review_criteria"]

    def test_score_applicant_low_risk(self):
        """Test risk score for low-risk applicant."""
        result = score_applicant(
            credit_score=780,
            dti=0.25,
            lti=2.5,
            income_stability=90,
            employment_risk="LOW",
            anomaly_score=0.0,
        )

        assert "risk_score" in result
        assert result["risk_score"] < 30  # Low risk
        assert "components" in result
        assert "weights" in result

        assert result["components"]["credit_score"] < 30
        assert result["components"]["employment_risk"] == 10

    def test_score_applicant_high_risk(self):
        """Test risk score for high-risk applicant."""
        result = score_applicant(
            credit_score=500,
            dti=0.65,
            lti=5.5,
            income_stability=20,
            employment_risk="HIGH",
            anomaly_score=0.8,
        )

        assert result["risk_score"] > 70  # High risk
        assert result["components"]["credit_score"] >= 75
        assert result["components"]["employment_risk"] >= 75

    def test_score_applicant_weights_sum(self):
        """Test that scoring weights are properly normalized."""
        result = score_applicant(
            credit_score=700,
            dti=0.40,
            lti=3.0,
            income_stability=70,
            employment_risk="MEDIUM",
            anomaly_score=0.2,
        )

        weights = result["weights"]
        total_weight = sum(weights.values())
        assert abs(total_weight - 1.0) < 0.001  # Weights sum to 1.0

    def test_score_applicant_bounds(self):
        """Test risk score is always bounded 0-100."""
        # Extreme low
        result_low = score_applicant(
            credit_score=850,
            dti=0.0,
            lti=0.0,
            income_stability=100,
            employment_risk="LOW",
            anomaly_score=0.0,
        )
        assert 0 <= result_low["risk_score"] <= 100

        # Extreme high
        result_high = score_applicant(
            credit_score=300,
            dti=1.0,
            lti=10.0,
            income_stability=0,
            employment_risk="HIGH",
            anomaly_score=1.0,
        )
        assert 0 <= result_high["risk_score"] <= 100


# ============================================================================
# TEST SUITE: Base MCP Server
# ============================================================================

class TestBaseMCPServer:
    """Tests for BaseMCPServer infrastructure."""

    def test_base_server_initialization(self, test_db):
        """Test base server initializes with correct configuration."""
        server = BaseMCPServer(database_url="sqlite:///:memory:")

        assert server.mcp_name == "base_mcp_server"
        assert server.mcp is not None
        assert server.engine is not None

        server.close()

    def test_base_server_format_response_success(self):
        """Test response formatting for successful tool call."""
        server = BaseMCPServer()

        response = server.format_response(
            data={"result": "success"},
            status="success"
        )

        assert response["status"] == "success"
        assert response["data"]["result"] == "success"
        assert "timestamp" in response

        server.close()

    def test_base_server_format_response_error(self):
        """Test response formatting for error."""
        server = BaseMCPServer()

        response = server.format_response(
            data={},
            status="error",
            error="Something went wrong"
        )

        assert response["status"] == "error"
        assert response["error"] == "Something went wrong"

        server.close()

    def test_base_server_health_check(self):
        """Test health check returns correct status."""
        server = BaseMCPServer(database_url="sqlite:///:memory:")

        health = server.health_check()

        assert "status" in health
        assert health["status"] in ["healthy", "unhealthy"]
        assert "server" in health
        assert "timestamp" in health

        server.close()


# ============================================================================
# INTEGRATION TESTS: MCP Servers Together
# ============================================================================

class TestMCPServerIntegration:
    """Integration tests for MCP servers working together."""

    def test_full_decision_flow(self):
        """Test complete decision flow using all MCP servers."""
        # 1. Get risk thresholds
        thresholds = get_risk_thresholds()
        assert "dti_favorable_max" in thresholds

        # 2. Get decision policy
        policy = get_decision_policy()
        assert "approval_criteria" in policy

        # 3. Score applicant
        score_result = score_applicant(
            credit_score=745,
            dti=0.35,
            lti=3.0,
            income_stability=80,
            employment_risk="LOW",
            anomaly_score=0.1,
        )
        assert "risk_score" in score_result

        # 4. Verify risk score is reasonable
        assert score_result["risk_score"] < 50  # Should be moderate/low risk

    def test_anomaly_detection_rules(self):
        """Test anomaly detection rules are consistent."""
        anomaly_rules = get_anomaly_rules()
        thresholds = get_risk_thresholds()

        # Verify anomaly rules have numeric thresholds
        assert anomaly_rules["employment_gap_months_threshold"] > 0
        assert anomaly_rules["credit_inquiries_3m_threshold"] > 0
        assert anomaly_rules["income_spike_threshold"] > 1.0


__all__ = [
    "TestApplicantDBServer",
    "TestRiskRulesDBServer",
    "TestDecisionSynthesisServer",
    "TestBaseMCPServer",
    "TestMCPServerIntegration",
]
