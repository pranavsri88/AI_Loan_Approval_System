# User Stories: Agentic AI Intelligent Loan Approval System

## Overview & Context

This document translates the functional and non-functional requirements (docs/requirements.md) and system design (docs/system_design.md) into user-centric narratives. Each user story follows the format:

```
As a <role>, I want <goal>, so that <benefit>.
```

### Stakeholder Roles

| Role | Description | Responsibilities |
|------|-------------|------------------|
| **Loan Applicant** | Individual seeking a loan | Submit application, view decision, understand approval/rejection reason |
| **Loan Officer** | Bank employee managing applications | Review borderline cases, approve/reject manual review items, provide feedback |
| **Compliance Auditor** | Regulatory/internal compliance officer | Query audit trails, verify decisions are compliant, monitor decision patterns |
| **Developer/Evaluator** | System developer or technical evaluator | Test agents, monitor performance, validate system behavior, debug issues |

### Traceability & Mapping

Each user story references requirement IDs from requirements.md (e.g., FR-UI-01, FR-API-01, NFR-01) to ensure traceability and test coverage.

---

## Epic 1: Application Submission

Stories around users submitting loan applications, form validation, input handling, and submission feedback.

### US-1.1: Submit Loan Application

**Epic:** Application Submission  
**Priority:** Must  
**Requirement IDs:** FR-UI-01, FR-API-01, FR-API-03  
**Story Points:** 5

As a **Loan Applicant**,
I want to submit a complete loan application with my personal and financial information,
so that the system can evaluate my eligibility for a loan.

**Acceptance Criteria:**

```gherkin
Given I am on the Streamlit chatbot UI
When I fill in all required fields:
  - Applicant ID: [auto-generated or provided]
  - Age: [18-80]
  - Income: [positive number]
  - Employment Type: [select from Salaried, Self-Employed, Unemployed, Retired]
  - Credit Score: [300-850]
  - Loan Amount: [1000-5000000]
  - Tenure (Months): [12-360]
  - Existing Liabilities: [0+]
  - Location: [2-letter country code]
And I click "Submit Application"
Then the system should:
  - Validate all fields per specification
  - Accept the application
  - Generate a trace_id
  - Return HTTP 202 (Accepted)
  - Display "Your application has been submitted"
  - Show the trace_id for tracking
```

**Example Scenario:**

```
Applicant: John Doe
Age: 35
Income: $85,000
Employment Type: Salaried
Credit Score: 745
Loan Amount: $150,000
Tenure: 180 months
Liabilities: $12,000
Location: US

Expected: Application accepted with trace_id "trace-abc123def456"
Processing starts immediately
```

**Notes:**
- Form should use client-side validation before submission
- Auto-fill timestamp (ISO 8601 UTC) if not provided
- Streamlit should disable submit button during submission (loading state)
- Clear error messages for any validation failures

---

### US-1.2: View Input Validation Errors

**Epic:** Application Submission  
**Priority:** Must  
**Requirement IDs:** FR-UI-05, FR-API-01, FR-API-05  
**Story Points:** 3

As a **Loan Applicant**,
I want to see clear error messages when I enter invalid data,
so that I can correct my application and resubmit.

**Acceptance Criteria:**

```gherkin
Given I am filling out the loan application form
When I enter an invalid value in any field:
  - Age: 17 (too young)
  - Credit Score: 900 (too high)
  - Loan Amount: 500 (too low)
  - Income: -5000 (negative)
Then the system should:
  - Display field-level error message inline
  - Highlight the invalid field
  - Disable Submit button until all errors resolved
  - Provide guidance: "[Field] must be [range/format]"
```

**Example Scenario:**

```
User enters age = 15
Error shown: "Age must be between 18 and 80 years"
Submit button disabled until corrected
User enters age = 25
Error clears, Submit button enabled
```

**Notes:**
- Use Streamlit's `st.error()` or styled containers for error display
- Validate on field blur or on submit
- Show all errors at once for better UX

---

### US-1.3: Submit Application and Receive Trace ID

**Epic:** Application Submission  
**Priority:** Must  
**Requirement IDs:** FR-API-01, FR-API-04, FR-UI-02, FR-ORCH-07  
**Story Points:** 3

As a **Loan Applicant**,
I want to receive a unique tracking ID when I submit my application,
so that I can check the status of my application later.

**Acceptance Criteria:**

```gherkin
Given I have submitted a valid loan application
When the FastAPI endpoint processes my request
Then the system should:
  - Return HTTP 202 (Accepted) status
  - Return JSON response with:
    {
      "trace_id": "trace-[UUID]",
      "applicant_id": "[provided]",
      "status": "PROCESSING"
    }
  - Display trace_id prominently in the UI
  - Store trace_id for later status queries
And I should be able to use the trace_id to check status
```

**Example Scenario:**

```
Request: POST /api/v1/applications with John's data
Response: {
  "trace_id": "trace-7f8d9c3e-4b1a-11ed-bdc3-0242ac120002",
  "applicant_id": "APP-12345",
  "status": "PROCESSING",
  "timestamp": "2026-10-29T14:30:01Z"
}
UI displays: "Your trace ID: trace-7f8d9c3e-4b1a-11ed-bdc3-0242ac120002"
```

**Notes:**
- Trace ID must be globally unique (UUID v4 recommended)
- Trace ID is immutable for entire application lifecycle
- Store in session state for polling status

---

### US-1.4: Retry Failed Submission

**Epic:** Application Submission  
**Priority:** Should  
**Requirement IDs:** FR-UI-05, FR-API-05, NFR-05  
**Story Points:** 3

