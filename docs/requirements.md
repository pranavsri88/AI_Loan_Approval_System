# Requirements Specification: Agentic AI Intelligent Loan Approval System

## Executive Summary

The Agentic AI Intelligent Loan Approval System is a multi-agent AI solution designed to automate and accelerate loan application evaluation. The system classifies applications into three outcomes: **Approved**, **Rejected**, or **Requires Manual Review**. Built on a distributed microservices architecture using Streamlit UI, FastAPI backend, LangGraph orchestration, and Claude AI agents, the system provides explainable, auditable decisions while maintaining consistent evaluation criteria across all applications.

**Key Stakeholders:** Loan officers, applicants, compliance team, risk management department

---

## Business Objectives

| Objective | Description |
|-----------|-------------|
| **Speed** | Process loan applications faster than manual review (target: <5 seconds per application) |
| **Consistency** | Deterministic decisions based on defined rules and risk thresholds |
| **Explainability** | Provide clear reasoning for all decision outcomes to support stakeholder trust |
| **Auditability** | Maintain complete, immutable audit trail for regulatory compliance |
| **Scalability** | Handle growing application volumes through horizontal scaling and concurrent processing |
| **Risk Management** | Minimize default rates and mitigate financial risk through systematic evaluation |

---

## System Overview

### Architecture Layers

```
┌─────────────────────────────────────────────┐
│  Presentation Layer (Streamlit UI)          │
├─────────────────────────────────────────────┤
│  Microservice Layer (FastAPI REST API)      │
├─────────────────────────────────────────────┤
│  Orchestration Layer (LangGraph + LangChain)│
├─────────────────────────────────────────────┤
│  Agent Layer (Domain-Specific Agents)       │
├─────────────────────────────────────────────┤
│  MCP Communication Layer (FastMCP Servers)  │
└─────────────────────────────────────────────┘
```

### Data Flow

1. User submits application via Streamlit chatbot
2. UI sends data to FastAPI microservice
3. Microservice validates input and forwards to orchestration layer
4. LangGraph orchestrator initiates agent workflow
5. Agents query MCP servers for contextual data
6. Agents perform analysis and return structured results
7. Orchestrator synthesizes outcomes and invokes Claude AI
8. Final decision is returned to chatbot UI with explanation

### Decision Classifications

- **Approved:** Application meets all criteria; loan is approved automatically
- **Rejected:** Application fails one or more critical criteria; loan is rejected automatically
- **Requires Manual Review:** Application is borderline or presents ambiguity; escalated to human reviewer

---

## Functional Requirements by Layer

### FR-UI: Presentation Layer (Streamlit)

| ID | Requirement | Details |
|---|---|---|
| FR-UI-01 | Loan Application Form | Collect all required input fields with inline validation |
| FR-UI-02 | Status Display | Show real-time processing status and decision results |
| FR-UI-03 | Decision Explanation | Display decision reason in user-friendly language, no PII |
| FR-UI-04 | Case History | Provide lookup and audit trail view for submitted applications |
| FR-UI-05 | Error Messaging | Show clear error messages for validation failures or system issues |
| FR-UI-06 | Timestamp Tracking | Display application submission time and decision timestamp |

### FR-API: FastAPI Microservice Layer

| ID | Requirement | Details |
|---|---|---|
| FR-API-01 | Input Validation | Validate all input fields per specification; reject invalid requests |
| FR-API-02 | Input Sanitization | Sanitize user input to prevent injection attacks |
| FR-API-03 | Request Routing | Route validated requests to orchestration layer |
| FR-API-04 | Response Formatting | Return structured JSON responses with status, decision, and metadata |
| FR-API-05 | Error Handling | Return appropriate HTTP status codes and error descriptions |
| FR-API-06 | Audit Logging | Log all requests with timestamp, applicant ID, and decision outcome |
| FR-API-07 | Rate Limiting | Implement rate limiting to prevent abuse (optional: 1000 req/min per IP) |

### FR-ORCH: Orchestration Layer (LangGraph)

