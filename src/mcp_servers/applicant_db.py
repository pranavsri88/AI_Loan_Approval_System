"""
ApplicantDB MCP Server.

Provides tools for querying applicant profile and history data.

Tools:
- get_applicant_history(applicant_id) -> applicant info + employment history
- get_employment_data(applicant_id) -> detailed employment history
- get_credit_inquiries(applicant_id) -> credit inquiry history for anomaly detection
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from fastmcp import FastMCP
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Applicant, EmploymentHistory, CreditHistory
from src.utils.config import settings


# Initialize MCP server
mcp = FastMCP("applicant_db")


def get_session():
    """Get database session."""
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


@mcp.tool
def get_applicant_history(applicant_id: str) -> Dict[str, Any]:
    """
    Get applicant profile and complete history.
    
    Returns:
    {
        "applicant": {applicant profile data},
        "employment_history": [list of jobs],
        "tenure_years": current tenure,
        "recent_changes": employment gaps or job changes
    }
    """
    session = get_session()
    try:
        applicant = session.query(Applicant).filter(
            Applicant.id == applicant_id
        ).first()
        
        if not applicant:
            return {"error": f"Applicant {applicant_id} not found"}
        
        # Get employment history
        employment = session.query(EmploymentHistory).filter(
            EmploymentHistory.applicant_id == applicant_id
        ).order_by(EmploymentHistory.start_date.desc()).all()
        
        # Calculate tenure and gaps
        current_tenure = 0
        recent_gap = None
        if employment:
            # First job is most recent
            current_job = employment[0]
            current_tenure = current_job.tenure_months
            
            # Check for employment gaps
            for i in range(len(employment) - 1):
                gap_months = (employment[i].start_date - employment[i+1].end_date).days // 30 if employment[i+1].end_date else 0
                if gap_months > 6:
                    recent_gap = {"start": employment[i+1].end_date.isoformat(), "months": gap_months}
        
        return {
            "applicant": {
                "id": applicant.id,
                "age": applicant.age,
                "income": float(applicant.income),
                "employment_type": applicant.employment_type,
                "credit_score": applicant.credit_score,
                "location": applicant.location,
            },
            "employment_history": [
                {
                    "job_title": e.job_title,
                    "company": e.company,
                    "start_date": e.start_date.isoformat(),
                    "end_date": e.end_date.isoformat() if e.end_date else None,
                    "tenure_months": e.tenure_months,
                }
                for e in employment
            ],
            "tenure_years": round(current_tenure / 12, 1),
            "recent_gap_months": recent_gap["months"] if recent_gap else 0,
        }
    finally:
        session.close()


@mcp.tool
def get_employment_data(applicant_id: str) -> Dict[str, Any]:
    """
    Get detailed employment history with stability assessment.
    
    Returns employment data including:
    - Job history with dates
    - Tenure at current job
    - Employment gaps
    - Job change frequency
    """
    session = get_session()
    try:
        employment = session.query(EmploymentHistory).filter(
            EmploymentHistory.applicant_id == applicant_id
        ).order_by(EmploymentHistory.start_date.desc()).all()
        
        if not employment:
            return {"error": f"No employment data for {applicant_id}"}
        
        # Calculate metrics
        total_jobs = len(employment)
        current_tenure_months = employment[0].tenure_months if employment else 0
        
        # Check for stability
        stability_score = min(100, current_tenure_months * 2)  # 60+ months = 100
        
        # Check gaps
        gaps = []
        for i in range(len(employment) - 1):
            if employment[i+1].end_date:
                gap_days = (employment[i].start_date - employment[i+1].end_date).days
                if gap_days > 0:
                    gaps.append({"months": gap_days // 30})
        
        return {
            "applicant_id": applicant_id,
            "jobs": [
                {
                    "title": e.job_title,
                    "company": e.company,
                    "start": e.start_date.isoformat(),
                    "end": e.end_date.isoformat() if e.end_date else None,
                    "duration_months": e.tenure_months,
                }
                for e in employment
            ],
            "current_tenure_months": current_tenure_months,
            "total_jobs": total_jobs,
            "employment_gaps": gaps,
            "stability_score": stability_score,
            "status": "STABLE" if current_tenure_months >= 24 else "MODERATE" if current_tenure_months >= 12 else "UNSTABLE",
        }
    finally:
        session.close()


@mcp.tool
def get_credit_inquiries(applicant_id: str) -> Dict[str, Any]:
    """
    Get credit inquiry history for anomaly detection.
    
    Returns:
    {
        "inquiries": [...],
        "recent_inquiries_3m": count,
        "inquiry_types": {type: count}
    }
    """
    session = get_session()
    try:
        inquiries = session.query(CreditHistory).filter(
            CreditHistory.applicant_id == applicant_id
        ).order_by(CreditHistory.inquiry_date.desc()).all()
        
        if not inquiries:
            return {
                "applicant_id": applicant_id,
                "inquiries": [],
                "recent_inquiries_3m": 0,
                "inquiry_types": {},
            }
        
        # Count inquiries in last 3 months
        now = datetime.utcnow()
        recent_count = sum(1 for i in inquiries if (now - i.inquiry_date).days <= 90)
        
        # Count by type
        inquiry_types = {}
        for inquiry in inquiries:
            inquiry_types[inquiry.inquiry_type] = inquiry_types.get(inquiry.inquiry_type, 0) + 1
        
        return {
            "applicant_id": applicant_id,
            "inquiries": [
                {
                    "date": i.inquiry_date.isoformat(),
                    "type": i.inquiry_type,
                    "notes": i.notes,
                }
                for i in inquiries
            ],
            "recent_inquiries_3m": recent_count,
            "inquiry_types": inquiry_types,
            "anomaly_flag": recent_count > 3,
        }
    finally:
        session.close()


def run_server(host: str = "127.0.0.1", port: int = 8001):
    """Run the ApplicantDB MCP server."""
    import uvicorn
    uvicorn.run("src.mcp_servers.applicant_db:mcp", host=host, port=port, reload=True)


if __name__ == "__main__":
    run_server()
