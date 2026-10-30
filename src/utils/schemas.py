"""
Shared Pydantic models for request/response validation and API contracts.

This module defines all data structures used across the system:
- Input schemas (application submissions)
- Agent output schemas (analysis results)
- API request/response schemas
- Database models

All models are reusable across API endpoints, agents, and tests.
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# INPUT SCHEMAS (Application Data)
# ============================================================================

class ApplicationData(BaseModel):
    """
    Input schema for loan application submission.

    Represents the initial data provided by applicant via UI.
    All fields are validated per requirements.md specifications.
    """
    applicant_id: str = Field(
        ...,
        min_length=8,
        max_length=20,
        description="Unique applicant identifier (UUID or alphanumeric)"
    )
    age: int = Field(
        ...,
        ge=18,
        le=80,
        description="Applicant age in years"
    )
    income: Decimal = Field(
        ...,
        gt=0,
        max_digits=10,
        decimal_places=2,
        description="Annual gross income in base currency"
    )
    employment_type: str = Field(
        ...,
        description="Employment type category"
    )
    credit_score: int = Field(
        ...,
        ge=300,
        le=850,
        description="Credit score (FICO range 300-850)"
    )
    loan_amount: Decimal = Field(
        ...,
        ge=Decimal("1000"),
        le=Decimal("5000000"),
        description="Requested loan amount"
    )
    tenure_months: int = Field(
        ...,
        ge=12,
        le=360,
        description="Loan repayment period in months"
    )
    existing_liabilities: Decimal = Field(
        ...,
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="Total existing debt/liabilities"
    )
    location: str = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Two-letter country code (ISO 3166-1)"
    )
    timestamp: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="Application submission timestamp (ISO 8601 UTC)"
    )

    @field_validator("employment_type")
    @classmethod
    def validate_employment_type(cls, v: str) -> str:
        """Validate employment type is one of allowed values."""
        allowed = {"Salaried", "Self-Employed", "Unemployed", "Retired"}
        if v not in allowed:
            raise ValueError(f"employment_type must be one of {allowed}, got {v}")
        return v

    @field_validator("location")
    @classmethod
    def validate_location(cls, v: str) -> str:
        """Validate location is uppercase 2-letter country code."""
        if not v.isupper() or not v.isalpha():
            raise ValueError("location must be uppercase 2-letter country code")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "applicant_id": "APP-12345",
                "age": 35,
                "income": 85000.00,
                "employment_type": "Salaried",
                "credit_score": 745,
                "loan_amount": 150000.00,
                "tenure_months": 180,
                "existing_liabilities": 12000.00,
                "location": "US",
                "timestamp": "2026-10-29T14:30:00Z"
            }
        }


# ============================================================================
# AGENT OUTPUT SCHEMAS (Analysis Results)
# ============================================================================

class ProfileAnalysis(BaseModel):
    """
    Output schema for Applicant Profile Agent.

    Contains analysis of applicant's personal and employment profile.
    """
    income_stability_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Income stability score (0=unstable, 100=very stable)"
    )
    employment_risk: str = Field(
        ...,
        pattern="^(LOW|MEDIUM|HIGH)$",
        description="Employment risk level"
    )
    credit_summary: str = Field(
        ...,
        description="Text summary of credit history"
    )
    completeness_flags: List[str] = Field(
        default_factory=list,
        description="List of anomalies or missing data flags"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Agent confidence in this analysis (0.0-1.0)"
    )
    reasoning: str = Field(
        ...,
        description="Explanation of analysis methodology"
    )


class FinancialAnalysis(BaseModel):
    """
    Output schema for Financial Risk Analysis Agent.

    Contains financial metrics, risk classifications, and anomaly detection.
    """
    dti: float = Field(
        ...,
        ge=0.0,
        description="Debt-to-income ratio"
    )
    dti_classification: str = Field(
        ...,
        pattern="^(FAVORABLE|ACCEPTABLE|BORDERLINE|HIGH_RISK)$",
        description="DTI classification"
    )
    credit_score_risk: str = Field(
        ...,
        pattern="^(LOW|MODERATE|MEDIUM|HIGH|VERY_HIGH)$",
        description="Credit score risk level"
    )
    lti: float = Field(
        ...,
        ge=0.0,
        description="Loan-to-income ratio"
    )
    loan_amount_risk: str = Field(
        ...,
        pattern="^(LOW|MODERATE|HIGH)$",
        description="Loan amount risk classification"
    )
    anomaly_detected: bool = Field(
        ...,
        description="Whether anomalies were detected"
    )
    anomaly_reasons: List[str] = Field(
        default_factory=list,
        description="List of detected anomalies"
    )
    risk_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Composite risk score (0=low risk, 100=high risk)"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Agent confidence in this analysis"
    )
    reasoning: str = Field(
        ...,
        description="Explanation of financial analysis"
    )


class DecisionResult(BaseModel):
    """
    Output schema for Loan Decision Agent.

    Contains final decision, risk score, confidence, and explanation.
    """
    classification: str = Field(
        ...,
        pattern="^(APPROVED|REJECTED|REQUIRES_REVIEW)$",
        description="Final loan decision classification"
    )
    risk_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Overall risk score (0=low risk, 100=high risk)"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Decision confidence (0.0-1.0)"
    )
    decision_factors: List[Dict[str, Any]] = Field(
        ...,
        description="Ranked list of decision factors with impact weights"
    )
    explanation: str = Field(
        ...,
        description="Human-readable decision explanation (no PII)"
    )


class ComplianceAction(BaseModel):
    """
    Output schema for Compliance & Action Orchestrator Agent.

    Contains action taken, notification status, case ID, and audit summary.
    """
    action_taken: str = Field(
        ...,
        pattern="^(APPROVED|REJECTED|ESCALATED)$",
        description="Action taken on application"
    )
    notification_status: str = Field(
        ...,
        pattern="^(SENT|PENDING|FAILED)$",
        description="Notification delivery status"
    )
    case_id: str = Field(
        ...,
        description="Unique immutable case identifier"
    )
    timestamp: datetime = Field(
        ...,
        description="Action timestamp (ISO 8601 UTC)"
    )
    summary: str = Field(
        ...,
        description="Action summary for audit log"
    )


# ============================================================================
# API REQUEST/RESPONSE SCHEMAS
# ============================================================================

class ApplicationRequest(BaseModel):
    """
    API request schema for POST /api/v1/applications.

    Maps to ApplicationData with same validations.
    """
    applicant_id: str
    age: int
    income: Decimal
    employment_type: str
    credit_score: int
    loan_amount: Decimal
    tenure_months: int
    existing_liabilities: Decimal
    location: str
    timestamp: Optional[datetime] = None


class ApplicationResponse(BaseModel):
    """
    API response schema for application submission.

    Returned immediately (HTTP 202) with trace_id for polling.
    """
    trace_id: str = Field(
        ...,
        description="Unique trace ID for tracking request"
    )
    applicant_id: str = Field(
        ...,
        description="Applicant ID from request"
    )
    status: str = Field(
        ...,
        pattern="^(PENDING|PROCESSING|COMPLETED)$",
        description="Current processing status"
    )
    timestamp: datetime = Field(
        ...,
        description="Response timestamp"
    )


class DecisionResponse(BaseModel):
    """
    API response schema for decision status/result.

    Returned when decision is complete (HTTP 200) or still processing (HTTP 202).
    """
    trace_id: str
    applicant_id: str
    status: str = Field(pattern="^(PROCESSING|COMPLETED)$")
    decision: Optional[str] = Field(
        None,
        pattern="^(APPROVED|REJECTED|REQUIRES_REVIEW)$"
    )
    risk_score: Optional[int] = None
    confidence: Optional[float] = None
    decision_factors: Optional[List[Dict[str, Any]]] = None
    explanation: Optional[str] = None
    timestamp: datetime


class ErrorResponse(BaseModel):
    """
    API error response schema (HTTP 400, 500, etc).

    Standard error format with trace_id for debugging.
    """
    error_code: str = Field(
        ...,
        description="Machine-readable error code"
    )
    message: str = Field(
        ...,
        description="Human-readable error message"
    )
    trace_id: str = Field(
        ...,
        description="Trace ID for debugging"
    )
    timestamp: datetime


class AuditTrailEntry(BaseModel):
    """
    Schema for audit trail database entries.

    Immutable record of decision process and outcomes.
    """
    trace_id: str
    case_id: str
    applicant_id: str
    timestamp_submitted: datetime
    agents_run: List[str]
    timestamps: Dict[str, datetime]
    profile_analysis: Optional[Dict[str, Any]] = None
    financial_analysis: Optional[Dict[str, Any]] = None
    decision_result: Optional[Dict[str, Any]] = None
    compliance_action: Optional[Dict[str, Any]] = None
    final_decision: str
    final_risk_score: int
    final_confidence: float
    explanation: str
    decision_factors: List[Dict[str, Any]]
    errors: Optional[List[Dict[str, Any]]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# ORCHESTRATION STATE SCHEMA (LangGraph)
# ============================================================================

class ApplicationState(BaseModel):
    """
    State schema for LangGraph workflow.

    Passed through all nodes and updated at each step.
    This is converted to TypedDict for LangGraph internally.
    """
    # Input
    applicant_data: ApplicationData
    trace_id: str

    # Intermediate results
    profile_analysis: Optional[ProfileAnalysis] = None
    financial_analysis: Optional[FinancialAnalysis] = None
    decision_result: Optional[DecisionResult] = None
    compliance_action: Optional[ComplianceAction] = None

    # Metadata
    agents_run: List[str] = Field(default_factory=list)
    timestamps: Dict[str, datetime] = Field(default_factory=dict)

    # Error handling
    error_state: Optional[Dict[str, Any]] = None

    # Final outputs
    final_decision: Optional[str] = None
    final_confidence: Optional[float] = None
    final_explanation: Optional[str] = None


__all__ = [
    "ApplicationData",
    "ProfileAnalysis",
    "FinancialAnalysis",
    "DecisionResult",
    "ComplianceAction",
    "ApplicationRequest",
    "ApplicationResponse",
    "DecisionResponse",
    "ErrorResponse",
    "AuditTrailEntry",
    "ApplicationState",
]
