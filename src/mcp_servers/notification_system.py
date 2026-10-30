"""
NotificationSystem MCP Server.

Provides tools for notifications, case management, and audit logging.

Tools:
- send_notification(applicant_id, notification_type, message) -> Send notification
- create_case(trace_id, applicant_id, decision) -> Create audit case
- write_audit_log(trace_id, applicant_id, event) -> Write audit event
"""

from datetime import datetime
from typing import Any, Dict
from uuid import uuid4
from fastmcp import FastMCP
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Notification, Case, AuditLog
from src.utils.config import settings


# Initialize MCP server
mcp = FastMCP("notification_system")


def get_session():
    """Get database session."""
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


@mcp.tool
def send_notification(
    applicant_id: str,
    case_id: str,
    notification_type: str,
    message: str,
) -> Dict[str, Any]:
    """
    Send notification to applicant.
    
    Args:
    - applicant_id: Applicant ID
    - case_id: Associated case ID
    - notification_type: 'email', 'sms', 'letter'
    - message: Notification message
    
    Returns:
    {
        "status": "SENT" | "PENDING" | "FAILED",
        "notification_id": str,
        "sent_at": datetime
    }
    """
    session = get_session()
    try:
        notification = Notification(
            case_id=case_id,
            applicant_id=applicant_id,
            notification_type=notification_type,
            status="SENT" if notification_type in ["email", "sms"] else "PENDING",
            message=message,
            sent_at=datetime.utcnow() if settings.enable_notifications else None,
        )
        session.add(notification)
        session.commit()
        
        return {
            "status": notification.status,
            "notification_id": str(notification.id),
            "sent_at": notification.sent_at.isoformat() if notification.sent_at else None,
            "applicant_id": applicant_id,
            "case_id": case_id,
        }
    finally:
        session.close()


@mcp.tool
def create_case(
    trace_id: str,
    applicant_id: str,
    decision: str,
    action_taken: str = "APPROVED",
) -> Dict[str, Any]:
    """
    Create audit case for decision.
    
    Args:
    - trace_id: Unique request trace ID
    - applicant_id: Applicant ID
    - decision: APPROVED | REJECTED | REQUIRES_REVIEW
    - action_taken: Action to take (optional)
    
    Returns:
    {
        "case_id": str,
        "trace_id": str,
        "applicant_id": str,
        "created_at": datetime
    }
    """
    session = get_session()
    try:
        # Generate case ID: CASE-YYYY-MM-DD-NNNNN
        now = datetime.utcnow()
        date_str = now.strftime("%Y-%m-%d")
        seq = session.query(Case).filter(
            Case.created_at >= now.replace(hour=0, minute=0, second=0, microsecond=0),
            Case.created_at < now.replace(hour=23, minute=59, second=59, microsecond=999999),
        ).count() + 1
        case_id = f"CASE-{date_str}-{seq:05d}"
        
        case = Case(
            case_id=case_id,
            trace_id=trace_id,
            applicant_id=applicant_id,
            decision=decision,
            action_taken=action_taken,
            summary=f"{decision} - {action_taken}",
        )
        session.add(case)
        session.commit()
        
        return {
            "case_id": case.case_id,
            "trace_id": trace_id,
            "applicant_id": applicant_id,
            "decision": decision,
            "created_at": case.created_at.isoformat(),
        }
    finally:
        session.close()


@mcp.tool
def write_audit_log(
    trace_id: str,
    applicant_id: str,
    case_id: str,
    decision: str,
    risk_score: int,
    confidence: float,
    explanation: str,
    agents_run: str = "[]",
    decision_factors: str = "[]",
) -> Dict[str, Any]:
    """
    Write immutable audit log entry.
    
    All data persisted for compliance. Never updated or deleted.
    
    Returns:
    {
        "audit_id": int,
        "trace_id": str,
        "case_id": str,
        "status": "LOGGED"
    }
    """
    session = get_session()
    try:
        audit = AuditLog(
            trace_id=trace_id,
            case_id=case_id,
            applicant_id=applicant_id,
            decision=decision,
            risk_score=risk_score,
            confidence=confidence,
            explanation=explanation,
            agents_run=agents_run,
            decision_factors=decision_factors,
        )
        session.add(audit)
        session.commit()
        
        return {
            "audit_id": audit.id,
            "trace_id": trace_id,
            "case_id": case_id,
            "applicant_id": applicant_id,
            "status": "LOGGED",
            "created_at": audit.created_at.isoformat(),
        }
    finally:
        session.close()


def run_server(host: str = "127.0.0.1", port: int = 8004):
    """Run the NotificationSystem MCP server."""
    import uvicorn
    uvicorn.run("src.mcp_servers.notification_system:mcp", host=host, port=port, reload=True)


if __name__ == "__main__":
    run_server()
