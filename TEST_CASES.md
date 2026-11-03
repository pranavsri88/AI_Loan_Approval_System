# Test Cases: All Decision Statuses

Comprehensive test cases for the Intelligent Loan Approval System covering all three decision statuses: **APPROVED**, **REJECTED**, and **REQUIRES_REVIEW**.

---

## Test Case 1: APPROVED Status (Strong Profile)

**Scenario:** High income, excellent credit score, low DTI, stable employment

**Input Data:**
```json
{
  "applicant_id": "TEST-APPROVED-001",
  "age": 38,
  "income": 120000,
  "employment_type": "Salaried",
  "credit_score": 760,
  "loan_amount": 200000,
  "tenure_months": 240,
  "existing_liabilities": 15000,
  "location": "US"
}
```

**Expected Outcome:**
- **Decision:** APPROVED ✅
- **Risk Score:** 10-20 (low risk)
- **Confidence:** 80%+
- **Reasoning:** Strong fundamentals - favorable DTI, good credit, stable employment

**Key Metrics:**
- DTI: 24.5% (FAVORABLE - below 36%)
- LTI: 1.67 (LOW - below 2.5)
- Credit Risk: LOW (760 score)
- Employment Risk: LOW (Salaried)

---

## Test Case 2: REJECTED Status (Poor Profile)

**Scenario:** Very low credit score, very high DTI, high LTI, unemployed

**Input Data:**
```json
{
  "applicant_id": "TEST-REJECTED-001",
  "age": 52,
  "income": 35000,
  "employment_type": "Unemployed",
  "credit_score": 480,
  "loan_amount": 250000,
  "tenure_months": 300,
  "existing_liabilities": 45000,
  "location": "UK"
}
```

**Expected Outcome:**
- **Decision:** REJECTED ❌
- **Risk Score:** 75-90 (very high risk)
- **Confidence:** 60-80%
- **Reasoning:** Multiple auto-rejection triggers - very poor credit, excessive DTI, high LTI, unemployment

**Key Metrics:**
- DTI: 128.6% (HIGH_RISK - far exceeds 50%)
- LTI: 7.14 (HIGH - exceeds 4.0)
- Credit Risk: VERY_HIGH (480 score)
- Employment Risk: HIGH (Unemployed)

---

## Test Case 3: APPROVED Status (Young Professional)

**Scenario:** Excellent credit, conservative loan size, low existing debt

**Input Data:**
```json
{
  "applicant_id": "TEST-APPROVED-002",
  "age": 31,
  "income": 95000,
  "employment_type": "Salaried",
  "credit_score": 800,
  "loan_amount": 120000,
  "tenure_months": 180,
  "existing_liabilities": 5000,
  "location": "US"
}
```

**Expected Outcome:**
- **Decision:** APPROVED ✅
- **Risk Score:** 10-15 (low risk)
- **Confidence:** 83%+
- **Reasoning:** Excellent credit, conservative loan amount, minimal existing debt

**Key Metrics:**
- DTI: 18.3% (FAVORABLE - well below 36%)
- LTI: 1.26 (LOW - well below 2.5)
- Credit Risk: LOW (800 score)
- Existing Debt: Minimal ($5,000)

---

## Test Case 4: REJECTED Status (Very High Risk)

**Scenario:** Poor credit, high existing debt, very low income, high loan request

**Input Data:**
```json
{
  "applicant_id": "TEST-REJECTED-002",
  "age": 45,
  "income": 30000,
  "employment_type": "Unemployed",
  "credit_score": 520,
  "loan_amount": 150000,
  "tenure_months": 240,
  "existing_liabilities": 75000,
  "location": "AU"
}
```

**Expected Outcome:**
- **Decision:** REJECTED ❌
- **Risk Score:** 80+ (extremely high risk)
- **Confidence:** 60%+
- **Reasoning:** Multiple rejection factors - very poor credit, excessive debt burden, unemployment, high LTI

**Key Metrics:**
- DTI: 300% (EXTREMELY HIGH - massively exceeds 50%)
- LTI: 5.0 (HIGH - exceeds 4.0)
- Credit Risk: VERY_HIGH (520 score)
- Employment: Unemployed

---

## Test Case 5: APPROVED Status (Self-Employed Professional)

**Scenario:** Good credit, moderate income, self-employed but stable, reasonable loan

