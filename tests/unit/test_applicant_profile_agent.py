"""
Unit tests for Applicant Profile Agent.

Tests agent with mocked MCP server responses and Claude responses.
"""

import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import datetime

from src.agents.applicant_profile_agent import ApplicantProfileAgent
from src.utils.schemas import ApplicationData, ProfileAnalysis


@pytest.fixture
def agent():
    """Fixture: Create ApplicantProfileAgent instance."""
    return ApplicantProfileAgent()


@pytest.fixture
def sample_applicant_data():
    """Fixture: Sample application data for testing."""
    return ApplicationData(
        applicant_id="APP-STABLE-001",
        age=35,
        income=Decimal("85000"),
        employment_type="Salaried",
        credit_score=745,
        loan_amount=Decimal("150000"),
        tenure_months=180,
        existing_liabilities=Decimal("12000"),
        location="US",
        timestamp=datetime.utcnow()
    )


@pytest.fixture
def mock_applicant_history():
    """Fixture: Mocked applicant history from ApplicantDB."""
    return {
        "applicant": {
            "id": "APP-STABLE-001",
            "age": 35,
            "income": 85000.00,
            "employment_type": "Salaried",
            "credit_score": 745,
            "liabilities": 12000.00,
            "location": "US"
        },
        "history_years": 7
    }


@pytest.fixture
def mock_employment_data_stable():
    """Fixture: Mocked employment data for stable employment."""
    return {
        "jobs": [
            {
                "title": "Senior Software Engineer",
                "company": "Tech Corp",
                "start_date": "2019-01-15",
                "end_date": None,
                "duration_months": 72
            },
            {
                "title": "Software Engineer",
                "company": "StartUp Inc",
                "start_date": "2018-06-01",
                "end_date": "2019-01-01",
                "duration_months": 7
            }
        ],
        "stability_score": 85,
        "total_years_employed": 6.5,
        "gaps": []
    }


@pytest.fixture
def mock_credit_inquiries():
    """Fixture: Mocked credit inquiries."""
    return {
        "inquiries": [
            {"date": "2026-03-15", "type": "Hard", "reason": "Mortgage Application"},
            {"date": "2025-09-20", "type": "Soft", "reason": "Credit Card Pre-approval"},
            {"date": "2025-01-10", "type": "Hard", "reason": "Auto Loan"}
        ],
        "recent_inquiries_3m": 0,
        "recent_inquiries_6m": 1,
        "anomaly_flags": []
    }


@pytest.fixture
def mock_claude_response_stable():
    """Fixture: Mocked Claude response for stable profile."""
    return {
        "income_stability_score": 85,
        "employment_risk": "LOW",
        "credit_summary": "Good credit history with 6+ years at current employer. No recent hard inquiries in 3 months.",
        "completeness_flags": [],
        "confidence": 0.92,
        "reasoning": "Applicant shows stable long-term employment at current position and consistent income. Credit profile clean."
    }


def test_applicant_profile_agent_stable_employment(agent, mock_applicant_history, 
                                                    mock_employment_data_stable, 
                                                    mock_credit_inquiries,
                                                    mock_claude_response_stable):
    """Test agent analyzes stable employment profile correctly."""
    with patch("src.agents.applicant_profile_agent.get_applicant_history", 
               return_value=mock_applicant_history):
        with patch("src.agents.applicant_profile_agent.get_employment_data", 
                   return_value=mock_employment_data_stable):
            with patch("src.agents.applicant_profile_agent.get_credit_inquiries", 
                       return_value=mock_credit_inquiries):
                with patch.object(agent, "invoke_claude", 
                                 return_value=mock_claude_response_stable):
                    result = agent.analyze("APP-STABLE-001")
    
    assert result["income_stability_score"] >= 80
    assert result["employment_risk"] == "LOW"
    assert result["confidence"] >= 0.9
    assert len(result["completeness_flags"]) == 0


