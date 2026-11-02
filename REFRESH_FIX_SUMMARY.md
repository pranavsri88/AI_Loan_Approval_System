# Refresh Decision & Audit Trail Fix - Summary

## Issue Reported
- ❌ "Refresh decision" button not working after submitting application
- ❌ "Refresh Audit trail" button not working after submitting application
- Error: `'NoneType' object has no attribute 'get'`

## Root Cause Analysis

### Primary Issue
In `src/orchestration/langgraph_workflow.py` (line 440), the code attempted to call `.get()` on a potentially `None` value:

```python
# BROKEN CODE
"risk_score": final_state.get("decision_result", {}).get("risk_score"),
```

When the workflow encountered errors (e.g., API authentication issues, missing MCP modules), `decision_result` could be `None`, causing an `AttributeError` when trying to call `.get()` on it.

### Secondary Issues
1. **Missing fastmcp module** - MCP servers tried to import `fastmcp` which wasn't properly installed
2. **Invalid Anthropic API key** - `.env` file contained placeholder key (`sk-ant-xxx-...`)

## Changes Made

### 1. Fixed langgraph_workflow.py (Primary Fix)
**File:** `src/orchestration/langgraph_workflow.py` (lines 434-448)

**Before:**
```python
result = {
    "trace_id": trace_id,
    "applicant_id": applicant_data.get("applicant_id"),
    "decision": final_state.get("final_decision", "UNKNOWN"),
    "confidence": final_state.get("final_confidence", 0.0),
    "risk_score": final_state.get("decision_result", {}).get("risk_score"),  # ❌ UNSAFE
    "case_id": final_state.get("case_id"),
    "agents_run": final_state.get("agents_run", []),
    "timestamp": datetime.utcnow().isoformat(),
}

if final_state.get("decision_result"):
    result["decision_factors"] = final_state["decision_result"].get("decision_factors", [])
    result["explanation"] = final_state["decision_result"].get("explanation", "")
```

**After:**
```python
# Safe handling of None decision_result
decision_result = final_state.get("decision_result") or {}
result = {
    "trace_id": trace_id,
    "applicant_id": applicant_data.get("applicant_id"),
    "decision": final_state.get("final_decision", "UNKNOWN"),
    "confidence": final_state.get("final_confidence", 0.0),
    "risk_score": decision_result.get("risk_score"),  # ✅ SAFE
    "case_id": final_state.get("case_id"),
    "agents_run": final_state.get("agents_run", []),
    "timestamp": datetime.utcnow().isoformat(),
    "decision_factors": decision_result.get("decision_factors", []),
    "explanation": decision_result.get("explanation", ""),
}
```

**Why this works:**
- `decision_result = final_state.get("decision_result") or {}` → Returns `{}` if `None`
- All subsequent `.get()` calls are safe and return appropriate defaults
- No more `AttributeError`

### 2. Installed Missing Dependencies
```bash
pip install mcp
```
This resolved the `ModuleNotFoundError: No module named 'fastmcp'` issue.

## Testing Results

### Test Cases Passed ✅
1. **Submit application** → Returns trace_id
2. **First refresh decision call** → Returns decision data
3. **Second refresh decision call** → Succeeds without errors
4. **First refresh audit trail call** → Returns audit trail data
5. **Second refresh audit trail call** → Succeeds without errors
6. **Invalid trace ID** → Returns proper 404 error

### API Endpoints Status
- ✅ `POST /api/v1/applications` → Working
- ✅ `GET /api/v1/applications/{trace_id}` → Working (Refresh Decision)
- ✅ `GET /api/v1/applications/{trace_id}/audit` → Working (Refresh Audit Trail)

## Frontend Impact

### Streamlit UI Behavior
**Before Fix:**
- Submit button works → Trace ID received
- Refresh Decision button → Shows error
- Refresh Audit Trail button → Shows error

**After Fix:**
- Submit button works → Trace ID received
- Refresh Decision button → ✅ Works! Shows decision data
- Refresh Audit Trail button → ✅ Works! Shows audit trail data
- Multiple clicks → ✅ No errors, consistent response

## Error Handling
The fix ensures graceful degradation:
- When `decision_result` is `None` (due to errors)
- Fields default to sensible values: `None`, `[]`, `""`
- API returns valid response (never crashes with AttributeError)
- Streamlit UI receives response and displays appropriately

## Recommendation for Production
1. **Obtain valid Anthropic API key** - Update `.env` with real key
2. **Handle workflow errors more explicitly** - Consider returning more detailed error information
3. **Cache decision results** - To reduce repeated API calls
4. **Add retry logic** - For transient failures in agent execution

## Files Modified
- `src/orchestration/langgraph_workflow.py` - Fixed None handling

## Verification
Run the test script to verify:
```bash
python /tmp/test_refresh.py
```

Expected output:
```
================================================================================
✅ All refresh tests passed!
================================================================================
```
