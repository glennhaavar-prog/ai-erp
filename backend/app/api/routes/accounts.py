"""
Accounts API - Chart of Accounts management
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.chart_of_accounts import Account

router = APIRouter(prefix="/api/accounts", tags=["Accounts"])


# Pydantic models for request/response
class AccountCreate(BaseModel):
    account_number: str = Field(..., min_length=4, max_length=10, description="Account number (e.g., 1920, 4000)")
    account_name: str = Field(..., min_length=1, max_length=255, description="Account name")
    account_type: str = Field(..., description="Account type: asset/liability/equity/revenue/expense")
    parent_account_number: Optional[str] = Field(None, description="Parent account for sub-accounts")
    default_vat_code: Optional[str] = Field(None, description="Default VAT code for this account")
    vat_deductible: bool = Field(True, description="Whether VAT is deductible")
    requires_reconciliation: bool = Field(False, description="Whether account requires reconciliation")


class AccountUpdate(BaseModel):
    account_name: Optional[str] = Field(None, min_length=1, max_length=255)
    account_type: Optional[str] = None
    default_vat_code: Optional[str] = None
    vat_deductible: Optional[bool] = None
    requires_reconciliation: Optional[bool] = None
    is_active: Optional[bool] = None


class AccountResponse(BaseModel):
    id: str
    client_id: str
    account_number: str
    account_name: str
    account_type: str
    parent_account_number: Optional[str]
    account_level: int
    default_vat_code: Optional[str]
    vat_deductible: bool
    requires_reconciliation: bool
    ai_usage_count: int
    is_active: bool
    created_at: str
    updated_at: str


@router.get("/")
async def list_accounts(
    client_id: UUID = Query(..., description="Client ID to filter accounts"),
    account_type: Optional[str] = Query(None, description="Filter by account type"),
    search: Optional[str] = Query(None, description="Search by account number or name"),
    active_only: bool = Query(True, description="Show only active accounts"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    List all accounts for a client
    
    Returns chart of accounts with filtering and search
    """
    # Build query
    query = select(Account).where(Account.client_id == client_id)
    
    # Apply filters
    if account_type:
        query = query.where(Account.account_type == account_type)
    
    if active_only:
        query = query.where(Account.is_active == True)
    
    if search:
        query = query.where(
            or_(
                Account.account_number.ilike(f"%{search}%"),
                Account.account_name.ilike(f"%{search}%")
            )
        )
    
    # Sort by account number
    query = query.order_by(Account.account_number.asc())
    
    # Execute
    result = await db.execute(query)
    accounts = result.scalars().all()
    
    # Convert to dict
    accounts_list = []
    for account in accounts:
        accounts_list.append({
            "id": str(account.id),
            "client_id": str(account.client_id),
            "account_number": account.account_number,
            "account_name": account.account_name,
            "account_type": account.account_type,
            "parent_account_number": account.parent_account_number,
            "account_level": account.account_level,
            "default_vat_code": account.default_vat_code,
            "vat_deductible": account.vat_deductible,
            "requires_reconciliation": account.requires_reconciliation,
            "ai_usage_count": account.ai_usage_count,
            "is_active": account.is_active,
            "created_at": account.created_at.isoformat(),
            "updated_at": account.updated_at.isoformat()
        })
    
    return {
        "accounts": accounts_list,
        "total_count": len(accounts_list)
    }


@router.get("/by-number/{account_number}")
async def get_account_by_number(
    account_number: str,
    client_id: UUID = Query(..., description="Client ID"),
    db: AsyncSession = Depends(get_db)
) -> AccountResponse:
    """
    Get a single account by account number
    """
    query = select(Account).where(
        and_(
            Account.client_id == client_id,
            Account.account_number == account_number
        )
    )
    result = await db.execute(query)
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_number} not found for this client")
    
    return AccountResponse(
        id=str(account.id),
        client_id=str(account.client_id),
        account_number=account.account_number,
        account_name=account.account_name,
        account_type=account.account_type,
        parent_account_number=account.parent_account_number,
        account_level=account.account_level,
        default_vat_code=account.default_vat_code,
        vat_deductible=account.vat_deductible,
        requires_reconciliation=account.requires_reconciliation,
        ai_usage_count=account.ai_usage_count,
        is_active=account.is_active,
        created_at=account.created_at.isoformat(),
        updated_at=account.updated_at.isoformat()
    )


@router.get("/{account_id}")
async def get_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> AccountResponse:
    """
    Get a single account by UUID
    """
    query = select(Account).where(Account.id == account_id)
    result = await db.execute(query)
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return AccountResponse(
        id=str(account.id),
        client_id=str(account.client_id),
        account_number=account.account_number,
        account_name=account.account_name,
        account_type=account.account_type,
        parent_account_number=account.parent_account_number,
        account_level=account.account_level,
        default_vat_code=account.default_vat_code,
        vat_deductible=account.vat_deductible,
        requires_reconciliation=account.requires_reconciliation,
        ai_usage_count=account.ai_usage_count,
        is_active=account.is_active,
        created_at=account.created_at.isoformat(),
        updated_at=account.updated_at.isoformat()
    )