def test_applicant_profile_agent_employment_gap():
    """Test agent detects employment gap anomaly."""
    agent = ApplicantProfileAgent()
    
    mock_history = {
        "applicant": {
            "id": "APP-GAP-001",
            "age": 42,
            "income": 75000.00,
            "employment_type": "Salaried",
            "credit_score": 710,
            "liabilities": 25000.00,
            "location": "US"
        }
    }
    
    mock_employment_gap = {
        "jobs": [
            {
                "title": "Manager",
                "company": "Company A",
                "start_date": "2024-06-01",
                "end_date": None,
                "duration_months": 16
            },
            {
                "title": "Engineer",
                "company": "Company B",
                "start_date": "2022-01-15",
                "end_date": "2023-01-15",
                "duration_months": 12
            }
        ],
        "stability_score": 55,
        "gaps": [
            {"start": "2023-01-15", "end": "2024-06-01", "months": 17}
        ]
    }
    
    mock_credit = {
        "inquiries": [],
        "recent_inquiries_3m": 0,
        "anomaly_flags": []
    }
    
    mock_claude_response = {
        "income_stability_score": 55,
        "employment_risk": "MEDIUM",
        "credit_summary": "Recent job change with 17-month employment gap detected.",
        "completeness_flags": ["Employment gap: 17 months between positions"],
        "confidence": 0.78,
        "reasoning": "Applicant changed jobs recently after 17-month gap. Income stability uncertain."
    }
    
    with patch("src.agents.applicant_profile_agent.get_applicant_history", 
               return_value=mock_history):
        with patch("src.agents.applicant_profile_agent.get_employment_data", 
                   return_value=mock_employment_gap):
            with patch("src.agents.applicant_profile_agent.get_credit_inquiries", 
                       return_value=mock_credit):
                with patch.object(agent, "invoke_claude", 
                                 return_value=mock_claude_response):
                    result = agent.analyze("APP-GAP-001")
    
    assert result["employment_risk"] in ["MEDIUM", "HIGH"]
    assert any("gap" in flag.lower() for flag in result["completeness_flags"])


def test_applicant_profile_agent_recent_job_change():
    """Test agent handles recent job change."""
    agent = ApplicantProfileAgent()
    
    mock_history = {
        "applicant": {
            "id": "APP-NEW-JOB-001",
            "age": 28,
            "income": 65000.00,
            "employment_type": "Salaried",
            "credit_score": 720,
            "liabilities": 8000.00,
            "location": "US"
        }
    }
    
    mock_employment = {
        "jobs": [
            {
                "title": "Junior Developer",
                "company": "Tech Startup",
                "start_date": "2026-08-01",
                "end_date": None,
                "duration_months": 3
            },
            {
                "title": "Developer",
                "company": "Old Company",
                "start_date": "2024-06-01",
                "end_date": "2026-07-31",
                "duration_months": 25
            }
        ],
        "stability_score": 40,
        "gaps": []
    }
    
    mock_credit = {
        "inquiries": [],
        "recent_inquiries_3m": 0,
        "anomaly_flags": []
    }
    
    mock_claude_response = {
        "income_stability_score": 45,
        "employment_risk": "MEDIUM",
        "credit_summary": "Recently changed jobs (3 months at new position). Previous employment stable.",
        "completeness_flags": ["Recently employed (3 months at current position)"],
        "confidence": 0.75,
        "reasoning": "Recent job change reduces stability assessment. Need to monitor income consistency."
    }
    
    with patch("src.agents.applicant_profile_agent.get_applicant_history", 
               return_value=mock_history):
        with patch("src.agents.applicant_profile_agent.get_employment_data", 
                   return_value=mock_employment):
            with patch("src.agents.applicant_profile_agent.get_credit_inquiries", 
                       return_value=mock_credit):
                with patch.object(agent, "invoke_claude", 
                                 return_value=mock_claude_response):
                    result = agent.analyze("APP-NEW-JOB-001")
    
    assert result["income_stability_score"] < 60
    assert result["employment_risk"] == "MEDIUM"
    assert any("recent" in flag.lower() for flag in result["completeness_flags"])


def test_applicant_profile_agent_high_credit_inquiries():
    """Test agent flags high credit inquiry activity."""
    agent = ApplicantProfileAgent()
    
    mock_history = {
        "applicant": {
            "id": "APP-INQUIRY-001",
            "age": 32,
            "income": 72000.00,
            "employment_type": "Salaried",
            "credit_score": 680,
            "liabilities": 35000.00,
            "location": "US"
        }
    }
    
    mock_employment = {
        "jobs": [
            {
                "title": "Accountant",
                "company": "Finance Corp",
                "start_date": "2020-03-01",
                "end_date": None,
                "duration_months": 67
            }
        ],
        "stability_score": 75,
        "gaps": []
    }
    
    mock_credit = {
        "inquiries": [
            {"date": "2026-10-15", "type": "Hard", "reason": "Credit Card"},
            {"date": "2026-10-10", "type": "Hard", "reason": "Personal Loan"},
            {"date": "2026-10-01", "type": "Hard", "reason": "Auto Loan"}
        ],
        "recent_inquiries_3m": 3,
        "recent_inquiries_6m": 5,
        "anomaly_flags": ["Multiple hard inquiries in short period"]
    }
    
    mock_claude_response = {
        "income_stability_score": 70,
        "employment_risk": "LOW",
        "credit_summary": "Stable employment but recent credit-seeking behavior flagged. 3 hard inquiries in past month.",
        "completeness_flags": ["Multiple credit inquiries: 3 hard inquiries in last 30 days"],
        "confidence": 0.72,
        "reasoning": "Employment stable but recent credit-seeking activity suggests financial pressure."
    }
    
    with patch("src.agents.applicant_profile_agent.get_applicant_history", 
               return_value=mock_history):
        with patch("src.agents.applicant_profile_agent.get_employment_data", 
                   return_value=mock_employment):
            with patch("src.agents.applicant_profile_agent.get_credit_inquiries", 
                       return_value=mock_credit):
                with patch.object(agent, "invoke_claude", 
                                 return_value=mock_claude_response):
                    result = agent.analyze("APP-INQUIRY-001")
    
    assert len(result["completeness_flags"]) > 0
    assert any("inquir" in flag.lower() for flag in result["completeness_flags"])


