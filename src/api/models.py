"""
FastAPI request/response models.

Uses Pydantic for validation. Most models reference shared schemas in utils/schemas.py
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class ApplicationRequest(BaseModel):
    """Request model for POST /applications"""
    applicant_id: str = Field(..., description="Unique applicant ID")
    age: int = Field(..., ge=18, le=80, description="Age in years")
    income: float = Field(..., gt=0, description="Annual gross income")
    employment_type: str = Field(..., description="Employment type")
    credit_score: int = Field(..., ge=300, le=850, description="Credit score")
    loan_amount: float = Field(..., ge=1000, description="Requested loan amount")
    tenure_months: int = Field(..., ge=12, le=360, description="Loan term in months")
    existing_liabilities: float = Field(..., ge=0, description="Existing debt")
    location: str = Field(..., min_length=2, max_length=2, description="Country code")


class ApplicationResponse(BaseModel):
    """Response model for POST /applications"""
    trace_id: str = Field(..., description="Unique trace ID for tracking")
    applicant_id: str = Field(..., description="Applicant ID")
    status: str = Field(..., description="Status: PENDING|COMPLETED")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Submission timestamp")


class DecisionResponse(BaseModel):
    """Response model for GET /applications/{trace_id}"""
    trace_id: str = Field(..., description="Trace ID")
    applicant_id: str = Field(..., description="Applicant ID")
    status: str = Field(..., description="Status: PROCESSING|COMPLETED")
    decision: Optional[str] = Field(None, description="APPROVED|REJECTED|REQUIRES_REVIEW")
    risk_score: Optional[int] = Field(None, description="Risk score 0-100")
    confidence: Optional[float] = Field(None, description="Confidence 0.0-1.0")
    decision_factors: Optional[List[Dict[str, Any]]] = Field(None, description="Decision factors")
    explanation: Optional[str] = Field(None, description="Decision explanation")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class ErrorResponse(BaseModel):
    """Error response model"""
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    trace_id: Optional[str] = Field(None, description="Trace ID for debugging")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Status: healthy|unhealthy")
    environment: str = Field(..., description="Environment: development|production")
    version: str = Field(..., description="API version")


__all__ = [
    "ApplicationRequest",
    "ApplicationResponse",
    "DecisionResponse",
    "ErrorResponse",
    "HealthResponse",
]
