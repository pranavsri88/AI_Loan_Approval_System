# Refresh Decision & Audit Trail - User Guide

## Overview
The Streamlit UI now has fully functional **Refresh** buttons to re-fetch decision and audit trail data without resubmitting applications.

## How to Use

### 1. Submit an Application
1. Go to the **📋 Application** tab
2. Fill in the loan application form
3. Click **📤 Submit Application**
4. You'll see: `✅ Application submitted! Trace ID: TRACE-xxxxx`

### 2. View and Refresh Decision
1. Switch to the **📊 Decision** tab
2. You'll see the decision information:
   - ✅ **APPROVED** / ❌ **REJECTED** / ⚠️ **REQUIRES MANUAL REVIEW**
   - **Confidence**: 0.0 - 1.0 confidence score
   - **Risk Score**: 0-100 risk assessment
   - **Case ID**: Unique case identifier
   - **Decision Explanation**: Reasoning behind the decision
   - **Decision Factors**: Key factors that influenced the decision

3. **To refresh the decision**, click the **🔄 Refresh Decision** button
   - The button will update the decision data from the server
   - Use this to check for updates if processing takes time
   - Can be clicked multiple times

### 3. View and Refresh Audit Trail
1. Switch to the **🔍 Audit Trail** tab
2. You'll see:
   - **Trace ID**: Application processing trace identifier
   - **Case ID**: Unique case ID
   - **Decision**: Final decision status
   - **Processing Pipeline**: Shows which agents processed the application
   - **Application Details**: Full loan application details

3. **To refresh the audit trail**, click the **🔄 Refresh Audit Trail** button
   - Updates the audit trail and processing pipeline info
   - Can be clicked multiple times
   - Useful for verifying all agents have completed processing

## What Each Tab Shows

### 📋 Application Tab
- **Purpose**: Submit new loan applications
- **Features**:
  - 10 input fields for applicant data
  - Auto-generated applicant ID
  - Submit and Clear buttons
  - Real-time input validation

### 📊 Decision Tab
- **Purpose**: View loan decision and reasoning
- **Features**:
  - Final decision status
  - Confidence score
  - Risk assessment
  - Decision factors breakdown
  - Detailed explanation of decision
  - Refresh button to get latest decision

### 🔍 Audit Trail Tab
- **Purpose**: View compliance and processing information
- **Features**:
  - Trace ID for tracking
  - Case ID for record keeping
  - Processing pipeline (which agents ran)
  - Application details summary
  - Refresh button to update pipeline info

## Troubleshooting

### Problem: Refresh buttons don't work
**Solution:**
1. Make sure the FastAPI backend is running on port 8000
2. Check System Status sidebar for connection status
3. Try the "🧪 Test API Connection" button in the sidebar
4. If API is down, restart it with: `python -m uvicorn src.api.main:app --reload`

### Problem: Decision shows but data is incomplete
**Reason:** This is normal when the workflow encounters errors
- Fields like `confidence`, `risk_score` may be `null`
- `decision_factors` may be empty
- Decision will be `REQUIRES_REVIEW` if agents couldn't complete

**Solution:** 
1. Contact support or check API logs
2. Retry submission with different application data

### Problem: Audit Trail shows limited agents_run
**Reason:** Some agents may have failed or been skipped
- This is by design - escalates to manual review
- Shows in `agents_run` array

**Solution:** 
1. This is expected behavior
2. Applications with errors are routed to manual review
3. Provide valid Anthropic API key for full agent execution

## API Endpoints (Behind the Scenes)

### Submit Application
```
POST /api/v1/applications
Returns: trace_id for polling
```

### Get Decision (Refresh Decision)
```
GET /api/v1/applications/{trace_id}
Returns: decision, confidence, risk_score, decision_factors, explanation
```

### Get Audit Trail (Refresh Audit Trail)
```
GET /api/v1/applications/{trace_id}/audit
Returns: trace_id, case_id, decision, agents_run, application details
```

## Performance Notes

- **First submission**: 0.5-30 seconds depending on LLM availability
- **Refresh Decision**: < 1 second (cached result)
- **Refresh Audit Trail**: < 1 second (cached result)
- All refresh operations are instant since they retrieve cached data

## Feature Status
- ✅ Submit Application - Fully working
- ✅ Refresh Decision - Fully working
- ✅ Refresh Audit Trail - Fully working
- ✅ Multiple refreshes - Supported
- ✅ Error handling - Graceful with sensible defaults
