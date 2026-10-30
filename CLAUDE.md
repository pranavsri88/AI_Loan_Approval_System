# CLAUDE.md: Agentic AI Intelligent Loan Approval System

Project setup, conventions, and development guidelines for Phase 1 and beyond.

---

## Project Overview

**Agentic AI Intelligent Loan Approval System** is a multi-agent AI solution that automates loan application evaluation. The system classifies applications as **Approved**, **Rejected**, or **Requires Manual Review** based on financial metrics, credit analysis, and decision rules.

### Business Goals
- **Speed:** Process applications in < 5 seconds
- **Consistency:** Deterministic decisions based on defined rules
- **Explainability:** Clear reasoning for every decision
- **Auditability:** Complete immutable audit trail for compliance

### Key Features
- 4 AI agents (Applicant Profile, Financial Risk, Loan Decision, Compliance & Action)
- LangGraph orchestration for agent coordination
- 4 MCP servers for standardized data access
- FastAPI REST API with structured logging
- Streamlit UI for applicant-facing interface
- SQLite audit trail for compliance

### Documentation Structure
- **docs/requirements.md** - Functional & non-functional requirements
- **docs/system_design.md** - Architecture, APIs, data models, design decisions
- **docs/user_stories.md** - User stories by epic, acceptance criteria, mapping to phases

---

## Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **UI** | Streamlit | 1.28+ | Web chatbot interface |
| **API** | FastAPI | 0.100+ | REST API microservice |
| **Orchestration** | LangGraph | Latest | Agent workflow coordination |
| **Agent Framework** | LangChain | Latest | AI agent abstractions |
| **LLM** | Anthropic Claude Sonnet 4.6 | Claude SDK v0.10+ | Decision-making agents |
| **MCP** | FastMCP | Latest | Model Context Protocol servers |
| **Database** | SQLite | 3.40+ | Audit trail & mock data |
| **ORM** | SQLAlchemy | 2.0+ | Database abstraction (optional) |
| **Validation** | Pydantic | 2.0+ | Input/output validation & schemas |
| **Logging** | Python logging + JSON | 3.10+ | Structured logging |
| **Testing** | Pytest | 7.4+ | Unit & integration tests |
| **Python** | Python | 3.10+ | Runtime |

### Dependency File
```
requirements.txt (see setup instructions below)
```

---

## Folder Structure

