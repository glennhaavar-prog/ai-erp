"""
Client Settings API - FIRMAINNSTILLINGER
Manage client-specific company settings
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import logging

from app.database import get_db
from app.models.client import Client
from app.models.client_settings import ClientSettings
from app.schemas.client_settings import (
    ClientSettingsResponse,
    ClientSettingsUpdate,
    ClientSettingsCreate,
    create_default_settings,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/clients", tags=["Client Settings"])


@router.get("/{client_id}/settings", response_model=ClientSettingsResponse)
async def get_client_settings(
    client_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get client-specific settings (FIRMAINNSTILLINGER)
    
    Returns all company configuration that should only be visible
    in the single client view, NOT in the multi-client list.
    """
    try:
        client_uuid = UUID(client_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client ID format")
    
    # Verify client exists
    client_query = select(Client).where(Client.id == client_uuid)
    client_result = await db.execute(client_query)
    client = client_result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Get settings
    settings_query = select(ClientSettings).where(ClientSettings.client_id == client_uuid)
    settings_result = await db.execute(settings_query)
    settings = settings_result.scalar_one_or_none()
    
    if not settings:
        # If no settings exist yet, create default settings
        logger.info(f"Creating default settings for client {client_id}")
        default_data = create_default_settings(
            client_id=client_uuid,
            company_name=client.name,
            org_number=client.org_number
        )
        settings = ClientSettings(**default_data)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    
    # Convert to response format
    return ClientSettingsResponse(
        id=settings.id,
        client_id=settings.client_id,
        company_info={
            "company_name": settings.company_name,
            "org_number": settings.org_number,
            "address": {
                "street": settings.address_street,
                "postal_code": settings.address_postal_code,
                "city": settings.address_city,
            },
            "phone": settings.phone,
            "email": settings.email,
            "ceo_name": settings.ceo_name,
            "chairman_name": settings.chairman_name,
            "industry": settings.industry,
            "nace_code": settings.nace_code,
            "accounting_year_start_month": settings.accounting_year_start_month,
            "incorporation_date": settings.incorporation_date,
            "legal_form": settings.legal_form,
        },
        accounting_settings={
            "chart_of_accounts": settings.chart_of_accounts,
            "vat_registered": settings.vat_registered,
            "vat_period": settings.vat_period,
            "currency": settings.currency,
            "rounding_rules": settings.rounding_rules or {"decimals": 2, "method": "standard"},
        },
        bank_accounts=settings.bank_accounts or [],
        payroll_employees={
            "has_employees": settings.has_employees,
            "payroll_frequency": settings.payroll_frequency,
            "employer_tax_zone": settings.employer_tax_zone,
        },
        services={
            "services_provided": settings.services_provided or {
                "bookkeeping": True,
                "payroll": False,
                "annual_accounts": True,
                "vat_reporting": True,
                "other": []
            },
            "task_templates": settings.task_templates or [],
        },
        responsible_accountant={
            "name": settings.responsible_accountant_name,
            "email": settings.responsible_accountant_email,
            "phone": settings.responsible_accountant_phone,
        },
        created_at=settings.created_at.isoformat(),
        updated_at=settings.updated_at.isoformat(),
    )


@router.put("/{client_id}/settings", response_model=ClientSettingsResponse)
async def update_client_settings(
    client_id: str,
    settings_update: ClientSettingsUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update client-specific settings (FIRMAINNSTILLINGER)
    
    All fields are optional - only provided fields will be updated.
    """
    try:
        client_uuid = UUID(client_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client ID format")
    
    # Verify client exists
    client_query = select(Client).where(Client.id == client_uuid)
    client_result = await db.execute(client_query)
    client = client_result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Get or create settings
    settings_query = select(ClientSettings).where(ClientSettings.client_id == client_uuid)
    settings_result = await db.execute(settings_query)
    settings = settings_result.scalar_one_or_none()
    
    if not settings:
        # Create settings if they don't exist
        default_data = create_default_settings(
            client_id=client_uuid,
            company_name=client.name,
            org_number=client.org_number
        )
        settings = ClientSettings(**default_data)
        db.add(settings)
    
    # Update company info
    if settings_update.company_info:
        ci = settings_update.company_info
        settings.company_name = ci.company_name
        settings.org_number = ci.org_number
        if ci.address:
            settings.address_street = ci.address.street
            settings.address_postal_code = ci.address.postal_code
            settings.address_city = ci.address.city
        settings.phone = ci.phone
        settings.email = ci.email
        settings.ceo_name = ci.ceo_name
        settings.chairman_name = ci.chairman_name
        settings.industry = ci.industry
        settings.nace_code = ci.nace_code
        settings.accounting_year_start_month = ci.accounting_year_start_month
        settings.incorporation_date = ci.incorporation_date
        settings.legal_form = ci.legal_form
    
    # Update accounting settings
    if settings_update.accounting_settings:
        acc = settings_update.accounting_settings
        settings.chart_of_accounts = acc.chart_of_accounts
        settings.vat_registered = acc.vat_registered
        settings.vat_period = acc.vat_period
        settings.currency = acc.currency
        settings.rounding_rules = acc.rounding_rules
    
    # Update bank accounts
    if settings_update.bank_accounts is not None:
        settings.bank_accounts = [ba.dict() for ba in settings_update.bank_accounts]
    
    # Update payroll/employees
    if settings_update.payroll_employees:
        pe = settings_update.payroll_employees
        settings.has_employees = pe.has_employees
        settings.payroll_frequency = pe.payroll_frequency
        settings.employer_tax_zone = pe.employer_tax_zone
    
    # Update services
    if settings_update.services:
        svc = settings_update.services
        if svc.services_provided:
            settings.services_provided = svc.services_provided.dict()
        if svc.task_templates is not None:
            settings.task_templates = svc.task_templates
    
    # Update responsible accountant
    if settings_update.responsible_accountant:
        ra = settings_update.responsible_accountant
        settings.responsible_accountant_name = ra.name
        settings.responsible_accountant_email = ra.email
        settings.responsible_accountant_phone = ra.phone
    
    await db.commit()
    await db.refresh(settings)
    
    logger.info(f"Updated settings for client {client_id}")
    
    # Return updated settings (reuse GET logic)
    return await get_client_settings(client_id, db)
