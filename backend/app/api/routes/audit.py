"""
Audit Trail API - Complete system event history
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import date, datetime
from typing import Optional, Dict, Any
from uuid import UUID

from app.database import get_db
from app.models.audit_trail import AuditTrail
from app.models.user import User

router = APIRouter(prefix="/api/audit", tags=["Audit"])


@router.get("/")
async def get_audit_trail(
    client_id: UUID = Query(..., description="Client ID to filter audit entries"),
    start_date: Optional[date] = Query(None, description="Start date (timestamp >= start_date)"),
    end_date: Optional[date] = Query(None, description="End date (timestamp <= end_date)"),
    action: Optional[str] = Query(None, description="Filter by action (create/update/delete)"),
    table_name: Optional[str] = Query(None, description="Filter by table name"),
    changed_by_type: Optional[str] = Query(None, description="Filter by changed_by_type (user/ai_agent/system)"),
    search: Optional[str] = Query(None, description="Search in table_name, action, or changed_by_name"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(50, ge=1, le=500, description="Number of entries per page"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get audit trail entries with filtering, sorting, and pagination.
    
    This endpoint provides a complete history of all changes made to the system
    for trust and transparency.
    
    Returns:
    - entries: List of audit trail entries
    - pagination: Page metadata
    - summary: Aggregated statistics
    """
    
    # Build base query
    query = select(AuditTrail)
    
    # Apply filters
    filters = [AuditTrail.client_id == client_id]
    
    if start_date:
        # Convert date to datetime at start of day
        start_datetime = datetime.combine(start_date, datetime.min.time())
        filters.append(AuditTrail.timestamp >= start_datetime)
    
    if end_date:
        # Convert date to datetime at end of day
        end_datetime = datetime.combine(end_date, datetime.max.time())
        filters.append(AuditTrail.timestamp <= end_datetime)
    
    if action:
        filters.append(AuditTrail.action == action)
    
    if table_name:
        filters.append(AuditTrail.table_name == table_name)
    
    if changed_by_type:
        filters.append(AuditTrail.changed_by_type == changed_by_type)
    
    # Search filter
    if search:
        search_pattern = f"%{search}%"
        search_filters = or_(
            AuditTrail.table_name.ilike(search_pattern),
            AuditTrail.action.ilike(search_pattern),
            AuditTrail.changed_by_name.ilike(search_pattern),
            AuditTrail.reason.ilike(search_pattern)
        )
        filters.append(search_filters)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Apply sorting (always by timestamp)
    if sort_order.lower() == "desc":
        query = query.order_by(AuditTrail.timestamp.desc())
    else:
        query = query.order_by(AuditTrail.timestamp.asc())
    
    # Get total count (before pagination)
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total_count = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.limit(page_size).offset(offset)
    
    # Execute query
    result = await db.execute(query)
    entries = result.scalars().all()
    
    # Build response data
    response_entries = []
    
    for entry in entries:
        entry_dict = {
            "id": str(entry.id),
            "client_id": str(entry.client_id) if entry.client_id else None,
            "table_name": entry.table_name,
            "record_id": str(entry.record_id),
            "action": entry.action,
            "changed_by_type": entry.changed_by_type,
            "changed_by_id": str(entry.changed_by_id) if entry.changed_by_id else None,
            "changed_by_name": entry.changed_by_name,
            "reason": entry.reason,
            "timestamp": entry.timestamp.isoformat(),
            "ip_address": entry.ip_address,
            "user_agent": entry.user_agent,
            # Include old/new values for transparency
            "old_value": entry.old_value,
            "new_value": entry.new_value,
        }
        
        response_entries.append(entry_dict)
    
    # Calculate pagination metadata
    total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
    has_next = page < total_pages
    has_prev = page > 1
    
    pagination = {
        "page": page,
        "page_size": page_size,
        "total_entries": total_count,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_prev": has_prev,
    }
    
    # Calculate summary statistics
    summary_query = select(
        func.count(AuditTrail.id).label("total_events"),
        func.count(func.distinct(AuditTrail.table_name)).label("tables_affected"),
        func.count(func.distinct(AuditTrail.changed_by_id)).label("unique_users"),
    ).where(AuditTrail.client_id == client_id)
    
    # Apply same date filters to summary
    summary_filters = []
    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        summary_filters.append(AuditTrail.timestamp >= start_datetime)
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        summary_filters.append(AuditTrail.timestamp <= end_datetime)
    
    if summary_filters:
        summary_query = summary_query.where(and_(*summary_filters))
    
    summary_result = await db.execute(summary_query)
    summary_row = summary_result.one()
    
    # Get action breakdown
    action_query = select(
        AuditTrail.action,
        func.count(AuditTrail.id).label("count")
    ).where(AuditTrail.client_id == client_id)
    
    if summary_filters:
        action_query = action_query.where(and_(*summary_filters))
    
    action_query = action_query.group_by(AuditTrail.action)
    action_result = await db.execute(action_query)
    action_breakdown = {row.action: row.count for row in action_result}
    
    summary = {
        "total_events": summary_row.total_events or 0,
        "tables_affected": summary_row.tables_affected or 0,
        "unique_users": summary_row.unique_users or 0,
        "action_breakdown": action_breakdown,
        "date_range": {
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None,
        },
        "filters_applied": {
            "action": action,
            "table_name": table_name,
            "changed_by_type": changed_by_type,
            "search": search,
        }
    }
    
    return {
        "entries": response_entries,
        "pagination": pagination,
        "summary": summary,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/{audit_id}")
async def get_audit_entry(
    audit_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a single audit trail entry by ID with full details.
    """
    query = select(AuditTrail).where(AuditTrail.id == audit_id)
    
    result = await db.execute(query)
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Audit trail entry not found")
    
    # Build detailed response
    entry_dict = {
        "id": str(entry.id),
        "client_id": str(entry.client_id) if entry.client_id else None,
        "table_name": entry.table_name,
        "record_id": str(entry.record_id),
        "action": entry.action,
        "changed_by_type": entry.changed_by_type,
        "changed_by_id": str(entry.changed_by_id) if entry.changed_by_id else None,
        "changed_by_name": entry.changed_by_name,
        "reason": entry.reason,
        "timestamp": entry.timestamp.isoformat(),
        "ip_address": entry.ip_address,
        "user_agent": entry.user_agent,
        "old_value": entry.old_value,
        "new_value": entry.new_value,
    }
    
    return entry_dict


@router.get("/tables/list")
async def get_audit_tables(
    client_id: UUID = Query(..., description="Client ID"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get list of all tables that have audit entries.
    Useful for populating filter dropdowns.
    """
    query = select(
        AuditTrail.table_name,
        func.count(AuditTrail.id).label("event_count")
    ).where(
        AuditTrail.client_id == client_id
    ).group_by(
        AuditTrail.table_name
    ).order_by(
        func.count(AuditTrail.id).desc()
    )
    
    result = await db.execute(query)
    tables = [
        {
            "table_name": row.table_name,
            "event_count": row.event_count
        }
        for row in result
    ]
    
    return {
        "tables": tables,
        "total_tables": len(tables)
    }