| ID | Requirement | Details |
|---|---|---|
| FR-ORCH-01 | Workflow Coordination | Orchestrate sequential/parallel execution of agents |
| FR-ORCH-02 | State Management | Maintain and pass application state through agent pipeline |
| FR-ORCH-03 | Decision Synthesis | Aggregate agent outputs into final decision logic |
| FR-ORCH-04 | Confidence Calculation | Calculate decision confidence based on agent certainty scores |
| FR-ORCH-05 | Manual Review Routing | Route applications with low confidence to Manual Review |
| FR-ORCH-06 | Error Recovery | Gracefully handle agent failures; fallback to Manual Review |
| FR-ORCH-07 | Trace Logging | Generate unique trace ID for end-to-end request tracking |

### FR-AG1: Applicant Profile Agent

**Responsibility:** Evaluate applicant's personal and employment profile

| Input | Output |
|-------|--------|
| Applicant ID, Age, Income, Employment Type | Income Stability Score (0-100) |
| | Employment Risk Level (Low/Medium/High) |
| | Credit History Summary |
| | Application Completeness Flags |

| ID | Requirement | Details |
|---|---|---|
| FR-AG1-01 | Profile Query | Query ApplicantDB MCP server for complete applicant history |
| FR-AG1-02 | Income Stability | Calculate stability score based on income consistency and trend |
| FR-AG1-03 | Employment Assessment | Classify employment type risk and assess job tenure |
| FR-AG1-04 | Completeness Check | Flag missing or inconsistent data fields |
| FR-AG1-05 | Anomaly Flag | Flag unusual patterns (gaps, job changes, income spikes) |
| FR-AG1-06 | Structured Output | Return JSON with all metrics and reasoning |

### FR-AG2: Financial Risk Analysis Agent

**Responsibility:** Analyze financial metrics and detect anomalies

| Input | Output |
|-------|--------|
| Income, Loan Amount, Tenure, Liabilities, Credit Score | Debt-to-Income Ratio (DTI) |
| | Credit Score Risk Level |
| | Loan-to-Income Ratio (LTI) |
| | Anomaly Detection Flag |
| | Reasoning Summary |

| ID | Requirement | Details |
|---|---|---|
| FR-AG2-01 | DTI Calculation | Calculate DTI = (Total Monthly Debt / Gross Monthly Income) |
| FR-AG2-02 | Credit Risk Classification | Map credit score to risk band (Excellent/Good/Fair/Poor/Very Poor) |
| FR-AG2-03 | LTI Calculation | Calculate LTI = (Loan Amount / Annual Income) |
| FR-AG2-04 | Anomaly Detection | Flag unusual patterns using RiskRulesDB thresholds |
| FR-AG2-05 | Risk Scoring | Generate numeric risk score (0-100) based on metrics |
| FR-AG2-06 | Thresholds Query | Query RiskRulesDB MCP server for current risk thresholds |
| FR-AG2-07 | Reasoning Output | Include explanation of risk classification |

### FR-AG3: Loan Decision Agent

**Responsibility:** Synthesize all analysis and generate final decision

| Input | Output |
|-------|--------|
| All prior agent outputs, risk scores, confidence levels | Classification (Approve/Reject/Review) |
| | Risk Score (0-100) |
| | Confidence Level (0-100) |
| | Decision Factors (key metrics influencing decision) |
| | Explanation (human-readable reasoning) |

| ID | Requirement | Details |
|---|---|---|
| FR-AG3-01 | Decision Rules Engine | Implement automatic approval/rejection criteria |
| FR-AG3-02 | Confidence Calculation | Calculate confidence based on agreement among agents and metrics |
| FR-AG3-03 | Borderline Detection | Identify borderline cases for Manual Review routing |
| FR-AG3-04 | Factor Ranking | Rank decision factors by influence (primary vs. secondary) |
| FR-AG3-05 | Explanation Generation | Generate clear, explainable decision summary |
| FR-AG3-06 | PII Masking | Ensure no sensitive applicant data in explanation |
| FR-AG3-07 | Async Invocation | Support asynchronous Claude AI invocation via Agent SDK |

