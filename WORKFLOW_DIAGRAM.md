# Loan Application Workflow Diagram

## LangGraph Workflow Architecture

```
                                    ┌─────────────────────┐
                                    │      START          │
                                    └──────────┬──────────┘
                                               │
                                    ┌──────────▼──────────┐
                                    │  VALIDATE INPUT     │
                                    │  - Required fields  │
                                    │  - Data types       │
                                    │  - Value ranges     │
                                    └──┬────────────┬─────┘
                                       │            │
                          ┌────────────┘            └──────────────┐
                          │ Invalid                                 │ Valid
                          │                                         │
                ┌─────────▼─────────┐              ┌──────────────▼────────┐
                │ MANUAL REVIEW     │              │  AGENT 1: PROFILE     │
                │ (Escalate)        │              │  - Query ApplicantDB  │
                └────────┬──────────┘              │  - Employment history │
                         │                         │  - Credit analysis    │
                    ┌────▼────────────────┐       │  - Stability score    │
                    │       END           │       └──────────────┬────────┘
                    └─────────────────────┘                      │
                                                   ┌─────────────▼──────────┐
                                                   │ AGENT 2: FINANCIAL     │
                                                   │ - Calculate DTI/LTI    │
                                                   │ - Classify credit risk │
                                                   │ - Detect anomalies     │
                                                   │ - Risk scoring         │
                                                   └─────────────┬──────────┘
                                                                 │
                                                   ┌─────────────▼──────────┐
                                                   │ AGENT 3: DECISION      │
                                                   │ - Synthesize analysis  │
                                                   │ - Apply decision rules │
                                                   │ - Calculate confidence │
                                                   │ - Identify factors     │
                                                   └─────────────┬──────────┘
                                                                 │
                                                   ┌─────────────▼──────────┐
                                                   │  ROUTING DECISION      │
                                                   │  ├─ Error state?       │
                                                   │  ├─ Confidence < 0.75? │
                                                   │  ├─ Anomalies?         │
                                                   │  └─ Decision?          │
                                                   └─────────────┬──────────┘
                                                                 │
                                                  ┌──────────────┴──────────────┐
                                                  │ Escalate to               Auto-execute
                                                  │ Manual Review             Compliance
                                                  │                           │
                                    ┌─────────────▼──────────┐ ┌──────────────▼────────┐
                                    │  MANUAL REVIEW NODE    │ │ AGENT 4: COMPLIANCE   │
                                    │  - Flag for underwriter│ │ - Create case ID      │
                                    │  - Await human review  │ │ - Send notification   │
                                    │  - Human decides       │ │ - Log audit trail     │
                                    └─────────────┬──────────┘ └──────────────┬────────┘
                                                  │                          │
                                                  └──────────────┬───────────┘
                                                                 │
                                                    ┌────────────▼────────────┐
                                                    │        END              │
                                                    │ Return final result     │
                                                    └─────────────────────────┘
```

---

## Decision Logic Tree

```
                            ┌──────────────────────────────────────┐
                            │  ALL ANALYSIS COMPLETE               │
                            │  (Profile + Financial + Confidence)  │
                            └──────────────┬───────────────────────┘
                                          │
                            ┌─────────────▼─────────────┐
                            │  CHECK CONFIDENCE         │
                            │  confidence >= 0.85?      │
                            └─────────────┬─────────────┘
                                          │
                    ┌─────────────────────┴─────────────────────┐
                    │ YES (High confidence)              NO (Low confidence)
                    │                                           │
          ┌─────────▼──────────┐                      ┌─────────▼──────────┐
          │ AUTO-APPROVE       │                      │ MANUAL REVIEW      │
          │ if ALL:            │                      │ Escalate to human  │
          │ • Profile LOW risk │                      └────────────────────┘
          │ • DTI FAVORABLE    │
          │ • Credit LOW/MOD   │
          │ • LTI FAVORABLE    │
          │ • No anomalies     │
          └─────────┬──────────┘
                    │
        ┌───────────┴────────────┐
        │ YES (All conditions)   │ NO (Some don't match)
        │                        │
   ┌────▼─────────┐       ┌──────▼──────────┐
   │  APPROVED    │       │ CHECK REJECT    │
   │  Risk LOW    │       │ Conditions      │
   │  Confidence  │       │                 │
   │  VERY HIGH   │       └──────┬──────────┘
   └────┬─────────┘              │
        │          ┌─────────────┴─────────────┐
        │          │ ANY (At least one)        │ NONE (None match)
        │          │                          │
        │     ┌────▼─────────┐        ┌────────▼────────┐
        │     │  REJECTED    │        │ MANUAL REVIEW   │
        │     │  Risk HIGH   │        │ Borderline case │
        │     │  No approval │        │ Requires review │
        │     └────┬─────────┘        └────────┬────────┘
        │          │                          │
        │     ┌────┴──────────────────────────┘
        │     │
   ┌────▼─────▼────────────────┐
   │   COMPLIANCE & ACTION      │
   │  ├─ Create case ID         │
   │  ├─ Send notification      │
   │  ├─ Log audit trail        │
   │  └─ Update status          │
   └────┬──────────────────────┘
        │
   ┌────▼─────────────────────┐
   │   FINAL RESULT            │
   │  • Decision (A/R/M)       │
   │  • Confidence score       │
   │  • Risk score             │
   │  • Case ID                │
   │  • Audit trail            │
   └────────────────────────────┘
```

