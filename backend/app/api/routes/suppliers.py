"""
Supplier Contact Register API - /api/contacts/suppliers

CRUD operations for supplier master data (leverandørkort).
Rules:
- No deletion allowed (only deactivation)
- Duplicate org_number check
- All changes logged in audit trail
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Query, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, func, select
from typing import List, Optional
from uuid import UUID
import json

from app.database import get_db
from app.models.supplier import Supplier, SupplierAuditLog
from app.models.supplier_ledger import SupplierLedger
from pydantic import BaseModel, Field


router = APIRouter()


# === PYDANTIC SCHEMAS ===

class SupplierAddressSchema(BaseModel):
    line1: Optional[str] = None
    line2: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: str = "Norge"


class SupplierContactSchema(BaseModel):
    person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None


class SupplierFinancialSchema(BaseModel):
    bank_account: Optional[str] = None
    iban: Optional[str] = None
    swift_bic: Optional[str] = None
    payment_terms_days: int = 30
    currency: str = "NOK"
    vat_code: Optional[str] = None
    default_expense_account: Optional[str] = None


class SupplierCreateSchema(BaseModel):
    # client_id is now passed as query parameter, not in body
    company_name: str = Field(..., min_length=1, max_length=255)
    org_number: Optional[str] = Field(None, max_length=20)
    address: Optional[SupplierAddressSchema] = None
    contact: Optional[SupplierContactSchema] = None
    financial: Optional[SupplierFinancialSchema] = None
    notes: Optional[str] = None


class SupplierUpdateSchema(BaseModel):
    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    org_number: Optional[str] = Field(None, max_length=20)
    address: Optional[SupplierAddressSchema] = None
    contact: Optional[SupplierContactSchema] = None
    financial: Optional[SupplierFinancialSchema] = None
    notes: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|inactive)$")


class SupplierResponseSchema(BaseModel):
    id: UUID
    client_id: UUID
    supplier_number: str
    company_name: str
    org_number: Optional[str]
    address: dict
    contact: dict
    financial: dict
    status: str
    notes: Optional[str]
    created_at: str
    updated_at: str
    created_by: Optional[UUID]
    updated_by: Optional[UUID]
    # Extended data
    balance: Optional[float] = None
    recent_transactions: Optional[list] = None
    open_invoices: Optional[list] = None


# === HELPER FUNCTIONS ===

async def generate_supplier_number(db: AsyncSession, client_id: UUID) -> str:
    """Generate next sequential supplier number for client"""
    result = await db.execute(
        select(Supplier)
        .where(Supplier.client_id == client_id)
        .order_by(Supplier.supplier_number.desc())
        .limit(1)
    )
    last_supplier = result.scalar_one_or_none()
    
    if last_supplier and last_supplier.supplier_number.isdigit():
        next_number = int(last_supplier.supplier_number) + 1
    else:
        next_number = 1
    
    return str(next_number).zfill(5)  # Zero-padded to 5 digits


async def check_duplicate_org_number(db: AsyncSession, client_id: UUID, org_number: str, exclude_id: Optional[UUID] = None) -> bool:
    """Check if org_number already exists for this client"""
    if not org_number:
        return False
    
    stmt = select(Supplier).where(
        and_(
            Supplier.client_id == client_id,
            Supplier.org_number == org_number
        )
    )
    
    if exclude_id:
        stmt = stmt.where(Supplier.id != exclude_id)
    
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


def log_audit(
    db: AsyncSession,
    supplier_id: UUID,
    action: str,
    changed_fields: Optional[dict] = None,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None,
    user_id: Optional[UUID] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """Create audit log entry"""
    log_entry = SupplierAuditLog(
        supplier_id=supplier_id,
        action=action,
        changed_fields=json.dumps(changed_fields) if changed_fields else None,
        old_values=json.dumps(old_values) if old_values else None,
        new_values=json.dumps(new_values) if new_values else None,
        performed_by=user_id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(log_entry)


async def get_supplier_balance(db: AsyncSession, supplier_id: UUID) -> float:
    """Get current balance from supplier ledger"""
    stmt = select(func.sum(SupplierLedger.remaining_amount)).where(
        and_(
            SupplierLedger.supplier_id == supplier_id,
            SupplierLedger.status != 'paid'
        )
    )
    result = await db.execute(stmt)
    balance = result.scalar()
    
    return float(balance) if balance else 0.0


async def get_recent_transactions(db: AsyncSession, supplier_id: UUID, limit: int = 10) -> list:
    """Get recent ledger entries for supplier"""
    stmt = (
        select(SupplierLedger)
        .where(SupplierLedger.supplier_id == supplier_id)
        .order_by(SupplierLedger.invoice_date.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    entries = result.scalars().all()
    
    return [entry.to_dict() for entry in entries]


async def get_open_invoices(db: AsyncSession, supplier_id: UUID) -> list:
    """Get open invoices for supplier"""
    stmt = (
        select(SupplierLedger)
        .where(
            and_(
                SupplierLedger.supplier_id == supplier_id,
                SupplierLedger.status.in_(['open', 'partially_paid'])
            )
        )
        .order_by(SupplierLedger.due_date.asc())
    )
    result = await db.execute(stmt)
    entries = result.scalars().all()
    
    return [entry.to_dict() for entry in entries]


# === API ENDPOINTS ===

@router.post("/", response_model=SupplierResponseSchema, status_code=201)
async def create_supplier(
    data: SupplierCreateSchema,
    client_id: UUID = Query(..., description="Client UUID"),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Create new supplier.
    
    - Validates org_number uniqueness
    - Generates sequential supplier_number
    - Logs creation in audit trail
    """
    # Check for duplicate org_number
    if data.org_number and await check_duplicate_org_number(db, client_id, data.org_number):
        raise HTTPException(
            status_code=400,
            detail=f"Supplier with org_number {data.org_number} already exists for this client"
        )
    
    # Generate supplier number
    supplier_number = await generate_supplier_number(db, client_id)
    
    # Create supplier
    supplier = Supplier(
        client_id=client_id,
        supplier_number=supplier_number,
        company_name=data.company_name,
        org_number=data.org_number,
        notes=data.notes,
        status="active"
    )
    
    # Address
    if data.address:
        supplier.address_line1 = data.address.line1
        supplier.address_line2 = data.address.line2
        supplier.postal_code = data.address.postal_code
        supplier.city = data.address.city
        supplier.country = data.address.country
    
    # Contact
    if data.contact:
        supplier.contact_person = data.contact.person
        supplier.phone = data.contact.phone
        supplier.email = data.contact.email
        supplier.website = data.contact.website
    
    # Financial
    if data.financial:
        supplier.bank_account = data.financial.bank_account
        supplier.iban = data.financial.iban
        supplier.swift_bic = data.financial.swift_bic
        supplier.payment_terms_days = data.financial.payment_terms_days
        supplier.currency = data.financial.currency
        supplier.vat_code = data.financial.vat_code
        supplier.default_expense_account = data.financial.default_expense_account
    
    db.add(supplier)
    await db.flush()
    
    # Audit log
    log_audit(
        db,
        supplier.id,
        action="create",
        new_values=supplier.to_dict(),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    await db.commit()
    await db.refresh(supplier)
    
    return supplier.to_dict()


@router.get("/")
async def list_suppliers(
    client_id: UUID,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    List suppliers for a client with pagination.
    
    Query params:
    - client_id: Client ID (required)
    - status: Filter by status (active/inactive) (optional)
    - search: Search by name or org_number (optional)
    - limit: Items per page (default: 50, max: 500)
    - offset: Starting index (default: 0)
    
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
    
    stmt = select(Supplier).where(Supplier.client_id == client_id)
    
    # Filter by status
    if status:
        stmt = stmt.where(Supplier.status == status)
    
    # Search
    if search:
        search_pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Supplier.company_name.ilike(search_pattern),
                Supplier.org_number.ilike(search_pattern),
                Supplier.supplier_number.ilike(search_pattern)
            )
        )
    
    # Get total count
    count_stmt = select(func.count()).select_from(Supplier).where(Supplier.client_id == client_id)
    if status:
        count_stmt = count_stmt.where(Supplier.status == status)
    if search:
        search_pattern = f"%{search}%"
        count_stmt = count_stmt.where(
            or_(
                Supplier.company_name.ilike(search_pattern),
                Supplier.org_number.ilike(search_pattern),
                Supplier.supplier_number.ilike(search_pattern)
            )
        )
    
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    
    # Pagination
    stmt = stmt.order_by(Supplier.company_name).limit(limit).offset(offset)
    result = await db.execute(stmt)
    suppliers = result.scalars().all()
    
    page_number = (offset // limit) + 1 if limit > 0 else 1
    
    return {
        "items": [supplier.to_dict() for supplier in suppliers],
        "total": total,
        "limit": limit,
        "offset": offset,
        "page_number": page_number
    }


@router.get("/{supplier_id}", response_model=SupplierResponseSchema)
async def get_supplier(
    supplier_id: UUID,
    include_balance: bool = True,
    include_transactions: bool = False,
    include_invoices: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Get supplier details.
    
    - Optionally include balance, recent transactions, and open invoices
    """
    stmt = select(Supplier).where(Supplier.id == supplier_id)
    result_exec = await db.execute(stmt)
    supplier = result_exec.scalar_one_or_none()
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    result = supplier.to_dict()
    
    # Add balance
    if include_balance:
        result["balance"] = await get_supplier_balance(db, supplier_id)
    
    # Add recent transactions
    if include_transactions:
        result["recent_transactions"] = await get_recent_transactions(db, supplier_id)
    
    # Add open invoices
    if include_invoices:
        result["open_invoices"] = await get_open_invoices(db, supplier_id)
    
    return result


@router.put("/{supplier_id}", response_model=SupplierResponseSchema)
async def update_supplier(
    supplier_id: UUID,
    data: SupplierUpdateSchema,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Update supplier details.
    
    - Validates org_number uniqueness if changed
    - Logs all changes in audit trail
    - Cannot change to 'deleted' status (only active/inactive)
    """
    stmt = select(Supplier).where(Supplier.id == supplier_id)
    result = await db.execute(stmt)
    supplier = result.scalar_one_or_none()
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Store old values for audit
    old_values = supplier.to_dict()
    changed_fields = []
    
    # Check org_number uniqueness if changing
    if data.org_number and data.org_number != supplier.org_number:
        if await check_duplicate_org_number(db, supplier.client_id, data.org_number, exclude_id=supplier_id):
            raise HTTPException(
                status_code=400,
                detail=f"Supplier with org_number {data.org_number} already exists for this client"
            )
    
    # Update fields
    if data.company_name is not None and data.company_name != supplier.company_name:
        supplier.company_name = data.company_name
        changed_fields.append("company_name")
    
    if data.org_number is not None and data.org_number != supplier.org_number:
        supplier.org_number = data.org_number
        changed_fields.append("org_number")
    
    if data.address:
        if data.address.line1 is not None:
            supplier.address_line1 = data.address.line1
            changed_fields.append("address_line1")
        if data.address.line2 is not None:
            supplier.address_line2 = data.address.line2
            changed_fields.append("address_line2")
        if data.address.postal_code is not None:
            supplier.postal_code = data.address.postal_code
            changed_fields.append("postal_code")
        if data.address.city is not None:
            supplier.city = data.address.city
            changed_fields.append("city")
        if data.address.country is not None:
            supplier.country = data.address.country
            changed_fields.append("country")
    
    if data.contact:
        if data.contact.person is not None:
            supplier.contact_person = data.contact.person
            changed_fields.append("contact_person")
        if data.contact.phone is not None:
            supplier.phone = data.contact.phone
            changed_fields.append("phone")
        if data.contact.email is not None:
            supplier.email = data.contact.email
            changed_fields.append("email")
        if data.contact.website is not None:
            supplier.website = data.contact.website
            changed_fields.append("website")
    
    if data.financial:
        if data.financial.bank_account is not None:
            supplier.bank_account = data.financial.bank_account
            changed_fields.append("bank_account")
        if data.financial.iban is not None:
            supplier.iban = data.financial.iban
            changed_fields.append("iban")
        if data.financial.swift_bic is not None:
            supplier.swift_bic = data.financial.swift_bic
            changed_fields.append("swift_bic")
        if data.financial.payment_terms_days is not None:
            supplier.payment_terms_days = data.financial.payment_terms_days
            changed_fields.append("payment_terms_days")
        if data.financial.currency is not None:
            supplier.currency = data.financial.currency
            changed_fields.append("currency")
        if data.financial.vat_code is not None:
            supplier.vat_code = data.financial.vat_code
            changed_fields.append("vat_code")
        if data.financial.default_expense_account is not None:
            supplier.default_expense_account = data.financial.default_expense_account
            changed_fields.append("default_expense_account")
    
    if data.notes is not None and data.notes != supplier.notes:
        supplier.notes = data.notes
        changed_fields.append("notes")
    
    if data.status is not None and data.status != supplier.status:
        supplier.status = data.status
        changed_fields.append("status")
        action = "deactivate" if data.status == "inactive" else "reactivate"
    else:
        action = "update"
    
    if changed_fields:
        await db.flush()
        
        # Audit log
        log_audit(
            db,
            supplier.id,
            action=action,
            changed_fields={"fields": changed_fields},
            old_values=old_values,
            new_values=supplier.to_dict(),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
    
    await db.commit()
    await db.refresh(supplier)
    
    return supplier.to_dict()


@router.delete("/{supplier_id}")
async def deactivate_supplier(
    supplier_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivate supplier (deletion not allowed).
    
    - Sets status to 'inactive'
    - Logs deactivation in audit trail
    """
    stmt = select(Supplier).where(Supplier.id == supplier_id)
    result = await db.execute(stmt)
    supplier = result.scalar_one_or_none()
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    if supplier.status == "inactive":
        return {"message": "Supplier already inactive"}
    
    old_values = supplier.to_dict()
    supplier.status = "inactive"
    
    await db.flush()
    
    # Audit log
    log_audit(
        db,
        supplier.id,
        action="deactivate",
        changed_fields={"fields": ["status"]},
        old_values=old_values,
        new_values=supplier.to_dict(),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    await db.commit()
    
    return {"message": "Supplier deactivated successfully"}


@router.get("/{supplier_id}/audit-log")
async def get_supplier_audit_log(
    supplier_id: UUID,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get audit log for supplier"""
    stmt = select(Supplier).where(Supplier.id == supplier_id)
    result = await db.execute(stmt)
    supplier = result.scalar_one_or_none()
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    stmt_logs = (
        select(SupplierAuditLog)
        .where(SupplierAuditLog.supplier_id == supplier_id)
        .order_by(SupplierAuditLog.performed_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result_logs = await db.execute(stmt_logs)
    logs = result_logs.scalars().all()
    
    return [log.to_dict() for log in logs]


# === BULK IMPORT ===

@router.post("/bulk", response_model=dict)
async def bulk_import_suppliers(
    request: Request,
    file: bytes = File(...),
    filename: str = Query(...),
    client_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk import suppliers from CSV or Excel file
    
    Expected CSV columns:
    - navn (required)
    - org_nummer (required)
    - epost
    - telefon
    - adresse
    - postnummer
    - poststed
    - land
    - kontonummer
    - betalingsbetingelser (e.g., "30 dager")
    - leverandor_type (goods/services)
    """
    from app.services.contact_import import parse_file, import_suppliers
    
    # client_id now comes from query parameter
    
    try:
        # Parse file
        df = parse_file(file, filename)
        
        # Import suppliers
        result = await import_suppliers(db, df, client_id)
        
        return result.to_dict()
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
