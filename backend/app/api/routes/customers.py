"""
Customer Contact Register API - /api/contacts/customers

CRUD operations for customer master data (kundekort).
Rules:
- No deletion allowed (only deactivation)
- Duplicate org_number/birth_number check
- All changes logged in audit trail
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Query, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import List, Optional
from uuid import UUID
import json

from app.database import get_db
from app.models.customer import Customer, CustomerAuditLog
from app.models.customer_ledger import CustomerLedger
from pydantic import BaseModel, Field


router = APIRouter()


# === PYDANTIC SCHEMAS ===

class CustomerAddressSchema(BaseModel):
    line1: Optional[str] = None
    line2: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: str = "Norge"


class CustomerContactSchema(BaseModel):
    person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class CustomerFinancialSchema(BaseModel):
    payment_terms_days: int = 14
    currency: str = "NOK"
    vat_code: Optional[str] = None
    default_revenue_account: Optional[str] = None
    kid_prefix: Optional[str] = None
    use_kid: bool = False
    credit_limit: Optional[int] = None
    reminder_fee: int = 0


class CustomerCreateSchema(BaseModel):
    # client_id is now passed as query parameter, not in body
    is_company: bool = True
    name: str = Field(..., min_length=1, max_length=255)
    org_number: Optional[str] = Field(None, max_length=20)
    birth_number: Optional[str] = Field(None, max_length=20)
    address: Optional[CustomerAddressSchema] = None
    contact: Optional[CustomerContactSchema] = None
    financial: Optional[CustomerFinancialSchema] = None
    notes: Optional[str] = None


class CustomerUpdateSchema(BaseModel):
    is_company: Optional[bool] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    org_number: Optional[str] = Field(None, max_length=20)
    birth_number: Optional[str] = Field(None, max_length=20)
    address: Optional[CustomerAddressSchema] = None
    contact: Optional[CustomerContactSchema] = None
    financial: Optional[CustomerFinancialSchema] = None
    notes: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|inactive)$")


class CustomerResponseSchema(BaseModel):
    id: UUID
    client_id: UUID
    customer_number: str
    is_company: bool
    name: str
    org_number: Optional[str]
    birth_number: Optional[str]
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

async def generate_customer_number(db: AsyncSession, client_id: UUID) -> str:
    """Generate next sequential customer number for client"""
    query = select(Customer).where(
        Customer.client_id == client_id
    ).order_by(Customer.customer_number.desc()).limit(1)
    
    result = await db.execute(query)
    last_customer = result.scalars().first()
    
    if last_customer and last_customer.customer_number.isdigit():
        next_number = int(last_customer.customer_number) + 1
    else:
        next_number = 1
    
    return str(next_number).zfill(5)  # Zero-padded to 5 digits


async def check_duplicate_identifier(db: AsyncSession, client_id: UUID, org_number: Optional[str], birth_number: Optional[str], exclude_id: Optional[UUID] = None) -> Optional[str]:
    """Check if org_number or birth_number already exists for this client"""
    if org_number:
        query = select(Customer).where(
            and_(
                Customer.client_id == client_id,
                Customer.org_number == org_number
            )
        )
        if exclude_id:
            query = query.where(Customer.id != exclude_id)
        
        result = await db.execute(query)
        if result.scalars().first():
            return f"org_number {org_number}"
    
    if birth_number:
        query = select(Customer).where(
            and_(
                Customer.client_id == client_id,
                Customer.birth_number == birth_number
            )
        )
        if exclude_id:
            query = query.where(Customer.id != exclude_id)
        
        result = await db.execute(query)
        if result.scalars().first():
            return f"birth_number {birth_number}"
    
    return None


def log_audit(
    db: AsyncSession,
    customer_id: UUID,
    action: str,
    changed_fields: Optional[dict] = None,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None,
    user_id: Optional[UUID] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """Create audit log entry"""
    log_entry = CustomerAuditLog(
        customer_id=customer_id,
        action=action,
        changed_fields=json.dumps(changed_fields) if changed_fields else None,
        old_values=json.dumps(old_values) if old_values else None,
        new_values=json.dumps(new_values) if new_values else None,
        performed_by=user_id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(log_entry)


async def get_customer_balance(db: AsyncSession, customer_id: UUID) -> float:
    """Get current balance from customer ledger"""
    query = select(func.sum(CustomerLedger.remaining_amount)).where(
        and_(
            CustomerLedger.customer_id == customer_id,
            CustomerLedger.status != 'paid'
        )
    )
    
    result = await db.execute(query)
    balance = result.scalar_one_or_none()
    
    return float(balance) if balance else 0.0


async def get_recent_transactions(db: AsyncSession, customer_id: UUID, limit: int = 10) -> list:
    """Get recent ledger entries for customer"""
    query = select(CustomerLedger).where(
        CustomerLedger.customer_id == customer_id
    ).order_by(CustomerLedger.invoice_date.desc()).limit(limit)
    
    result = await db.execute(query)
    entries = result.scalars().all()
    
    return [entry.to_dict() for entry in entries]


async def get_open_invoices(db: AsyncSession, customer_id: UUID) -> list:
    """Get open invoices for customer"""
    query = select(CustomerLedger).where(
        and_(
            CustomerLedger.customer_id == customer_id,
            CustomerLedger.status.in_(['open', 'partially_paid', 'overdue'])
        )
    ).order_by(CustomerLedger.due_date.asc())
    
    result = await db.execute(query)
    entries = result.scalars().all()
    
    return [entry.to_dict() for entry in entries]


# === API ENDPOINTS ===

@router.post("/", response_model=CustomerResponseSchema, status_code=201)
async def create_customer(
    data: CustomerCreateSchema,
    client_id: UUID = Query(..., description="Client UUID"),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Create new customer.
    
    - Validates org_number/birth_number uniqueness
    - Generates sequential customer_number
    - Logs creation in audit trail
    """
    # Check for duplicate identifier
    duplicate = await check_duplicate_identifier(db, client_id, data.org_number, data.birth_number)
    if duplicate:
        raise HTTPException(
            status_code=400,
            detail=f"Customer with {duplicate} already exists for this client"
        )
    
    # Generate customer number
    customer_number = await generate_customer_number(db, client_id)
    
    # Create customer
    customer = Customer(
        client_id=client_id,
        customer_number=customer_number,
        is_company=data.is_company,
        name=data.name,
        org_number=data.org_number,
        birth_number=data.birth_number,
        notes=data.notes,
        status="active"
    )
    
    # Address
    if data.address:
        customer.address_line1 = data.address.line1
        customer.address_line2 = data.address.line2
        customer.postal_code = data.address.postal_code
        customer.city = data.address.city
        customer.country = data.address.country
    
    # Contact
    if data.contact:
        customer.contact_person = data.contact.person
        customer.phone = data.contact.phone
        customer.email = data.contact.email
    
    # Financial
    if data.financial:
        customer.payment_terms_days = data.financial.payment_terms_days
        customer.currency = data.financial.currency
        customer.vat_code = data.financial.vat_code
        customer.default_revenue_account = data.financial.default_revenue_account
        customer.kid_prefix = data.financial.kid_prefix
        customer.use_kid = data.financial.use_kid
        customer.credit_limit = data.financial.credit_limit
        customer.reminder_fee = data.financial.reminder_fee
    
    db.add(customer)
    await db.flush()
    
    # Audit log
    log_audit(
        db,
        customer.id,
        action="create",
        new_values=customer.to_dict(),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    await db.commit()
    await db.refresh(customer)
    
    return customer.to_dict()


@router.get("/", response_model=List[CustomerResponseSchema])
async def list_customers(
    client_id: UUID,
    status: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    List customers for a client.
    
    - Filter by status (active/inactive)
    - Search by name, org_number, or birth_number
    - Pagination support
    """
    query = select(Customer).where(Customer.client_id == client_id)
    
    # Filter by status
    if status:
        query = query.where(Customer.status == status)
    
    # Search
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Customer.name.ilike(search_pattern),
                Customer.org_number.ilike(search_pattern),
                Customer.birth_number.ilike(search_pattern),
                Customer.customer_number.ilike(search_pattern)
            )
        )
    
    # Pagination
    query = query.order_by(Customer.name).offset(skip).limit(limit)
    result = await db.execute(query)
    customers = result.scalars().all()
    
    return [customer.to_dict() for customer in customers]


@router.get("/{customer_id}", response_model=CustomerResponseSchema)
async def get_customer(
    customer_id: UUID,
    include_balance: bool = True,
    include_transactions: bool = False,
    include_invoices: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Get customer details.
    
    - Optionally include balance, recent transactions, and open invoices
    """
    query = select(Customer).where(Customer.id == customer_id)
    result_query = await db.execute(query)
    customer = result_query.scalars().first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    result = customer.to_dict()
    
    # Add balance
    if include_balance:
        result["balance"] = await get_customer_balance(db, customer_id)
    
    # Add recent transactions
    if include_transactions:
        result["recent_transactions"] = await get_recent_transactions(db, customer_id)
    
    # Add open invoices
    if include_invoices:
        result["open_invoices"] = await get_open_invoices(db, customer_id)
    
    return result


@router.put("/{customer_id}", response_model=CustomerResponseSchema)
async def update_customer(
    customer_id: UUID,
    data: CustomerUpdateSchema,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Update customer details.
    
    - Validates org_number/birth_number uniqueness if changed
    - Logs all changes in audit trail
    - Cannot change to 'deleted' status (only active/inactive)
    """
    query = select(Customer).where(Customer.id == customer_id)
    result = await db.execute(query)
    customer = result.scalars().first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Store old values for audit
    old_values = customer.to_dict()
    changed_fields = []
    
    # Check identifier uniqueness if changing
    if (data.org_number and data.org_number != customer.org_number) or \
       (data.birth_number and data.birth_number != customer.birth_number):
        duplicate = await check_duplicate_identifier(
            db,
            customer.client_id,
            data.org_number if data.org_number != customer.org_number else None,
            data.birth_number if data.birth_number != customer.birth_number else None,
            exclude_id=customer_id
        )
        if duplicate:
            raise HTTPException(
                status_code=400,
                detail=f"Customer with {duplicate} already exists for this client"
            )
    
    # Update fields
    if data.is_company is not None and data.is_company != customer.is_company:
        customer.is_company = data.is_company
        changed_fields.append("is_company")
    
    if data.name is not None and data.name != customer.name:
        customer.name = data.name
        changed_fields.append("name")
    
    if data.org_number is not None and data.org_number != customer.org_number:
        customer.org_number = data.org_number
        changed_fields.append("org_number")
    
    if data.birth_number is not None and data.birth_number != customer.birth_number:
        customer.birth_number = data.birth_number
        changed_fields.append("birth_number")
    
    if data.address:
        if data.address.line1 is not None:
            customer.address_line1 = data.address.line1
            changed_fields.append("address_line1")
        if data.address.line2 is not None:
            customer.address_line2 = data.address.line2
            changed_fields.append("address_line2")
        if data.address.postal_code is not None:
            customer.postal_code = data.address.postal_code
            changed_fields.append("postal_code")
        if data.address.city is not None:
            customer.city = data.address.city
            changed_fields.append("city")
        if data.address.country is not None:
            customer.country = data.address.country
            changed_fields.append("country")
    
    if data.contact:
        if data.contact.person is not None:
            customer.contact_person = data.contact.person
            changed_fields.append("contact_person")
        if data.contact.phone is not None:
            customer.phone = data.contact.phone
            changed_fields.append("phone")
        if data.contact.email is not None:
            customer.email = data.contact.email
            changed_fields.append("email")
    
    if data.financial:
        if data.financial.payment_terms_days is not None:
            customer.payment_terms_days = data.financial.payment_terms_days
            changed_fields.append("payment_terms_days")
        if data.financial.currency is not None:
            customer.currency = data.financial.currency
            changed_fields.append("currency")
        if data.financial.vat_code is not None:
            customer.vat_code = data.financial.vat_code
            changed_fields.append("vat_code")
        if data.financial.default_revenue_account is not None:
            customer.default_revenue_account = data.financial.default_revenue_account
            changed_fields.append("default_revenue_account")
        if data.financial.kid_prefix is not None:
            customer.kid_prefix = data.financial.kid_prefix
            changed_fields.append("kid_prefix")
        if data.financial.use_kid is not None:
            customer.use_kid = data.financial.use_kid
            changed_fields.append("use_kid")
        if data.financial.credit_limit is not None:
            customer.credit_limit = data.financial.credit_limit
            changed_fields.append("credit_limit")
        if data.financial.reminder_fee is not None:
            customer.reminder_fee = data.financial.reminder_fee
            changed_fields.append("reminder_fee")
    
    if data.notes is not None and data.notes != customer.notes:
        customer.notes = data.notes
        changed_fields.append("notes")
    
    if data.status is not None and data.status != customer.status:
        customer.status = data.status
        changed_fields.append("status")
        action = "deactivate" if data.status == "inactive" else "reactivate"
    else:
        action = "update"
    
    if changed_fields:
        await db.flush()
        
        # Audit log
        log_audit(
            db,
            customer.id,
            action=action,
            changed_fields={"fields": changed_fields},
            old_values=old_values,
            new_values=customer.to_dict(),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
    
    await db.commit()
    await db.refresh(customer)
    
    return customer.to_dict()


@router.delete("/{customer_id}")
async def deactivate_customer(
    customer_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivate customer (deletion not allowed).
    
    - Sets status to 'inactive'
    - Logs deactivation in audit trail
    """
    query = select(Customer).where(Customer.id == customer_id)
    result = await db.execute(query)
    customer = result.scalars().first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    if customer.status == "inactive":
        return {"message": "Customer already inactive"}
    
    old_values = customer.to_dict()
    customer.status = "inactive"
    
    await db.flush()
    
    # Audit log
    log_audit(
        db,
        customer.id,
        action="deactivate",
        changed_fields={"fields": ["status"]},
        old_values=old_values,
        new_values=customer.to_dict(),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    await db.commit()
    
    return {"message": "Customer deactivated successfully"}


@router.get("/{customer_id}/audit-log")
async def get_customer_audit_log(
    customer_id: UUID,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get audit log for customer"""
    query = select(Customer).where(Customer.id == customer_id)
    result = await db.execute(query)
    customer = result.scalars().first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    logs_query = select(CustomerAuditLog).where(
        CustomerAuditLog.customer_id == customer_id
    ).order_by(CustomerAuditLog.performed_at.desc()).offset(skip).limit(limit)
    
    logs_result = await db.execute(logs_query)
    logs = logs_result.scalars().all()
    
    return [log.to_dict() for log in logs]


# === BULK IMPORT ===

@router.post("/bulk", response_model=dict)
async def bulk_import_customers(
    request: Request,
    file: bytes = File(...),
    filename: str = Query(...),
    client_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk import customers from CSV or Excel file
    
    Expected CSV columns:
    - navn (required)
    - org_nummer (required for B2B)
    - epost
    - telefon
    - adresse
    - postnummer
    - poststed
    - land
    - kontonummer
    - betalingsbetingelser (e.g., "14 dager")
    - kunde_type (b2b/b2c)
    """
    from app.services.contact_import import parse_file, import_customers
    
    # client_id now comes from query parameter
    
    try:
        # Parse file
        df = parse_file(file, filename)
        
        # Import customers
        result = await import_customers(db, df, client_id)
        
        return result.to_dict()
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
