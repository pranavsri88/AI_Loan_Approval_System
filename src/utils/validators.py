"""Input field validators for loan applications."""

from decimal import Decimal
from pydantic import field_validator


def validate_credit_score(v: int) -> int:
    """Validate credit score is in FICO range (300-850)."""
    if not isinstance(v, int):
        raise ValueError("Credit score must be an integer")
    if not (300 <= v <= 850):
        raise ValueError(f"Credit score must be between 300-850, got {v}")
    return v


def validate_employment_type(v: str) -> str:
    """Validate employment type is one of allowed values."""
    allowed = {"Salaried", "Self-Employed", "Unemployed", "Retired"}
    if v not in allowed:
        raise ValueError(f"Employment type must be one of {allowed}, got {v}")
    return v


def validate_location(v: str) -> str:
    """Validate location is 2-letter uppercase country code."""
    if not v.isupper() or not v.isalpha() or len(v) != 2:
        raise ValueError(f"Location must be 2-letter uppercase country code (e.g., 'US'), got {v}")
    return v


def validate_income(v: Decimal) -> Decimal:
    """Validate income is positive and within reasonable bounds."""
    if v <= 0:
        raise ValueError(f"Income must be positive, got {v}")
    if v > Decimal("9999999"):
        raise ValueError(f"Income exceeds maximum allowed ({Decimal('9999999')}), got {v}")
    return v


def validate_loan_amount(v: Decimal) -> Decimal:
    """Validate loan amount is within bounds."""
    if v < Decimal("1000"):
        raise ValueError(f"Loan amount must be at least $1,000, got {v}")
    if v > Decimal("5000000"):
        raise ValueError(f"Loan amount must not exceed $5,000,000, got {v}")
    return v


def validate_age(v: int) -> int:
    """Validate age is within acceptable range."""
    if not (18 <= v <= 80):
        raise ValueError(f"Age must be between 18-80, got {v}")
    return v


def validate_tenure(v: int) -> int:
    """Validate loan tenure in months."""
    if not (12 <= v <= 360):
        raise ValueError(f"Tenure must be between 12-360 months, got {v}")
    return v


__all__ = [
    "validate_credit_score",
    "validate_employment_type",
    "validate_location",
    "validate_income",
    "validate_loan_amount",
    "validate_age",
    "validate_tenure",
]
