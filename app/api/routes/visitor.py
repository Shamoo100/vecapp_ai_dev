"""API routes for visitor management."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from app.core.api_key_auth import get_current_tenant, verify_api_key
from app.core.database import Database
from app.models.tenant import Tenant
from app.agents.data_collection_agent import DataCollectionAgent
from app.api.schemas import VisitorCreate, VisitorResponse

router = APIRouter(prefix="/api/v1/visitors", tags=["visitors"])

@router.post("/", response_model=VisitorResponse)
async def create_visitor(
    visitor: VisitorCreate,
    tenant: Tenant = Depends(get_current_tenant),
    api_key: str = Depends(verify_api_key)
):
    """Create a new visitor and initiate data collection workflow.
    
    Args:
        visitor: Visitor data
        tenant: Current tenant context
        api_key: API key for authentication
        
    Returns:
        Created visitor details
        
    Raises:
        HTTPException: If creation fails
    """
    try:
        # Initialize Data Collection Agent
        dca = DataCollectionAgent(
            agent_id=f"dca-{tenant.id}",
            tenant_id=tenant.id,
            database=Database()
        )
        
        # Process visitor data
        result = await dca.process(visitor.dict())
        
        return VisitorResponse(
            id=result['visitor_id'],
            **visitor.dict(),
            created_at=datetime.utcnow(),
            status="processing"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{visitor_id}", response_model=VisitorResponse)
async def get_visitor(
    visitor_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    api_key: str = Depends(verify_api_key)
):
    """Get visitor details by ID.
    
    Args:
        visitor_id: ID of the visitor
        tenant: Current tenant context
        api_key: API key for authentication
        
    Returns:
        Visitor details
        
    Raises:
        HTTPException: If visitor not found
    """
    try:
        db = Database()
        visitor = await db.get_visitor(visitor_id, tenant.id)
        if not visitor:
            raise HTTPException(status_code=404, detail="Visitor not found")
        return VisitorResponse(**visitor)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[VisitorResponse])
async def list_visitors(
    tenant: Tenant = Depends(get_current_tenant),
    api_key: str = Depends(verify_api_key),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = None
):
    """List visitors with pagination and optional filtering.
    
    Args:
        tenant: Current tenant context
        api_key: API key for authentication
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Optional status filter
        
    Returns:
        List of visitors
    """
    try:
        db = Database()
        visitors = await db.list_visitors(
            tenant_id=tenant.id,
            skip=skip,
            limit=limit,
            status=status
        )
        return [VisitorResponse(**visitor) for visitor in visitors]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))