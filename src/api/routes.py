"""
FastAPI API routes for loan applications.

Endpoints:
- POST /applications - Submit new application
- GET /applications/{case_id} - Get application status/decision
- GET /health - Health check
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from src.orchestration.langgraph_workflow import run_application
from src.api.models import ApplicationRequest, ApplicationResponse, DecisionResponse, ErrorResponse
from src.utils.logger import get_logger
from src.utils.config import settings

logger = get_logger(__name__)

router = APIRouter()

# In-memory storage for demo (Phase 5)
# Phase 5B: Replace with database persistence
_application_cache: Dict[str, Dict[str, Any]] = {}


@router.post(
    "/applications",
    response_model=ApplicationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit Loan Application",
    description="Submit a new loan application for processing",
)
async def submit_application(request: ApplicationRequest) -> ApplicationResponse:
    """
    Submit a new loan application.
    
    Accepts applicant data, validates with Pydantic, executes the complete
    loan decision workflow using all 4 agents, and returns a trace_id for
    polling the decision.
    
    Args:
        request: ApplicationRequest with 10 required fields
    
    Returns:
        ApplicationResponse with trace_id and status PENDING
    
    Raises:
        HTTPException: If validation fails or workflow errors occur
    """
    trace_id = None
    
    try:
        logger.info(f"Received application submission: {request.applicant_id}")
        
        # Convert request to dict for orchestrator
        app_data = request.dict()
        
        # Execute workflow
        logger.debug(f"Executing loan application workflow for {request.applicant_id}")
        result = run_application(app_data)
        
        trace_id = result.get("trace_id")
        
        # Cache result for polling
        _application_cache[trace_id] = result
        
        logger.info(f"Application workflow complete: {trace_id} → {result.get('decision')}")
        
        # Return response (immediately, decision cached)
        # Note: timestamp will default to utcnow() if not provided
        return ApplicationResponse(
            trace_id=trace_id,
            applicant_id=request.applicant_id,
            status="COMPLETED",
        )
    
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    
    except Exception as e:
        logger.error(f"Application submission failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Application processing failed"
        )


@router.get(
    "/applications/{trace_id}",
    response_model=DecisionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Application Decision",
    description="Get the decision and details for a submitted application",
)
async def get_application_decision(trace_id: str) -> DecisionResponse:
    """
    Get application decision and status.
    
    Polls the decision for a previously submitted application using the
    trace_id returned from submission.
    
    Args:
        trace_id: Trace ID from application submission
    
    Returns:
        DecisionResponse with decision (APPROVED|REJECTED|REQUIRES_REVIEW),
        confidence, risk score, decision factors, and explanation
    
    Raises:
        HTTPException: If trace_id not found or application not ready
    """
    logger.info(f"Retrieving application decision: {trace_id}")
    
    # Look up in cache
    if trace_id not in _application_cache:
        logger.warning(f"Trace ID not found: {trace_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application not found: {trace_id}"
        )
    
    result = _application_cache[trace_id]
    
    # Check for errors
    if "error" in result:
        logger.warning(f"Application has error: {result['error']}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return DecisionResponse(
        trace_id=trace_id,
        applicant_id=result.get("applicant_id"),
        status="COMPLETED",
        decision=result.get("decision"),
        risk_score=result.get("risk_score"),
        confidence=result.get("confidence"),
        decision_factors=result.get("decision_factors", []),
        explanation=result.get("explanation"),
    )


@router.get(
    "/applications/{trace_id}/audit",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get Application Audit Trail",
    description="Get immutable audit trail for a processed application",
)
async def get_audit_trail(trace_id: str) -> Dict[str, Any]:
    """
    Get audit trail for application.
    
    Returns immutable record of all decisions, agents run, and reasoning
    for compliance and auditability.
    
    Args:
        trace_id: Trace ID from application submission
    
    Returns:
        Audit trail with agents_run, timestamps, decision factors, and explanation
    
    Raises:
        HTTPException: If trace_id not found
    """
    logger.info(f"Retrieving audit trail: {trace_id}")
    
    if trace_id not in _application_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application not found: {trace_id}"
        )
    
    result = _application_cache[trace_id]
    
    return {
        "trace_id": trace_id,
        "applicant_id": result.get("applicant_id"),
        "case_id": result.get("case_id"),
        "decision": result.get("decision"),
        "agents_run": result.get("agents_run", []),
        "timestamp": result.get("timestamp"),
        "explanation": result.get("explanation"),
        "decision_factors": result.get("decision_factors", []),
    }


@router.get(
    "/health",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check API health status",
)
async def health() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns:
        Health status with environment and configuration info
    """
    return {
        "status": "healthy",
        "environment": settings.app_env,
        "debug": settings.debug,
    }


__all__ = ["router"]
