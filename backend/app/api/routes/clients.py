"""
Clients API - Manage clients (companies)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any, List
from uuid import UUID, uuid4
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.client import Client
from app.models.review_queue import ReviewQueue
from app.schemas.client import ClientCreateSchema, ClientUpdateSchema, ClientResponse
from app.services.brreg import search_companies, get_company_details

router = APIRouter(prefix="/api/clients", tags=["Clients"])


class StatusSummary(BaseModel):
    vouchers_pending: int
    bank_items_open: int
    reconciliation_status: str
    vat_status: str


class ClientListItem(BaseModel):
    id: str
    name: str
    org_number: str
    status_summary: StatusSummary


class ClientListResponse(BaseModel):
    items: list[ClientListItem]
    total: int


class ClientDetail(BaseModel):
    id: str
    name: str
    org_number: str
    address: str | None = None
    contact_person: str | None = None
    contact_email: str | None = None
    fiscal_year_start: str | None = None
    vat_registered: bool = True
    status_summary: StatusSummary


async def get_status_summary(client_id: UUID, db: AsyncSession) -> StatusSummary:
    """Calculate status summary for a client"""
    # TODO: Implement actual calculation per client
    # For now, return defaults to get API working
    return StatusSummary(
        vouchers_pending=0,
        bank_items_open=0,
        reconciliation_status="not_started",
        vat_status="not_started"
    )


@router.get("/search-brreg")
async def search_brreg_companies(
    q: str = Query(..., min_length=2, description="Company name search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results")
) -> List[Dict[str, Any]]:
    """
    Search Norwegian company registry (Brønnøysundregistrene) by company name
    
    This endpoint provides autocomplete functionality for client creation.
    
    Query params:
    - q: Search query (minimum 2 characters, e.g., "GHB")
    - limit: Maximum number of results (default: 10, max: 50)
    
    Returns:
    List of companies with:
    - name: Company name
    - org_number: Organization number (9 digits)
    - address: Formatted address
    - postal_code: Postal code
    - city: City name
    - municipality: Municipality name
    - nace_code: Industry classification code
    - nace_description: Industry description
    - organizational_form: Company type (AS, ASA, etc.)
    
    Example:
    GET /api/clients/search-brreg?q=GHB
    
    Response:
    [
        {
            "name": "GHB AS",
            "org_number": "123456789",
            "address": "Testgate 1",
            "postal_code": "0001",
            "city": "Oslo",
            "nace_description": "Consulting"
        }
    ]
    """
    companies = await search_companies(q, limit=limit)
    return companies


@router.get("/brreg/{org_number}")
async def get_brreg_company_details(
    org_number: str
) -> Dict[str, Any]:
    """
    Get detailed company information from Brønnøysundregistrene by org number
    
    Path params:
    - org_number: 9-digit organization number
    
    Returns:
    Company details or 404 if not found
    """
    company = await get_company_details(org_number)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found in Brønnøysundregistrene")
    return company


@router.post("/", response_model=ClientDetail, status_code=201)
async def create_client(
    data: ClientCreateSchema,
    tenant_id: UUID = Query(..., description="Tenant UUID"),
    db: AsyncSession = Depends(get_db)
) -> ClientDetail:
    """
    Create new client (company)
    
    - Validates org_number uniqueness
    - Generates sequential client_number
    - Creates default settings (to be implemented)
    - Auto-creates default chart of accounts (to be implemented)
    """
    
    # Check org_number uniqueness
    existing_query = select(Client).where(Client.org_number == data.org_number)
    existing_result = await db.execute(existing_query)
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Client with org_number {data.org_number} already exists"
        )
    
    # Generate sequential client_number
    last_query = (
        select(Client)
        .where(Client.tenant_id == tenant_id)
        .order_by(Client.client_number.desc())
        .limit(1)
    )
    last_result = await db.execute(last_query)
    last_client = last_result.scalar_one_or_none()
    
    if last_client and last_client.client_number.isdigit():
        next_number = int(last_client.client_number) + 1
    else:
        next_number = 1
    
    client_number = str(next_number).zfill(5)  # "00001", "00002", etc.
    
    # Parse fiscal_year_start to month integer (MM-DD -> month)
    fiscal_month = int(data.fiscal_year_start.split('-')[0])
    
    # Create client
    client = Client(
        id=uuid4(),
        tenant_id=tenant_id,
        client_number=client_number,
        name=data.name,
        org_number=data.org_number,
        industry=data.industry,
        start_date=data.start_date,
        address=data.address,
        contact_person=data.contact_person,
        contact_email=data.contact_email,
        fiscal_year_start=fiscal_month,
        vat_registered=data.vat_registered,
        is_demo=False,  # Real client, not demo
        status="active",
    )
    
    db.add(client)
    await db.flush()
    
    # TODO: Create default chart of accounts (NS 4102) - to be implemented later
    # TODO: Create default settings - to be implemented later
    # TODO: Create default fiscal year - to be implemented later
    
    await db.commit()
    await db.refresh(client)
    
    status_summary = await get_status_summary(client.id, db)
    
    return ClientDetail(
        id=str(client.id),
        name=client.name,
        org_number=client.org_number,
        address=client.address,
        contact_person=client.contact_person,
        contact_email=client.contact_email,
        fiscal_year_start=data.fiscal_year_start,
        vat_registered=client.vat_registered,
        status_summary=status_summary
    )


@router.get("/")
async def get_clients(
    limit: int = 50,
    offset: int = 0,
    status: str = Query("active", description="Filter by status (active/inactive/all)"),
    tenant_id: UUID = Query(None, description="Filter by tenant ID"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get list of all clients with status summary and pagination
    
    Query params:
    - limit: Items per page (default: 50, max: 500)
    - offset: Starting index (default: 0)
    - status: Filter by status (active/inactive/all, default: active)
    - tenant_id: Filter by tenant ID (optional)
    
    Returns:
    {
        "items": [...],
        "total": int,
        "limit": int,
        "offset": int,
        "page_number": int
    }
    """
    # Validate limit
    limit = min(max(limit, 1), 500)
    offset = max(offset, 0)
    
    # Build query filters
    filters = []
    if status != "all":
        filters.append(Client.status == status)
    if tenant_id:
        filters.append(Client.tenant_id == tenant_id)
    
    # Get total count
    count_query = select(func.count()).select_from(Client)
    if filters:
        for f in filters:
            count_query = count_query.where(f)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Get paginated results
    query = select(Client).order_by(Client.name).limit(limit).offset(offset)
    if filters:
        for f in filters:
            query = query.where(f)
    
    result = await db.execute(query)
    clients = result.scalars().all()
    
    items = []
    for client in clients:
        status_summary = await get_status_summary(client.id, db)
        items.append(
            ClientListItem(
                id=str(client.id),
                name=client.name,
                org_number=client.org_number,
                status_summary=status_summary
            )
        )
    
    page_number = (offset // limit) + 1 if limit > 0 else 1
    
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "page_number": page_number
    }


