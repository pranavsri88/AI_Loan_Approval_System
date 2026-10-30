# What's Left to Make the App Executable?

**TL;DR:** App is 73% done. Need 8 small files (~270 lines) to make it fully executable. Estimated **1.5-2 hours of work**.

---

## Quick Reference: What Can You Run NOW?

```bash
# ✅ WORKS NOW - Start the REST API
python -m uvicorn src.api.main:app --reload --port 8000
# Access at: http://localhost:8000/docs

# ✅ WORKS NOW - Start the Streamlit UI
streamlit run src/ui/streamlit_app.py
# Access at: http://localhost:8501

# ✅ WORKS NOW - Start MCP Servers (4 separate terminals)
python -m src.mcp_servers.applicant_db      # port 8001
python -m src.mcp_servers.risk_rules_db     # port 8002
python -m src.mcp_servers.decision_synthesis # port 8003
python -m src.mcp_servers.notification_system # port 8004

# ✅ WORKS NOW - Run Tests
pytest tests/unit/test_mcp_servers.py -v   # 21/21 passing
pytest tests/unit/ -v
```

---

## Missing Files to Complete the App

### 1. **src/utils/constants.py** (20 lines, 15 min)
**What it needs:** Decision thresholds and band definitions

```python
# DTI Classifications
DTI_FAVORABLE_MAX = 0.36
DTI_ACCEPTABLE_MAX = 0.50
DTI_BORDERLINE_MAX = 0.63

# Credit Score Classifications
CREDIT_EXCELLENT_MIN = 750
CREDIT_GOOD_MIN = 700
CREDIT_FAIR_MIN = 650
CREDIT_POOR_MIN = 550

# LTI Classifications
LTI_FAVORABLE_MAX = 2.5
LTI_ACCEPTABLE_MAX = 4.0
LTI_HIGH_RISK_MIN = 4.0

# Risk Score Interpretation
RISK_VERY_LOW = range(0, 25)      # 0-24
RISK_LOW = range(25, 50)          # 25-49
RISK_MEDIUM = range(50, 75)       # 50-74
RISK_HIGH = range(75, 100)        # 75-99
RISK_VERY_HIGH = 100              # 100
```

---

### 2. **src/utils/validators.py** (40 lines, 15 min)
**What it needs:** Input field validators

```python
from pydantic import field_validator

def validate_credit_score(v: int) -> int:
    if not (300 <= v <= 850):
        raise ValueError("Credit score must be between 300-850")
    return v

def validate_employment_type(v: str) -> str:
    allowed = {"Salaried", "Self-Employed", "Unemployed", "Retired"}
    if v not in allowed:
        raise ValueError(f"Employment type must be one of {allowed}")
    return v

def validate_location(v: str) -> str:
    if not (v.isupper() and v.isalpha() and len(v) == 2):
        raise ValueError("Location must be 2-letter country code (e.g., 'US')")
    return v

def validate_income(v: Decimal) -> Decimal:
    if v <= 0:
        raise ValueError("Income must be positive")
    if v > Decimal("9999999"):
        raise ValueError("Income exceeds maximum allowed")
    return v
```

---

### 3. **scripts/init_db.py** (15 lines, 5 min)
**What it needs:** Initialize SQLite database

```python
#!/usr/bin/env python3
"""Initialize SQLite database with schema."""

from src.database.models import create_tables
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

if __name__ == "__main__":
    logger.info("Initializing database...")
    create_tables(settings.database_url)
    logger.info(f"Database initialized at {settings.database_url}")
```

**Run it:**
```bash
python scripts/init_db.py
# Output: Database initialized at sqlite:///./data/loans.db
```

---

### 4. **src/orchestration/state.py** (15 lines, 5 min)
**What it needs:** Workflow state definition for LangGraph

```python
"""LangGraph workflow state definition."""

from src.utils.schemas import ApplicationState

# LangGraph expects TypedDict, but Pydantic models work too
# Just re-export ApplicationState which has all required fields

__all__ = ["ApplicationState"]
```

---

### 5. **src/orchestration/nodes.py** (80 lines, 25 min)
**What it needs:** Six workflow nodes that orchestrate agents