**Input Data:**
```json
{
  "applicant_id": "TEST-APPROVED-SE-001",
  "age": 42,
  "income": 85000,
  "employment_type": "Self-Employed",
  "credit_score": 745,
  "loan_amount": 120000,
  "tenure_months": 180,
  "existing_liabilities": 12000,
  "location": "CA"
}
```

**Expected Outcome:**
- **Decision:** APPROVED ✅
- **Risk Score:** 20-30 (low-moderate risk)
- **Confidence:** 75-85%
- **Reasoning:** Acceptable credit, manageable DTI despite self-employment, conservative loan sizing

**Key Metrics:**
- DTI: 33.6% (FAVORABLE)
- LTI: 1.41 (LOW)
- Credit Risk: MODERATE (745 score)
- Employment Risk: MEDIUM (Self-Employed)

---

## Test Case 6: REJECTED Status (High DTI Anomaly)

**Scenario:** Good credit but DTI exceeds threshold (50%+)

**Input Data:**
```json
{
  "applicant_id": "TEST-REJECTED-DTI-001",
  "age": 40,
  "income": 50000,
  "employment_type": "Salaried",
  "credit_score": 720,
  "loan_amount": 160000,
  "tenure_months": 300,
  "existing_liabilities": 20000,
  "location": "IE"
}
```

**Expected Outcome:**
- **Decision:** REJECTED ❌
- **Risk Score:** 45-55 (moderate-high risk)
- **Confidence:** 70%+
- **Reasoning:** DTI exceeds 50% threshold (financial anomaly detected) - auto-rejection trigger

**Key Metrics:**
- DTI: 52.80% (HIGH_RISK - exceeds 50% threshold) ⚠️
- LTI: 3.2 (MODERATE)
- Credit Risk: MODERATE (720 score)
- Anomalies: DTI exceeds 50%

---

## Test Case 7: BORDERLINE Status (Mixed Signals)

**Scenario:** Moderate credit (700), borderline DTI (46%), mixed profile

**Input Data:**
```json
{
  "applicant_id": "TEST-BORDERLINE-001",
  "age": 35,
  "income": 70000,
  "employment_type": "Salaried",
  "credit_score": 700,
  "loan_amount": 145000,
  "tenure_months": 240,
  "existing_liabilities": 25000,
  "location": "US"
}
```

**Expected Outcome:**
- **Decision:** APPROVED or REQUIRES_REVIEW (system dependent)
- **Risk Score:** 30-40 (moderate risk)
- **Confidence:** 80%+
- **Reasoning:** Mixed signals - moderate credit, borderline DTI

**Key Metrics:**
- DTI: 46.07% (BORDERLINE - near 50% threshold)
- LTI: 2.07 (MODERATE)
- Credit Risk: MODERATE (700 score)
- Employment: Stable (Salaried)

---

## Decision Logic Summary

### AUTO-APPROVAL Criteria:
✅ DTI is FAVORABLE (< 36%) or ACCEPTABLE (< 43%)
✅ Credit Risk is LOW or MODERATE  
✅ No financial anomalies
✅ Employment Risk is LOW or MEDIUM
✅ Confidence >= 75%

### AUTO-REJECTION Criteria:
❌ Credit Risk is VERY_HIGH (score < 550)
❌ DTI is HIGH_RISK (>= 50%) AND Credit Risk is HIGH
❌ LTI >= 4.0 AND Income is LOW
❌ Financial anomalies (DTI > 50%)

---

## Running Test Cases

```bash
# Test APPROVED case
curl -X POST http://localhost:8000/api/v1/applications \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "TEST-APPROVED-001",
    "age": 38,
    "income": 120000,
    "employment_type": "Salaried",
    "credit_score": 760,
    "loan_amount": 200000,
    "tenure_months": 240,
    "existing_liabilities": 15000,
    "location": "US"
  }'

# Test REJECTED case
curl -X POST http://localhost:8000/api/v1/applications \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "TEST-REJECTED-001",
    "age": 52,
    "income": 35000,
    "employment_type": "Unemployed",
    "credit_score": 480,
    "loan_amount": 250000,
    "tenure_months": 300,
    "existing_liabilities": 45000,
    "location": "UK"
  }'

# Get decision result (replace TRACE_ID with actual trace ID)
curl http://localhost:8000/api/v1/applications/{TRACE_ID}

# Get audit trail
curl http://localhost:8000/api/v1/applications/{TRACE_ID}/audit
```

**Last Updated:** 2026-11-03  
**Status:** Production Ready ✅
