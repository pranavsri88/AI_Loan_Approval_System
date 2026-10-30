# Phase 3: Applicant Profile Agent Implementation ✓

**Date:** 2026-10-29  
**Phase:** 3 - Agents Implementation  
**Status:** ✅ First Agent Complete - Ready for Review  
**Component:** Applicant Profile Agent (Agent 1 of 4)

---

## What Was Implemented

### 1. Agent Prompts (src/agents/prompts.py)

Created centralized prompt templates for all 4 agents:

- **APPLICANT_PROFILE_SYSTEM_PROMPT** - System instructions for profile analysis
- **APPLICANT_PROFILE_USER_PROMPT_TEMPLATE** - User prompt template with field placeholders
- **FINANCIAL_RISK_SYSTEM_PROMPT** - Financial risk assessment instructions
- **FINANCIAL_RISK_USER_PROMPT_TEMPLATE** - Financial metrics prompt template
- **LOAN_DECISION_SYSTEM_PROMPT** - Decision synthesis instructions
- **LOAN_DECISION_USER_PROMPT_TEMPLATE** - Decision context template
- **COMPLIANCE_ACTION_SYSTEM_PROMPT** - Compliance & action instructions
- **COMPLIANCE_ACTION_USER_PROMPT_TEMPLATE** - Final action template

**Key Design:**
- System prompts define Claude's expert role and expected output format (JSON)
- User prompts use `.format()` templates for dynamic context injection
- All prompts include structured output requirements for reliable JSON parsing
- Prompts are centralized for easy reuse and testing

### 2. Applicant Profile Agent (src/agents/applicant_profile_agent.py)

Implemented first agent extending BaseAgent:

**Architecture:**
```python
class ApplicantProfileAgent(BaseAgent):
    agent_name = "ApplicantProfileAgent"
    mcp_server_url = "http://127.0.0.1:8001"  # ApplicantDB
    
    def analyze(self, applicant_id: str, **kwargs) -> Dict[str, Any]:
        # Fetch data from MCP servers
        # Invoke Claude Sonnet 4.6
        # Validate against ProfileAnalysis schema
        # Return structured output
```

**Key Methods:**

1. `analyze(applicant_id)` - Main entry point
   - Fetches applicant history via ApplicantDB MCP
   - Retrieves employment data and stability score
   - Gets credit inquiries for anomaly detection
   - Constructs context for Claude
   - Invokes Claude via inherited `invoke_claude()` method
   - Validates output against ProfileAnalysis Pydantic schema
   - Returns dictionary matching schema

2. `_fetch_applicant_history()` - Calls ApplicantDB `get_applicant_history` tool
3. `_fetch_employment_data()` - Calls ApplicantDB `get_employment_data` tool
4. `_fetch_credit_inquiries()` - Calls ApplicantDB `get_credit_inquiries` tool
5. `_format_employment_history()` - Formats employment jobs for Claude prompt
6. `_format_credit_inquiries()` - Formats credit data for Claude prompt

**Data Flow:**
```
applicant_id
    ↓
ApplicantDB MCP server (3 tools)
    ↓ get_applicant_history()
    ↓ get_employment_data()
    ↓ get_credit_inquiries()
    ↓
Format context
    ↓
Claude Sonnet 4.6 (invoke_claude)
    ↓
ProfileAnalysis schema validation
    ↓
Return ProfileAnalysis dict
```

**Output Schema (ProfileAnalysis):**
```python
{
    "income_stability_score": 85,           # 0-100
    "employment_risk": "LOW",               # LOW, MEDIUM, HIGH
    "credit_summary": "...",                # Text summary
    "completeness_flags": [],               # Anomalies/missing data
    "confidence": 0.92,                     # 0.0-1.0
    "reasoning": "..."                      # Explanation
}
```

### 3. Unit Tests (tests/unit/test_applicant_profile_agent.py)