### FR-AG4: Compliance & Action Orchestrator Agent

**Responsibility:** Log decisions, trigger notifications, and manage audit trail

| Input | Output |
|-------|--------|
| Final decision, classification, risk score | Action Taken (Approved/Rejected/Escalated) |
| | Notification Status (Sent/Pending/Failed) |
| | Case ID |
| | Decision Timestamp |
| | Audit Summary |

| ID | Requirement | Details |
|---|---|---|
| FR-AG4-01 | Decision Logging | Persist decision with all metadata to audit database |
| FR-AG4-02 | Case ID Generation | Generate unique, immutable case ID |
| FR-AG4-03 | Notification Trigger | Invoke NotificationSystem MCP server to send case notifications |
| FR-AG4-04 | Audit Trail Recording | Record full decision chain with agent outputs and timestamps |
| FR-AG4-05 | Action Classification | Map decision to action (e.g., send approval letter, schedule follow-up) |
| FR-AG4-06 | Regulatory Logging | Ensure logs meet compliance requirements (retention, immutability) |
| FR-AG4-07 | Error Notification | Alert compliance team if decision logging fails |

### FR-MCP: MCP Server Communication

| MCP Server | Purpose | Key Operations |
|---|---|---|
| **ApplicantDB** | Applicant profile and historical data | Query applicant record, fetch employment history, retrieve credit notes |
| **RiskRulesDB** | Risk thresholds and rules | Fetch current DTI/LTI thresholds, credit score bands, anomaly rules |
| **DecisionSynthesis** | Decision logic and rules | Query decision precedents, fetch decision templates, validate rules |
| **NotificationSystem** | Notifications and case management | Send email/SMS notification, log case, escalate to manual queue |

| ID | Requirement | Details |
|---|---|---|
| FR-MCP-01 | Protocol Compliance | All agent-MCP communication via standardized FastMCP protocol |
| FR-MCP-02 | Error Handling | Implement timeout and retry logic for MCP calls |
| FR-MCP-03 | Response Caching | Cache stable data (rules, thresholds) to reduce latency |
| FR-MCP-04 | Fallback Behavior | Define fallback responses if MCP server is unavailable |
| FR-MCP-05 | Schema Validation | Validate all MCP responses match expected schema |

---

## Input Validation Requirements

| Field | Type | Range/Format | Required | Validation Rules | Notes |
|-------|------|--------------|----------|------------------|-------|
| Applicant ID | String | UUID or alphanumeric | Yes | `^[A-Z0-9]{8,20}$` | Unique identifier for applicant |
| Age | Integer | 18-80 | Yes | `18 <= age <= 80` | Must be legal adult |
| Income | Decimal | 0-9,999,999 | Yes | `> 0` | Annual income in base currency units |
| Employment Type | Enum | {Salaried, Self-Employed, Unemployed, Retired} | Yes | One of enum values | Categorized employment status |
| Credit Score | Integer | 300-850 | Yes | `300 <= score <= 850` | Standard credit score range |
| Loan Amount | Decimal | 1,000-5,000,000 | Yes | `1000 <= amount <= 5000000` | Requested loan amount |
| Tenure (Months) | Integer | 12-360 | Yes | `12 <= tenure <= 360` | Loan repayment period in months |
| Existing Liabilities | Decimal | 0-9,999,999 | Yes | `>= 0` | Total outstanding debt |
| Location | String | ISO 3166-1 code | Yes | `^[A-Z]{2}$` | Two-letter country code |
| Application Timestamp | DateTime | ISO 8601 format | Yes | `YYYY-MM-DDTHH:MM:SSZ` | UTC timestamp of submission |

**Validation Error Handling:**
- Return HTTP 400 with field-specific error messages
- Log validation failures for compliance
- Do not proceed to orchestration layer if validation fails

---

## Decision Rules

### Credit Score Risk Classification

