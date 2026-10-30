# MCP Integration Example: How Agents Use MCP Tools

This document shows how AI agents will invoke MCP server tools to make loan decisions.

---

## End-to-End Example: Processing a Loan Application

### Application Input

```python
{
    "applicant_id": "APP-12345",
    "age": 35,
    "income": 85000.00,
    "employment_type": "Salaried",
    "credit_score": 745,
    "loan_amount": 150000.00,
    "tenure_months": 180,
    "existing_liabilities": 12000.00,
    "location": "US",
    "timestamp": "2026-10-29T14:30:00Z"
}
```

---

## Step 1: Applicant Profile Agent

**Responsibility:** Analyze applicant's personal and employment profile.

### MCP Tools Called:

#### Tool 1: `get_applicant_history(applicant_id="APP-12345")`

**Request:**
```python
from src.mcp_servers.applicant_db import get_applicant_history

result = get_applicant_history("APP-12345")
```

**Response:**
```python
{
    "applicant": {
        "id": "APP-12345",
        "age": 35,
        "income": 85000.00,
        "employment_type": "Salaried",
        "credit_score": 745,
        "location": "US",
    },
    "employment_history": [
        {
            "job_title": "Senior Software Engineer",
            "company": "Tech Corp",
            "start_date": "2023-10-15",
            "end_date": None,  # Current job
            "tenure_months": 36,
        },
        {
            "job_title": "Software Engineer",
            "company": "Startup Inc",
            "start_date": "2021-10-15",
            "end_date": "2023-10-15",
            "tenure_months": 24,
        }
    ],
    "tenure_years": 3.0,
    "recent_gap_months": 0,  # No employment gap
}
```

#### Tool 2: `get_employment_data(applicant_id="APP-12345")`

**Request:**
```python
result = get_employment_data("APP-12345")
```

**Response:**
```python
{
    "applicant_id": "APP-12345",
    "jobs": [...],
    "current_tenure_months": 36,
    "total_jobs": 2,
    "employment_gaps": [],
    "stability_score": 72,  # 36 months * 2 = 72
    "status": "STABLE",  # >= 24 months
}
```

#### Tool 3: `get_credit_inquiries(applicant_id="APP-12345")`

**Request:**
```python
result = get_credit_inquiries("APP-12345")
```

**Response:**
```python
{
    "applicant_id": "APP-12345",
    "inquiries": [
        {
            "date": "2026-10-15",
            "type": "hard",
            "notes": "Auto loan inquiry",
        }
    ],
    "recent_inquiries_3m": 1,
    "inquiry_types": {"hard": 1},
    "anomaly_flag": False,  # 1 inquiry < threshold of 3
}
```

### Agent Output: `ProfileAnalysis`

```python
{
    "income_stability_score": 75,  # Based on tenure & income consistency
    "employment_risk": "LOW",  # Stable 3-year employment
    "credit_summary": "1 recent inquiry (automotive). No anomalies.",
    "completeness_flags": [],  # No missing/anomalous data
    "confidence": 0.92,
    "reasoning": "Applicant has stable employment for 3 years at Tech Corp with consistent income. Only 1 credit inquiry in 3 months indicates targeted borrowing. No employment gaps or income anomalies detected."
}
```

---

## Step 2: Financial Risk Agent

**Responsibility:** Analyze financial metrics and detect anomalies.

### MCP Tools Called:

#### Tool 1: `get_risk_thresholds()`

**Request:**
```python
from src.mcp_servers.risk_rules_db import get_risk_thresholds

thresholds = get_risk_thresholds()
```

**Response:**
```python
{
    "dti_favorable_max": 0.36,
    "dti_acceptable_max": 0.50,
    "dti_borderline_max": 0.63,
    "credit_excellent_min": 750,
    "credit_good_min": 700,
    "credit_fair_min": 650,
    "credit_poor_min": 550,
    "lti_favorable_max": 2.5,
    "lti_acceptable_max": 4.0,
    "lti_high_risk_min": 4.0,
}
```

#### Tool 2: `classify_by_rules(dti=0.35, credit_score=745, lti=2.8)`

**Calculations:**
```python
# DTI (Debt-to-Income Ratio)
monthly_debt = (12000 + (150000/180)) => $12,833.33
gross_monthly_income = 85000 / 12 => $7,083.33
dti = 12833 / 7083 = 1.81  # WAIT: This seems wrong, let me recalculate
```

