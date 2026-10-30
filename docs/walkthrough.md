# 🎯 Code Walkthrough: Layer-by-Layer Explanation

A complete walkthrough of the Agentic AI Loan Approval System, from user input to final decision.

## 🔧 Recent Improvements (Latest Build)

### Bug Fixes
- ✅ **Audit Trail Auto-Fetch** - Audit trail now auto-fetches when tab loads (no manual refresh needed)
- ✅ **Type Safety** - Added proper type checking for string operations in Streamlit UI
- ✅ **Session State** - Added `audit_result` initialization to prevent NoneType errors
- ✅ **Agent Lazy Loading** - Fixed compliance agent to use getter function pattern
- ✅ **Graph Entry Point** - Explicitly set workflow entry point to ensure proper routing
- ✅ **Request Timeout** - Increased request timeout to 15 seconds for agent processing (from 10s)

### Performance Optimizations
- **Agent Processing Time**: ~10-11 seconds (Claude Haiku API calls are the bottleneck)
- **Timeout Strategy**: 15 seconds allows for reliable agent completion without failures
- **User Feedback**: "Processing..." spinner during wait prevents perception of hanging
- **Graceful Handling**: Timeout errors display helpful messaging to retry

### User Experience
- **Decision Display Tab**: Auto-fetches decision immediately on tab load
- **Audit Trail Tab**: Auto-fetches audit trail immediately on tab load
- **Error Handling**: Graceful degradation with helpful messages if data not ready
- **Type Checking**: Safe string slicing with proper None validation
- **Progress Visibility**: Clear status messages during multi-second processing

---

## Architecture Overview

```
User Input (Chatbot UI)
    ↓
Layer 1: Streamlit UI (Conversational Interface)
    ↓
Layer 2: FastAPI (REST API with Validation)
    ↓
Layer 3: LangGraph Orchestrator (Workflow Coordination)
    ↓
Layer 4: AI Agents (Claude Haiku 4.5 Reasoning)
    ↓
Layer 5: MCP Servers (Data & Tool Access)
    ↓
Layer 6: SQLite Database (Persistence & Audit)
    ↓
Final Decision Output
```

---

## Layer 1: Streamlit Chatbot UI

### Purpose
Collect loan application data from user through conversational interface and display decision results.

### Files
- **src/ui/app.py** (400+ lines)

### Key Functions

#### `chat_input()` - Collect User Input
```python
# Located in src/ui/app.py (lines ~150-200)

def chat_input(placeholder: str) -> str:
    """Collect user input through Streamlit chat interface"""
    # Data In: Field name (e.g., "age", "income")
    # Data Out: User-entered string value
    return st.chat_input(placeholder)
```

**Data Flow:**
```
Input:  Field prompt text
        ├─ "What is your age? (18-80)"
        └─ "What is your annual income?"
        
Output: User response string
        ├─ "35"
        └─ "85000"
```

#### `parse_field_value()` - Validate & Parse Input
```python
# Located in src/ui/app.py (lines ~90-130)

def parse_field_value(field: str, value: str) -> Any:
    """Parse and validate user input for a specific field"""
    # Data In: Field name + string value
    # Data Out: Parsed & validated value or ValueError
```

**Data Flow:**
```
Input:  ("age", "35")
        ("credit_score", "1000")  ← Invalid!
        
Output: 35 (int)
        ValueError: "Credit score must be between 300 and 850"
```

#### `call_api()` - Submit to Backend
```python
# Located in src/ui/app.py (lines ~60-85)

def call_api(application_data: Dict[str, Any]) -> Dict[str, Any]:
    """Call FastAPI endpoint and retrieve decision"""
    response = requests.post(
        f"{st.session_state.api_url}/api/v1/applications",
        json=application_data,
        timeout=10
    )
    # Data In: Complete application dict (9 fields)
    # Data Out: Decision result with trace_id, decision, factors
```

**Data Flow:**
```
Input:  {
          "applicant_id": "APP-001",
          "age": 35,
          "income": 85000,
          "employment_type": "Salaried",
          "credit_score": 745,
          "loan_amount": 150000,
          "tenure_months": 180,
          "existing_liabilities": 12000,
          "location": "US"
        }
        
Output: {
          "decision": "APPROVED",
          "confidence": 0.92,
          "risk_score": 20,
          "case_id": "CASE-2026-10-29-12345",
          "agents_run": ["validate", "profile", "financial", "decision", "compliance"],
          "decision_factors": [...]
        }
```

### Streamlit Session State
```python
st.session_state.messages          # Chat history
st.session_state.current_application  # Form being filled
st.session_state.field_index       # Current field number (0-8)
st.session_state.decision_result   # Final decision display
```

---

## Layer 2: FastAPI REST API

### Purpose
Accept HTTP requests, validate input, invoke orchestrator, return results.

### Files
- **src/api/main.py** (100 lines) - App setup
- **src/api/routes.py** (180 lines) - Endpoint handlers
- **src/api/models.py** (90 lines) - Request/response validation
- **src/api/middleware.py** (70 lines) - Logging & error handling

### Key Functions

#### `submit_application()` - POST /api/v1/applications
```python
# Located in src/api/routes.py (lines ~50-110)

@app.post("/api/v1/applications", response_model=ApplicationResponse)
async def submit_application(request: ApplicationRequest) -> ApplicationResponse:
    """Submit a new loan application"""
    # Data In: ApplicationRequest (Pydantic model with 9 fields)
    # Data Out: ApplicationResponse (trace_id + status)
    
    # Step 1: Validate with Pydantic
    app_data = request.dict()
    
    # Step 2: Call orchestrator
    result = run_application(app_data)
    
    # Step 3: Cache result in memory
    _application_cache[trace_id] = result
    
    # Step 4: Return response
    return ApplicationResponse(...)
```

**Data Flow:**
```
HTTP POST /api/v1/applications
Body: {
  "applicant_id": "APP-001",
  "age": 35,
  "income": 85000,
  ...
}
↓
Pydantic Validation (ApplicationRequest model)
↓
run_application(app_data)  [→ Layer 3]
↓
HTTP 202 Response:
{
  "trace_id": "TRACE-abc123",
  "applicant_id": "APP-001",
  "status": "COMPLETED",
  "timestamp": "..."
}
```