| Band | Range | Risk Level | Description |
|------|-------|-----------|-------------|
| Excellent | 750-850 | Low | Strong payment history; minimal default risk |
| Good | 700-749 | Moderate | Reliable credit profile; acceptable risk |
| Fair | 650-699 | Medium | Mixed credit history; review other factors |
| Poor | 550-649 | High | Delinquency history; significant concern |
| Very Poor | <550 | Very High | Severe credit issues; automatic rejection candidate |

### Debt-to-Income Ratio (DTI) Thresholds

| DTI Range | Classification | Implication |
|-----------|-----------------|-------------|
| < 0.36 | Favorable | Low monthly debt burden; favorable for approval |
| 0.36 - 0.43 | Acceptable | Moderate debt; acceptable if other factors strong |
| 0.43 - 0.50 | Borderline | High debt burden; flag for manual review |
| > 0.50 | High Risk | Excessive monthly obligation; automatic rejection candidate |

**DTI Formula:** `DTI = (Monthly Loan Payment + Other Monthly Debt) / Gross Monthly Income`

### Loan-to-Income Ratio (LTI) Thresholds

| LTI Range | Classification | Implication |
|-----------|-----------------|-------------|
| < 2.5 | Favorable | Loan is 2.5x or less annual income; low risk |
| 2.5 - 4.0 | Acceptable | Loan is 2.5x to 4x annual income; moderate risk |
| > 4.0 | High Risk | Loan exceeds 4x annual income; automatic rejection candidate |

**LTI Formula:** `LTI = Loan Amount / Gross Annual Income`

### Automatic Approval Criteria

Application is **APPROVED** if ALL of the following are true:

```
credit_score >= 750
AND dti < 0.36
AND lti < 2.5
AND no_anomalies_detected == true
AND employment_type != "Unemployed"
AND income_stability_score >= 70
```

### Automatic Rejection Criteria

Application is **REJECTED** if ANY of the following are true:

```
credit_score < 550
OR dti > 0.50
OR lti > 4.0
OR (employment_type == "Unemployed" AND income_stability_score < 50)
OR employment_gap > 6 months
```

### Manual Review Routing Criteria

Application is routed to **REQUIRES MANUAL REVIEW** if:

```
decision_confidence < 0.75
OR (dti >= 0.36 AND dti <= 0.50)
OR anomaly_score > 0.6
OR (age < 21 OR age > 70) AND other_factors_strong
OR recent_credit_inquiry_count > 3
OR application_has_flag == true
```

**Decision Confidence Formula:**
```
confidence = (agent_agreement + metric_alignment + historical_match) / 3
- agent_agreement: correlation of agent recommendations (0-1)
- metric_alignment: adherence to decision rules (0-1)
- historical_match: similarity to approved historical applications (0-1)
```

---

## Non-Functional Requirements

### NFR-01: Latency

| Metric | Target | Notes |
|--------|--------|-------|
| Single application processing | < 5 seconds | End-to-end from submission to decision |
| Individual agent response time | < 2 seconds | Per agent, at 95th percentile |
| API endpoint response | < 3 seconds | Including validation and response formatting |
| MCP server response | < 1 second | For query operations |

### NFR-02: Throughput & Scalability

| Metric | Target | Notes |
|--------|--------|-------|
| Concurrent applications | 100+ simultaneous | Without performance degradation |
| Peak throughput | 50 applications/second | With horizontal scaling |
| Scaling approach | Horizontal | Deploy multiple API/orchestration instances |

### NFR-03: Auditability

| Requirement | Details |
|---|---|
| Decision Logging | All decisions logged with: timestamp, applicant ID, agents involved, confidence scores, decision factors |
| Immutability | Decision records cannot be modified after creation (use append-only log) |
| Trace ID | Unique identifier for full request flow; present in all logs |
| Audit Query | Ability to retrieve full decision history for any applicant |
| Retention Policy | Maintain records for minimum 7 years per regulatory requirement |

### NFR-04: Loose Coupling

