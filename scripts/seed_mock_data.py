"""
Seed mock database with sample applicants and rules.

Creates 10 varied applicant profiles covering:
- Clear approval cases (strong credit, low DTI, stable employment)
- Clear rejection cases (poor credit, high DTI, unstable)
- Borderline cases (mixed signals)
- Incomplete data cases
- Anomalous profiles (income spikes, employment gaps)

Run: python scripts/seed_mock_data.py
"""

from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.models import (
    Base, Applicant, EmploymentHistory, CreditHistory, RiskRule
)
from src.utils.config import settings


def seed_applicants(session) -> None:
    """Seed 10 varied applicant profiles."""
    
    applicants = [
        # 1. CLEAR APPROVAL: Excellent credit, stable, low DTI
        {
            "id": "APP-CLEAR-APPROVE-1",
            "age": 42,
            "income": Decimal("120000"),
            "employment_type": "Salaried",
            "credit_score": 780,
            "existing_liabilities": Decimal("15000"),
            "location": "US",
            "jobs": [
                ("Senior Software Engineer", "Tech Corp", -60, None),  # 5 years
            ],
            "credit_inquiries": [
                ("2026-09-01", "Hard", "Home refinance"),
            ]
        },
        # 2. CLEAR APPROVAL: Good credit, stable, manageable debt
        {
            "id": "APP-CLEAR-APPROVE-2",
            "age": 35,
            "income": Decimal("85000"),
            "employment_type": "Salaried",
            "credit_score": 745,
            "existing_liabilities": Decimal("12000"),
            "location": "US",
            "jobs": [
                ("Manager", "Finance Co", -36, None),  # 3 years
            ],
            "credit_inquiries": [
                ("2026-08-15", "Soft", "Auto loan"),
            ]
        },
        # 3. CLEAR REJECTION: Very poor credit score
        {
            "id": "APP-CLEAR-REJECT-1",
            "age": 38,
            "income": Decimal("55000"),
            "employment_type": "Salaried",
            "credit_score": 520,  # < 550: auto-reject
            "existing_liabilities": Decimal("35000"),
            "location": "US",
            "jobs": [
                ("Retail", "Store", -12, None),
            ],
            "credit_inquiries": [
                ("2026-07-01", "Hard", "Credit card"),
                ("2026-06-15", "Hard", "Personal loan"),
                ("2026-05-01", "Hard", "Auto loan"),
            ]
        },
        # 4. CLEAR REJECTION: Very high DTI
        {
            "id": "APP-CLEAR-REJECT-2",
            "age": 45,
            "income": Decimal("60000"),  # Monthly: $5000
            "employment_type": "Salaried",
            "credit_score": 680,
            "existing_liabilities": Decimal("180000"),  # Monthly: $3000+
            "location": "US",
            "jobs": [
                ("Technician", "Factory", -24, None),
            ],
            "credit_inquiries": []
        },
        # 5. BORDERLINE: Good credit but borderline DTI
        {
            "id": "APP-BORDERLINE-1",
            "age": 32,
            "income": Decimal("70000"),  # Monthly: $5833
            "employment_type": "Salaried",
            "credit_score": 710,
            "existing_liabilities": Decimal("20000"),  # Monthly: ~$800
            "location": "US",
            "jobs": [
                ("Specialist", "Company", -30, None),
            ],
            "credit_inquiries": [
                ("2026-09-01", "Hard", "Auto loan"),
            ]
        },
        # 6. BORDERLINE: Recent job change, good other metrics
        {
            "id": "APP-BORDERLINE-2",
            "age": 40,
            "income": Decimal("95000"),
            "employment_type": "Salaried",
            "credit_score": 735,
            "existing_liabilities": Decimal("10000"),
            "location": "US",
            "jobs": [
                ("Director", "New Company", -8, None),  # < 1 year
                ("Manager", "Old Company", -84, -8),  # 7 years
            ],
            "credit_inquiries": [
                ("2026-08-01", "Hard", "Home search"),
            ]
        },
        # 7. ANOMALOUS: Income spike
        {
            "id": "APP-ANOMALY-INCOME-SPIKE",
            "age": 50,
            "income": Decimal("180000"),  # Spike from $100k
            "employment_type": "Self-Employed",
            "credit_score": 710,
            "existing_liabilities": Decimal("25000"),
            "location": "US",
            "jobs": [
                ("Business Owner", "Self", -36, None),
            ],
            "credit_inquiries": [
                ("2026-09-05", "Hard", "Expansion loan"),
                ("2026-09-03", "Hard", "Business line"),
                ("2026-09-01", "Hard", "Equipment financing"),
                ("2026-08-28", "Hard", "Working capital"),
            ]
        },
        # 8. ANOMALOUS: Employment gap
        {
            "id": "APP-ANOMALY-EMP-GAP",
            "age": 38,
            "income": Decimal("75000"),
            "employment_type": "Salaried",
            "credit_score": 690,
            "existing_liabilities": Decimal("30000"),
            "location": "US",
            "jobs": [
                ("Developer", "Tech Startup", -18, None),  # 1.5 years
                ("Gap", "Unemployed", -12, -30),  # 12-month gap
                ("Analyst", "Bank", -60, -42),  # 5+ years
            ],
            "credit_inquiries": []
        },
        # 9. INCOMPLETE: Missing stable employment
        {
            "id": "APP-INCOMPLETE-1",
            "age": 26,
            "income": Decimal("45000"),
            "employment_type": "Salaried",
            "credit_score": 650,
            "existing_liabilities": Decimal("8000"),
            "location": "US",
            "jobs": [
                ("Junior Dev", "Startup", -6, None),  # Only 6 months
            ],
            "credit_inquiries": [
                ("2026-09-10", "Soft", "First-time buyer"),
            ]
        },
        # 10. MARGINAL: Middle-of-road metrics
        {
            "id": "APP-MARGINAL-1",
            "age": 48,
            "income": Decimal("65000"),
            "employment_type": "Salaried",
            "credit_score": 665,
            "existing_liabilities": Decimal("22000"),
            "location": "CA",
            "jobs": [
                ("Supervisor", "Plant", -20, None),
            ],
            "credit_inquiries": [
                ("2026-07-15", "Hard", "Debt consolidation"),
            ]
        },
    ]
    
    for app_data in applicants:
        app = Applicant(
            id=app_data["id"],
            age=app_data["age"],
            income=app_data["income"],
            employment_type=app_data["employment_type"],
            credit_score=app_data["credit_score"],
            existing_liabilities=app_data["existing_liabilities"],
            location=app_data["location"],
        )
        session.add(app)
        
        # Add employment history
        for job_title, company, start_offset_months, end_offset_months in app_data.get("jobs", []):
            now = datetime.utcnow()
            start_date = now + timedelta(days=start_offset_months * 30)
            end_date = None
            if end_offset_months is not None:
                end_date = now + timedelta(days=end_offset_months * 30)
            
            tenure = (now - start_date).days // 30
            
            emp = EmploymentHistory(
                applicant_id=app_data["id"],
                job_title=job_title,
                company=company,
                start_date=start_date,
                end_date=end_date,
                tenure_months=max(1, tenure),
            )
            session.add(emp)
        
        # Add credit inquiries
        for inquiry_date, inquiry_type, notes in app_data.get("credit_inquiries", []):
            credit = CreditHistory(
                applicant_id=app_data["id"],
                inquiry_date=datetime.fromisoformat(inquiry_date),
                inquiry_type=inquiry_type,
                notes=notes,
            )
            session.add(credit)
    
    session.commit()
    print("✓ Seeded 10 varied applicant profiles")