Actually, let me recalculate based on monthly obligations:

```python
# Monthly obligations
monthly_debt_obligations = 12000 / 12 = $1,000  # Existing liabilities
monthly_loan_payment = (150000 / 180) * (interest_factor) ≈ $1,000  # Estimated
total_monthly_debt = $2,000

# Monthly income
gross_monthly_income = 85000 / 12 = $7,083.33

# DTI
dti = 2000 / 7083 = 0.282 (favorable!)

# LTI (Loan-to-Income)
lti = 150000 / 85000 = 1.76 (favorable!)
```

**Request:**
```python
result = classify_by_rules(dti=0.28, credit_score=745, lti=1.76)
```

**Response:**
```python
{
    "dti": {
        "value": 0.28,
        "classification": "FAVORABLE",  # < 0.36
    },
    "credit_score": {
        "value": 745,
        "classification": "GOOD",  # 700-749
        "risk_level": "MODERATE",
    },
    "lti": {
        "value": 1.76,
        "classification": "FAVORABLE",  # < 2.5
    },
}
```

#### Tool 3: `get_anomaly_rules()`

**Request:**
```python
result = get_anomaly_rules()
```

**Response:**
```python
{
    "income_spike_threshold": 1.5,  # 150%
    "employment_gap_months_threshold": 6,
    "credit_inquiries_3m_threshold": 3,
    "liabilities_spike_threshold": 1.3,  # 130%
    "rules": [
        {"name": "income_spike", "description": "Income increased >150%", "severity": "MEDIUM"},
        {"name": "employment_gap", "description": "Employment gap > 6 months", "severity": "MEDIUM"},
        {"name": "credit_inquiries", "description": "More than 3 inquiries in 90 days", "severity": "LOW"},
        {"name": "liabilities_spike", "description": "Liabilities increased >130%", "severity": "HIGH"},
    ],
}
```

**Anomaly Check:**
```python
# Check against rules
- Income spike: No previous data, so N/A
- Employment gap: 0 months (no gap) ✓
- Credit inquiries: 1 in 3m < 3 threshold ✓
- Liabilities spike: ~$1,000 new debt / $12,000 existing = 8% < 130% ✓

anomaly_detected = False
```

### Agent Output: `FinancialAnalysis`

```python
{
    "dti": 0.28,
    "dti_classification": "FAVORABLE",
    "credit_score_risk": "MODERATE",
    "lti": 1.76,
    "loan_amount_risk": "LOW",
    "anomaly_detected": False,
    "anomaly_reasons": [],
    "risk_score": 22,  # Composite score (low risk)
    "confidence": 0.95,
    "reasoning": "Strong financial profile with favorable DTI (0.28) and LTI (1.76). Good credit score (745) with no recent anomalies. Total monthly debt-to-income ratio is well below threshold. No red flags detected."
}
```

---

## Step 3: Loan Decision Agent

**Responsibility:** Synthesize analyses and make approval decision.

### MCP Tools Called:

#### Tool 1: `get_decision_policy()`

**Request:**
```python
from src.mcp_servers.decision_synthesis import get_decision_policy

policy = get_decision_policy()
```

**Response:**
```python
{
    "approval_criteria": {
        "all_required": [
            "credit_score >= 750",
            "dti < 0.36",
            "lti < 2.5",
            "employment_risk == LOW",
            "anomaly_detected == false",
        ],
        "description": "All criteria must be true to auto-approve",
    },
    "rejection_criteria": {
        "any_trigger": [
            "credit_score < 550",
            "dti > 0.63",
            "lti > 4.0",
            "employment_type == Unemployed AND income_stability < 50",
        ],
        "description": "Any criterion triggers auto-reject",
    },
    "manual_review_criteria": {
        "any_trigger": [
            "confidence < 0.75",
            "dti in range (0.50, 0.63)",
            "anomaly_score > 0.5",
            "age < 21 OR age > 70 WITH strong_other_factors",
            "recent_employment_gap > 6",
        ],
        "description": "Any criterion routes to manual review",
    },
}
```

#### Tool 2: `score_applicant(...)`

**Request:**
```python
result = score_applicant(
    credit_score=745,
    dti=0.28,
    lti=1.76,
    income_stability=75,  # From profile analysis
    employment_risk="LOW",
    anomaly_score=0.0,
)
```