```
ai-loan-approval-system/
├── CLAUDE.md                              # This file: project setup & conventions
├── README.md                              # User-facing project description
├── requirements.txt                       # Python dependencies
├── Dockerfile                             # Container image
├── docker-compose.yml                     # Local dev environment
│
├── docs/
│   ├── requirements.md                    # Requirements specification
│   ├── system_design.md                   # Architecture & design
│   └── user_stories.md                    # User stories by epic
│
├── src/
│   ├── __init__.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                        # FastAPI app initialization & startup
│   │   ├── routes.py                      # API endpoints
│   │   ├── models.py                      # Pydantic request/response schemas
│   │   └── middleware.py                  # Logging, auth, CORS middleware
│   │
│   ├── orchestration/
│   │   ├── __init__.py
│   │   ├── langgraph_workflow.py          # Main LangGraph graph definition
│   │   ├── state.py                       # ApplicationState TypedDict
│   │   ├── nodes.py                       # Node execution functions (validate, profile, financial, decision, compliance)
│   │   └── routing.py                     # Conditional routing logic
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py                  # Base class for all agents
│   │   ├── applicant_profile_agent.py     # Agent 1: Profile analysis
│   │   ├── financial_risk_agent.py        # Agent 2: Financial metrics
│   │   ├── loan_decision_agent.py         # Agent 3: Decision synthesis
│   │   └── compliance_agent.py            # Agent 4: Logging & notifications
│   │
│   ├── mcp_servers/
│   │   ├── __init__.py
│   │   ├── base.py                        # Base MCP server class
│   │   ├── applicant_db.py                # ApplicantDB MCP server
│   │   ├── risk_rules_db.py               # RiskRulesDB MCP server
│   │   ├── decision_synthesis.py          # DecisionSynthesis MCP server
│   │   └── notification_system.py         # NotificationSystem MCP server
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   └── streamlit_app.py               # Streamlit application
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── schemas.py                     # Shared Pydantic models (agent I/O)
│   │   ├── logger.py                      # Structured logging setup
│   │   ├── config.py                      # Configuration loader (env vars)
│   │   ├── validators.py                  # Input validation logic
│   │   ├── constants.py                   # Constants (thresholds, enums)
│   │   └── helpers.py                     # Utility functions
│   │
│   └── database/
│       ├── __init__.py
│       ├── models.py                      # SQLAlchemy ORM models
│       ├── repository.py                  # Data access layer (CRUD)
│       └── init_db.py                     # Database initialization
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                        # Pytest fixtures & configuration
│   │
│   ├── unit/
│   │   ├── test_api.py                    # API endpoint tests
│   │   ├── test_agents.py                 # Agent logic tests
│   │   ├── test_validators.py             # Input validation tests
│   │   └── test_schemas.py                # Pydantic model tests
│   │
│   ├── integration/
│   │   ├── test_orchestration.py          # LangGraph workflow tests
│   │   ├── test_mcp_servers.py            # MCP server tests
│   │   └── test_end_to_end.py             # E2E workflow tests
│   │
│   └── fixtures/
│       ├── mock_data.py                   # Mock applicant/financial data
│       └── sample_applications.py         # Sample loan applications
│
├── db/
│   ├── __init__.py
│   ├── sqlite.py                          # SQLite connection & setup
│   └── migrations/
│       └── 001_initial_schema.sql         # Schema creation DDL
│
├── config/
│   ├── dev.env                            # Development environment variables
│   ├── prod.env                           # Production environment variables
│   ├── logging_config.json                # Structured logging configuration
│   └── rules_config.json                  # Decision rules & thresholds
│
├── scripts/
│   ├── init_db.py                         # Initialize database & tables
│   ├── seed_mock_data.py                  # Populate mock data
│   └── test_agents.py                     # Manual agent testing script
│
├── logs/
│   └── app.log                            # Application logs (generated at runtime)
│
└── data/
    ├── loans.db                           # SQLite database (generated at runtime)
    └── backups/
        └── loans_backup.db                # Database backups
```

---

## Run Commands

### Prerequisites
```bash
# Ensure Python 3.10+
python --version

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp config/dev.env .env
# OR for production
cp config/prod.env .env

# Set ANTHROPIC_API_KEY
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Database Setup
```bash
# Initialize SQLite database with schema
python scripts/init_db.py

# Seed mock data (applicants, rules, test cases)
python scripts/seed_mock_data.py

# Verify schema
sqlite3 data/loans.db ".schema"
```

### Running the Application

#### Option 1: Streamlit UI (Development)
```bash
# Start Streamlit app (http://localhost:8501)
streamlit run src/ui/streamlit_app.py

# From different terminal, start FastAPI backend
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Option 2: FastAPI Only (API Testing)
```bash
# Start FastAPI server (http://localhost:8000)
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Test API endpoints
curl -X POST http://localhost:8000/api/v1/applications \
  -H "Content-Type: application/json" \
  -d @tests/fixtures/sample_applications.json

# View API docs
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

#### Option 3: Docker (Production-like)
```bash
# Build & run with Docker Compose
docker-compose up --build

# View logs
docker-compose logs -f fastapi
docker-compose logs -f streamlit

# Stop services
docker-compose down
```

### Testing

#### Run All Tests
```bash
# Run all tests with coverage report
pytest tests/ -v --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

#### Run Specific Test Suites
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Specific test file
pytest tests/unit/test_agents.py -v

# Specific test function
pytest tests/unit/test_agents.py::test_applicant_profile_agent -v