def seed_risk_rules(session) -> None:
    """Seed decision thresholds and rules."""
    
    rules = [
        # DTI Thresholds
        ("DTI_FAVORABLE_MAX", "dti", "max_value", None, 0.36, "DTI < 0.36"),
        ("DTI_ACCEPTABLE_MAX", "dti", "max_value", None, 0.43, "DTI 0.36-0.43"),
        ("DTI_BORDERLINE_MAX", "dti", "max_value", None, 0.50, "DTI 0.43-0.50"),
        ("DTI_HIGH_RISK_MIN", "dti", "min_value", None, 0.50, "DTI > 0.50"),
        
        # Credit Score Bands
        ("CREDIT_EXCELLENT_MIN", "credit_score", "min_value", None, 750.0, "Credit >= 750"),
        ("CREDIT_GOOD_MIN", "credit_score", "min_value", None, 700.0, "Credit >= 700"),
        ("CREDIT_FAIR_MIN", "credit_score", "min_value", None, 650.0, "Credit >= 650"),
        ("CREDIT_POOR_MIN", "credit_score", "min_value", None, 550.0, "Credit >= 550"),
        
        # LTI Thresholds
        ("LTI_FAVORABLE_MAX", "lti", "max_value", None, 2.5, "LTI < 2.5"),
        ("LTI_ACCEPTABLE_MAX", "lti", "max_value", None, 4.0, "LTI < 4.0"),
        ("LTI_HIGH_RISK_MIN", "lti", "min_value", None, 4.0, "LTI >= 4.0"),
        
        # Confidence & Anomaly
        ("CONFIDENCE_THRESHOLD", "confidence", "threshold", None, 0.75, "Confidence >= 0.75 to auto-decide"),
        ("ANOMALY_SCORE_THRESHOLD", "anomaly", "threshold", None, 0.6, "Anomaly score > 0.6 flags review"),
        
        # Income stability
        ("INCOME_STABILITY_HIGH_TENURE", "income_stability", "tenure_months", None, 60.0, ">= 5 years employed"),
        ("EMPLOYMENT_GAP_MAX_MONTHS", "employment", "gap_months", None, 6.0, "Gap > 6 months anomaly"),
        ("CREDIT_INQUIRIES_RECENT_THRESHOLD", "credit", "inquiries_3m", None, 3.0, "More than 3 in 3 months anomaly"),
    ]
    
    for rule_name, rule_type, param_name, string_val, float_val, description in rules:
        rule = RiskRule(
            rule_name=rule_name,
            rule_type=rule_type,
            param_name=param_name,
            float_value=float_val,
            string_value=string_val,
            description=description,
        )
        session.add(rule)
    
    session.commit()
    print("✓ Seeded risk rules and thresholds")


def main():
    """Initialize database and seed data."""
    from src.database.models import create_tables
    
    # Create tables
    create_tables(settings.database_url)
    print(f"✓ Created tables in {settings.db_path}")
    
    # Create session
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Seed data
        seed_applicants(session)
        seed_risk_rules(session)
        
        print("\n✅ Database seeding complete!")
        print(f"   Database: {settings.db_path}")
        print(f"   Applicants: 10")
        print(f"   Rules: 18")
        
    finally:
        session.close()


if __name__ == "__main__":
    main()