#### `get_application_decision()` - GET /api/v1/applications/{trace_id}
```python
# Located in src/api/routes.py (lines ~115-160)

@app.get("/api/v1/applications/{trace_id}")
async def get_application_decision(trace_id: str) -> DecisionResponse:
    """Retrieve decision for submitted application"""
    # Data In: trace_id (string)
    # Data Out: DecisionResponse (full decision details)
    
    result = _application_cache[trace_id]
    return DecisionResponse(...)
```

**Data Flow:**
```
HTTP GET /api/v1/applications/TRACE-abc123
↓
Lookup in cache: _application_cache[trace_id]
↓
HTTP 200 Response:
{
  "trace_id": "TRACE-abc123",
  "decision": "APPROVED",
  "confidence": 0.92,
  "risk_score": 20,
  "decision_factors": [...],
  "explanation": "..."
}
```

#### `get_audit_trail()` - GET /api/v1/applications/{trace_id}/audit
```python
# Located in src/api/routes.py (lines ~165-200)

@app.get("/api/v1/applications/{trace_id}/audit")
async def get_audit_trail(trace_id: str) -> Dict[str, Any]:
    """Get immutable audit trail"""
    # Data In: trace_id
    # Data Out: Audit log with agents_run, timestamps, decisions
```

**Data Flow:**
```
HTTP GET /api/v1/applications/TRACE-abc123/audit
↓
Lookup audit data: audit = _application_cache[trace_id]["audit"]
↓
HTTP 200 Response:
{
  "trace_id": "TRACE-abc123",
  "case_id": "CASE-2026-10-29-12345",
  "applicant_id": "APP-001",
  "decision": "APPROVED",
  "agents_run": ["validate", "profile", "financial", "decision", "compliance"],
  "timestamp": "..."
}
```

### Pydantic Models
```python
# src/api/models.py

class ApplicationRequest:
    """Input validation - 10 required fields"""
    applicant_id: str
    age: int (18-80)
    income: float (> 0)
    employment_type: str
    credit_score: int (300-850)
    loan_amount: float (>= 1000)
    tenure_months: int (12-360)
    existing_liabilities: float (>= 0)
    location: str (2-letter code)

class DecisionResponse:
    """Output - decision with full details"""
    trace_id: str
    decision: str (APPROVED|REJECTED|REQUIRES_REVIEW)
    confidence: float (0.0-1.0)
    risk_score: int (0-100)
    decision_factors: List[Dict]
    explanation: str
```

---

## Layer 3: LangGraph Orchestrator

### Purpose
Coordinate execution of 4 agents, route decisions, manage state transitions.

### Files
- **src/orchestration/langgraph_workflow.py** (350 lines)
- **src/orchestration/graph_export.py** (80 lines) - Mermaid export

### Key Functions

#### `run_application()` - Main Entry Point
```python
# Located in src/orchestration/langgraph_workflow.py (lines ~200-260)

def run_application(applicant_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute end-to-end workflow"""
    # Data In: Application data dict (9 fields)
    # Data Out: Final decision with trace_id, case_id, agents_run
    
    trace_id = f"TRACE-{uuid.uuid4().hex[:12]}"
    
    # Step 1: Create initial state
    initial_state: ApplicationState = {
        "applicant_data": applicant_data,
        "trace_id": trace_id,
        "profile_analysis": None,
        "financial_analysis": None,
        "decision_result": None,
        "compliance_action": None,
        "agents_run": [],
        "timestamps": {"start": datetime.utcnow()},
        "final_decision": None,
        "final_confidence": None,
        "case_id": None
    }
    
    # Step 2: Create and compile graph
    graph = create_graph()
    
    # Step 3: Invoke workflow
    final_state = graph.invoke(initial_state)
    
    # Step 4: Extract and return results
    return {
        "trace_id": trace_id,
        "decision": final_state["final_decision"],
        "confidence": final_state["final_confidence"],
        "case_id": final_state["case_id"],
        "agents_run": final_state["agents_run"],
        "decision_factors": final_state.get("decision_result", {}).get("decision_factors", []),
        "explanation": final_state.get("decision_result", {}).get("explanation", "")
    }
```

**Data Flow:**
```
Input: {"applicant_id": "APP-001", "age": 35, ...}
  ↓
Initial State Created:
{
  "applicant_data": {...},
  "trace_id": "TRACE-abc123",
  "agents_run": [],
  "profile_analysis": None,
  ...
}
  ↓
Graph Compiled (6 nodes)
  ↓
Graph Invoked
  ↓
Output: {
  "decision": "APPROVED",
  "confidence": 0.92,
  "case_id": "CASE-...",
  "agents_run": ["validate", "profile", "financial", "decision", "compliance"]
}
```

#### `validate_input_node()` - Node 1: Input Validation
```python
# Located in src/orchestration/langgraph_workflow.py (lines ~80-110)

def validate_input_node(state: ApplicationState) -> ApplicationState:
    """Validate application input data"""
    # Data In: state.applicant_data (raw dict)
    # Data Out: Updated state with validated ApplicationData object
    
    # Step 1: Check required fields
    required_fields = ["applicant_id", "age", "income", ...]
    
    # Step 2: Convert to ApplicationData (Pydantic)
    app_data = ApplicationData(**state["applicant_data"])
    state["applicant_data"] = app_data.dict()
    
    # Step 3: Mark as run
    state["agents_run"].append("validate")
    
    return state
```

**State Transitions:**
```
Before: applicant_data = {"age": 35, ...}  (dict, unchecked)
After:  applicant_data = {...}  (validated ApplicationData.dict())
        agents_run = ["validate"]
```