# With live print output
pytest tests/ -v -s
```

#### Manual Agent Testing
```bash
# Test individual agents with sample data
python scripts/test_agents.py

# Test MCP servers
python scripts/test_mcp_servers.py
```

### Linting & Type Checking (Optional)
```bash
# Type checking with mypy
mypy src/ --ignore-missing-imports

# Linting with flake8
flake8 src/ --max-line-length=120

# Format code with black
black src/ tests/
```

### Logging & Debugging
```bash
# View logs in real-time
tail -f logs/app.log

# Search logs by trace ID
grep "trace-abc123" logs/app.log | jq '.'

# View JSON logs with jq
tail -f logs/app.log | jq 'select(.level == "ERROR")'
```

---

## Coding Conventions

### 1. Type Hints (Mandatory)

**Rule:** Every function and variable must have explicit type hints.

```python
# ✅ GOOD
from typing import Optional, List, Dict
from decimal import Decimal
from datetime import datetime

def calculate_dti(
    monthly_debt: Decimal,
    gross_monthly_income: Decimal
) -> float:
    """Calculate debt-to-income ratio."""
    return float(monthly_debt / gross_monthly_income)

def analyze_profile(
    applicant_id: str,
    age: int,
    history: List[Dict[str, str]]
) -> Dict[str, any]:
    """Analyze applicant profile and return metrics."""
    ...

# ❌ AVOID
def calculate_dti(monthly_debt, gross_monthly_income):
    return monthly_debt / gross_monthly_income
```

**Pydantic Models for all I/O:**
```python
from pydantic import BaseModel, Field
from decimal import Decimal

class ApplicationData(BaseModel):
    """Input schema for loan application."""
    applicant_id: str = Field(..., min_length=8, max_length=20)
    age: int = Field(..., ge=18, le=80)
    income: Decimal = Field(..., gt=0, le=9999999)
    credit_score: int = Field(..., ge=300, le=850)
    # ... other fields