```python
"""LangGraph workflow nodes."""

from src.orchestration.state import ApplicationState
from src.agents.applicant_profile_agent import ApplicantProfileAgent
from src.agents.financial_risk_agent import FinancialRiskAgent
from src.agents.loan_decision_agent import LoanDecisionAgent
from src.agents.compliance_agent import ComplianceAgent
from src.utils.logger import get_logger

logger = get_logger(__name__)

def validate_input_node(state: ApplicationState) -> ApplicationState:
    """Validate input application data."""
    logger.info(f"Validating input for {state.applicant_data.applicant_id}")
    # Pydantic validation already happened, just pass through
    return state

def applicant_profile_node(state: ApplicationState) -> ApplicationState:
    """Execute Applicant Profile Agent."""
    logger.info("Running applicant profile analysis...")
    agent = ApplicantProfileAgent()
    profile = agent.analyze(state.applicant_data, state.trace_id)
    state.profile_analysis = profile
    state.agents_run.append("applicant_profile")
    return state

def financial_risk_node(state: ApplicationState) -> ApplicationState:
    """Execute Financial Risk Agent."""
    logger.info("Running financial risk analysis...")
    agent = FinancialRiskAgent()
    financial = agent.analyze(state.applicant_data, state.trace_id)
    state.financial_analysis = financial
    state.agents_run.append("financial_risk")
    return state

def loan_decision_node(state: ApplicationState) -> ApplicationState:
    """Execute Loan Decision Agent."""
    logger.info("Running loan decision synthesis...")
    agent = LoanDecisionAgent()
    decision = agent.make_decision(
        profile=state.profile_analysis,
        financial=state.financial_analysis,
        trace_id=state.trace_id
    )
    state.decision_result = decision
    state.agents_run.append("loan_decision")
    return state

def compliance_node(state: ApplicationState) -> ApplicationState:
    """Execute Compliance & Action Agent."""
    logger.info("Running compliance checks...")
    agent = ComplianceAgent()
    compliance = agent.execute(
        decision=state.decision_result,
        applicant_id=state.applicant_data.applicant_id,
        trace_id=state.trace_id
    )
    state.compliance_action = compliance
    state.agents_run.append("compliance")
    
    # Set final outputs
    state.final_decision = state.decision_result.classification
    state.final_confidence = state.decision_result.confidence
    state.final_explanation = state.decision_result.explanation
    
    return state

def error_handler_node(state: ApplicationState) -> ApplicationState:
    """Handle errors and route to manual review."""
    logger.error(f"Error processing application {state.applicant_data.applicant_id}")
    state.final_decision = "REQUIRES_REVIEW"
    state.final_confidence = 0.0
    state.final_explanation = "Application encountered errors and requires manual review"
    return state
```

---

### 6. **src/orchestration/routing.py** (40 lines, 20 min)
**What it needs:** Conditional routing logic between nodes

```python
"""LangGraph conditional routing functions."""

from src.orchestration.state import ApplicationState
from src.utils.logger import get_logger

logger = get_logger(__name__)

def route_after_validation(state: ApplicationState) -> str:
    """Route after validation node."""
    # If validation passed, proceed to profile analysis
    return "profile_node"

def route_after_profile(state: ApplicationState) -> str:
    """Route after profile analysis."""
    if state.profile_analysis is None:
        logger.warning("Profile analysis failed")
        return "error_node"
    
    if state.profile_analysis.confidence < 0.5:
        logger.warning("Low confidence in profile analysis - escalating")
        return "error_node"
    
    return "financial_node"

def route_after_financial(state: ApplicationState) -> str:
    """Route after financial analysis."""
    if state.financial_analysis is None:
        logger.warning("Financial analysis failed")
        return "error_node"
    
    # If anomalies detected, escalate to manual review
    if state.financial_analysis.anomaly_detected:
        logger.info("Anomalies detected - routing to manual review")
        return "error_node"
    
    return "decision_node"

def route_after_decision(state: ApplicationState) -> str:
    """Route after loan decision."""
    if state.decision_result is None:
        logger.warning("Decision failed")
        return "error_node"
    
    # If low confidence, escalate to manual review
    if state.decision_result.confidence < 0.75:
        logger.info("Low decision confidence - routing to manual review")
        return "error_node"
    
    return "compliance_node"
```

---

### 7. **scripts/test_agents.py** (60 lines, 15 min)
**What it needs:** Manual end-to-end test script