#### `profile_agent_node()` - Node 2: Profile Analysis
```python
# Located in src/orchestration/langgraph_workflow.py (lines ~115-145)

def profile_agent_node(state: ApplicationState) -> ApplicationState:
    """Execute Applicant Profile Agent"""
    # Data In: state.applicant_data
    # Data Out: state.profile_analysis (ProfileAnalysis dict)
    
    applicant_id = state["applicant_data"].get("applicant_id")
    
    # Call Agent 1: Profile
    profile_result = profile_agent.analyze(applicant_id)
    
    state["profile_analysis"] = profile_result
    state["agents_run"].append("profile")
    
    return state
```

**State Transitions:**
```
Before: profile_analysis = None
After:  profile_analysis = {
          "income_stability_score": 85,
          "employment_risk": "LOW",
          "credit_summary": "...",
          "confidence": 0.92,
          ...
        }
        agents_run = ["validate", "profile"]
```

#### `financial_agent_node()` - Node 3: Financial Risk
```python
# Located in src/orchestration/langgraph_workflow.py (lines ~150-180)

def financial_agent_node(state: ApplicationState) -> ApplicationState:
    """Execute Financial Risk Agent"""
    # Data In: state.applicant_data + state.profile_analysis
    # Data Out: state.financial_analysis (FinancialAnalysis dict)
    
    profile = state["profile_analysis"] or {}
    
    # Call Agent 2: Financial Risk
    financial_result = financial_agent.analyze(
        state["applicant_data"],
        stability_score=profile.get("income_stability_score", 50),
        employment_risk=profile.get("employment_risk", "MEDIUM")
    )
    
    state["financial_analysis"] = financial_result
    state["agents_run"].append("financial")
    
    return state
```

**State Transitions:**
```
Before: financial_analysis = None
After:  financial_analysis = {
          "dti": 0.35,
          "dti_classification": "FAVORABLE",
          "credit_score_risk": "LOW",
          "lti": 1.9,
          "risk_score": 20,
          "confidence": 0.92,
          ...
        }
        agents_run = ["validate", "profile", "financial"]
```

#### `decision_agent_node()` - Node 4: Decision Synthesis
```python
# Located in src/orchestration/langgraph_workflow.py (lines ~185-220)

def decision_agent_node(state: ApplicationState) -> ApplicationState:
    """Execute Loan Decision Agent"""
    # Data In: state.profile_analysis + state.financial_analysis
    # Data Out: state.decision_result + state.final_decision
    
    # Call Agent 3: Decision
    decision_result = decision_agent.analyze(
        state["profile_analysis"] or {},
        state["financial_analysis"] or {}
    )
    
    state["decision_result"] = decision_result
    state["final_decision"] = decision_result.get("classification")
    state["final_confidence"] = decision_result.get("confidence")
    state["agents_run"].append("decision")
    
    return state
```

**State Transitions:**
```
Before: decision_result = None
        final_decision = None
        final_confidence = None
        
After:  decision_result = {
          "classification": "APPROVED",
          "risk_score": 20,
          "confidence": 0.92,
          "decision_factors": [...],
          "explanation": "..."
        }
        final_decision = "APPROVED"
        final_confidence = 0.92
        agents_run = ["validate", "profile", "financial", "decision"]
```

#### `should_escalate_to_review()` - Conditional Routing
```python
# Located in src/orchestration/langgraph_workflow.py (lines ~225-250)

def should_escalate_to_review(state: ApplicationState) -> str:
    """Decide: manual review or compliance action?"""
    # Data In: state.final_decision, state.final_confidence, financial_analysis
    # Data Out: "manual_review" or "execute"
    
    if state.get("error_state"):
        return "manual_review"
    
    confidence = state.get("final_confidence", 1.0)
    if confidence < settings.confidence_threshold:  # 0.75
        return "manual_review"
    
    financial = state.get("financial_analysis", {})
    if financial.get("anomaly_detected"):
        return "manual_review"
    
    decision = state.get("final_decision", "REQUIRES_REVIEW")
    if decision == "REQUIRES_REVIEW":
        return "manual_review"
    
    return "execute"  # Go to compliance
```

**Routing Logic:**
```
Input: state with final_decision, final_confidence, anomalies
  ↓
Conditions:
  ├─ error_state present? → "manual_review"
  ├─ confidence < 0.75? → "manual_review"
  ├─ anomalies? → "manual_review"
  ├─ decision == REQUIRES_REVIEW? → "manual_review"
  └─ else → "execute"
  ↓
Output: "manual_review" or "execute"
```

#### `manual_review_node()` - Node 5a: Manual Review Path
```python
# Located in src/orchestration/langgraph_workflow.py (lines ~255-270)

def manual_review_node(state: ApplicationState) -> ApplicationState:
    """Escalate to human underwriter"""
    # Data In: All prior analysis
    # Data Out: Decision marked as REQUIRES_REVIEW
    
    if state["final_decision"] != "REQUIRES_REVIEW":
        state["final_decision"] = "REQUIRES_REVIEW"
    
    state["agents_run"].append("manual_review")
    
    return state
```

**State Transitions:**
```
Terminal node - awaits human review
agents_run = ["validate", "profile", "financial", "decision", "manual_review"]
```

#### `compliance_agent_node()` - Node 5b: Compliance & Action
```python
# Located in src/orchestration/langgraph_workflow.py (lines ~275-305)

def compliance_agent_node(state: ApplicationState) -> ApplicationState:
    """Execute Compliance & Action Agent"""
    # Data In: state.decision_result + applicant_id
    # Data Out: state.compliance_action + state.case_id
    
    # Call Agent 4: Compliance
    compliance_result = compliance_agent.analyze(
        state["decision_result"] or {},
        state["applicant_data"].get("applicant_id", "UNKNOWN"),
        state["trace_id"]
    )
    
    state["compliance_action"] = compliance_result
    state["case_id"] = compliance_result.get("case_id")
    state["agents_run"].append("compliance")
    
    return state
```

**State Transitions:**
```
Before: compliance_action = None
        case_id = None
        
After:  compliance_action = {
          "action_taken": "APPROVED",
          "notification_status": "SENT",
          "case_id": "CASE-2026-10-29-12345",
          ...
        }
        case_id = "CASE-2026-10-29-12345"
        agents_run = ["validate", "profile", "financial", "decision", "compliance"]
```