class ProfileAnalysis(BaseModel):
    """Output schema for profile analysis agent."""
    income_stability_score: int = Field(..., ge=0, le=100)
    employment_risk: str = Field(..., pattern="^(LOW|MEDIUM|HIGH)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
```

### 2. Small, Readable Functions

**Rule:** Functions should be < 20 lines; break complex logic into smaller functions.

```python
# ✅ GOOD: Small, focused functions
def validate_credit_score(score: int) -> bool:
    """Validate credit score is within acceptable range."""
    return 300 <= score <= 850

def classify_credit_risk(score: int) -> str:
    """Map credit score to risk level."""
    if score >= 750:
        return "LOW"
    elif score >= 700:
        return "MODERATE"
    # ... etc

def assess_credit_profile(score: int, history: Dict) -> Dict[str, any]:
    """Assess applicant's credit profile."""
    if not validate_credit_score(score):
        raise ValueError("Invalid credit score")
    risk = classify_credit_risk(score)
    summary = extract_history_summary(history)
    return {
        "risk_level": risk,
        "summary": summary,
        "score": score
    }

# ❌ AVOID: Large, monolithic functions
def assess_everything(data):
    if not (300 <= data['score'] <= 850):
        raise ValueError
    # ... 50 lines of logic mixed together
```

### 3. Docstrings on Every Agent and Node (Critical for Live Explanation)

**Rule:** Every agent and orchestration node MUST have a detailed docstring explaining:
- What it does (high-level)
- What it takes as input
- What it returns as output
- Key decision logic or rules applied
- Latency/performance characteristics

**Agent Docstring Template:**
```python
def applicant_profile_agent(state: ApplicationState) -> ApplicationState:
    """
    Applicant Profile Analysis Agent - Evaluates personal and employment profile.
    
    This agent queries the ApplicantDB MCP server to retrieve applicant history,
    calculates income stability metrics, assesses employment risk, and flags
    any anomalies in employment history or profile completeness.
    
    INPUT:
      state.applicant_data: ApplicationData
        - age, income, employment_type, existing_liabilities, location, timestamp
    
    OUTPUT:
      state.profile_analysis: ProfileAnalysis
        - income_stability_score (0-100): Higher = more stable
        - employment_risk: "LOW" | "MEDIUM" | "HIGH"
        - credit_summary: Text summary of credit history
        - completeness_flags: List of missing/anomalous fields
        - confidence (0.0-1.0): Certainty of analysis
    
    DECISION LOGIC:
      1. Query ApplicantDB for employment history (job dates, tenure, gaps)
      2. Calculate income stability based on:
         - Years at current job (>= 5 years = stable)
         - Income consistency (< 10% variance = stable)
         - Employment gaps (> 6 months = anomaly flag)
      3. Classify employment risk:
         - LOW: Employed >= 2 years at same company, stable income
         - MEDIUM: 1-2 years or recent job change
         - HIGH: Unemployed or multiple recent changes
      4. Summarize credit history from credit notes
      5. Flag completeness issues and anomalies
    
    LATENCY:
      Target: < 2 seconds (p95)
      Breakdown:
        - ApplicantDB query: 200-300ms
        - Claude AI invocation: 1500-1800ms
        - Post-processing: 50-100ms
    
    ERRORS:
      - MCP server unavailable: Fallback to cached data
      - Claude API timeout: Escalate to manual review
      - Invalid input data: Raise ValueError
    """
    # Implementation details
    ...
```

**Node Docstring Template:**
```python
def profile_agent_node(state: ApplicationState) -> ApplicationState:
    """
    LangGraph Node: Execute Applicant Profile Agent.
    
    Orchestration node that invokes the applicant_profile_agent and updates
    the workflow state. Handles errors by catching exceptions and updating
    error_state if agent fails.
    
    INPUT:
      state: ApplicationState with applicant_data populated
    
    OUTPUT:
      state: Updated with profile_analysis field
    
    EXECUTION FLOW:
      1. Check applicant_data is complete
      2. Invoke applicant_profile_agent(state)
      3. Update state with profile_analysis output
      4. Log execution time
      5. On error: Update error_state and return for error_handler
    
    ROUTING:
      Next node: financial_agent_node (if success)
      Error path: error_handler_node (if exception raised)
    """
    # Implementation details
    ...
```

### 4. Pydantic Models for All Data Schemas

**Rule:** Use Pydantic for all input/output validation. Define models in `src/utils/schemas.py` for reusability.

```python
# src/utils/schemas.py
from pydantic import BaseModel, Field, validator
from decimal import Decimal
from datetime import datetime
from typing import List, Optional

class ApplicationData(BaseModel):
    """Input: Loan application data from user."""
    applicant_id: str = Field(..., description="Unique applicant ID")
    age: int = Field(..., ge=18, le=80, description="Applicant age in years")
    income: Decimal = Field(..., gt=0, le=Decimal("9999999"), description="Annual gross income")
    employment_type: str = Field(..., description="Employment type")
    credit_score: int = Field(..., ge=300, le=850, description="Credit score (FICO)")
    loan_amount: Decimal = Field(..., ge=Decimal("1000"), le=Decimal("5000000"))
    tenure_months: int = Field(..., ge=12, le=360)
    existing_liabilities: Decimal = Field(..., ge=0)
    location: str = Field(..., description="2-letter country code")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    @validator("employment_type")
    def validate_employment(cls, v: str) -> str:
        allowed = {"Salaried", "Self-Employed", "Unemployed", "Retired"}
        if v not in allowed:
            raise ValueError(f"Must be one of {allowed}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "applicant_id": "APP-12345",
                "age": 35,
                "income": 85000.00,
                # ... etc
            }
        }
```

### 5. Error Handling & Logging

**Rule:** Log all errors with trace_id, include context, use structured JSON logging.

```python
# ✅ GOOD: Structured logging with trace_id
from src.utils.logger import get_logger

logger = get_logger(__name__)