Comprehensive test coverage with 7 tests using mocked responses:

| Test | Scenario | Expected Outcome |
|------|----------|------------------|
| `test_applicant_profile_agent_stable_employment` | 6-year tenure, no gaps, clean credit | LOW risk, 85+ stability score |
| `test_applicant_profile_agent_employment_gap` | 17-month employment gap | MEDIUM risk, flags gap anomaly |
| `test_applicant_profile_agent_recent_job_change` | 3 months at new job | MEDIUM risk, low stability |
| `test_applicant_profile_agent_high_credit_inquiries` | 3 hard inquiries in 30 days | Flags inquiry anomaly |
| `test_applicant_profile_agent_missing_employment_history` | Young with no history | HIGH risk, insufficient data |
| `test_applicant_profile_agent_mcp_error` | MCP server returns error | Returns error gracefully |
| `test_applicant_profile_agent_output_schema_validation` | Self-employed for 11 years | Output validates against ProfileAnalysis |

**Test Pattern:**
- Mock MCP server responses (get_applicant_history, get_employment_data, get_credit_inquiries)
- Mock Claude response via `invoke_claude()`
- Call `agent.analyze(applicant_id)`
- Assert output matches expected schema and values

**Coverage:**
- Happy path: Stable employment profile ✓
- Anomalies: Employment gaps, recent changes, high inquiries ✓
- Edge cases: Missing history, MCP errors ✓
- Schema validation: Output matches ProfileAnalysis ✓

---

## Code Quality

### Type Hints
- ✅ All functions have explicit type hints
- ✅ Return types specified on all methods
- ✅ Pydantic models for input/output validation
- ✅ No implicit `Any` types

### Documentation
- ✅ Module docstring explaining responsibilities
- ✅ Class docstring with MCP server, outputs, decision logic
- ✅ Method docstrings with Args, Returns, Raises
- ✅ Inline comments only for non-obvious logic

### Error Handling
- ✅ Try/catch with structured logging
- ✅ MCP errors handled gracefully (return error dict)
- ✅ Claude timeout/failures propagated to caller
- ✅ Validation errors from Pydantic re-raised

### Testing
- ✅ 7 comprehensive unit tests
- ✅ Mock MCP server responses
- ✅ Mock Claude responses
- ✅ Test both happy path and error scenarios
- ✅ Validate output schema

---

## MCP Server Integration

Agent connects to **ApplicantDB MCP server** (port 8001) with 3 tools:

1. **`get_applicant_history(applicant_id)`**
   - Returns: `{"applicant": {...}, "history_years": int}`
   - Data: age, income, employment_type, credit_score, liabilities, location

2. **`get_employment_data(applicant_id)`**
   - Returns: `{"jobs": [...], "stability_score": 0-100, "gaps": [...]}`
   - Data: Job history with tenure, career gaps

3. **`get_credit_inquiries(applicant_id)`**
   - Returns: `{"inquiries": [...], "recent_inquiries_3m": int, "anomaly_flags": [...]}`
   - Data: Credit pulls, inquiry dates, anomaly detection

---

## Claude Sonnet 4.6 Integration

Agent invokes Claude via inherited `invoke_claude()` method with:

**System Prompt:**
- Defines Claude's role: "expert loan underwriter specializing in applicant profile analysis"
- Specifies output format: JSON with 6 fields (income_stability_score, employment_risk, credit_summary, etc.)
- Includes decision logic for risk classification

**User Prompt:**
- Provides applicant data (age, income, employment type, credit score, liabilities, location)
- Includes employment history (formatted from MCP data)
- Includes credit inquiries summary
- Asks for analysis and scoring

**Output Parsing:**
- Claude returns JSON in markdown code block
- BaseAgent's `invoke_claude()` extracts and parses JSON
- Validates against ProfileAnalysis schema
- Returns as Python dict