#### `create_graph()` - Build LangGraph
```python
# Located in src/orchestration/langgraph_workflow.py (lines ~310-335)

def create_graph() -> CompiledStateGraph:
    """Create and compile the LangGraph workflow"""
    
    graph = StateGraph(ApplicationState)
    
    # Add nodes
    graph.add_node("validate", validate_input_node)
    graph.add_node("profile", profile_agent_node)
    graph.add_node("financial", financial_agent_node)
    graph.add_node("decision", decision_agent_node)
    graph.add_node("manual_review", manual_review_node)
    graph.add_node("compliance", compliance_agent_node)

    # Set entry point (ensures validate is reachable)
    graph.set_entry_point("validate")
    
    # Add edges (sequential)
    graph.add_edge("validate", "profile")
    graph.add_edge("profile", "financial")
    graph.add_edge("financial", "decision")
    
    # Add conditional routing
    graph.add_conditional_edges(
        "decision",
        should_escalate_to_review,
        {
            "manual_review": "manual_review",
            "execute": "compliance"
        }
    )
    
    # Add terminal edges
    graph.add_edge("manual_review", END)
    graph.add_edge("compliance", END)
    
    return graph.compile()
```

**Graph Structure:**
```
       ↓
   [validate]
       ↓
   [profile]
       ↓
   [financial]
       ↓
   [decision]
       ↓
   [routing decision]
       ↙            ↘
[manual_review]  [compliance]
       ↘            ↙
        [END]
```

---

## Layer 4: AI Agents

### Purpose
Use Claude Haiku 4.5 to analyze specific aspects and make reasoning-based assessments.

### Files
- **src/agents/base_agent.py** (150 lines) - Base class
- **src/agents/applicant_profile_agent.py** (130 lines) - Agent 1
- **src/agents/financial_risk_agent.py** (130 lines) - Agent 2
- **src/agents/loan_decision_agent.py** (160 lines) - Agent 3
- **src/agents/compliance_agent.py** (120 lines) - Agent 4
- **src/agents/prompts.py** (150 lines) - Prompt templates

### Lazy Agent Initialization

**Pattern: Prevent MCP connection issues during module import**

```python
# Located in src/orchestration/langgraph_workflow.py (lines ~69-90)

_agents_cache = {}

def get_profile_agent():
    if "profile" not in _agents_cache:
        _agents_cache["profile"] = ApplicantProfileAgent()
    return _agents_cache["profile"]

def get_financial_agent():
    if "financial" not in _agents_cache:
        _agents_cache["financial"] = FinancialRiskAgent()
    return _agents_cache["financial"]

def get_decision_agent():
    if "decision" not in _agents_cache:
        _agents_cache["decision"] = LoanDecisionAgent()
    return _agents_cache["decision"]

def get_compliance_agent():
    if "compliance" not in _agents_cache:
        _agents_cache["compliance"] = ComplianceAgent()
    return _agents_cache["compliance"]
```

**Why This Matters:**
- Agents connect to MCP servers on initialization
- Lazy initialization defers MCP connections until first use
- Prevents FastAPI startup failures if MCP servers are slightly delayed
- Uses instance caching to avoid redundant reconnections
- Called by workflow nodes: `get_profile_agent().analyze(...)`

### Base Agent Pattern

#### `invoke_claude()` - Core LLM Invocation
```python
# Located in src/agents/base_agent.py (lines ~50-100)

def invoke_claude(
    self,
    system_prompt: str,
    user_prompt: str,
    output_schema: Dict[str, Any]
) -> Dict[str, Any]:
    """Call Claude Haiku 4.5 with structured output"""
    
    # Step 1: Prepare client
    client = Anthropic(api_key=settings.anthropic_api_key)
    
    # Step 2: Call Claude
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )
    
    # Step 3: Extract and parse response
    response_text = response.content[0].text
    
    # Step 4: Extract JSON from markdown code block
    json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
    json_str = json_match.group(1)
    
    # Step 5: Parse and validate
    output_dict = json.loads(json_str)
    
    return output_dict
```

**Data Flow:**
```
Input: {
  "system_prompt": "You are an expert loan underwriter...",
  "user_prompt": "Analyze this applicant: age 35, income $85k, credit 745...",
  "output_schema": {"income_stability_score": <int>, ...}
}
  ↓
Claude Haiku 4.5 API Call (HTTP to Anthropic)
  ↓
Claude Response:
```json
{
  "income_stability_score": 85,
  "employment_risk": "LOW",
  "credit_summary": "Good employment history...",
  "confidence": 0.92,
  ...
}
```
  ↓
Output: Parsed JSON dict
```

### Agent 1: Applicant Profile Agent

#### `analyze()` - Profile Analysis Entry Point
```python
# Located in src/agents/applicant_profile_agent.py (lines ~40-120)

def analyze(self, applicant_id: str, **kwargs) -> Dict[str, Any]:
    """Analyze applicant profile"""
    
    # Step 1: Fetch data from MCP servers
    app_history = self._fetch_applicant_history(applicant_id)      # MCP call
    emp_data = self._fetch_employment_data(applicant_id)           # MCP call
    credit_data = self._fetch_credit_inquiries(applicant_id)       # MCP call
    
    # Step 2: Format for Claude
    employment_history_text = self._format_employment_history(emp_data)
    credit_inquiries_text = self._format_credit_inquiries(credit_data)
    
    # Step 3: Build prompts
    user_prompt = APPLICANT_PROFILE_USER_PROMPT_TEMPLATE.format(
        age=app_history["applicant"]["age"],
        income=app_history["applicant"]["income"],
        employment_type=app_history["applicant"]["employment_type"],
        credit_score=app_history["applicant"]["credit_score"],
        employment_history=employment_history_text,
        credit_inquiries=credit_inquiries_text
    )
    
    # Step 4: Invoke Claude
    claude_response = self.invoke_claude(
        system_prompt=APPLICANT_PROFILE_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        output_schema=ProfileAnalysis.schema()
    )
    
    # Step 5: Validate and return
    profile = ProfileAnalysis(
        income_stability_score=claude_response.get("income_stability_score", 50),
        employment_risk=claude_response.get("employment_risk", "MEDIUM"),
        credit_summary=claude_response.get("credit_summary", ""),
        completeness_flags=claude_response.get("completeness_flags", []),
        confidence=claude_response.get("confidence", 0.5),
        reasoning=claude_response.get("reasoning", "")
    )
    
    return profile.dict()
```

