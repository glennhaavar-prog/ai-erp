"""
Vouchers API - Bilagsvisning (General Ledger entries with documents)

Kontali ERP - Fase 1
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.general_ledger import GeneralLedger, GeneralLedgerLine
from app.models.document import Document
from app.models.chart_of_accounts import Account

router = APIRouter(prefix="/api/vouchers", tags=["vouchers"])


@router.get("/{voucher_id}")
async def get_voucher(
    voucher_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Hent bilag med konteringer og vedlagt dokument.
    
    Returnerer:
    - Bilagsinformasjon (voucher_number, dato, beskrivelse)
    - Konteringslinjer (konto, debet, kredit, beskrivelse)
    - Vedlagt dokument (PDF/bilde/EHF) hvis finnes
    """
    
    # Hent bilag med linjer
    query = (
        select(GeneralLedger)
        .where(GeneralLedger.id == voucher_id)
        .options(selectinload(GeneralLedger.lines))
    )
    
    result = await db.execute(query)
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Bilag ikke funnet")
    
    # Hent kontonavn fra chart_of_accounts
    accounts_query = select(Account).where(Account.client_id == entry.client_id)
    accounts_result = await db.execute(accounts_query)
    accounts = {acc.account_number: acc.account_name for acc in accounts_result.scalars().all()}
    
    # Bygg response med konteringslinjer
    lines = []
    for line in sorted(entry.lines, key=lambda x: x.line_number):
        lines.append({
            "line_number": line.line_number,
            "account_number": line.account_number,
            "account_name": accounts.get(line.account_number, "Ukjent konto"),
            "line_description": line.line_description,
            "debit_amount": float(line.debit_amount or 0),
            "credit_amount": float(line.credit_amount or 0),
            "vat_code": line.vat_code,
            "vat_amount": float(line.vat_amount or 0) if line.vat_amount else None,
        })
    
    # Hent dokument hvis source_id peker til vendor_invoice
    document_url = None
    document_type = None
    
    if entry.source_type == "vendor_invoice" and entry.source_id:
        # Hent dokument knyttet til vendor_invoice
        doc_query = (
            select(Document)
            .where(Document.entity_type == "vendor_invoice")
            .where(Document.entity_id == entry.source_id)
            .order_by(Document.created_at.desc())
        )
        doc_result = await db.execute(doc_query)
        document = doc_result.scalar_one_or_none()
        
        if document:
            document_url = document.file_path or document.s3_key
            document_type = document.mime_type
    
    # Beregn totaler
    total_debit = sum(line.debit_amount for line in entry.lines)
    total_credit = sum(line.credit_amount for line in entry.lines)
    is_balanced = abs(total_debit - total_credit) < 0.01
    
    return {
        "id": str(entry.id),
        "client_id": str(entry.client_id),
        "voucher_number": entry.voucher_number,
        "voucher_series": entry.voucher_series,
        "entry_date": entry.entry_date.isoformat(),
        "accounting_date": entry.accounting_date.isoformat(),
        "period": entry.period,
        "fiscal_year": entry.fiscal_year,
        "description": entry.description,
        "source_type": entry.source_type,
        "source_id": str(entry.source_id) if entry.source_id else None,
        "created_by_type": entry.created_by_type,
        "status": entry.status,
        "is_reversed": entry.is_reversed,
        "lines": lines,
        "total_debit": float(total_debit),
        "total_credit": float(total_credit),
        "is_balanced": is_balanced,
        "document": {
            "url": document_url,
            "type": document_type,
        } if document_url else None,
        "created_at": entry.created_at.isoformat(),
    }


@router.get("/by-number/{voucher_number}")
async def get_voucher_by_number(
    voucher_number: str,
    client_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Hent bilag basert på bilagsnummer (f.eks. 2026-0001).
    
    Nyttig for kryssnavigering når man bare har bilagsnummer.
    """
    
    query = (
        select(GeneralLedger)
        .where(GeneralLedger.client_id == client_id)
        .where(GeneralLedger.voucher_number == voucher_number)
        .options(selectinload(GeneralLedger.lines))
    )
    
    result = await db.execute(query)
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(
            status_code=404,
            detail=f"Bilag {voucher_number} ikke funnet for klient {client_id}"
        )
    
    # Bruk samme logikk som get_voucher
    return await get_voucher(entry.id, db)