```python
#!/usr/bin/env python3
"""Manual test script for end-to-end workflow."""

from decimal import Decimal
from src.utils.schemas import ApplicationData
from src.orchestration.langgraph_workflow import create_workflow
from src.utils.logger import get_logger

logger = get_logger(__name__)

def test_approval_candidate():
    """Test with application likely to be approved."""
    app_data = ApplicationData(
        applicant_id="APP-TEST-001",
        age=35,
        income=Decimal("85000"),
        employment_type="Salaried",
        credit_score=760,  # Good/Excellent
        loan_amount=Decimal("150000"),
        tenure_months=180,
        existing_liabilities=Decimal("12000"),
        location="US",
    )
    
    logger.info(f"Testing approval candidate: {app_data.applicant_id}")
    workflow = create_workflow()
    
    result = workflow.invoke({
        "applicant_data": app_data,
        "trace_id": "trace-test-001",
        "profile_analysis": None,
        "financial_analysis": None,
        "decision_result": None,
        "compliance_action": None,
        "agents_run": [],
        "timestamps": {},
        "error_state": None,
        "final_decision": None,
        "final_confidence": None,
        "final_explanation": None,
    })
    
    print(f"\n{'='*60}")
    print(f"WORKFLOW RESULT: {result['final_decision']}")
    print(f"Confidence: {result['final_confidence']:.2%}")
    print(f"Explanation: {result['final_explanation']}")
    print(f"Agents run: {', '.join(result['agents_run'])}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    test_approval_candidate()
```

**Run it:**
```bash
python scripts/test_agents.py
```

---

### 8. **db/migrations/001_initial_schema.sql** (Optional)
**Note:** You can skip this if using SQLAlchemy's `create_tables()` in `init_db.py`. The SQLAlchemy models already define the schema.

---

## Implementation Order

**Priority 1: Foundation (30 min)**
1. `src/utils/constants.py` (15 min)
2. `src/utils/validators.py` (15 min)

**Priority 2: Database (10 min)**
3. `scripts/init_db.py` (5 min)
4. `src/orchestration/state.py` (5 min)

**Priority 3: Orchestration (45 min)**
5. `src/orchestration/nodes.py` (25 min)
6. `src/orchestration/routing.py` (20 min)

**Priority 4: Testing (15 min)**
7. `scripts/test_agents.py` (15 min)

**Total: ~100 minutes**

---

## After Implementation: How to Run End-to-End

```bash
# Step 1: Initialize database
python scripts/init_db.py

# Step 2: Seed mock data
python scripts/seed_mock_data.py

# Step 3: Start MCP servers (4 terminals)
python -m src.mcp_servers.applicant_db &
python -m src.mcp_servers.risk_rules_db &
python -m src.mcp_servers.decision_synthesis &
python -m src.mcp_servers.notification_system &

# Step 4: Start API server
python -m uvicorn src.api.main:app --reload &

# Step 5: Test end-to-end workflow
python scripts/test_agents.py

# Expected output:
# ============================================================
# WORKFLOW RESULT: APPROVED (or REQUIRES_REVIEW, or REJECTED)
# Confidence: 95.23%
# Explanation: Strong financial profile with stable employment...
# Agents run: applicant_profile, financial_risk, loan_decision, compliance
# ============================================================
```

---

## Summary Table

| File | Lines | Time | Difficulty | Purpose |
|------|-------|------|------------|---------|
| constants.py | 20 | 15m | Trivial | Decision thresholds |
| validators.py | 40 | 15m | Easy | Input validation |
| init_db.py | 15 | 5m | Trivial | Database setup |
| state.py | 15 | 5m | Trivial | Workflow state |
| nodes.py | 80 | 25m | Medium | Orchestration nodes |
| routing.py | 40 | 20m | Medium | Conditional routing |
| test_agents.py | 60 | 15m | Easy | E2E testing |
| **TOTAL** | **270** | **100m** | **Medium** | **App Execution** |

---

## Current Completion

```
Layer 1: Config & Schemas ......... ✅ 100%
Layer 2: Database ................. ✅ 90% (need init_db.py)
Layer 3: API ...................... ✅ 100%
Layer 4: UI ....................... ✅ 100%
Layer 5: MCP Servers .............. ✅ 100% (21 tests passing)
Layer 6: Agents ................... ✅ 100%
Layer 7: Orchestration ............ ⚠️  25% (need 3 files)
Layer 8: Scripts .................. ⚠️  50% (need test script)

OVERALL: 73% (22/30 files)

To Reach 100%: Need 8 small files (~270 lines, ~1.5-2 hours)
```

---

## Next Steps

1. **Now:** You can run API, Streamlit, MCP servers individually
2. **Next:** Implement the 8 files above
3. **Then:** Run full end-to-end workflow
4. **Finally:** Deploy to production

---

**Questions?**
- See [EXECUTION_READINESS_ASSESSMENT.md](EXECUTION_READINESS_ASSESSMENT.md) for detailed breakdown
- See [MCP_IMPLEMENTATION_COMPLETE.md](MCP_IMPLEMENTATION_COMPLETE.md) for MCP server status
- See CLAUDE.md for project setup instructions