**Data Flow:**
```
Input: applicant_id = "APP-001"
  ↓
MCP Calls:
  ├─ get_applicant_history("APP-001") → {"applicant": {...}, ...}
  ├─ get_employment_data("APP-001") → {"jobs": [...], ...}
  └─ get_credit_inquiries("APP-001") → {"inquiries": [...], ...}
  ↓
Format for Claude:
  ├─ employment_history_text = "Senior Engineer at TechCorp: 72 months..."
  └─ credit_inquiries_text = "3 inquiries, 0 in last 3 months..."
  ↓
Claude Invocation:
  Input: System prompt + formatted user prompt
  ↓
Claude Response:
{
  "income_stability_score": 85,
  "employment_risk": "LOW",
  "credit_summary": "Excellent employment history...",
  "confidence": 0.92
}
  ↓
Output: ProfileAnalysis dict
{
  "income_stability_score": 85,
  "employment_risk": "LOW",
  "credit_summary": "...",
  "completeness_flags": [],
  "confidence": 0.92,
  "reasoning": "..."
}
```

### Agent 2: Financial Risk Agent

#### `analyze()` - Financial Risk Entry Point
```python
# Located in src/agents/financial_risk_agent.py (lines ~40-140)

def analyze(self, applicant_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Analyze financial risk"""
    
    # Step 1: Deterministic calculations (IN CODE, NOT LLM)
    income = float(applicant_data.get("income", 0))
    liabilities = float(applicant_data.get("existing_liabilities", 0))
    loan_amount = float(applicant_data.get("loan_amount", 0))
    tenure_months = int(applicant_data.get("tenure_months", 12))
    credit_score = int(applicant_data.get("credit_score", 600))
    
    # Calculate DTI
    monthly_income = income / 12
    monthly_debt_current = liabilities / 12
    monthly_debt_new = loan_amount / tenure_months
    total_monthly_debt = monthly_debt_current + monthly_debt_new
    dti = total_monthly_debt / monthly_income if monthly_income > 0 else 1.0
    
    # Calculate LTI
    lti = loan_amount / income if income > 0 else 0.0
    
    # Classify DTI
    if dti < 0.36:
        dti_classification = "FAVORABLE"
    elif dti < 0.43:
        dti_classification = "ACCEPTABLE"
    elif dti < 0.50:
        dti_classification = "BORDERLINE"
    else:
        dti_classification = "HIGH_RISK"
    
    # Classify Credit
    if credit_score >= 750:
        credit_risk = "LOW"
    elif credit_score >= 700:
        credit_risk = "MODERATE"
    # ... etc
    
    # Detect Anomalies
    anomalies = []
    if dti > 0.50:
        anomalies.append("DTI exceeds 50%")
    if credit_score < 550:
        anomalies.append("Credit score below 550")
    
    # Step 2: Invoke Claude for reasoning
    user_prompt = FINANCIAL_RISK_USER_PROMPT_TEMPLATE.format(
        dti=dti,
        credit_score=credit_score,
        credit_classification=credit_risk,
        lti=lti,
        income=income,
        monthly_debt=total_monthly_debt,
        loan_amount=loan_amount,
        tenure_months=tenure_months,
        stability_score=kwargs.get("stability_score", 50),
        employment_risk=kwargs.get("employment_risk", "MEDIUM"),
        anomalies_detected=len(anomalies) > 0
    )
    
    claude_response = self.invoke_claude(
        system_prompt=FINANCIAL_RISK_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        output_schema=FinancialAnalysis.schema()
    )
    
    # Step 3: Combine calculations + reasoning
    analysis = FinancialAnalysis(
        dti=dti,
        dti_classification=dti_classification,
        credit_score_risk=credit_risk,
        lti=lti,
        loan_amount_risk=lti_classification,
        anomaly_detected=len(anomalies) > 0,
        anomaly_reasons=anomalies,
        risk_score=claude_response.get("risk_score", 50),
        confidence=claude_response.get("confidence", 0.5),
        reasoning=claude_response.get("reasoning", "")
    )
    
    return analysis.dict()
```

**Data Flow:**
```
Input: {
  "income": 85000,
  "existing_liabilities": 12000,
  "loan_amount": 150000,
  "tenure_months": 180,
  "credit_score": 745,
  "stability_score": 85,
  "employment_risk": "LOW"
}
  ↓
Deterministic Calculations (NO LLM):
  ├─ DTI = (12000/12 + 150000/180) / (85000/12) = 0.35 → FAVORABLE
  ├─ LTI = 150000 / 85000 = 1.76 → FAVORABLE
  ├─ Credit Risk = 745 → MODERATE
  └─ Anomalies = [] (none detected)
  ↓
Claude Invocation (for reasoning):
  Input: "DTI is 0.35 (FAVORABLE), credit 745 (MODERATE)..."
  ↓
Claude Response:
{
  "risk_score": 30,
  "confidence": 0.90,
  "reasoning": "Strong DTI with moderate credit..."
}
  ↓
Output: FinancialAnalysis dict
{
  "dti": 0.35,
  "dti_classification": "FAVORABLE",
  "credit_score_risk": "MODERATE",
  "lti": 1.76,
  "loan_amount_risk": "FAVORABLE",
  "anomaly_detected": false,
  "anomaly_reasons": [],
  "risk_score": 30,
  "confidence": 0.90
}
```

### Agent 3: Loan Decision Agent