def risky_operation(trace_id: str, applicant_id: str) -> Dict:
    """Perform risky operation with proper error handling."""
    try:
        logger.info(
            "Operation started",
            extra={"trace_id": trace_id, "applicant_id": applicant_id}
        )
        result = perform_work()
        logger.info(
            "Operation succeeded",
            extra={"trace_id": trace_id, "applicant_id": applicant_id, "duration_ms": 150}
        )
        return result
    except ValueError as e:
        logger.error(
            f"Input validation failed: {str(e)}",
            extra={"trace_id": trace_id, "applicant_id": applicant_id, "error": str(e)}
        )
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error: {str(e)}",
            extra={"trace_id": trace_id, "applicant_id": applicant_id},
            exc_info=True
        )
        raise

# ❌ AVOID: Silent failures, print statements
def risky_operation(data):
    try:
        result = perform_work()
        print("Success!")  # Never use print()
        return result
    except:
        pass  # Never silently catch all exceptions
```

### 6. Comments & Documentation

**Rule:** Docstrings on functions/classes/modules; minimal inline comments (only for non-obvious WHY).

```python
# ✅ GOOD: Clear docstrings, no obvious comments
def calculate_dti(
    monthly_debt: Decimal,
    gross_monthly_income: Decimal
) -> float:
    """
    Calculate debt-to-income ratio.
    
    DTI is the percentage of gross monthly income that goes toward debt payments.
    Formula: DTI = (Monthly Debt / Gross Monthly Income)
    
    Args:
        monthly_debt: Total monthly debt obligations in dollars
        gross_monthly_income: Gross monthly income before taxes
    
    Returns:
        DTI as float (0.0-1.0 typical range)
    
    Raises:
        ValueError: If income is zero or negative
    """
    if gross_monthly_income <= 0:
        raise ValueError("Gross monthly income must be positive")
    return float(monthly_debt / gross_monthly_income)

# ❌ AVOID: No docstring, obvious comments
def calculate_dti(monthly_debt, gross_monthly_income):
    # Calculate DTI
    dti = monthly_debt / gross_monthly_income  # Divide debt by income
    return dti
```

### 7. Testing: Unit & Integration Tests

**Rule:** Write tests alongside code. Run tests after every change.

```python
# tests/unit/test_agents.py
import pytest
from decimal import Decimal
from src.agents.applicant_profile_agent import applicant_profile_agent
from src.utils.schemas import ApplicationData, ProfileAnalysis

def test_applicant_profile_agent_stable_employment():
    """Test profile agent with stable long-term employment."""
    state = {
        "applicant_data": ApplicationData(
            applicant_id="APP-001",
            age=45,
            income=Decimal("100000"),
            employment_type="Salaried",
            existing_liabilities=Decimal("20000"),
            location="US"
        ),
        "trace_id": "trace-test-001"
    }
    
    result = applicant_profile_agent(state)
    
    assert result["profile_analysis"].income_stability_score >= 80
    assert result["profile_analysis"].employment_risk == "LOW"
    assert result["profile_analysis"].confidence >= 0.9

def test_applicant_profile_agent_employment_gap():
    """Test profile agent detects employment gaps."""
    # Test data with 12-month gap
    state = {...}
    result = applicant_profile_agent(state)
    
    assert "Employment gap detected" in result["profile_analysis"].completeness_flags
```

### 8. Naming Conventions

```python
# Constants (SCREAMING_SNAKE_CASE)
DTI_FAVORABLE_THRESHOLD = 0.36
DTI_BORDERLINE_THRESHOLD = 0.50
CONFIDENCE_THRESHOLD_FOR_AUTO_DECISION = 0.75
MAX_AGENT_RETRIES = 2
AGENT_TIMEOUT_SECONDS = 2

# Functions (snake_case)
def calculate_dti(monthly_debt: Decimal, income: Decimal) -> float: ...
def classify_credit_risk(score: int) -> str: ...

