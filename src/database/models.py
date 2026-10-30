"""
SQLAlchemy ORM models for SQLite database.
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Text, ForeignKey,
    create_engine, Index
)
from sqlalchemy.orm import declarative_base, relationship, Session
from sqlalchemy.types import Numeric

Base = declarative_base()


class Applicant(Base):
    __tablename__ = "applicants"

    id = Column(String(20), primary_key=True, index=True)
    age = Column(Integer, nullable=False)
    income = Column(Numeric(10, 2), nullable=False)
    employment_type = Column(String(50), nullable=False)
    credit_score = Column(Integer, nullable=False)
    existing_liabilities = Column(Numeric(10, 2), nullable=False)
    location = Column(String(2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employment_history = relationship(
        "EmploymentHistory", back_populates="applicant", cascade="all, delete-orphan"
    )
    credit_history = relationship(
        "CreditHistory", back_populates="applicant", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_applicant_credit_score", "credit_score"),
        Index("ix_applicant_employment_type", "employment_type"),
    )


class EmploymentHistory(Base):
    __tablename__ = "employment_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    applicant_id = Column(String(20), ForeignKey("applicants.id"), index=True)
    job_title = Column(String(100), nullable=False)
    company = Column(String(100), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    tenure_months = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    applicant = relationship("Applicant", back_populates="employment_history")


class CreditHistory(Base):
    __tablename__ = "credit_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    applicant_id = Column(String(20), ForeignKey("applicants.id"), index=True)
    inquiry_date = Column(DateTime, nullable=False)
    inquiry_type = Column(String(50), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    applicant = relationship("Applicant", back_populates="credit_history")


class RiskRule(Base):
    __tablename__ = "risk_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_name = Column(String(100), unique=True, index=True)
    rule_type = Column(String(50), nullable=False)
    param_name = Column(String(100), nullable=True)
    float_value = Column(Float, nullable=True)
    int_value = Column(Integer, nullable=True)
    string_value = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trace_id = Column(String(100), unique=True, index=True)
    case_id = Column(String(50), unique=True, index=True)
    applicant_id = Column(String(20), ForeignKey("applicants.id"), index=True)
    agents_run = Column(Text, nullable=False)
    decision = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=True)
    risk_score = Column(Integer, nullable=True)
    decision_factors = Column(Text, nullable=True)
    explanation = Column(Text, nullable=False)
    errors = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(50), index=True)
    applicant_id = Column(String(20), index=True)
    notification_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(50), unique=True, index=True)
    trace_id = Column(String(100), unique=True, index=True)
    applicant_id = Column(String(20), index=True)
    decision = Column(String(50), nullable=False)
    action_taken = Column(String(50), nullable=False)
    summary = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def create_tables(database_url: str) -> None:
    """Create all tables in the database."""
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)


__all__ = [
    "Base",
    "Applicant",
    "EmploymentHistory",
    "CreditHistory",
    "RiskRule",
    "AuditLog",
    "Notification",
    "Case",
    "create_tables",
]