**Response:**
```python
{
    "risk_score": 28,  # Low risk
    "components": {
        "credit_score": 25,       # Good score = 25 points
        "dti": 20,                # Favorable DTI = 20 points
        "lti": 15,                # Favorable LTI = 15 points
        "income_stability": 10,   # Stable = 10 points
        "employment_risk": 10,    # Low = 10 points
        "anomaly": 0,             # None = 0 points
    },
    "weights": {
        "credit": 0.35,
        "dti": 0.25,
        "lti": 0.15,
        "income_stability": 0.10,
        "employment": 0.10,
        "anomaly": 0.05,
    },
    "interpretation": "Low Risk",
}
```

### Decision Logic:

```python
# Check approval criteria (ALL must be true)
criteria_check = {
    "credit_score >= 750": 745 >= 750,  # ❌ FALSE (745 < 750)
    "dti < 0.36": 0.28 < 0.36,          # ✓ TRUE
    "lti < 2.5": 1.76 < 2.5,            # ✓ TRUE
    "employment_risk == LOW": "LOW" == "LOW",  # ✓ TRUE
    "anomaly_detected == false": False == False,  # ✓ TRUE
}

# Credit score doesn't meet excellent threshold, but good
# Not auto-approved, but not rejected either

# Check rejection criteria (ANY trigger = reject)
rejection_check = {
    "credit_score < 550": 745 < 550,     # ❌ FALSE
    "dti > 0.63": 0.28 > 0.63,           # ❌ FALSE
    "lti > 4.0": 1.76 > 4.0,             # ❌ FALSE
    "unemployed & unstable": False,      # ❌ FALSE
}
# No rejection triggers

# Check manual review criteria (ANY trigger = review)
review_check = {
    "confidence < 0.75": 0.95 < 0.75,    # ❌ FALSE (high confidence)
    "dti in borderline": 0.28 in (0.50, 0.63),  # ❌ FALSE
    "anomaly_score > 0.5": 0.0 > 0.5,    # ❌ FALSE
    "extreme age": 35 < 21 or 35 > 70,   # ❌ FALSE
    "employment_gap > 6": 0 > 6,         # ❌ FALSE
}
# No manual review triggers needed

# Decision: REQUIRES_REVIEW (doesn't meet auto-approve, but strong candidate)
# High confidence (0.95), low risk (28/100), stable employment & finances
```

### Agent Output: `DecisionResult`

```python
{
    "classification": "REQUIRES_REVIEW",  # Strong approval candidate
    "risk_score": 28,
    "confidence": 0.95,  # High confidence despite not meeting excellent credit threshold
    "decision_factors": [
        {"factor": "Employment Stability", "impact": "POSITIVE", "weight": 0.15},
        {"factor": "Debt-to-Income Ratio", "impact": "POSITIVE", "weight": 0.25},
        {"factor": "Credit Score (Good not Excellent)", "impact": "NEUTRAL", "weight": 0.35},
        {"factor": "Loan-to-Income Ratio", "impact": "POSITIVE", "weight": 0.15},
        {"factor": "No Financial Anomalies", "impact": "POSITIVE", "weight": 0.05},
    ],
    "explanation": "Strong financial profile with stable employment (3 years), favorable debt metrics (DTI 0.28, LTI 1.76), and good credit score (745). No financial anomalies detected. High confidence decision. Routed to manual review for potential approval due to not meeting excellent credit threshold (750+), but strong overall profile warrants expedited review."
}
```

---

## Step 4: Compliance Agent

**Responsibility:** Create case, send notification, log audit trail.

### MCP Tools Called:

#### Tool 1: `create_case(...)`

**Request:**
```python
from src.mcp_servers.notification_system import create_case

result = create_case(
    trace_id="trace-20261029-abc123",
    applicant_id="APP-12345",
    decision="REQUIRES_REVIEW",
    action_taken="ESCALATED",
)
```

**Response:**
```python
{
    "case_id": "CASE-2026-10-29-00001",
    "trace_id": "trace-20261029-abc123",
    "applicant_id": "APP-12345",
    "decision": "REQUIRES_REVIEW",
    "created_at": "2026-10-29T14:35:00Z",
}
```

#### Tool 2: `send_notification(...)`