# Classes (PascalCase)
class ApplicationData(BaseModel): ...
class ProfileAnalysis(BaseModel): ...
class ApplicantProfileAgent: ...

# Private functions/variables (_snake_case)
def _validate_input(data: Dict) -> bool: ...
_internal_cache: Dict = {}

# LangGraph nodes (descriptive_verb_noun)
def validate_input_node(state: ApplicationState) -> ApplicationState: ...
def profile_agent_node(state: ApplicationState) -> ApplicationState: ...
def error_handler_node(state: ApplicationState) -> ApplicationState: ...
```

---

## Development Workflow: Build in Small Steps

### Golden Rule: **Build → Test → Commit** (Every 30-60 minutes)

This ensures code quality, enables live code walkthrough during evaluation, and prevents large refactoring later.

### Phase 1 Workflow (Weeks 1-2)

#### Week 1: Architecture & Foundations

**Day 1: Project Structure & Config**
```bash
# 1. Create folder structure
mkdir -p src/{api,orchestration,agents,mcp_servers,ui,utils,database}
mkdir -p tests/{unit,integration,fixtures}
mkdir -p config logs data

# 2. Create base files (empty modules)
touch src/__init__.py src/api/__init__.py src/orchestration/__init__.py ...

# 3. Setup environment
cp config/dev.env .env
export ANTHROPIC_API_KEY="sk-ant-..."

# 4. Create requirements.txt and install
pip install fastapi uvicorn streamlit pydantic sqlalchemy langgraph langchain anthropic

# 5. Test installation
python -c "import fastapi; import streamlit; import langgraph; print('OK')"

# 6. COMMIT
git add -A && git commit -m "feat: Project structure setup and dependencies"
```

**Day 2: Core Models & Schemas**
```bash
# 1. Create src/utils/schemas.py with all Pydantic models
#    (ApplicationData, ProfileAnalysis, FinancialAnalysis, DecisionResult, etc.)

# 2. Create src/utils/constants.py with decision thresholds
#    (DTI ranges, credit score bands, LTI ranges)

# 3. Run tests
pytest tests/unit/test_schemas.py -v

# 4. COMMIT
git add src/utils/schemas.py src/utils/constants.py && \
  git commit -m "feat: Define all Pydantic models and constants"
```

**Day 3: Database Setup**
```bash
# 1. Create src/database/models.py with SQLAlchemy ORM models
# 2. Create db/sqlite.py with connection setup
# 3. Create scripts/init_db.py to initialize schema
# 4. Run initialization
python scripts/init_db.py

# 5. Test database
sqlite3 data/loans.db ".schema"

# 6. COMMIT
git add src/database/ db/ scripts/init_db.py && \
  git commit -m "feat: Database schema and initialization"
```

**Day 4: Logging & Configuration**
```bash
# 1. Create src/utils/logger.py with structured JSON logging
# 2. Create src/utils/config.py to load env variables
# 3. Create config/logging_config.json
# 4. Test logging
python -c "from src.utils.logger import get_logger; logger = get_logger('test'); logger.info('Test log')"

# 5. Verify logs are structured JSON
grep "Test log" logs/app.log | jq '.'

# 6. COMMIT
git add src/utils/logger.py src/utils/config.py config/logging_config.json && \
  git commit -m "feat: Structured logging and configuration management"
```

**Day 5: Input Validators**
```bash
# 1. Create src/utils/validators.py with validation for each input field
# 2. Write unit tests in tests/unit/test_validators.py
# 3. Run tests
pytest tests/unit/test_validators.py -v

# 4. COMMIT
git add src/utils/validators.py tests/unit/test_validators.py && \
  git commit -m "feat: Input field validators with comprehensive tests"
```

#### Week 2: MCP Servers & Agents Foundation

**Day 6: MCP Server Base & ApplicantDB**
```bash
# 1. Create src/mcp_servers/base.py (abstract base class)
# 2. Create src/mcp_servers/applicant_db.py
# 3. Write unit tests
pytest tests/unit/test_mcp_servers.py -v

