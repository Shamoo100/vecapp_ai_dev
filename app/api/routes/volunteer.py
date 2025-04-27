"""API routes for volunteer management."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from app.core.auth import get_current_tenant, verify_api_key
from app.core.database import Database
from app.models.tenant import Tenant
from app.agents.volunteer_coordination_agent import VolunteerCoordinationAgent
from app.core.messaging import MessageQueue
from app.core.notifications import NotificationService
from app.api.schemas import VolunteerAssignmentCreate, VolunteerAssignmentResponse

router = APIRouter(prefix="/api/v1/volunteers", tags=["volunteers"])

@router.post("/assignments", response_model=VolunteerAssignmentResponse)
async def create_assignment(
    assignment: VolunteerAssignmentCreate,
    tenant: Tenant = Depends(get_current_tenant),
    api_key: str = Depends(verify_api_key)
):
    """Create a new volunteer assignment.
    
    Args:
        assignment: Assignment details
        tenant: Current tenant context
        api_key: API key for authentication
        
    Returns:
        Created assignment details
        
    Raises:
        HTTPException: If creation fails
    """
    try:
        vca = VolunteerCoordinationAgent(
            agent_id=f"vca-{tenant.id}",
            tenant_id=tenant.id,
            message_queue=MessageQueue(),
            notification_service=NotificationService()
        )
        
        result = await vca.process(assignment.dict())
        
        return VolunteerAssignmentResponse(
            id=result['assignment_id'],
            **assignment.dict(),
            created_at=datetime.utcnow(),
            status="assigned"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/assignments/{assignment_id}", response_model=VolunteerAssignmentResponse)
async def get_assignment(
    assignment_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    api_key: str = Depends(verify_api_key)
):
    """Get assignment details by ID.
    
    Args:
        assignment_id: ID of the assignment
        tenant: Current tenant context
        api_key: API key for authentication
        
    Returns:
        Assignment details
        
    Raises:
        HTTPException: If assignment not found
    """
    try:
        db = Database()
        assignment = await db.get_volunteer_assignment(assignment_id, tenant.id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        return VolunteerAssignmentResponse(**assignment)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/assignments", response_model=List[VolunteerAssignmentResponse])
async def list_assignments(
    tenant: Tenant = Depends(get_current_tenant),
    api_key: str = Depends(verify_api_key),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    volunteer_id: Optional[str] = None
):
    """List volunteer assignments with pagination and filtering.
    
    Args:
        tenant: Current tenant context
        api_key: API key for authentication
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Optional status filter
        volunteer_id: Optional volunteer ID filter
        
    Returns:
        List of assignments
    """
    try:
        db = Database()
        assignments = await db.list_volunteer_assignments(
            tenant_id=tenant.id,
            skip=skip,
            limit=limit,
            status=status,
            volunteer_id=volunteer_id
        )
        return [VolunteerAssignmentResponse(**assignment) for assignment in assignments]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))