---

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `src/agents/prompts.py` | 150 | Centralized prompt templates |
| `src/agents/applicant_profile_agent.py` | 130 | Agent implementation |
| `tests/unit/test_applicant_profile_agent.py` | 280 | Unit tests with mocks |

**Total:** ~560 lines of code + tests

---

## Next Steps (After User Review)

### Financial Risk Agent (Agent 2)
- Connect to RiskRulesDB MCP server
- Compute DTI, LTI deterministically in code
- Classify credit risk based on thresholds
- Detect financial anomalies
- Invoke Claude for reasoning and risk scoring
- Return FinancialAnalysis schema

### Loan Decision Agent (Agent 3)
- Synthesize profile + financial analysis
- Apply decision rules and policies
- Classify as APPROVED, REJECTED, or REQUIRES_REVIEW
- Calculate decision confidence
- Identify key decision factors
- Return DecisionResult schema

### Compliance & Action Agent (Agent 4)
- Execute final action (notify applicant, log case)
- Connect to NotificationSystem MCP server
- Create immutable audit trail
- Generate case summaries
- Return ComplianceAction schema

---

## Key Design Decisions

### 1. Inherited BaseAgent
- ✅ Reuses MCP client setup and Claude invocation logic
- ✅ Consistent error handling across all agents
- ✅ Structured logging with trace_id
- ✅ JSON parsing and validation in one place

### 2. Centralized Prompts
- ✅ Easy to iterate on prompts without changing agent code
- ✅ Single source of truth for system instructions
- ✅ Reusable templates with `.format()` placeholders
- ✅ Can be overridden per environment if needed

### 3. Direct MCP Function Calls
- ✅ No HTTP client overhead (in-process FastMCP)
- ✅ Synchronous, predictable control flow
- ✅ Easy to mock in tests
- ✅ Can switch to remote later if needed

### 4. Deterministic + LLM Reasoning
- ✅ Calculations (stability score) done in code
- ✅ Claude handles subjective assessment and reasoning
- ✅ Clear separation of concerns
- ✅ Easier to audit and explain decisions

### 5. Schema Validation
- ✅ All outputs validated against Pydantic models
- ✅ Type safety end-to-end
- ✅ Catches malformed Claude responses
- ✅ Enables API contracts and documentation

---

## Testing the Agent

**Option 1: Install and run pytest**
```bash
pip install -r requirements.txt
python -m pytest tests/unit/test_applicant_profile_agent.py -v
```

**Option 2: Manual testing**
```python
from src.agents.applicant_profile_agent import ApplicantProfileAgent

agent = ApplicantProfileAgent()
result = agent.analyze("APP-STABLE-001")
print(result)
```

**Option 3: In orchestration (Phase 3B)**
```python
# LangGraph will orchestrate agents when full workflow implemented
```

---

## Checklist: Agent Implementation Complete ✓

- [x] Agent extends BaseAgent
- [x] Connects to MCP server (ApplicantDB)
- [x] Fetches context via MCP tools
- [x] Constructs Claude prompts from templates
- [x] Invokes Claude Sonnet 4.6
- [x] Validates output against Pydantic schema
- [x] Returns structured output
- [x] Comprehensive unit tests (7 tests)
- [x] Error handling and logging
- [x] Type hints throughout
- [x] Documentation on every method
- [x] No external dependencies beyond base agent

---

## Performance Targets (from CLAUDE.md)

**Applicant Profile Agent Latency:**
- Target: < 2 seconds (p95)
- Breakdown:
  - ApplicantDB queries: 200-300ms
  - Claude AI invocation: 1500-1800ms
  - Post-processing: 50-100ms

---

## Author

**Phase 3 Implementation:** Applicant Profile Agent  
**Status:** ✅ Ready for Review & Integration Testing  
**Next:** User reviews → Proceeds to Financial Risk Agent  

See [CLAUDE.md](CLAUDE.md) for coding conventions and [docs/system_design.md](docs/system_design.md) for architecture overview.