def test_applicant_profile_agent_missing_employment_history():
    """Test agent handles missing employment history."""
    agent = ApplicantProfileAgent()
    
    mock_history = {
        "applicant": {
            "id": "APP-NO-HISTORY-001",
            "age": 22,
            "income": 35000.00,
            "employment_type": "Salaried",
            "credit_score": 620,
            "liabilities": 5000.00,
            "location": "US"
        }
    }
    
    mock_employment = {
        "jobs": [],
        "stability_score": 0,
        "gaps": []
    }
    
    mock_credit = {
        "inquiries": [],
        "recent_inquiries_3m": 0,
        "anomaly_flags": []
    }
    
    mock_claude_response = {
        "income_stability_score": 25,
        "employment_risk": "HIGH",
        "credit_summary": "No employment history found. Insufficient data for stability assessment.",
        "completeness_flags": ["No employment history available", "Young applicant with limited work history"],
        "confidence": 0.60,
        "reasoning": "Insufficient employment history to assess income stability. High risk due to lack of data."
    }
    
    with patch("src.agents.applicant_profile_agent.get_applicant_history", 
               return_value=mock_history):
        with patch("src.agents.applicant_profile_agent.get_employment_data", 
                   return_value=mock_employment):
            with patch("src.agents.applicant_profile_agent.get_credit_inquiries", 
                       return_value=mock_credit):
                with patch.object(agent, "invoke_claude", 
                                 return_value=mock_claude_response):
                    result = agent.analyze("APP-NO-HISTORY-001")
    
    assert result["income_stability_score"] < 50
    assert result["employment_risk"] == "HIGH"
    assert len(result["completeness_flags"]) >= 2


def test_applicant_profile_agent_mcp_error():
    """Test agent handles MCP server error gracefully."""
    agent = ApplicantProfileAgent()
    
    mock_error = {"error": "Applicant not found"}
    
    with patch("src.agents.applicant_profile_agent.get_applicant_history", 
               return_value=mock_error):
        result = agent.analyze("APP-INVALID-ID")
    
    assert "error" in result


def test_applicant_profile_agent_output_schema_validation():
    """Test agent output validates against ProfileAnalysis schema."""
    agent = ApplicantProfileAgent()
    
    mock_history = {
        "applicant": {
            "id": "APP-SCHEMA-001",
            "age": 40,
            "income": 95000.00,
            "employment_type": "Self-Employed",
            "credit_score": 735,
            "liabilities": 18000.00,
            "location": "US"
        }
    }
    
    mock_employment = {
        "jobs": [
            {
                "title": "Business Owner",
                "company": "Self",
                "start_date": "2015-01-01",
                "end_date": None,
                "duration_months": 135
            }
        ],
        "stability_score": 70,
        "gaps": []
    }
    
    mock_credit = {
        "inquiries": [],
        "recent_inquiries_3m": 0,
        "anomaly_flags": []
    }
    
    mock_claude_response = {
        "income_stability_score": 70,
        "employment_risk": "MEDIUM",
        "credit_summary": "Self-employed for 11+ years. Moderate income stability.",
        "completeness_flags": [],
        "confidence": 0.80,
        "reasoning": "Self-employment adds risk but long-term business history suggests stability."
    }
    
    with patch("src.agents.applicant_profile_agent.get_applicant_history", 
               return_value=mock_history):
        with patch("src.agents.applicant_profile_agent.get_employment_data", 
                   return_value=mock_employment):
            with patch("src.agents.applicant_profile_agent.get_credit_inquiries", 
                       return_value=mock_credit):
                with patch.object(agent, "invoke_claude", 
                                 return_value=mock_claude_response):
                    result = agent.analyze("APP-SCHEMA-001")
    
    # Validate result can be parsed as ProfileAnalysis
    profile = ProfileAnalysis(**result)
    assert profile.income_stability_score == 70
    assert profile.employment_risk == "MEDIUM"
    assert profile.confidence == 0.80


__all__ = [
    "test_applicant_profile_agent_stable_employment",
    "test_applicant_profile_agent_employment_gap",
    "test_applicant_profile_agent_recent_job_change",
    "test_applicant_profile_agent_high_credit_inquiries",
    "test_applicant_profile_agent_missing_employment_history",
    "test_applicant_profile_agent_mcp_error",
    "test_applicant_profile_agent_output_schema_validation",
]