@router.post("/")
async def create_account(
    client_id: UUID = Query(..., description="Client ID"),
    account_data: AccountCreate = None,
    db: AsyncSession = Depends(get_db)
) -> AccountResponse:
    """
    Create a new account
    
    Validates that account number doesn't already exist for this client
    """
    # Check if account number already exists
    check_query = select(Account).where(
        and_(
            Account.client_id == client_id,
            Account.account_number == account_data.account_number
        )
    )
    result = await db.execute(check_query)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Account number {account_data.account_number} already exists for this client"
        )
    
    # Validate account number format (Norwegian standard: 4 digits minimum)
    if not account_data.account_number.isdigit():
        raise HTTPException(
            status_code=400,
            detail="Account number must contain only digits"
        )
    
    if len(account_data.account_number) < 4:
        raise HTTPException(
            status_code=400,
            detail="Account number must be at least 4 digits (Norwegian standard NS 4102)"
        )
    
    # Determine account level
    account_level = 1
    if account_data.parent_account_number:
        parent_query = select(Account).where(
            and_(
                Account.client_id == client_id,
                Account.account_number == account_data.parent_account_number
            )
        )
        parent_result = await db.execute(parent_query)
        parent = parent_result.scalar_one_or_none()
        if parent:
            account_level = parent.account_level + 1
    
    # Create new account
    new_account = Account(
        client_id=client_id,
        account_number=account_data.account_number,
        account_name=account_data.account_name,
        account_type=account_data.account_type,
        parent_account_number=account_data.parent_account_number,
        account_level=account_level,
        default_vat_code=account_data.default_vat_code,
        vat_deductible=account_data.vat_deductible,
        requires_reconciliation=account_data.requires_reconciliation,
        is_active=True,
        ai_usage_count=0
    )
    
    db.add(new_account)
    await db.commit()
    await db.refresh(new_account)
    
    return AccountResponse(
        id=str(new_account.id),
        client_id=str(new_account.client_id),
        account_number=new_account.account_number,
        account_name=new_account.account_name,
        account_type=new_account.account_type,
        parent_account_number=new_account.parent_account_number,
        account_level=new_account.account_level,
        default_vat_code=new_account.default_vat_code,
        vat_deductible=new_account.vat_deductible,
        requires_reconciliation=new_account.requires_reconciliation,
        ai_usage_count=new_account.ai_usage_count,
        is_active=new_account.is_active,
        created_at=new_account.created_at.isoformat(),
        updated_at=new_account.updated_at.isoformat()
    )


@router.put("/{account_id}")
async def update_account(
    account_id: UUID,
    account_data: AccountUpdate,
    db: AsyncSession = Depends(get_db)
) -> AccountResponse:
    """
    Update an existing account
    """
    # Get account
    query = select(Account).where(Account.id == account_id)
    result = await db.execute(query)
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Update fields
    if account_data.account_name is not None:
        account.account_name = account_data.account_name
    if account_data.account_type is not None:
        account.account_type = account_data.account_type
    if account_data.default_vat_code is not None:
        account.default_vat_code = account_data.default_vat_code
    if account_data.vat_deductible is not None:
        account.vat_deductible = account_data.vat_deductible
    if account_data.requires_reconciliation is not None:
        account.requires_reconciliation = account_data.requires_reconciliation
    if account_data.is_active is not None:
        account.is_active = account_data.is_active
    
    account.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(account)
    
    return AccountResponse(
        id=str(account.id),
        client_id=str(account.client_id),
        account_number=account.account_number,
        account_name=account.account_name,
        account_type=account.account_type,
        parent_account_number=account.parent_account_number,
        account_level=account.account_level,
        default_vat_code=account.default_vat_code,
        vat_deductible=account.vat_deductible,
        requires_reconciliation=account.requires_reconciliation,
        ai_usage_count=account.ai_usage_count,
        is_active=account.is_active,
        created_at=account.created_at.isoformat(),
        updated_at=account.updated_at.isoformat()
    )


@router.delete("/{account_id}")
async def delete_account(
    account_id: UUID,
    soft_delete: bool = Query(True, description="Soft delete (deactivate) vs hard delete"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Delete an account (soft delete by default)
    """
    # Get account
    query = select(Account).where(Account.id == account_id)
    result = await db.execute(query)
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if soft_delete:
        # Soft delete: just mark as inactive
        account.is_active = False
        account.updated_at = datetime.utcnow()
        await db.commit()
        return {"message": f"Account {account.account_number} deactivated"}
    else:
        # Hard delete
        await db.delete(account)
        await db.commit()
        return {"message": f"Account {account.account_number} deleted"}