#### `analyze()` - Decision Synthesis Entry Point
```python
# Located in src/agents/loan_decision_agent.py (lines ~40-180)

def analyze(
    self,
    profile_analysis: Dict[str, Any],
    financial_analysis: Dict[str, Any],
    **kwargs
) -> Dict[str, Any]:
    """Make final decision"""
    
    # Step 1: Extract metrics
    profile_conf = profile_analysis.get("confidence", 0.5)
    financial_conf = financial_analysis.get("confidence", 0.5)
    profile_risk = profile_analysis.get("employment_risk", "MEDIUM")
    dti_class = financial_analysis.get("dti_classification", "BORDERLINE")
    credit_risk = financial_analysis.get("credit_score_risk", "MEDIUM")
    anomalies = financial_analysis.get("anomaly_detected", False)
    
    # Step 2: Apply decision rules (IN CODE)
    auto_approve = (
        profile_risk == "LOW" and
        dti_class in ["FAVORABLE", "ACCEPTABLE"] and
        credit_risk in ["LOW", "MODERATE"] and
        not anomalies and
        profile_conf >= 0.85 and
        financial_conf >= 0.85
    )
    
    auto_reject = (
        profile_risk == "HIGH" or
        dti_class == "HIGH_RISK" or
        credit_risk in ["HIGH", "VERY_HIGH"] or
        anomalies
    )
    
    if auto_approve:
        classification = "APPROVED"
    elif auto_reject:
        classification = "REJECTED"
    else:
        classification = "REQUIRES_REVIEW"
    
    # Step 3: Calculate composite risk
    composite_risk = int((dti_risk * 0.4 + credit_risk_score * 0.4 + profile_risk_score * 0.2))
    
    # Step 4: Calculate confidence
    avg_confidence = (profile_conf + financial_conf) / 2
    if anomalies:
        avg_confidence *= 0.8
    
    # Step 5: Identify decision factors
    decision_factors = [...]
    
    # Step 6: Invoke Claude for final reasoning
    user_prompt = LOAN_DECISION_USER_PROMPT_TEMPLATE.format(...)
    claude_response = self.invoke_claude(...)
    
    # Step 7: Return decision
    decision = DecisionResult(
        classification=classification,
        risk_score=composite_risk,
        confidence=avg_confidence,
        decision_factors=decision_factors,
        explanation=claude_response.get("explanation", "")
    )
    
    return decision.dict()
```

**Data Flow:**
```
Input:
  profile_analysis = {
    "confidence": 0.92,
    "employment_risk": "LOW",
    ...
  }
  financial_analysis = {
    "confidence": 0.90,
    "dti_classification": "FAVORABLE",
    "credit_score_risk": "MODERATE",
    ...
  }
  ↓
Decision Rules (CODE-BASED):
  ├─ Auto-approve? YES (all conditions met)
  ├─ Auto-reject? NO
  └─ Classification = "APPROVED"
  ↓
Risk & Confidence Calculation:
  ├─ composite_risk = 25/100
  └─ avg_confidence = 0.91
  ↓
Claude Invocation (for reasoning):
  Input: "Decision: APPROVED, factors: LOW risk, FAVORABLE DTI..."
  ↓
Claude Response:
{
  "explanation": "Strong applicant with excellent financial metrics...",
  "decision_factors": [...]
}
  ↓
Output: DecisionResult dict
{
  "classification": "APPROVED",
  "risk_score": 25,
  "confidence": 0.91,
  "decision_factors": [...],
  "explanation": "..."
}
```

### Agent 4: Compliance & Action Agent

#### `analyze()` - Compliance Entry Point
```python
# Located in src/agents/compliance_agent.py (lines ~40-120)

def analyze(
    self,
    decision_result: Dict[str, Any],
    applicant_id: str,
    trace_id: str,
    **kwargs
) -> Dict[str, Any]:
    """Execute compliance action"""
    
    # Step 1: Map decision to action
    decision = decision_result.get("classification", "REQUIRES_REVIEW")
    
    if decision == "APPROVED":
        action_taken = "APPROVED"
        summary = "Application APPROVED. Loan can proceed with underwriting."
    elif decision == "REJECTED":
        action_taken = "REJECTED"
        summary = "Application REJECTED. Applicant does not meet lending criteria."
    else:
        action_taken = "ESCALATED"
        summary = "Application ESCALATED to manual review for underwriter assessment."
    
    # Step 2: Generate case ID
    now = datetime.utcnow()
    case_id = f"CASE-{now.strftime('%Y-%m-%d')}-{hash(trace_id) % 100000:05d}"
    
    # Step 3: Prepare audit entry
    # (Audit trail is immutable - built in Layer 5)
    
    # Step 4: Invoke Claude for final reasoning
    user_prompt = COMPLIANCE_ACTION_USER_PROMPT_TEMPLATE.format(
        classification=decision,
        timestamp=now.isoformat(),
        case_id=case_id,
        risk_score=decision_result.get("risk_score", 50),
        confidence=decision_result.get("confidence", 0.5),
        applicant_id=applicant_id
    )
    
    claude_response = self.invoke_claude(
        system_prompt=COMPLIANCE_ACTION_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        output_schema=ComplianceAction.schema()
    )
    
    # Step 5: Return compliance action
    action = ComplianceAction(
        action_taken=action_taken,
        notification_status=claude_response.get("notification_status", "SENT"),
        case_id=case_id,
        timestamp=now,
        summary=summary
    )
    
    return action.dict()
```

**Data Flow:**
```
Input: {
  "classification": "APPROVED",
  "risk_score": 25,
  "confidence": 0.91
}
applicant_id = "APP-001"
trace_id = "TRACE-abc123"
  ↓
Decision → Action Mapping (CODE-BASED):
  ├─ APPROVED → APPROVED action
  ├─ REJECTED → REJECTED action
  └─ REQUIRES_REVIEW → ESCALATED action
  ↓
Case ID Generation:
  case_id = "CASE-2026-10-29-12345"
  ↓
Claude Invocation:
  Input: "Action: APPROVED, risk 25, confidence 91%..."
  ↓
Claude Response:
{
  "action_taken": "APPROVED",
  "notification_status": "SENT"
}
  ↓
Output: ComplianceAction dict
{
  "action_taken": "APPROVED",
  "notification_status": "SENT",
  "case_id": "CASE-2026-10-29-12345",
  "timestamp": "...",
  "summary": "Application APPROVED..."
}
```