| Requirement | Details |
|---|---|
| Agent Independence | Agents do not call each other directly; all communication via orchestration layer |
| Standardized Interfaces | All agent input/output follows defined JSON schema |
| MCP Protocol | All external service communication uses FastMCP protocol |
| Service Registry | Agents can be replaced/upgraded without changing orchestration logic |

### NFR-05: Error Handling

| Scenario | Behavior | Details |
|---|---|---|
| Agent Failure | Route to Manual Review | If any agent fails, escalate instead of failing |
| MCP Server Unavailable | Use cached data or fallback | Query cache before timeout; if cache miss, escalate |
| API Error | Return error response with trace ID | Enable debugging and support investigation |
| Invalid Decision Output | Escalate to Manual Review | If decision cannot be classified, escalate for review |

### NFR-06: Logging & Monitoring

| Requirement | Details |
|---|---|
| Log Format | Structured JSON format with: timestamp, trace_id, level, service, message, metadata |
| Log Level | Support DEBUG, INFO, WARN, ERROR levels |
| Metrics Collection | Track: decision distribution (Approve/Reject/Review %), processing time percentiles, agent success rates, MCP error rates |
| Alerting | Alert on: error rates > 1%, latency > 5s, MCP unavailability, decision failures |

### NFR-07: PII Security

| Requirement | Details |
|---|---|
| PII Identification | Classify fields as PII: Applicant ID, Age, Income, Employment details, Location |
| Encryption at Rest | Encrypt PII in database using AES-256 |
| Encryption in Transit | Use HTTPS/TLS 1.3 for all API communication |
| Log Masking | Mask PII in logs (e.g., `Applicant-****`, `Income: ***`) |
| Decision Explanations | Never include PII in explanations shown to applicants (e.g., not "Income $50K" but "Income level is favorable") |
| Data Retention | Implement retention policy; purge data after 7 years unless regulatory hold |

### NFR-08: Availability & Reliability

| Metric | Target | Notes |
|---|---|---|
| System Uptime | 99.5% | 3.6 hours downtime per month |
| MCP Server Failover | 60 seconds | Time to detect and failover to backup MCP server |
| Recovery Time Objective (RTO) | 15 minutes | Restore service after critical failure |
| Recovery Point Objective (RPO) | 1 minute | Data loss tolerance |

---

## Validation & Business Logic

### Age Validation Rules

- Minimum age: 18 years (legal adult)
- Maximum age: 80 years (practical upper limit)
- For applicants 18-20: Flag as "First-Time Applicant"; require stronger financial indicators
- For applicants 70-80: Flag for manual review if credit score < 700

### Income Validation Rules

- Minimum: > 0 (must have positive income)
- Maximum: 9,999,999 (practical business limit)
- For self-employed: Require 2+ years of tax returns for verification
- For salaried: Accept current year income

### Employment Type Business Logic

| Employment Type | Handling |
|---|---|
| Salaried | Verify current employment; check employment duration ≥ 6 months |
| Self-Employed | Require 2+ years of business history; verify via tax returns |
| Retired | Verify income source (pension/portfolio); check stability score ≥ 60 |
| Unemployed | Automatic rejection UNLESS income source verified (e.g., dividends, rental income) |

### Liabilities Calculation

```
Monthly Debt = (Existing Liabilities / 12) + (Loan Amount * Monthly Interest Rate)
```

Monthly interest rate derived from loan tenure and standard interest assumptions.

---

## Assumptions

1. **Data Pre-validation:** Applicant data is pre-validated at source; system assumes data format compliance
2. **MCP Availability:** MCP servers are highly available; system implements caching for resilience
3. **LLM Context Window:** Claude Sonnet 4.6 has sufficient context for agent outputs (est. 2000-3000 tokens)
4. **Historical Data:** Complete historical applicant data is available for profile analysis
5. **Credit Rules Stability:** Credit risk rules and thresholds are stable; updates are managed through DecisionSynthesis MCP server
6. **Regulatory Alignment:** Jurisdiction-specific regulations are not encoded; all evaluations are rule-based without country-specific logic
7. **User Honesty:** Applicant-provided data is assumed truthful; system does not perform independent verification (e.g., income verification with tax authorities)

