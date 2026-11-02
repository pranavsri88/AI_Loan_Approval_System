# AI Loan Approval System - Test Cases

Comprehensive test cases for all three decision statuses: APPROVED, REJECTED, and REQUIRES_REVIEW.

---

## Test Case 1: ✅ APPROVED

**Profile**: Strong financial profile with excellent credit and low debt

| Field | Value |
|-------|-------|
| **Applicant ID** | TEST-APPROVED-001 |
| **Age** | 45 |
| **Annual Income** | $120,000 |
| **Credit Score** | 785 |
| **Employment Type** | Salaried |
| **Loan Amount** | $200,000 |
| **Loan Term** | 252 months (21 years) |
| **Existing Liabilities** | $15,000 |
| **Location** | US |

**Expected Decision**: **APPROVED** ✅

**Expected Metrics**:
- Confidence: 85%+
- Risk Score: < 50/100
- DTI: ~15% (favorable)
- LTI: ~1.67x (reasonable)

**Why Approved**:
- Excellent credit score (785 > 750)
- Low monthly debt obligations
- Stable employment (Salaried)
- Mid-career age (45 years)
- Reasonable loan-to-income ratio

**cURL Command**:
```bash
curl -X POST http://localhost:8000/api/v1/applications \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "TEST-APPROVED-001",
    "age": 45,
    "income": 120000,
    "employment_type": "Salaried",
    "credit_score": 785,
    "loan_amount": 200000,
    "tenure_months": 252,
    "existing_liabilities": 15000,
    "location": "US"
  }'
```

---

## Test Case 2: ❌ REJECTED

**Profile**: Weak financial profile with poor credit and excessive debt

| Field | Value |
|-------|-------|
| **Applicant ID** | TEST-REJECTED-001 |
| **Age** | 35 |
| **Annual Income** | $45,000 |
| **Credit Score** | 520 |
| **Employment Type** | Salaried |
| **Loan Amount** | $250,000 |
| **Loan Term** | 360 months (30 years) |
| **Existing Liabilities** | $40,000 |
| **Location** | US |

**Expected Decision**: **REJECTED** ❌

**Expected Metrics**:
- Confidence: 20-30%
- Risk Score: 75+/100
- DTI: ~96% (very high)
- LTI: ~5.56x (too high)

**Why Rejected**:
- Very poor credit score (520 < 600)
- Extremely high monthly debt obligations
- Loan amount far exceeds annual income
- Cannot sustain debt repayment
- High default risk

**cURL Command**:
```bash
curl -X POST http://localhost:8000/api/v1/applications \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "TEST-REJECTED-001",
    "age": 35,
    "income": 45000,
    "employment_type": "Salaried",
    "credit_score": 520,
    "loan_amount": 250000,
    "tenure_months": 360,
    "existing_liabilities": 40000,
    "location": "US"
  }'
```

---

## Test Case 3: ⚠️ REQUIRES_REVIEW (Manual Review)

**Profile**: Borderline profile - not clearly approved or rejected, needs human judgment

| Field | Value |
|-------|-------|
| **Applicant ID** | TEST-MANUAL-001 |
| **Age** | 32 |
| **Annual Income** | $65,000 |
| **Credit Score** | 680 |
| **Employment Type** | Salaried |
| **Loan Amount** | $180,000 |
| **Loan Term** | 240 months (20 years) |
| **Existing Liabilities** | $25,000 |
| **Location** | US |

**Expected Decision**: **REQUIRES_REVIEW** ⚠️

**Expected Metrics**:
- Confidence: 45-55%
- Risk Score: 55-65/100
- DTI: ~38% (borderline)
- LTI: ~2.77x (moderate)

**Why Manual Review**:
- Fair credit score (680 - between good and poor)
- Borderline DTI ratio (38% is at acceptable threshold)
- Moderate loan-to-income ratio
- Mixed financial signals
- Requires human underwriter assessment

**cURL Command**:
```bash
curl -X POST http://localhost:8000/api/v1/applications \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "TEST-MANUAL-001",
    "age": 32,
    "income": 65000,
    "employment_type": "Salaried",
    "credit_score": 680,
    "loan_amount": 180000,
    "tenure_months": 240,
    "existing_liabilities": 25000,
    "location": "US"
  }'
```

---

## Additional Test Cases (Edge Cases)

### Test Case 4: APPROVED - Conservative Borrower

**Profile**: Excellent credit, minimal debt, very conservative loan request

| Field | Value |
|-------|-------|
| **Applicant ID** | TEST-APPROVED-CONSERVATIVE |
| **Age** | 50 |
| **Annual Income** | $150,000 |
| **Credit Score** | 800 |
| **Employment Type** | Salaried |
| **Loan Amount** | $100,000 |
| **Loan Term** | 120 months (10 years) |
| **Existing Liabilities** | $5,000 |
| **Location** | US |

**Expected**: **APPROVED** with 95%+ confidence

---

### Test Case 5: REJECTED - Unemployed with Large Loan

**Profile**: Unemployed individual requesting excessive loan

