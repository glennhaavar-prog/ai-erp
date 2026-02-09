"""
Tenants API - Get tenant information
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any

from app.database import get_db
from app.models.tenant import Tenant

router = APIRouter(prefix="/api/tenants", tags=["Tenants"])


@router.get("/demo")
async def get_demo_tenant(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get the demo tenant information
    
    Returns the first demo tenant (there should only be one in demo environment)
    """
    query = select(Tenant).where(Tenant.is_demo == True).limit(1)
    result = await db.execute(query)
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Demo tenant not found")
    
    return {
        "id": str(tenant.id),
        "name": tenant.name,
        "is_demo": tenant.is_demo,
    }