@router.get("/{client_id}")
async def get_client(
    client_id: str,
    db: AsyncSession = Depends(get_db)
) -> ClientDetail:
    """
    Get a single client by ID with full details
    """
    try:
        query = select(Client).where(Client.id == UUID(client_id))
        result = await db.execute(query)
        client = result.scalar_one_or_none()
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        status_summary = await get_status_summary(client.id, db)
        
        # Convert fiscal_year_start from month integer to MM-DD format
        fiscal_year_str = f"{client.fiscal_year_start:02d}-01" if client.fiscal_year_start else "01-01"
        
        return ClientDetail(
            id=str(client.id),
            name=client.name,
            org_number=client.org_number,
            address=client.address,
            contact_person=client.contact_person,
            contact_email=client.contact_email,
            fiscal_year_start=fiscal_year_str,
            vat_registered=client.vat_registered,
            status_summary=status_summary
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client ID format")


@router.put("/{client_id}", response_model=ClientDetail)
async def update_client(
    client_id: str,
    data: ClientUpdateSchema,
    db: AsyncSession = Depends(get_db)
) -> ClientDetail:
    """
    Update client settings
    
    - Can update name, address, contacts, fiscal settings
    - Cannot change org_number (immutable)
    """
    try:
        query = select(Client).where(Client.id == UUID(client_id))
        result = await db.execute(query)
        client = result.scalar_one_or_none()
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Update fields if provided
        if data.name is not None:
            client.name = data.name
        if data.industry is not None:
            client.industry = data.industry
        if data.address is not None:
            client.address = data.address
        if data.contact_person is not None:
            client.contact_person = data.contact_person
        if data.contact_email is not None:
            client.contact_email = data.contact_email
        if data.fiscal_year_start is not None:
            fiscal_month = int(data.fiscal_year_start.split('-')[0])
            client.fiscal_year_start = fiscal_month
        if data.vat_registered is not None:
            client.vat_registered = data.vat_registered
        if data.status is not None:
            client.status = data.status
        
        client.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(client)
        
        status_summary = await get_status_summary(client.id, db)
        
        fiscal_year_str = f"{client.fiscal_year_start:02d}-01" if client.fiscal_year_start else "01-01"
        
        return ClientDetail(
            id=str(client.id),
            name=client.name,
            org_number=client.org_number,
            address=client.address,
            contact_person=client.contact_person,
            contact_email=client.contact_email,
            fiscal_year_start=fiscal_year_str,
            vat_registered=client.vat_registered,
            status_summary=status_summary
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client ID format")


@router.delete("/{client_id}")
async def delete_client(
    client_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Soft delete a client (set inactive)
    
    - Does not actually delete from database
    - Sets status to "inactive"
    """
    try:
        query = select(Client).where(Client.id == UUID(client_id))
        result = await db.execute(query)
        client = result.scalar_one_or_none()
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        client.status = "inactive"
        client.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {
            "message": f"Client '{client.name}' deactivated successfully",
            "client_id": str(client.id)
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client ID format")


# =====================================================================
# AI CONFIDENCE THRESHOLDS - Module 1 Feedback Loop
# =====================================================================

class ThresholdSettings(BaseModel):
    """AI confidence threshold settings"""
    ai_threshold_account: int  # 0-100
    ai_threshold_vat: int      # 0-100
    ai_threshold_global: int   # 0-100


@router.get("/{client_id}/thresholds")
async def get_threshold_settings(
    client_id: str,
    db: AsyncSession = Depends(get_db)
) -> ThresholdSettings:
    """
    Get AI confidence threshold settings for a client.
    
    These thresholds determine when AI suggestions require manual review:
    - ai_threshold_account: Minimum confidence for account number (0-100)
    - ai_threshold_vat: Minimum confidence for VAT code (0-100)
    - ai_threshold_global: Overall minimum confidence (0-100)
    
    If any suggestion is below threshold, item goes to Review Queue.
    """
    try:
        query = select(Client).where(Client.id == UUID(client_id))
        result = await db.execute(query)
        client = result.scalar_one_or_none()
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        return ThresholdSettings(
            ai_threshold_account=client.ai_threshold_account,
            ai_threshold_vat=client.ai_threshold_vat,
            ai_threshold_global=client.ai_threshold_global
        )
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client ID format")


@router.put("/{client_id}/thresholds")
async def update_threshold_settings(
    client_id: str,
    settings: ThresholdSettings,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update AI confidence threshold settings for a client.
    
    Request body:
    {
      "ai_threshold_account": 80,
      "ai_threshold_vat": 85,
      "ai_threshold_global": 85
    }
    
    All values must be between 0 and 100.
    
    Higher thresholds = more items require manual review (safer, slower)
    Lower thresholds = more auto-approval (riskier, faster)
    
    Recommended defaults:
    - Account: 80% (account selection is critical)
    - VAT: 85% (VAT errors are costly)
    - Global: 85% (overall safety threshold)
    """
    # Validate threshold values
    if not (0 <= settings.ai_threshold_account <= 100):
        raise HTTPException(
            status_code=400,
            detail="ai_threshold_account must be between 0 and 100"
        )
    
    if not (0 <= settings.ai_threshold_vat <= 100):
        raise HTTPException(
            status_code=400,
            detail="ai_threshold_vat must be between 0 and 100"
        )
    
    if not (0 <= settings.ai_threshold_global <= 100):
        raise HTTPException(
            status_code=400,
            detail="ai_threshold_global must be between 0 and 100"
        )
    
    try:
        query = select(Client).where(Client.id == UUID(client_id))
        result = await db.execute(query)
        client = result.scalar_one_or_none()
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Update thresholds
        client.ai_threshold_account = settings.ai_threshold_account
        client.ai_threshold_vat = settings.ai_threshold_vat
        client.ai_threshold_global = settings.ai_threshold_global
        client.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(client)
        
        return {
            "message": "Threshold settings updated successfully",
            "client_id": str(client.id),
            "thresholds": {
                "ai_threshold_account": client.ai_threshold_account,
                "ai_threshold_vat": client.ai_threshold_vat,
                "ai_threshold_global": client.ai_threshold_global
            }
        }
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client ID format")