---

## Out of Scope

| Item | Rationale |
|---|---|
| Real-time Credit Report Integration | External API dependency; out of scope for proof-of-concept |
| Biometric Verification | Requires additional identity verification infrastructure |
| Video KYC (Know Your Customer) | Requires additional compliance and video processing infrastructure |
| Advanced Fraud Detection | Limited to basic anomaly detection; advanced ML fraud models out of scope |
| Multi-Currency Support | Assumes single base currency; multi-currency requires exchange rate logic |
| Mobile App | Only Streamlit web interface provided |
| Integration with Legacy Banking Systems | Assumes standalone system; legacy integration is future phase |
| Machine Learning Model Retraining | Decision rules are static; adaptive learning is future enhancement |
| Feedback Loop for Model Improvement | No mechanism to retrain agents based on actual loan performance |
| Predictive Analytics | System only evaluates application at submission; no predictive modeling |

---

## Acceptance Criteria

### System Completion Criteria

| Criterion | Threshold | Verification |
|---|---|---|
| Input Validation | 100% of fields validated per spec | Unit test coverage ≥ 95% |
| Decision Speed | 80% of applications processed in < 5 seconds | Load test with 100 concurrent applications |
| Manual Review Routing | Correctly routes borderline cases | Test suite covers all routing criteria |
| Audit Logging | 100% of decisions logged with full metadata | Audit log inspection for sample decisions |
| Agent Outputs | All outputs are structured and parseable | Schema validation against JSON schema |
| Confidence Alignment | Confidence scores correlate with decision correctness | Test with 100+ historical cases |
| PII Protection | No PII in decision explanations or logs | Log inspection and explanation review |
| Error Resilience | System handles MCP failures gracefully | Chaos testing with simulated service outages |

### Evaluation Criteria (Live Demo)

| Criterion | Evidence |
|---|---|
| Agentic AI Architecture Understanding | Live code walkthrough explaining agent responsibilities and data flow |
| LangGraph Orchestration | Demonstrate correct workflow coordination; show state transitions |
| MCP Integration | Explain MCP server communication; show agent-server interaction |
| Code Maintainability | Clear separation of concerns; reusable components; documented interfaces |
| Explainability | Decision explanations are understandable to non-technical stakeholders |
| End-to-End Workflow | Submit application → Processing → Decision → Notification (< 5s) |
| Live Code Modification | Ability to explain and modify code during evaluation session |

---

## Testing Strategy

### Unit Testing

- Input validation logic: 100 test cases covering valid/invalid inputs
- Decision rules engine: Test each approval/rejection/review criterion independently
- Agent output parsing: Verify structured JSON compliance

### Integration Testing

- Agent communication: Test MCP server interaction and error handling
- Orchestration workflow: Simulate complete application flow with mock data
- API endpoints: Test request/response formatting and error handling

### Load Testing

- Concurrent applications: 100+ simultaneous requests
- Measure: Latency (p50, p95, p99), throughput, error rates
- Success criteria: p95 latency < 5 seconds, error rate < 0.1%

### UAT Testing

- Use realistic loan application scenarios (approved, rejected, manual review)
- Verify decision explanations are clear and non-technical
- Test audit trail functionality

---

## Glossary

| Term | Definition |
|---|---|
| **DTI** | Debt-to-Income ratio; monthly debt obligations divided by gross monthly income |
| **LTI** | Loan-to-Income ratio; total loan amount divided by gross annual income |
| **MCP** | Model Context Protocol; standardized protocol for agent communication |
| **PII** | Personally Identifiable Information; sensitive applicant data |
| **Trace ID** | Unique identifier for end-to-end request flow; enables debugging and auditing |
| **Confidence Score** | Numeric measure (0-100) of decision certainty; triggers Manual Review if < 0.75 |
| **Anomaly Detection** | Identification of unusual patterns in applicant profile (income spikes, job gaps, etc.) |

---

**Document Version:** 1.0  
**Last Updated:** 2026-10-29  
**Status:** Approved for Implementation