**Request:**
```python
from src.mcp_servers.notification_system import send_notification

result = send_notification(
    applicant_id="APP-12345",
    case_id="CASE-2026-10-29-00001",
    notification_type="email",
    message="Your loan application (APP-12345) has been received and is under review. Expected decision within 2 business days. Case ID: CASE-2026-10-29-00001",
)
```

**Response:**
```python
{
    "status": "SENT",
    "notification_id": "123456",
    "sent_at": "2026-10-29T14:35:05Z",
    "applicant_id": "APP-12345",
    "case_id": "CASE-2026-10-29-00001",
}
```

#### Tool 3: `write_audit_log(...)`

**Request:**
```python
import json
from src.mcp_servers.notification_system import write_audit_log

result = write_audit_log(
    trace_id="trace-20261029-abc123",
    applicant_id="APP-12345",
    case_id="CASE-2026-10-29-00001",
    decision="REQUIRES_REVIEW",
    risk_score=28,
    confidence=0.95,
    explanation="Strong profile, escalated for manual review due to good (not excellent) credit score.",
    agents_run=json.dumps(["applicant_profile", "financial_risk", "loan_decision", "compliance"]),
    decision_factors=json.dumps([...]),
)
```

**Response:**
```python
{
    "audit_id": 42,
    "trace_id": "trace-20261029-abc123",
    "case_id": "CASE-2026-10-29-00001",
    "applicant_id": "APP-12345",
    "status": "LOGGED",
    "created_at": "2026-10-29T14:35:06Z",
}
```

### Audit Trail Persisted:

```
╔═══════════════════════════════════════════════════════════════════╗
║                    IMMUTABLE AUDIT LOG                            ║
╠═══════════════════════════════════════════════════════════════════╣
║ Trace ID:        trace-20261029-abc123                            ║
║ Case ID:         CASE-2026-10-29-00001                            ║
║ Applicant ID:    APP-12345                                        ║
║ Decision:        REQUIRES_REVIEW                                  ║
║ Risk Score:      28/100                                           ║
║ Confidence:      95%                                              ║
║ Agents Run:      [applicant_profile, financial_risk,              ║
║                   loan_decision, compliance]                      ║
║ Timestamps:      14:30:00 (start)                                 ║
║                  14:35:00 (decision)                              ║
║                  14:35:06 (logged)                                ║
║ Status:          LOGGED (immutable, never deleted)                ║
╚═══════════════════════════════════════════════════════════════════╝
```

---

## Complete Data Flow

```
Application Input
  └─> Applicant Profile Agent
      ├─> ApplicantDB: get_applicant_history
      ├─> ApplicantDB: get_employment_data
      ├─> ApplicantDB: get_credit_inquiries
      └─> ProfileAnalysis Output
          │
          └─> Financial Risk Agent
              ├─> RiskRulesDB: get_risk_thresholds
              ├─> RiskRulesDB: classify_by_rules
              ├─> RiskRulesDB: get_anomaly_rules
              └─> FinancialAnalysis Output
                  │
                  └─> Loan Decision Agent
                      ├─> DecisionSynthesis: get_decision_policy
                      ├─> DecisionSynthesis: score_applicant
                      └─> DecisionResult Output
                          │
                          └─> Compliance Agent
                              ├─> NotificationSystem: create_case
                              ├─> NotificationSystem: send_notification
                              └─> NotificationSystem: write_audit_log
                                  │
                                  └─> Case Created
                                      Notification Sent
                                      Audit Trail Logged
```

---

## Key Takeaways

1. **Modular Design**: Each agent focuses on one domain (profile, financial, decision, compliance)
2. **Tool Reusability**: MCP tools can be called by multiple agents
3. **Error Tolerance**: Tool failures don't crash agents; errors are logged
4. **Auditability**: Every decision is logged with trace_id and timestamps
5. **Explainability**: Each agent provides detailed reasoning
6. **Confidence**: Decisions include confidence scores for escalation logic
7. **Scalability**: MCP servers can run independently and scale horizontally

---

## Next: Agent Implementation

With MCP servers fully tested and documented, agents can now be implemented to:
1. Call MCP tools via LangGraph
2. Process tool responses with Claude AI
3. Make decisions based on business logic
4. Pass results to next agent in workflow

See [Agent Implementation Guide](./agent_implementation.md) for details.