---

## Data Flow Through Agents

```
INPUT APPLICATION DATA
│
├─ applicant_id
├─ age, income, employment_type
├─ credit_score
├─ loan_amount, tenure_months
├─ existing_liabilities
└─ location

            │
            ▼

    ┌───────────────────┐
    │ AGENT 1: PROFILE  │
    └───────┬───────────┘
            │
            ├─ ApplicantDB MCP (3 tools)
            │  ├─ get_applicant_history()
            │  ├─ get_employment_data()
            │  └─ get_credit_inquiries()
            │
            ├─ Format context for Claude
            │
            ├─ Claude Sonnet 4.6 invocation
            │
            └─ Output: ProfileAnalysis
               ├─ income_stability_score
               ├─ employment_risk
               ├─ credit_summary
               ├─ completeness_flags
               ├─ confidence
               └─ reasoning

                    │
                    ▼

    ┌───────────────────────┐
    │ AGENT 2: FINANCIAL    │
    └───────┬───────────────┘
            │
            ├─ DETERMINISTIC CALCULATIONS
            │  ├─ DTI = (monthly_debt + new_loan) / monthly_income
            │  ├─ LTI = loan_amount / income
            │  ├─ Classify DTI: FAVORABLE → ACCEPTABLE → BORDERLINE → HIGH_RISK
            │  ├─ Classify LTI: FAVORABLE → ACCEPTABLE → HIGH_RISK
            │  ├─ Classify Credit: LOW → MODERATE → MEDIUM → HIGH → VERY_HIGH
            │  └─ Detect anomalies: DTI > 0.50? LTI > 4.0? Credit < 550?
            │
            ├─ RiskRulesDB MCP (optional)
            │
            ├─ Claude Sonnet 4.6 invocation (reasoning)
            │
            └─ Output: FinancialAnalysis
               ├─ dti, dti_classification
               ├─ credit_score_risk
               ├─ lti, loan_amount_risk
               ├─ anomaly_detected, anomaly_reasons
               ├─ risk_score (0-100)
               ├─ confidence
               └─ reasoning

                    │
                    ▼

    ┌───────────────────────┐
    │ AGENT 3: DECISION     │
    └───────┬───────────────┘
            │
            ├─ Synthesize Profile + Financial
            │
            ├─ Apply decision rules
            │  ├─ Rule 1: If excellent_profile AND low_risk AND high_confidence → APPROVED
            │  ├─ Rule 2: If poor_profile OR high_risk → REJECTED
            │  └─ Rule 3: Else → REQUIRES_REVIEW
            │
            ├─ Calculate composite risk (0-100)
            │  └─ DTI_risk(0.4) + CreditRisk(0.4) + ProfileRisk(0.2)
            │
            ├─ Calculate confidence
            │  └─ avg(profile_conf, financial_conf) * anomaly_penalty
            │
            ├─ Identify decision factors
            │
            ├─ Claude Sonnet 4.6 invocation (final reasoning)
            │
            └─ Output: DecisionResult
               ├─ classification: APPROVED|REJECTED|REQUIRES_REVIEW
               ├─ risk_score (0-100)
               ├─ confidence (0.0-1.0)
               ├─ decision_factors []
               └─ explanation

                    │
                    ▼

        ┌─────────────────────────┐
        │ CONDITIONAL ROUTING     │
        └─────────┬───────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
   (Manual Review)     (Compliance)
        │                   │
        ▼                   ▼

    ┌──────────────┐   ┌───────────────────────┐
    │ MANUAL REVIEW│   │ AGENT 4: COMPLIANCE   │
    │ (No more     │   └───────┬───────────────┘
    │  processing) │           │
    └──────────────┘           ├─ NotificationSystem MCP
                               │  ├─ create_case()
                               │  ├─ send_notification()
                               │  └─ write_audit_log()
                               │
                               ├─ Generate case ID
                               │  └─ CASE-YYYY-MM-DD-NNNNN
                               │
                               ├─ Create audit trail entry
                               │
                               ├─ Claude Sonnet 4.6 (final action)
                               │
                               └─ Output: ComplianceAction
                                  ├─ action_taken: APPROVED|REJECTED|ESCALATED
                                  ├─ notification_status: SENT|PENDING|FAILED
                                  ├─ case_id
                                  ├─ timestamp
                                  └─ summary

                                       │
                                       ▼

                            ┌─────────────────────┐
                            │  FINAL RESULT       │
                            ├─────────────────────┤
                            │ trace_id            │
                            │ applicant_id        │
                            │ decision            │
                            │ confidence          │
                            │ risk_score          │
                            │ case_id             │
                            │ agents_run []       │
                            │ timestamp           │
                            │ explanation         │
                            └─────────────────────┘
```