# 4. COMMIT
git add src/mcp_servers/base.py src/mcp_servers/applicant_db.py && \
  git commit -m "feat: MCP ApplicantDB server with query tools"
```

**Day 7: Risk & Decision MCP Servers**
```bash
# 1. Create src/mcp_servers/risk_rules_db.py
# 2. Create src/mcp_servers/decision_synthesis.py
# 3. Test both
pytest tests/unit/test_mcp_servers.py::test_risk_rules_db -v

# 4. COMMIT
git add src/mcp_servers/risk_rules_db.py src/mcp_servers/decision_synthesis.py && \
  git commit -m "feat: MCP RiskRulesDB and DecisionSynthesis servers"
```

**Day 8: Agent Base Class**
```bash
# 1. Create src/agents/base_agent.py (abstract base)
#    - Defines invoke() method
#    - Handles Claude AI invocation
#    - Manages MCP tool calls
#    - Includes comprehensive docstring on agent lifecycle

# 2. Unit test base class
pytest tests/unit/test_agents.py::test_agent_base -v

# 3. COMMIT
git add src/agents/base_agent.py tests/unit/test_agents.py && \
  git commit -m "feat: Agent base class with Claude integration"
```

**Day 9: Applicant Profile Agent Implementation**
```bash
# 1. Create src/agents/applicant_profile_agent.py
#    - Extends BaseAgent
#    - Implements analyze() method
#    - Queries ApplicantDB MCP
#    - Invokes Claude for analysis
#    - INCLUDE: Detailed docstring (copy template above)

# 2. Write unit tests
#    - test_stable_employment()
#    - test_employment_gap_detected()
#    - test_missing_history()

pytest tests/unit/test_agents.py::test_applicant_profile_agent -v

# 3. Manual test with sample data
python scripts/test_agents.py --agent profile

# 4. COMMIT
git add src/agents/applicant_profile_agent.py && \
  git commit -m "feat: Applicant Profile Agent with full documentation"
```

**Day 10: Financial Risk Agent Implementation**
```bash
# 1. Create src/agents/financial_risk_agent.py
#    - Calculate DTI, LTI
#    - Classify credit risk
#    - Detect anomalies
#    - Query RiskRulesDB MCP
#    - INCLUDE: Detailed docstring

# 2. Write unit tests
#    - test_dti_calculation()
#    - test_credit_score_classification()
#    - test_anomaly_detection()

pytest tests/unit/test_agents.py::test_financial_risk_agent -v

# 3. COMMIT
git add src/agents/financial_risk_agent.py && \
  git commit -m "feat: Financial Risk Agent with comprehensive testing"
```

### Continuous Testing Approach

**After Each Implementation:**
```bash
# 1. Run unit tests for changed module
pytest tests/unit/test_<module>.py -v

# 2. Run type checking (optional but recommended)
mypy src/<module>.py --ignore-missing-imports

# 3. Check logging works
python -c "from src.utils.logger import get_logger; logger = get_logger('test'); logger.info('Test')"

# 4. If all pass, commit
git add <files> && git commit -m "feat: <description>"

# 5. Every end of day, run full suite
pytest tests/ -v --cov=src
```

### Example: Adding a New Agent During Live Evaluation

If evaluator asks you to add a new agent during walkthrough:

```bash
# 1. Discuss approach with evaluator (2-3 min)
# 2. Create agent file with detailed docstring (5 min)
# 3. Write unit test (5 min)
# 4. Run test (1 min)
# 5. Show code & tests to evaluator
# 6. Explain via docstrings why design works this way
```

This is why **comprehensive docstrings** are critical—they let you quickly explain code without lengthy context switching.

---

## Testing Strategy

### Test Pyramid

```
         [E2E Tests]              (1-2 tests)
        [Integration]             (10-15 tests)
       [Unit Tests]               (50+ tests)