As a **Loan Applicant**,
I want to easily resubmit my application if the submission fails,
so that I can recover from temporary system errors.

**Acceptance Criteria:**

```gherkin
Given my application submission failed (e.g., API timeout)
When I see an error message with retry option
Then the system should:
  - Show error: "[Error type]: [Details]"
  - Provide a "Retry" button
When I click "Retry"
Then the system should:
  - Re-submit the application with same data
  - Clear previous error message
  - Show spinner while processing
  - Return to normal submission flow
```

**Example Scenario:**

```
Submission fails with: "503 Service Unavailable"
UI shows: "Connection error. [Retry]"
User clicks "Retry"
Application re-submits successfully
```

**Notes:**
- Preserve form data during retry (don't clear)
- Max 3 automatic retries before user intervention
- Log retry attempts for debugging

---

## Epic 2: Profile Analysis

Stories around applicant profile evaluation by the Applicant Profile Agent.

### US-2.1: Analyze Applicant Profile

**Epic:** Profile Analysis  
**Priority:** Must  
**Requirement IDs:** FR-AG1-01, FR-AG1-02, FR-AG1-03, FR-AG1-04  
**Story Points:** 8

As a **Developer**,
I want the Applicant Profile Agent to query applicant history and calculate income stability,
so that the system can assess employment risk and profile completeness.

**Acceptance Criteria:**

```gherkin
Given the LangGraph workflow has validated the applicant data
When the profile_agent node is executed
Then the system should:
  - Query ApplicantDB MCP server for applicant history
  - Retrieve employment history (job titles, dates, tenure)
  - Retrieve credit inquiry history (if available)
  - Invoke Claude AI to analyze the profile
  - Return ProfileAnalysis JSON with:
    {
      "income_stability_score": 75,
      "employment_risk": "LOW",
      "credit_summary": "Good credit history, no delinquencies",
      "completeness_flags": [],
      "confidence": 0.92,
      "reasoning": "[Explanation of assessment]"
    }
  - Complete execution in < 2 seconds (p95)
```

**Example Scenario:**

```
Applicant: age 35, employed 5 years as Software Engineer, annual income $85k
Employment history: Same company 5 years, no gaps
Credit notes: 3 credit inquiries in past 2 years, no delinquencies

Expected output:
- income_stability_score: 85 (5+ years stable employment)
- employment_risk: "LOW"
- credit_summary: "Good credit profile with limited recent inquiries"
- completeness_flags: [] (no missing fields)
- confidence: 0.95
```

**Notes:**
- Ensure MCP server returns complete employment history
- Handle missing data gracefully (e.g., no credit notes yet)
- Profile analysis is deterministic given same input

---

### US-2.2: Flag Anomalies in Employment History

**Epic:** Profile Analysis  
**Priority:** Should  
**Requirement IDs:** FR-AG1-05  
**Story Points:** 5

As a **Developer**,
I want the Applicant Profile Agent to detect anomalies in employment history,
so that unusual patterns are flagged for manual review.

**Acceptance Criteria:**

```gherkin
Given the profile_agent analyzes employment history
When it detects anomalies (employment gaps > 6 months, recent job changes, etc.)
Then it should:
  - Identify each anomaly (gap, job change, etc.)
  - Calculate severity (LOW, MEDIUM, HIGH)
  - Add to completeness_flags array
  - Include reasoning in output
When completeness_flags is non-empty
Then downstream decision_agent should reduce confidence or route to manual review
```

**Example Scenarios:**

```
Scenario 1: Employment Gap
Employment: Job1 (2020-2022), Gap (2022-2023), Job2 (2023-present)
Flag: "Employment gap of 12 months (2022-2023)"
Severity: MEDIUM

Scenario 2: Frequent Job Changes
Employment: Job1 (2022-2023), Job2 (2023-2024), Job3 (2024-present)
Flag: "Frequent job changes: 3 jobs in 2 years"
Severity: MEDIUM

Scenario 3: No Anomalies
Employment: Job1 (2018-present, 6 years), no gaps
Flag: None
```

**Notes:**
- Define anomaly thresholds in config (employment_gap_months, etc.)
- Multiple anomalies can be flagged simultaneously
- Anomalies reduce confidence but don't auto-reject

---

## Epic 3: Risk Analysis

Stories around financial risk calculation by the Financial Risk Agent.

### US-3.1: Calculate Debt-to-Income Ratio

**Epic:** Risk Analysis  
**Priority:** Must  
**Requirement IDs:** FR-AG2-01, FR-AG2-02  
**Story Points:** 5

As a **Developer**,
I want the Financial Risk Agent to calculate DTI and classify it,
so that we can assess the applicant's monthly debt burden.

**Acceptance Criteria:**

```gherkin
Given the financial_agent receives applicant data and profile analysis
When it calculates DTI:
  DTI = (Monthly Debt / Gross Monthly Income)
  Monthly Debt = (Existing Liabilities / 12) + (Loan Monthly Payment)
Then it should:
  - Retrieve DTI thresholds from RiskRulesDB
  - Classify DTI as FAVORABLE/ACCEPTABLE/BORDERLINE/HIGH_RISK
  - Return DTI value (0.0+) and classification
  - Provide reasoning

And expected classification should be:
  DTI < 0.36 → FAVORABLE
  0.36 <= DTI < 0.43 → ACCEPTABLE
  0.43 <= DTI < 0.50 → BORDERLINE
  DTI >= 0.50 → HIGH_RISK
```

**Example Scenario:**

```
Applicant:
- Annual Income: $85,000 (Monthly: $7,083)
- Existing Liabilities: $12,000 (Monthly: $1,000)
- Loan Request: $150,000 over 180 months
- Loan Monthly Payment: $1,200 (estimated)

Calculation:
DTI = ($1,000 + $1,200) / $7,083 = $2,200 / $7,083 = 0.31

Classification: FAVORABLE (< 0.36)
```

**Notes:**
- Use standard interest rate assumptions for monthly payment calculation
- DTI thresholds are configurable (stored in RiskRulesDB)
- Borderline DTI (0.43-0.50) triggers manual review

---

### US-3.2: Classify Credit Score Risk

**Epic:** Risk Analysis  
**Priority:** Must  
**Requirement IDs:** FR-AG2-02  
**Story Points:** 3

As a **Developer**,
I want the Financial Risk Agent to map credit score to risk level,
so that we understand credit risk at a glance.

**Acceptance Criteria:**

```gherkin
Given the applicant's credit score (300-850)
When the agent classifies it using credit score bands
Then it should map to:
  750-850 → Excellent (LOW risk)
  700-749 → Good (MODERATE risk)
  650-699 → Fair (MEDIUM risk)
  550-649 → Poor (HIGH risk)
  <550 → Very Poor (VERY HIGH risk)
And return the classification and risk level
```

**Example Scenarios:**

```
Score 780 → Excellent / LOW
Score 725 → Good / MODERATE
Score 670 → Fair / MEDIUM
Score 600 → Poor / HIGH
Score 520 → Very Poor / VERY HIGH
```

**Notes:**
- Credit score bands are fixed per standard credit reporting
- Classification directly influences decision confidence

---

### US-3.3: Calculate Loan-to-Income Ratio

**Epic:** Risk Analysis  
**Priority:** Must  
**Requirement IDs:** FR-AG2-03  
**Story Points:** 3

As a **Developer**,
I want the Financial Risk Agent to calculate LTI and classify it,
so that we assess loan size relative to income.

**Acceptance Criteria:**

```gherkin
Given the applicant's annual income and requested loan amount
When the agent calculates LTI:
  LTI = Loan Amount / Gross Annual Income
Then it should:
  - Classify LTI as FAVORABLE/ACCEPTABLE/HIGH_RISK
  - Return LTI value and classification

Classification:
  LTI < 2.5 → FAVORABLE
  2.5 <= LTI < 4.0 → ACCEPTABLE
  LTI >= 4.0 → HIGH_RISK
```

**Example Scenario:**

```
Applicant:
- Annual Income: $85,000
- Loan Request: $150,000

LTI = $150,000 / $85,000 = 1.76

Classification: FAVORABLE (< 2.5)
```

**Notes:**
- LTI is more forward-looking than DTI
- High LTI can indicate overextension even with good DTI

---

### US-3.4: Detect Financial Anomalies

**Epic:** Risk Analysis  
**Priority:** Should  
**Requirement IDs:** FR-AG2-04  
**Story Points:** 5

As a **Developer**,
I want the Financial Risk Agent to detect unusual financial patterns,
so that anomalies are flagged for further investigation.

**Acceptance Criteria:**

```gherkin
Given the applicant's financial data and credit history
When the agent checks for anomalies using RiskRulesDB rules
Then it should detect and flag:
  - Income spikes (> 1.5x prior year)
  - Recent credit inquiries (> 3 in past 3 months)
  - Sudden liability increases
And return:
  {
    "anomaly_detected": bool,
    "anomaly_reasons": ["reason1", "reason2"],
    "anomaly_score": 0.0-1.0
  }
When anomaly_detected == true
Then downstream agents should reduce confidence or trigger manual review
```

**Example Scenarios:**

```
Scenario 1: Income Spike
Prior income: $70,000
Current income: $120,000 (71% increase)
Flag: "Income spike of 71% year-over-year"
Anomaly Score: 0.7 (MEDIUM)

Scenario 2: Multiple Credit Inquiries
Recent inquiries: 5 in last 2 months
Flag: "5 credit inquiries in past 2 months (threshold: 3)"
Anomaly Score: 0.6 (MEDIUM)

Scenario 3: No Anomalies
Stable income, normal credit inquiries, consistent liabilities
Anomaly Score: 0.1 (LOW)
```

**Notes:**
- Anomaly thresholds are configurable
- Multiple anomalies can occur; combine scores
- Anomalies don't auto-reject, but reduce decision confidence

---

## Epic 4: Decision & Explanation

Stories around decision synthesis, confidence calculation, and explainable outcomes.

### US-4.1: Generate Loan Decision

**Epic:** Decision & Explanation  
**Priority:** Must  
**Requirement IDs:** FR-AG3-01, FR-AG3-02, FR-AG3-03  
**Story Points:** 8

As a **Developer**,
I want the Loan Decision Agent to synthesize all analysis and generate a decision,
so that the system automatically classifies applications as APPROVED, REJECTED, or REQUIRES_REVIEW.

**Acceptance Criteria:**

```gherkin
Given all prior agents have completed analysis
When the decision_agent invokes Claude AI
Then it should apply decision rules:

Automatic APPROVED if:
  credit_score >= 750 AND
  dti < 0.36 AND
  lti < 2.5 AND
  no_anomalies == true AND
  employment_risk == "LOW"

Automatic REJECTED if:
  credit_score < 550 OR
  dti > 0.50 OR
  lti > 4.0 OR
  (employment_type == "Unemployed" AND income_stability < 50)

Otherwise: REQUIRES_REVIEW

And return DecisionResult with:
  {
    "classification": "APPROVED|REJECTED|REQUIRES_REVIEW",
    "risk_score": 0-100,
    "confidence": 0.0-1.0,
    "decision_factors": [...],
    "explanation": "[Human-readable explanation]"
  }
```

**Example Scenarios:**

```
Scenario 1: Auto-Approval
Credit: 780 (Excellent), DTI: 0.32 (Favorable), LTI: 1.76 (Favorable)
Employment: Salaried, 5 years (LOW risk)
Anomalies: None
Decision: APPROVED
Confidence: 0.95
Risk Score: 20

Scenario 2: Auto-Rejection
Credit: 480 (Very Poor)
Decision: REJECTED (credit_score < 550)
Confidence: 0.98
Risk Score: 95

Scenario 3: Manual Review
Credit: 710 (Good), DTI: 0.45 (Borderline)
Decision: REQUIRES_REVIEW (confidence < 0.75)
Confidence: 0.68
Risk Score: 50
```

**Notes:**
- Decision rules are deterministic and non-contradictory
- Risk score: 0=safest, 100=riskiest
- Confidence: 0.0-1.0, where >= 0.75 triggers auto-decision

---

### US-4.2: Calculate Decision Confidence

**Epic:** Decision & Explanation  
**Priority:** Must  
**Requirement IDs:** FR-AG3-02, FR-ORCH-04  
**Story Points:** 5

As a **Developer**,
I want the system to calculate confidence based on agent agreement and metric alignment,
so that borderline cases are routed to manual review.

**Acceptance Criteria:**

```gherkin
Given all agent analyses are complete
When the decision_agent calculates confidence
Then it should compute:
  confidence = (agent_agreement + metric_alignment + historical_match) / 3
  
Where:
  - agent_agreement: Correlation of agent recommendations (0-1)
  - metric_alignment: Adherence to decision rules (0-1)
  - historical_match: Similarity to past approved cases (0-1)

If confidence >= 0.75: Auto-decide (APPROVED or REJECTED)
If confidence < 0.75: Route to REQUIRES_REVIEW
```

**Example Scenario:**

```
Agents unanimous: All agents recommend APPROVED → agreement = 1.0
Metrics strong: All metrics favor approval → alignment = 0.95
Historical: Similar profiles approved 90% of time → match = 0.88

Confidence = (1.0 + 0.95 + 0.88) / 3 = 0.94

Decision: APPROVED (confidence >= 0.75)
```

**Notes:**
- Low confidence doesn't reject; it escalates to manual review
- Confidence threshold (0.75) is configurable
- Must handle disagreement gracefully

---

### US-4.3: Provide Explainable Decision Explanation

**Epic:** Decision & Explanation  
**Priority:** Must  
**Requirement IDs:** FR-AG3-05, FR-AG3-06, FR-UI-03, NFR-07  
**Story Points:** 5

As a **Loan Applicant**,
I want to see a clear, non-technical explanation of why my application was approved, rejected, or requires review,
so that I understand the decision and can take appropriate action.

**Acceptance Criteria:**

```gherkin
Given a decision has been made
When the decision explanation is generated
Then it should:
  - Avoid technical jargon (DTI instead of "debt burden")
  - Include primary factors influencing decision
  - Exclude PII (no specific income values, just "Income level is favorable")
  - Be 100-200 words, suitable for applicant viewing
  - Follow template:
    "Your loan application has been [APPROVED/REJECTED/escalated for review].
     [Primary Reason]. [Secondary Factors]. 
     Risk Level: [Low/Medium/High].
     Next Steps: [What happens next]."
```

**Example Output (Approval):**

```
Your loan application has been approved!

Your application meets our lending criteria based on:
• Your credit score (745) shows a good payment history
• Your monthly debt obligations are well-managed (32% of income)
• Your requested loan amount is reasonable relative to your income
• Your employment is stable (5 years at current company)

Your loan has been approved for $150,000 over 180 months.
Funds will be disbursed within 2-3 business days. 
You will receive a formal approval letter via email.
```

**Example Output (Rejection):**

```
Your loan application has been declined.

Unfortunately, your application does not meet our lending criteria at this time. 
This is primarily because your monthly debt obligations are too high 
relative to your income to safely accommodate an additional loan.

We recommend:
• Paying down existing debts to improve your debt-to-income ratio
• Reapplying in 6-12 months with improved financial metrics

If you have questions, please contact our support team.
```

**Notes:**
- Explanation template stored in config
- Dynamically populate with applicant data
- Use simple language, short sentences
- No PII in explanation

---

### US-4.4: Rank Decision Factors by Influence

**Epic:** Decision & Explanation  
**Priority:** Should  
**Requirement IDs:** FR-AG3-04  
**Story Points:** 3

As a **Loan Officer**,
I want to see which factors had the most influence on the decision,
so that I can understand the decision logic and validate the outcome.

**Acceptance Criteria:**

```gherkin
Given a decision has been made
When decision_factors are generated
Then each factor should include:
  {
    "factor": "credit_score",
    "value": 745,
    "impact": "PRIMARY|SECONDARY",
    "description": "Good (700-749)"
  }

Factors ranked by influence:
  PRIMARY (impact > 0.3): Credit score, DTI, LTI, employment stability
  SECONDARY (impact 0.1-0.3): Age, location, anomalies
  TERTIARY (impact < 0.1): Other flags, notes

Display order: Highest impact first
```

**Example Output:**

```
Decision Factors (APPROVED):
1. [PRIMARY] Credit Score: 745 → Good (0.35 weight)
2. [PRIMARY] DTI: 0.32 → Favorable (0.30 weight)
3. [PRIMARY] LTI: 1.76 → Favorable (0.25 weight)
4. [SECONDARY] Employment: Salaried, 5 years (0.10 weight)
```

**Notes:**
- Factor weights defined in config (must sum to 1.0)
- Primary factors drive decision; secondary factors are supporting
- Transparency aids both applicants and loan officers

---

## Epic 5: Compliance & Notification

Stories around decision logging, audit trails, notifications, and case management.

### US-5.1: Log Decision to Audit Trail

**Epic:** Compliance & Notification  
**Priority:** Must  
**Requirement IDs:** FR-AG4-01, FR-AG4-04, NFR-03  
**Story Points:** 5

As a **Compliance Auditor**,
I want all decisions to be logged immutably with full metadata,
so that we maintain a complete audit trail for regulatory compliance.

**Acceptance Criteria:**

```gherkin
Given a decision has been finalized
When the compliance_agent executes
Then it should log to audit_logs table:
  {
    "trace_id": "trace-abc123",
    "applicant_id": "APP-12345",
    "case_id": "CASE-2026-10-29-001",
    "agents_run": ["profile_agent", "financial_agent", "decision_agent", "compliance_agent"],
    "timestamps": {
      "submitted": "2026-10-29T14:30:01Z",
      "profile_analysis": "2026-10-29T14:30:05Z",
      "financial_analysis": "2026-10-29T14:30:10Z",
      "decision": "2026-10-29T14:30:20Z",
      "compliance": "2026-10-29T14:30:25Z"
    },
    "decision": "APPROVED|REJECTED|REQUIRES_REVIEW",
    "confidence": 0.95,
    "risk_score": 25,
    "decision_factors": [...],
    "explanation": "[explanation text]",
    "created_at": "2026-10-29T14:30:25Z"
  }

And the record must be:
  - Immutable (no UPDATE/DELETE allowed)
  - Permanently stored for >= 7 years
  - Queryable by trace_id or applicant_id
```

**Notes:**
- Use append-only database table
- All timestamps in UTC ISO 8601 format
- Store full agent outputs for audit purposes
- Never update audit log; append only

---

### US-5.2: Generate Unique Case ID

**Epic:** Compliance & Notification  
**Priority:** Must  
**Requirement IDs:** FR-AG4-02  
**Story Points:** 2

As a **Compliance Auditor**,
I want each decision to have a unique, immutable case ID,
so that I can reference and track individual loan decisions.

**Acceptance Criteria:**

```gherkin
Given a decision is being logged
When the compliance_agent executes
Then it should generate a unique case_id:
  Format: "CASE-YYYY-MM-DD-NNNNN"
  Example: "CASE-2026-10-29-001234"
  Where NNNNN is sequential per day

And the case_id should:
  - Be globally unique
  - Be immutable for lifetime of case
  - Be human-readable (date + sequence)
  - Be used in all notifications and communications
```

**Example Scenarios:**

```
First case on 2026-10-29: CASE-2026-10-29-00001
Second case on 2026-10-29: CASE-2026-10-29-00002
First case on 2026-10-30: CASE-2026-10-30-00001
```

**Notes:**
- Case ID is for external reference (applicants, loan officers)
- Trace ID is internal system identifier
- Both must be logged together

---

### US-5.3: Send Notification to Applicant

**Epic:** Compliance & Notification  
**Priority:** Should  
**Requirement IDs:** FR-AG4-03  
**Story Points:** 3

As a **Compliance System** (automated),
I want to send notifications to applicants about their decision,
so that they are promptly informed of the outcome.

**Acceptance Criteria:**

```gherkin
Given a decision is finalized
When the compliance_agent invokes NotificationSystem MCP
Then it should:
  - Prepare notification message (email/SMS format)
  - Include case_id for reference
  - Include decision and brief reasoning
  - Send via NotificationSystem (email, SMS, or both)
  - Log notification status (SENT, QUEUED, FAILED)
  - Return notification_status in compliance_action output

Notification content:
  Subject: "Your Loan Application Decision - Case [CASE-ID]"
  Body: "[Decision]. [Brief explanation]. Next steps: [...]"
```

**Example Email:**

```
Subject: Your Loan Application Decision - Case CASE-2026-10-29-001234

Dear John,

Your loan application has been approved!

Your requested loan of $150,000 has been approved. 
You will receive a formal approval letter within 1 business day.

Case Reference: CASE-2026-10-29-001234

Best regards,
Loan Approval System
```

**Notes:**
- NotificationSystem is mock for now (log to file/email service)
- Implement retry logic for failed notifications
- Do not include sensitive financial data in notification

---

### US-5.4: Query Audit Trail by Trace ID

**Epic:** Compliance & Notification  
**Priority:** Should  
**Requirement IDs:** FR-UI-04, FR-API-06, NFR-03, NFR-06  
**Story Points:** 5

As a **Compliance Auditor**,
I want to query the audit trail using trace_id,
so that I can review the full decision history for any application.

**Acceptance Criteria:**

```gherkin
Given I have a trace_id (e.g., "trace-abc123")
When I query GET /api/v1/applications/{applicant_id}/audit
Then the system should:
  - Return all audit log entries for that applicant
  - Include timestamps for each step
  - Include all agent outputs
  - Include decision and explanation
  - Include case_id and notification status
  - Return complete decision chain for inspection

Response format:
  {
    "applicant_id": "APP-12345",
    "total_decisions": 1,
    "decisions": [
      {
        "trace_id": "trace-abc123",
        "case_id": "CASE-2026-10-29-001",
        "decision": "APPROVED",
        "timestamps": {...},
        "agents_run": [...],
        "confidence": 0.95,
        "explanation": "..."
      }
    ]
  }
```

**Notes:**
- Audit query available only to authorized users (Compliance Auditor, Loan Officer)
- Include pagination for large datasets (default limit=10)
- Query performance critical; create index on applicant_id

---

## Epic 6: Manual Review

Stories around borderline cases, escalation, and human review workflows.

### US-6.1: Identify Cases for Manual Review

**Epic:** Manual Review  
**Priority:** Must  
**Requirement IDs:** FR-ORCH-05, FR-AG3-03, FR-UI-02  
**Story Points:** 5

As a **System** (automated),
I want to identify cases that require manual review based on defined criteria,
so that human loan officers can assess borderline decisions.

**Acceptance Criteria:**

```gherkin
Given a decision has been made
When the system evaluates manual review triggers:
  1. Decision confidence < 0.75
  2. DTI in borderline range (0.36-0.50)
  3. Anomalies detected (anomaly_score > 0.6)
  4. Age outside range (< 21 or > 70) with mixed signals
  5. Recent credit inquiries (> 3 in past 3 months)
Then if any trigger is true:
  - Set classification to "REQUIRES_REVIEW"
  - Log the trigger reason
  - Escalate to manual_review_queue
  - Notify loan officer that case needs review
```

**Example Scenarios:**

```
Scenario 1: Low Confidence
Credit: 710, DTI: 0.42, LTI: 2.8, age: 22
Mixed signals: Good credit but borderline DTI, young applicant
Calculated confidence: 0.68 (< 0.75)
Trigger: Confidence too low
Classification: REQUIRES_REVIEW

Scenario 2: Borderline DTI
Credit: 750, DTI: 0.45, LTI: 2.2, no anomalies
Normally would approve, but DTI in borderline range
Trigger: Borderline DTI (0.36-0.50)
Classification: REQUIRES_REVIEW

Scenario 3: Anomalies Detected
Credit: 720, DTI: 0.35, LTI: 2.0, but:
  - Income spike 70% year-over-year
  - 5 credit inquiries in 2 months
Anomaly score: 0.75 (> 0.6)
Trigger: Anomalies detected
Classification: REQUIRES_REVIEW
```

**Notes:**
- Multiple triggers can fire simultaneously
- Log all trigger reasons in decision_factors
- Manual review is not rejection; it's escalation

---

### US-6.2: View Manual Review Queue

**Epic:** Manual Review  
**Priority:** Should  
**Requirement IDs:** FR-UI-04  
**Story Points:** 5

As a **Loan Officer**,
I want to see all pending manual review cases in a queue,
so that I can prioritize and process them systematically.

**Acceptance Criteria:**

```gherkin
Given I am a loan officer viewing the Streamlit dashboard
When I navigate to "Manual Review Queue"
Then the system should display:
  - Table of cases requiring manual review
  - Columns: Case ID, Applicant ID, Risk Score, Decision Confidence, Reason
  - Sort by: Risk Score (descending), Submit Time
  - Filter options: By risk level, by reason, by date range
  - For each case: View full details, approve/reject/escalate button

Example table:
  Case ID              Risk Score  Confidence  Reason
  CASE-2026-10-29-001  50          0.68        Low confidence
  CASE-2026-10-29-002  55          0.72        Borderline DTI
  CASE-2026-10-29-003  60          0.70        Anomalies detected
```

**Notes:**
- Queue persists across sessions
- Real-time updates when new cases arrive (poll or WebSocket)
- Display recent decisions at top

---

### US-6.3: Review and Override Manual Case Decision

**Epic:** Manual Review  
**Priority:** Should  
**Requirement IDs:** FR-UI-04  
**Story Points:** 5

As a **Loan Officer**,
I want to review a manual case, understand the system recommendation, and make a final decision,
so that borderline cases are handled with human judgment.

**Acceptance Criteria:**

```gherkin
Given I click on a case in the manual review queue
When I open the case details view
Then I should see:
  - Applicant information (name, income, credit score, etc.)
  - System analysis summary (all agent outputs)
  - Decision recommendation with confidence score
  - Decision factors and explanation
  - Historical similar cases (if available)
  - Audit trail of all processing steps

And I should have action buttons:
  - [Approve] - Accept system recommendation or override
  - [Reject] - Reject the application
  - [Request More Info] - Ask for additional documentation
  - [Escalate] - Route to senior manager
  - [Save for Later] - Keep case open for further review

When I click [Approve] or [Reject]:
  - Log my decision override
  - Send notification to applicant
  - Close case and remove from queue
  - Record my reasoning (optional notes)
```

**Example Workflow:**

```
Case: CASE-2026-10-29-001
System Recommendation: REQUIRES_REVIEW (confidence 0.68)
Loan Officer Review: 
  - Views credit history: Good, stable
  - Views employment: 3 years at current company
  - Notes: "Confident in approval despite borderline DTI"
Action: [Approve]
Decision Override Logged: Loan Officer Jane Doe approved case 001 on 2026-10-29 14:45
Notification Sent to Applicant
```

**Notes:**
- All overrides must be logged with officer name and timestamp
- Enable audit trail to show human interventions
- Consider requiring manager approval for large loan amounts

---

## Epic 7: Observability & Monitoring

Stories around logging, debugging, performance monitoring, and system health.

### US-7.1: Log All Requests with Trace ID

**Epic:** Observability & Monitoring  
**Priority:** Must  
**Requirement IDs:** NFR-06, FR-ORCH-07, FR-API-06  
**Story Points:** 5

As a **Developer**,
I want all system requests to be logged with a unique trace_id,
so that I can track end-to-end request flow for debugging and auditing.

**Acceptance Criteria:**

```gherkin
Given any request enters the system
When the API or LangGraph processes it
Then every log message should include:
  {
    "timestamp": "2026-10-29T14:30:01.123456Z",
    "trace_id": "trace-abc123def456",
    "applicant_id": "APP-12345",
    "service": "fastapi|langgraph|agents|mcp",
    "component": "api|profile_agent|financial_agent|...",
    "level": "DEBUG|INFO|WARNING|ERROR",
    "message": "[Log message]",
    "latency_ms": 123,
    "status": "SUCCESS|FAILED"
  }

And logs should be:
  - Structured JSON format (not plain text)
  - Written to logs/app.log
  - Rotated daily or at 100MB
  - Searchable by trace_id
```

**Example Log Sequence:**

```json
{"timestamp":"2026-10-29T14:30:01.100Z","trace_id":"trace-abc","service":"fastapi","component":"api","level":"INFO","message":"POST /api/v1/applications received","applicant_id":"APP-12345"}
{"timestamp":"2026-10-29T14:30:01.150Z","trace_id":"trace-abc","service":"fastapi","component":"api","level":"DEBUG","message":"Input validation passed","latency_ms":50}
{"timestamp":"2026-10-29T14:30:01.200Z","trace_id":"trace-abc","service":"langgraph","component":"orchestrator","level":"INFO","message":"Invoking profile_agent","latency_ms":50}
{"timestamp":"2026-10-29T14:30:05.300Z","trace_id":"trace-abc","service":"agents","component":"profile_agent","level":"INFO","message":"Profile analysis complete","latency_ms":4100,"status":"SUCCESS"}
...
{"timestamp":"2026-10-29T14:30:25.900Z","trace_id":"trace-abc","service":"fastapi","component":"api","level":"INFO","message":"Response sent, total latency 24.8s","status":"SUCCESS"}
```

**Notes:**
- Trace ID propagates through entire request lifecycle
- Enable grep/filter logs by trace_id: `grep "trace-abc" logs/app.log`
- Configure log retention (7-30 days depending on volume)

---

### US-7.2: Monitor Request Latency and Performance

**Epic:** Observability & Monitoring  
**Priority:** Should  
**Requirement IDs:** NFR-01, NFR-06  
**Story Points:** 5

As a **Developer**,
I want to monitor request latency percentiles and identify performance bottlenecks,
so that we can meet the <5 second SLA and detect regressions.

**Acceptance Criteria:**

```gherkin
Given the system is processing applications
When requests complete
Then the system should track metrics:
  - Total end-to-end latency
  - Per-agent latency (profile, financial, decision, compliance)
  - API response latency
  - MCP query latency
  - Database operation latency

And compute statistics:
  - p50, p95, p99 latency percentiles
  - Error rate (%)
  - Success rate (%)
  - Average per-agent latency

Example Metrics:
  Total End-to-End Latency:
    p50: 3.2 seconds
    p95: 4.8 seconds
    p99: 5.1 seconds
  
  Per-Agent Latency:
    profile_agent: p95 = 1.8s
    financial_agent: p95 = 1.9s
    decision_agent: p95 = 0.9s
    compliance_agent: p95 = 0.5s
```

**Notes:**
- Use prometheus or similar metrics library
- Export metrics to monitoring dashboard (Grafana, DataDog)
- Alert if p95 latency > 5 seconds or error rate > 1%
- Review metrics weekly for regressions

---

### US-7.3: Query Logs by Trace ID for Debugging

**Epic:** Observability & Monitoring  
**Priority:** Should  
**Requirement IDs:** NFR-06, FR-ORCH-07  
**Story Points:** 3

As a **Developer**,
I want to query logs by trace_id to see the complete request flow,
so that I can quickly debug issues and understand what happened.

**Acceptance Criteria:**

```gherkin
Given a failing application with trace_id "trace-xyz789"
When I run: grep "trace-xyz789" logs/app.log
Then I should see:
  - All log entries for this request
  - Chronological order with timestamps
  - Each component's processing (API → LangGraph → Agents → MCP)
  - Latency for each step
  - Errors or warnings
  - Final decision and status

Example Output:
  $ grep "trace-xyz789" logs/app.log | jq '.'
  [
    {"timestamp":"...","message":"Request received","status":"SUCCESS"},
    {"timestamp":"...","message":"Validation passed","latency_ms":50},
    {"timestamp":"...","message":"Profile analysis","latency_ms":1800},
    ...
  ]
```

**Notes:**
- Logs should be searchable/filterable (jq, logstash, etc.)
- Include this trace ID in all error messages returned to users
- Educate support team on using trace ID for debugging

---

### US-7.4: Monitor Error Rates and Alert

**Epic:** Observability & Monitoring  
**Priority:** Should  
**Requirement IDs:** NFR-06, NFR-05  
**Story Points:** 5

As a **Developer**,
I want to monitor error rates and be alerted when errors exceed thresholds,
so that we can respond quickly to system issues.

**Acceptance Criteria:**

```gherkin
Given the system is processing requests
When errors occur (validation failures, agent failures, MCP failures)
Then the system should:
  - Increment error counter by error type
  - Calculate error rate per minute/hour
  - Log error with full context (trace_id, error message, stack trace)
  - Alert if error rate > 1% or specific error rate > 5%

Alert Conditions:
  - Overall error rate > 1%: "High error rate detected"
  - Validation errors > 5%: "Input validation failures high"
  - Agent failures > 3%: "Agent [name] failure rate high"
  - MCP failures > 10%: "MCP server [name] unavailable"

Alert Mechanism:
  - Send email to dev team
  - Post to Slack #alerts channel
  - Include: Error type, rate, sample trace IDs, suggested action
```

**Example Alert:**

```
🚨 Alert: High Error Rate Detected

Error Rate: 3.5% (threshold: 1%)
Errors in last 5 minutes: 7 out of 200 requests

Top Errors:
1. Validation error: age out of range (4 errors)
2. MCP timeout: RiskRulesDB (2 errors)
3. Claude API error (1 error)

Sample trace IDs for debugging:
  - trace-abc123
  - trace-def456
  - trace-ghi789

Action: Check system health, review error logs
```

**Notes:**
- Thresholds should be tuned after baseline established
- Use alerting service (PagerDuty, AlertManager, etc.)
- Include resolution steps in alert

---

## Story-to-Build-Phase Mapping Table

This table maps user stories to implementation phases for sprint planning and sequencing.

| Phase | Duration | Key Stories | Dependencies | Deliverables |
|-------|----------|-------------|--------------|--------------|
| **Phase 1: Architecture Setup** | Week 1-2 | US-6.1 (planning) | None | Project structure, FastAPI skeleton, LangGraph graph definition, SQLite schema |
| **Phase 2: MCP Servers & Agents** | Week 2-4 | US-2.1, US-2.2, US-3.1-4, US-7.1 | Phase 1 | 4 MCP servers, 4 agents, Claude integration, basic logging |
| **Phase 3: Orchestration & API** | Week 4-5 | US-1.1-4, US-4.1-4, US-5.1-4 | Phase 2 | LangGraph workflow, FastAPI endpoints, decision synthesis, audit logging |
| **Phase 4: UI & Testing** | Week 5-6 | US-1.1-4, US-4.1-2, US-6.2-3, US-7.2-4 | Phase 3 | Streamlit UI, unit/integration tests, performance monitoring |
| **Phase 5: Deployment & Hardening** | Week 7 | US-5.2, US-7.3-4, US-6.3 | Phase 4 | Docker setup, manual review workflow, comprehensive monitoring, documentation |

### Story Priority by Phase

**Must-Have (MVP) Stories:**
- US-1.1, US-1.2: Application submission and validation
- US-2.1, US-3.1-3: Profile and financial analysis
- US-4.1-2: Decision generation and confidence calculation
- US-5.1-2: Audit logging and case ID generation
- US-7.1: Request logging with trace ID

**Should-Have Stories:**
- US-1.3: Trace ID tracking
- US-3.4, US-4.4: Anomaly detection and factor ranking
- US-5.3-4: Notifications and audit trail querying
- US-6.1-2: Manual review identification and queue viewing
- US-7.2-4: Performance monitoring and alerting

**Could-Have Stories:**
- US-1.4: Retry logic
- US-6.3: Manual review override with feedback
- Advanced observability features

**Won't-Have (v2+):**
- Real-time credit report integration
- Biometric verification
- Mobile app
- Machine learning model retraining

---

## Dependencies & Blockers

### Critical Dependencies

1. **Anthropic API Access:** Claude Sonnet 4.6 model access required for all agents
2. **FastAPI & LangGraph Setup:** Core orchestration depends on these frameworks
3. **MCP Server Framework:** FastMCP library must be installed for agent communication
4. **SQLite Database:** Audit trail persistence depends on database layer

### Integration Points

1. **Streamlit ↔ FastAPI:** HTTP communication (REST API)
2. **FastAPI ↔ LangGraph:** In-process function calls
3. **LangGraph ↔ Agents:** In-process execution via node functions
4. **Agents ↔ MCP Servers:** RPC communication via FastMCP protocol
5. **Agents ↔ Claude AI:** Async API calls via Anthropic SDK
6. **Orchestrator ↔ SQLite:** Async database writes for audit trail

### Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Claude API rate limits | Blocks agent execution | Implement queue + retry logic |
| MCP server unavailability | Missing data for analysis | Fallback to cached data, route to manual review |
| SQLite concurrency | Audit trail corruption | Use connection pooling, test with concurrent load |
| Latency misses 5s SLA | Poor user experience | Profile agents, optimize MCP queries, parallel processing if possible |

---

## Acceptance Testing Strategy

### Manual Testing Scenarios

1. **Happy Path:** Valid application → Approval
2. **Auto-Rejection:** Failed credit check → Rejection
3. **Manual Review:** Borderline DTI → Escalation
4. **Error Recovery:** API timeout → Retry succeeds
5. **Audit Trail:** Query logs by trace ID → Full history visible

### Automated Test Coverage

- Unit tests: 80%+ code coverage
- Integration tests: All workflows tested (approval, rejection, review)
- API tests: All endpoints with valid/invalid inputs
- E2E tests: Full application flow from UI to decision

### Performance Testing

- Load: 100 concurrent applications
- Latency: p95 < 5 seconds, p99 < 5.5 seconds
- Error rate: < 0.1%

---

**Document Version:** 1.0  
**Last Updated:** 2026-10-29  
**Status:** User Stories Complete, Ready for Sprint Planning