| Field | Value |
|-------|-------|
| **Applicant ID** | TEST-REJECTED-UNEMPLOYED |
| **Age** | 40 |
| **Annual Income** | $20,000 |
| **Credit Score** | 600 |
| **Employment Type** | Unemployed |
| **Loan Amount** | $300,000 |
| **Loan Term** | 360 months |
| **Existing Liabilities** | $50,000 |
| **Location** | US |

**Expected**: **REJECTED** with 90%+ confidence

---

### Test Case 6: REQUIRES_REVIEW - Self-Employed

**Profile**: Self-employed with good income but variable employment classification

| Field | Value |
|-------|-------|
| **Applicant ID** | TEST-MANUAL-SELF-EMPLOYED |
| **Age** | 38 |
| **Annual Income** | $95,000 |
| **Credit Score** | 710 |
| **Employment Type** | Self-Employed |
| **Loan Amount** | $200,000 |
| **Loan Term** | 240 months |
| **Existing Liabilities** | $20,000 |
| **Location** | US |

**Expected**: **REQUIRES_REVIEW** - Self-employment needs human assessment

---

## Running the Tests Through UI

### Steps to Test in Streamlit UI:

1. **Open the application**: http://localhost:8501

2. **For each test case**:
   - Fill in the Application Form with the values above
   - Click "📤 Submit Application"
   - Copy the Trace ID
   - Go to "📊 Decision" tab
   - Verify the decision matches expected result
   - Click "🔄 Refresh Decision" to verify persistence
   - Go to "🔍 Audit Trail" tab to see processing details

3. **Verify metrics**:
   - Check confidence level
   - Check risk score
   - Review decision explanation
   - Confirm decision factors

---

## Running All Tests with cURL

Run all tests automatically:

```bash
#!/bin/bash

# Test 1: APPROVED
echo "Testing APPROVED case..."
RESULT1=$(curl -s -X POST http://localhost:8000/api/v1/applications \
  -H "Content-Type: application/json" \
  -d '{"applicant_id":"TEST-APPROVED-001","age":45,"income":120000,"employment_type":"Salaried","credit_score":785,"loan_amount":200000,"tenure_months":252,"existing_liabilities":15000,"location":"US"}')
TRACE1=$(echo $RESULT1 | python3 -c "import sys,json; print(json.load(sys.stdin)['trace_id'])")
sleep 1
curl -s http://localhost:8000/api/v1/applications/$TRACE1 | python3 -m json.tool | grep -E "decision|confidence|risk_score"

# Test 2: REJECTED
echo -e "\nTesting REJECTED case..."
RESULT2=$(curl -s -X POST http://localhost:8000/api/v1/applications \
  -H "Content-Type: application/json" \
  -d '{"applicant_id":"TEST-REJECTED-001","age":35,"income":45000,"employment_type":"Salaried","credit_score":520,"loan_amount":250000,"tenure_months":360,"existing_liabilities":40000,"location":"US"}')
TRACE2=$(echo $RESULT2 | python3 -c "import sys,json; print(json.load(sys.stdin)['trace_id'])")
sleep 1
curl -s http://localhost:8000/api/v1/applications/$TRACE2 | python3 -m json.tool | grep -E "decision|confidence|risk_score"

# Test 3: REQUIRES_REVIEW
echo -e "\nTesting REQUIRES_REVIEW case..."
RESULT3=$(curl -s -X POST http://localhost:8000/api/v1/applications \
  -H "Content-Type: application/json" \
  -d '{"applicant_id":"TEST-MANUAL-001","age":32,"income":65000,"employment_type":"Salaried","credit_score":680,"loan_amount":180000,"tenure_months":240,"existing_liabilities":25000,"location":"US"}')
TRACE3=$(echo $RESULT3 | python3 -c "import sys,json; print(json.load(sys.stdin)['trace_id'])")
sleep 1
curl -s http://localhost:8000/api/v1/applications/$TRACE3 | python3 -m json.tool | grep -E "decision|confidence|risk_score"
```

---

## Expected Outcomes

### Success Criteria:

✅ **APPROVED** - Confidence 85%+, Risk < 50  
✅ **REJECTED** - Confidence 70%+, Risk 75+  
✅ **REQUIRES_REVIEW** - Confidence 50±5%, Risk 60±10  

### Validation Points:

1. Decision matches expected status
2. Confidence score is reasonable
3. Risk score reflects profile
4. Explanation is coherent
5. Refresh buttons work without errors
6. Audit trail shows correct agents
7. All response fields are populated

---

## Testing Strategy

### Phase 1: Basic Validation
- Run Test Cases 1-3
- Verify decision types are correct
- Confirm metrics are in expected ranges

### Phase 2: Edge Cases
- Run Test Cases 4-6
- Verify edge case handling
- Check error messages if applicable

### Phase 3: UI Experience
- Submit each case through UI
- Test refresh functionality
- Verify audit trail details
- Check explanations readability

### Phase 4: Stress Testing
- Submit multiple applications
- Verify caching works
- Check response times
- Monitor API logs

---

## Notes

- All test cases use realistic financial profiles
- Metrics are calculated based on actual financial formulas
- Confidence scores reflect certainty level
- Risk scores range from 0-100 (higher = riskier)
- All timestamps are recorded for audit trail
- Each test generates unique Trace IDs for tracking