```

### Test Coverage Goals
- Unit tests: 80%+ of functions
- Integration tests: All workflows (approval, rejection, manual review)
- E2E tests: Happy path + error scenarios

### Running Tests

```bash
# All tests with coverage
pytest tests/ -v --cov=src --cov-report=html

# Just unit tests
pytest tests/unit/ -v

# Just integration tests
pytest tests/integration/ -v

# Single test file
pytest tests/unit/test_agents.py -v

# Single test function
pytest tests/unit/test_agents.py::test_applicant_profile_agent -v

# With output/prints
pytest tests/ -v -s

# Watch mode (auto-run on save) - requires pytest-watch
ptw tests/ -- -v
```

### Mock Data for Testing

All mock data in `tests/fixtures/mock_data.py`:
- 10 sample applicants (various profiles)
- Pre-defined test cases (should-approve, should-reject, should-review)
- Expected outcomes for validation

### Example Unit Test

```python
# tests/unit/test_agents.py
import pytest
from decimal import Decimal
from src.agents.applicant_profile_agent import applicant_profile_agent
from src.utils.schemas import ApplicationData, ApplicationState

@pytest.fixture
def mock_state():
    """Fixture: Mock application state."""
    return {
        "applicant_data": ApplicationData(
            applicant_id="APP-TEST-001",
            age=35,
            income=Decimal("85000"),
            employment_type="Salaried",
            credit_score=745,
            loan_amount=Decimal("150000"),
            tenure_months=180,
            existing_liabilities=Decimal("12000"),
            location="US"
        ),
        "trace_id": "trace-test-001",
        "profile_analysis": None,
        "error_state": None
    }

def test_applicant_profile_agent_with_stable_employment(mock_state):
    """Test profile agent returns HIGH stability for long-term employed applicant."""
    # Execute agent
    result_state = applicant_profile_agent(mock_state)
    
    # Assertions
    profile = result_state["profile_analysis"]
    assert profile is not None
    assert profile.income_stability_score >= 80
    assert profile.employment_risk == "LOW"
    assert profile.confidence >= 0.9
    assert len(profile.completeness_flags) == 0

def test_applicant_profile_agent_flags_employment_gap(mock_state):
    """Test profile agent detects employment gap anomaly."""
    # Modify state to have employment gap
    mock_state["applicant_data"].employment_type = "Salaried"
    # (In real test, mock MCP to return history with gap)
    
    result_state = applicant_profile_agent(mock_state)
    profile = result_state["profile_analysis"]
    
    assert any("employment gap" in flag.lower() for flag in profile.completeness_flags)
    assert profile.confidence < 0.9
```

---

## Key Principles for Phase 1

1. **Type Safety:** Every variable, parameter, return value has explicit types
2. **Explainability:** Docstrings on every agent and node (for live walkthrough)
3. **Auditability:** Structured logging with trace_id on every operation
4. **Testability:** Write tests alongside code; run after every change
5. **Incremental:** Small commits (30-60 min intervals); no monolithic changes
6. **Reusability:** Pydantic models and constants centralized in utils/
7. **Documentation:** Comment the WHY, not the WHAT; code is self-documenting

---

## Attribution

Co-Authored-By: Claude Haiku 4.5 <[EMAIL_REDACTED]>

---

## Quick Reference

| Need | Command |
|------|---------|
| Start FastAPI | `python -m uvicorn src.api.main:app --reload` |
| Start Streamlit | `streamlit run src/ui/streamlit_app.py` |
| Run tests | `pytest tests/ -v` |
| Run single test | `pytest tests/unit/test_agents.py::test_name -v` |
| Init database | `python scripts/init_db.py` |
| View logs | `tail -f logs/app.log` |
| Search logs | `grep "trace-id" logs/app.log \| jq '.'` |
| Check types | `mypy src/ --ignore-missing-imports` |
| Format code | `black src/ tests/` |

---

**Last Updated:** 2026-10-29  
**Phase:** 1 (Project Setup)  
**Status:** Ready for Development