---

## Layer 5: MCP Servers

### Purpose
Provide standardized tool interfaces for agents to query data and external systems.

### Files
- **src/mcp_servers/applicant_db.py** - Applicant data access
- **src/mcp_servers/risk_rules_db.py** - Risk thresholds & rules
- **src/mcp_servers/decision_synthesis.py** - Decision policies
- **src/mcp_servers/notification_system.py** - Notifications & audit

### ApplicantDB MCP Server

#### Tool 1: `get_applicant_history(applicant_id)`
```python
@tool
def get_applicant_history(applicant_id: str) -> Dict:
    """Get applicant profile and history"""
    # Query database: Applicant table
    applicant = db.query(Applicant).filter_by(id=applicant_id).first()
    
    return {
        "applicant": {
            "id": applicant.id,
            "age": applicant.age,
            "income": applicant.income,
            "employment_type": applicant.employment_type,
            "credit_score": applicant.credit_score,
            "liabilities": applicant.liabilities,
            "location": applicant.location
        },
        "history_years": applicant.created_at.year
    }
```

**Data Flow:**
```
MCP Request: {"tool": "get_applicant_history", "applicant_id": "APP-001"}
  ↓
Database Query: SELECT * FROM applicants WHERE id = "APP-001"
  ↓
Response:
{
  "applicant": {
    "id": "APP-001",
    "age": 35,
    "income": 85000,
    "employment_type": "Salaried",
    "credit_score": 745,
    "liabilities": 12000,
    "location": "US"
  },
  "history_years": 2019
}
```

#### Tool 2: `get_employment_data(applicant_id)`
```python
@tool
def get_employment_data(applicant_id: str) -> Dict:
    """Get employment history"""
    # Query database: EmploymentHistory table
    jobs = db.query(EmploymentHistory).filter_by(applicant_id=applicant_id).all()
    
    return {
        "jobs": [
            {
                "title": job.title,
                "company": job.company,
                "start_date": job.start_date,
                "end_date": job.end_date,
                "duration_months": (job.end_date - job.start_date).days // 30
            }
            for job in jobs
        ],
        "stability_score": calculate_stability(jobs),
        "gaps": detect_employment_gaps(jobs)
    }
```

**Data Flow:**
```
MCP Request: {"tool": "get_employment_data", "applicant_id": "APP-001"}
  ↓
Database Query: SELECT * FROM employment_history WHERE applicant_id = "APP-001"
  ↓
Calculations: stability_score = 85, gaps = []
  ↓
Response:
{
  "jobs": [
    {
      "title": "Senior Engineer",
      "company": "TechCorp",
      "duration_months": 72
    },
    {
      "title": "Engineer",
      "company": "StartupXYZ",
      "duration_months": 24
    }
  ],
  "stability_score": 85,
  "gaps": []
}
```

#### Tool 3: `get_credit_inquiries(applicant_id)`
```python
@tool
def get_credit_inquiries(applicant_id: str) -> Dict:
    """Get credit inquiries and history"""
    # Query database: CreditHistory table
    inquiries = db.query(CreditHistory).filter_by(applicant_id=applicant_id).all()
    
    recent_3m = len([i for i in inquiries if (datetime.now() - i.date).days < 90])
    anomalies = detect_anomalies(inquiries)
    
    return {
        "inquiries": [
            {"date": i.date, "type": i.type, "reason": i.reason}
            for i in inquiries
        ],
        "recent_inquiries_3m": recent_3m,
        "anomaly_flags": anomalies
    }
```

**Data Flow:**
```
MCP Request: {"tool": "get_credit_inquiries", "applicant_id": "APP-001"}
  ↓
Database Query: SELECT * FROM credit_history WHERE applicant_id = "APP-001"
  ↓
Analysis: recent_3m = 0, anomaly_flags = []
  ↓
Response:
{
  "inquiries": [
    {"date": "2026-03-15", "type": "Hard", "reason": "Mortgage Application"},
    {"date": "2025-09-20", "type": "Soft", "reason": "Credit Card Pre-approval"}
  ],
  "recent_inquiries_3m": 0,
  "anomaly_flags": []
}
```

### RiskRulesDB MCP Server

#### Tool: `get_risk_thresholds()`
```python
@tool
def get_risk_thresholds() -> Dict:
    """Get current risk thresholds"""
    return {
        "dti_favorable": 0.36,
        "dti_acceptable": 0.43,
        "dti_borderline": 0.50,
        "credit_excellent": 750,
        "credit_good": 700,
        "credit_fair": 650,
        "credit_poor": 550,
        "lti_favorable": 2.5,
        "lti_acceptable": 4.0
    }
```

---

## Layer 6: SQLite Database

### Purpose
Persistent storage, audit trail, and mock data.

### Files
- **src/database/models.py** - SQLAlchemy ORM models
- **data/loans.db** - SQLite database file

### Key Tables

#### Applicant
```
id (PK)          | String
age              | Integer
income           | Float
employment_type | String
credit_score    | Integer
liabilities      | Float
location         | String
created_at      | DateTime
```

#### EmploymentHistory
```
id (PK)           | Integer
applicant_id (FK) | String
title             | String
company           | String
start_date        | DateTime
end_date          | DateTime (nullable)
```

#### CreditHistory
```
id (PK)           | Integer
applicant_id (FK) | String
date              | DateTime
type              | String (Hard/Soft)
reason            | String
```

#### AuditLog (Immutable)
```
id (PK)           | Integer
trace_id          | String (indexed)
case_id           | String
applicant_id (FK) | String
decision          | String
risk_score        | Integer
confidence        | Float
explanation       | Text
agents_run        | JSON array
timestamps        | JSON object
created_at        | DateTime
```

---

## Complete Data Flow Example

### Approval Case: APP-CLEAR-APPROVE-1