---

## Conditional Routing Decision Points

```
AFTER AGENT 3 (DECISION)
│
├─ Is there an error state?
│  ├─ YES → MANUAL REVIEW (human handles error)
│  └─ NO → Continue
│
├─ Is confidence < 0.75 (threshold)?
│  ├─ YES → MANUAL REVIEW (uncertain decision)
│  └─ NO → Continue
│
├─ Were anomalies detected?
│  ├─ YES → MANUAL REVIEW (suspicious patterns)
│  └─ NO → Continue
│
├─ Did Agent 3 classify as REQUIRES_REVIEW?
│  ├─ YES → MANUAL REVIEW (agent unsure)
│  └─ NO → Continue
│
└─ ELSE → EXECUTE COMPLIANCE (proceed with decision)
   ├─ Agent 4: Create case + send notification
   └─ Final result returned
```

---

## State Transitions

```
START
  │
  ├─ State: empty
  │
  ▼
VALIDATE
  │
  ├─ State: applicant_data added
  ├─ agents_run: [validate]
  │
  ▼
PROFILE
  │
  ├─ State: profile_analysis added
  ├─ agents_run: [validate, profile]
  │
  ▼
FINANCIAL
  │
  ├─ State: financial_analysis added
  ├─ agents_run: [validate, profile, financial]
  │
  ▼
DECISION
  │
  ├─ State: decision_result, final_decision, final_confidence added
  ├─ agents_run: [validate, profile, financial, decision]
  │
  ▼
ROUTE
  │
  ├─ Evaluate: error? low_confidence? anomalies? requires_review?
  │
  ├─ YES (any) → MANUAL_REVIEW
  │             ├─ agents_run: [..., manual_review]
  │             └─ END
  │
  └─ NO (all) → COMPLIANCE
               ├─ agents_run: [..., compliance]
               ├─ State: compliance_action, case_id added
               └─ END
```

---

## Agent Dependencies

```
                    ┌──────────────────────────────────────┐
                    │  APPLICANT DATA (from API)           │
                    └──────────────┬───────────────────────┘
                                   │
                    ┌──────────────▼─────────────────────┐
                    │  AGENT 1 (PROFILE)                 │
                    ├────────────────────────────────────┤
                    │ Depends on: ApplicantDB MCP         │
                    │ Input: applicant_id                 │
                    │ Output: ProfileAnalysis             │
                    └──────────────┬─────────────────────┘
                                   │
                    ┌──────────────▼─────────────────────┐
                    │  AGENT 2 (FINANCIAL)               │
                    ├────────────────────────────────────┤
                    │ Depends on: RiskRulesDB MCP         │
                    │ Input: applicant_data + profile     │
                    │ Output: FinancialAnalysis           │
                    └──────────────┬─────────────────────┘
                                   │
                    ┌──────────────▼─────────────────────┐
                    │  AGENT 3 (DECISION)                │
                    ├────────────────────────────────────┤
                    │ Depends on: DecisionSynthesis MCP   │
                    │ Input: profile + financial          │
                    │ Output: DecisionResult              │
                    └──────────────┬─────────────────────┘
                                   │
                    ┌──────────────▼─────────────────────┐
                    │  AGENT 4 (COMPLIANCE)              │
                    ├────────────────────────────────────┤
                    │ Depends on: NotificationSystem MCP  │
                    │ Input: decision + applicant_id      │
                    │ Output: ComplianceAction            │
                    └──────────────┬─────────────────────┘
                                   │
                    ┌──────────────▼─────────────────────┐
                    │  FINAL RESULT                       │
                    │  ├─ decision                        │
                    │  ├─ confidence                      │
                    │  ├─ case_id                         │
                    │  ├─ risk_score                      │
                    │  └─ explanation                     │
                    └───────────────────────────────────┘
```

---

**Generated:** 2026-10-29  
**For:** Agentic AI Intelligent Loan Approval System  
**Phase:** 4 - LangGraph Orchestration