```
USER INPUT (Streamlit)
  ↓
[age: 45, income: 120000, employment: Salaried, credit: 780, 
 loan: 200000, tenure: 240, liabilities: 15000, location: US]
  ↓

LAYER 2: FastAPI
  ├─ Validate with Pydantic (ApplicationRequest)
  └─ Call orchestrator via run_application()
  ↓

LAYER 3: LangGraph Orchestrator
  ├─ [validate] Check fields ✓
  ├─ [profile] Call Agent 1
  │  ├─ MCP: get_applicant_history() → {age: 45, income: 120000, ...}
  │  ├─ MCP: get_employment_data() → {jobs: [...], stability: 85}
  │  ├─ MCP: get_credit_inquiries() → {inquiries: [], recent_3m: 0}
  │  ├─ Claude: Analyze profile
  │  └─ Output: ProfileAnalysis {stability: 90, risk: LOW, conf: 0.92}
  │
  ├─ [financial] Call Agent 2
  │  ├─ Deterministic: DTI = 0.25 (FAVORABLE)
  │  ├─ Deterministic: LTI = 1.67 (FAVORABLE)
  │  ├─ Deterministic: Credit = 780 (LOW risk)
  │  ├─ Claude: Synthesize reasoning
  │  └─ Output: FinancialAnalysis {dti: 0.25, risk: 20, conf: 0.93}
  │
  ├─ [decision] Call Agent 3
  │  ├─ Rules: All conditions met → APPROVED
  │  ├─ Risk: composite = 20/100
  │  ├─ Confidence: 0.92
  │  ├─ Claude: Final reasoning
  │  └─ Output: DecisionResult {class: APPROVED, conf: 0.92}
  │
  ├─ [routing] Check if escalate
  │  └─ Confidence 0.92 >= 0.75 → Continue to compliance (NOT manual review)
  │
  └─ [compliance] Call Agent 4
     ├─ Action: APPROVED
     ├─ Generate case ID: CASE-2026-10-29-12345
     ├─ Claude: Final compliance check
     └─ Output: ComplianceAction {action: APPROVED, case: CASE-..., notif: SENT}
     
LAYER 5: MCP Servers (called by agents above)
  └─ NotificationSystem: write_audit_log()
     └─ Create immutable entry in AuditLog table
     
LAYER 6: SQLite Database
  └─ INSERT into AuditLog:
     {trace_id, case_id, applicant_id, decision: APPROVED, 
      risk_score: 20, confidence: 0.92, agents_run: [...], ...}
     
LAYER 2: FastAPI Response
  └─ HTTP 202 Response:
     {
       "trace_id": "TRACE-abc123",
       "decision": "APPROVED",
       "confidence": 0.92,
       "risk_score": 20,
       "case_id": "CASE-2026-10-29-12345",
       "agents_run": ["validate", "profile", "financial", "decision", "compliance"],
       "decision_factors": [...],
       "explanation": "Strong applicant with excellent metrics..."
     }

LAYER 1: Streamlit UI
  ├─ Display green badge: ✅ APPROVED
  ├─ Show metrics: Confidence 92%, Risk 20/100
  ├─ Display factors: Employment Excellent, DTI FAVORABLE, Credit LOW
  ├─ Show agent trace:
  │  ✅ Validate → ✅ Profile → ✅ Financial → ✅ Decision → ✅ Compliance
  └─ Show audit trail from database
```

---

## Performance & Timing Characteristics

### Request Processing Timeline

```
User submits application
  ↓
Streamlit → FastAPI (10-11 seconds)
  ├─ Validation: 100-200ms
  ├─ Profile Agent + Claude API: 2-3 seconds
  ├─ Financial Agent + Claude API: 2-3 seconds
  ├─ Decision Agent + Claude API: 2-3 seconds
  ├─ Compliance Agent + Claude API: 1-2 seconds
  ├─ Cache storage: 50-100ms
  └─ Response formatting: 50-100ms
  ↓
Decision available for retrieval
  ↓
Streamlit auto-fetches and displays
  ↓
User sees result (15-16 seconds total from submission)
```

### Timeout Configuration

| Operation | Timeout | Reason | Status |
|-----------|---------|--------|--------|
| Application submission | 15 seconds | Allow all 4 agents to run | ✅ Updated |
| Decision retrieval | 15 seconds | Accommodate slower network | ✅ Updated |
| Audit trail retrieval | 15 seconds | Accommodate slower network | ✅ Updated |
| MCP server queries | 1 second | Local network, should be fast | Baseline |
| Health check | 5 seconds | Quick service status | Baseline |

### Why 15 Seconds?

- **Claude Haiku API**: 500-2000ms per agent call (baseline)
- **4 Agents**: 4 × 2s average = 8 seconds
- **Safety Margin**: +7 seconds for network latency, queue wait, and variations
- **User Experience**: Spinner shows "Processing..." so no perception of hanging
- **Reliability**: Far fewer timeout errors than 10 second setting

### Caching Behavior

Once decision is computed and cached:
- First retrieval: 10-11 seconds (API processing)
- Subsequent retrievals: <100ms (from cache)
- Cache persists during application session
- Manual refresh bypasses cache and recalculates

---

## Key Integration Points

### Pydantic Models (Type Safety)
- ApplicationRequest (Layer 2) → ApplicationData (Layer 3)
- ProfileAnalysis (Layer 4) → State (Layer 3)
- FinancialAnalysis (Layer 4) → State (Layer 3)
- DecisionResult (Layer 4) → State (Layer 3)
- ComplianceAction (Layer 4) → State (Layer 3)

### Data Transformations
1. **User Input → ApplicationRequest** (Streamlit sends JSON)
2. **ApplicationRequest → ApplicationData** (FastAPI validates)
3. **ApplicationData → Agent Queries** (Orchestrator passes to agents)
4. **Agent Outputs → DecisionResponse** (Aggregated for UI)
5. **Decision → AuditLog** (Immutable trail in database)

### Concurrency & State
- ApplicationState in LangGraph (single execution context per trace_id)
- Session state in Streamlit (per-user browser session)
- Immutable database entries (no overwrites, only appends)

---

**This walkthrough covers the complete journey from user input to final decision across all 6 layers.**

