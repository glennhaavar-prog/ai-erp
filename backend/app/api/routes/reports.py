"""
Reports API - Saldobalanse, Resultatregnskap, Balanse, Hovedbok

Kontali ERP - Fase 1
"""
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.general_ledger import GeneralLedger, GeneralLedgerLine
from app.models.chart_of_accounts import Account
from app.models.client import Client
from app.utils.export_utils import (
    generate_pdf_saldobalanse,
    generate_excel_saldobalanse,
    generate_pdf_resultat,
    generate_excel_resultat,
    generate_pdf_balanse,
    generate_excel_balanse,
    generate_pdf_hovedbok,
    generate_excel_hovedbok,
)

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/saldobalanse")
async def get_saldobalanse(
    client_id: UUID = Query(..., description="Client UUID"),
    from_date: Optional[date] = Query(None, description="Fra-dato (inklusiv)"),
    to_date: Optional[date] = Query(None, description="Til-dato (inklusiv)"),
    account_from: Optional[str] = Query(None, description="Kontoområde fra"),
    account_to: Optional[str] = Query(None, description="Kontoområde til"),
    db: AsyncSession = Depends(get_db)
):
    """
    Saldobalanse - viser saldo per konto for valgt periode.
    
    Filtre:
    - client_id: Obligatorisk
    - from_date/to_date: Valgfri periode
    - account_from/account_to: Valgfri kontoområde (f.eks. 3000-8999)
    
    Returnerer:
    - Lista med kontoer, inngående saldo, bevegelser, utgående saldo
    """
    
    # Bygg query - summer alle posteringer per konto
    query = (
        select(
            GeneralLedgerLine.account_number,
            func.sum(GeneralLedgerLine.debit_amount).label("total_debit"),
            func.sum(GeneralLedgerLine.credit_amount).label("total_credit")
        )
        .join(GeneralLedger, GeneralLedgerLine.general_ledger_id == GeneralLedger.id)
        .where(GeneralLedger.client_id == client_id)
        .where(GeneralLedger.status == "posted")
    )
    
    # Filtrer på dato hvis oppgitt
    if from_date:
        query = query.where(GeneralLedger.accounting_date >= from_date)
    if to_date:
        query = query.where(GeneralLedger.accounting_date <= to_date)
    
    # Filtrer på kontoområde hvis oppgitt
    if account_from:
        query = query.where(GeneralLedgerLine.account_number >= account_from)
    if account_to:
        query = query.where(GeneralLedgerLine.account_number <= account_to)
    
    query = query.group_by(GeneralLedgerLine.account_number)
    query = query.order_by(GeneralLedgerLine.account_number)
    
    result = await db.execute(query)
    rows = result.all()
    
    # Hent kontobeskrivelser
    accounts_query = select(Account).where(
        Account.client_id == client_id
    )
    accounts_result = await db.execute(accounts_query)
    accounts = {acc.account_number: acc for acc in accounts_result.scalars().all()}
    
    # Bygg response
    balances = []
    for row in rows:
        account_number = row.account_number
        total_debit = float(row.total_debit or 0)
        total_credit = float(row.total_credit or 0)
        balance = total_debit - total_credit
        
        account = accounts.get(account_number)
        
        balances.append({
            "account_number": account_number,
            "account_name": account.account_name if account else "Ukjent konto",
            "total_debit": total_debit,
            "total_credit": total_credit,
            "balance": balance
        })
    
    # Beregn totaler
    total_debit = sum(b["total_debit"] for b in balances)
    total_credit = sum(b["total_credit"] for b in balances)
    
    return {
        "client_id": str(client_id),
        "from_date": from_date.isoformat() if from_date else None,
        "to_date": to_date.isoformat() if to_date else None,
        "account_from": account_from,
        "account_to": account_to,
        "balances": balances,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "is_balanced": abs(total_debit - total_credit) < 0.01
    }


@router.get("/resultat")
async def get_resultatregnskap(
    client_id: UUID = Query(..., description="Client UUID"),
    from_date: Optional[date] = Query(None, description="Fra-dato (inklusiv)"),
    to_date: Optional[date] = Query(None, description="Til-dato (inklusiv)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Resultatregnskap - viser inntekter (3000-3999) og kostnader (4000-8999).
    
    Returnerer:
    - Inntekter (gruppert)
    - Kostnader (gruppert)
    - Resultat før skatt
    """
    
    # Resultatregnskap = kontoer 3000-8999
    query = (
        select(
            GeneralLedgerLine.account_number,
            func.sum(GeneralLedgerLine.debit_amount).label("total_debit"),
            func.sum(GeneralLedgerLine.credit_amount).label("total_credit")
        )
        .join(GeneralLedger, GeneralLedgerLine.general_ledger_id == GeneralLedger.id)
        .where(GeneralLedger.client_id == client_id)
        .where(GeneralLedger.status == "posted")
        .where(GeneralLedgerLine.account_number >= "3000")
        .where(GeneralLedgerLine.account_number <= "8999")
    )
    
    if from_date:
        query = query.where(GeneralLedger.accounting_date >= from_date)
    if to_date:
        query = query.where(GeneralLedger.accounting_date <= to_date)
    
    query = query.group_by(GeneralLedgerLine.account_number)
    query = query.order_by(GeneralLedgerLine.account_number)
    
    result = await db.execute(query)
    rows = result.all()
    
    # Hent kontobeskrivelser
    accounts_query = select(Account).where(
        Account.client_id == client_id
    )
    accounts_result = await db.execute(accounts_query)
    accounts = {acc.account_number: acc for acc in accounts_result.scalars().all()}
    
    # Skill inntekter (3000-3999) fra kostnader (4000-8999)
    # Kategoriser kostnader: 4000=Varekjøp, 5000=Lønn, 6000=Andre driftskostnader
    inntekter = []
    varekjop = []  # 4000-4999
    lonnkostnader = []  # 5000-5999
    andre_driftskostnader = []  # 6000-8999
    
    for row in rows:
        account_number = row.account_number
        total_debit = float(row.total_debit or 0)
        total_credit = float(row.total_credit or 0)
        
        # Inntekter: kredit = positivt, debet = negativt
        # Kostnader: debet = positivt, kredit = negativt
        if account_number.startswith("3"):
            amount = total_credit - total_debit  # Inntekter
        else:
            amount = total_debit - total_credit  # Kostnader
        
        account = accounts.get(account_number)
        
        item = {
            "account_number": account_number,
            "account_name": account.account_name if account else "Ukjent konto",
            "amount": amount
        }
        
        if account_number.startswith("3"):
            inntekter.append(item)
        elif account_number.startswith("4"):
            varekjop.append(item)
        elif account_number.startswith("5"):
            lonnkostnader.append(item)
        elif account_number.startswith("6") or account_number.startswith("7") or account_number.startswith("8"):
            andre_driftskostnader.append(item)
    
    # Beregn summer
    sum_inntekter = sum(i["amount"] for i in inntekter)
    sum_varekjop = sum(v["amount"] for v in varekjop)
    sum_lonnkostnader = sum(l["amount"] for l in lonnkostnader)
    sum_andre_driftskostnader = sum(a["amount"] for a in andre_driftskostnader)
    sum_kostnader = sum_varekjop + sum_lonnkostnader + sum_andre_driftskostnader
    resultat = sum_inntekter - sum_kostnader
    
    return {
        "client_id": str(client_id),
        "from_date": from_date.isoformat() if from_date else None,
        "to_date": to_date.isoformat() if to_date else None,
        "inntekter": inntekter,
        "sum_inntekter": sum_inntekter,
        "kostnader": {
            "varekjop": {
                "items": varekjop,
                "sum": sum_varekjop
            },
            "lonnkostnader": {
                "items": lonnkostnader,
                "sum": sum_lonnkostnader
            },
            "andre_driftskostnader": {
                "items": andre_driftskostnader,
                "sum": sum_andre_driftskostnader
            }
        },
        "sum_kostnader": sum_kostnader,
        "resultat": resultat
    }


@router.get("/balanse")
async def get_balanse(
    client_id: UUID = Query(..., description="Client UUID"),
    to_date: Optional[date] = Query(None, description="Balansedato (default = i dag)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Balanserapport - viser eiendeler (1000-1999) og gjeld/egenkapital (2000-2999).
    
    Balanse = øyeblikksbilde per dato (ikke periode).
    
    VIKTIG: Inkluderer automatisk udisponert overskudd (årets resultat) under egenkapital.
    """
    
    # Balanse = kontoer 1000-2999, alle posteringer fram til to_date
    query = (
        select(
            GeneralLedgerLine.account_number,
            func.sum(GeneralLedgerLine.debit_amount).label("total_debit"),
            func.sum(GeneralLedgerLine.credit_amount).label("total_credit")
        )
        .join(GeneralLedger, GeneralLedgerLine.general_ledger_id == GeneralLedger.id)
        .where(GeneralLedger.client_id == client_id)
        .where(GeneralLedger.status == "posted")
        .where(GeneralLedgerLine.account_number >= "1000")
        .where(GeneralLedgerLine.account_number <= "2999")
    )
    
    if to_date:
        query = query.where(GeneralLedger.accounting_date <= to_date)
    
    query = query.group_by(GeneralLedgerLine.account_number)
    query = query.order_by(GeneralLedgerLine.account_number)
    
    result = await db.execute(query)
    rows = result.all()
    
    # Hent kontobeskrivelser
    accounts_query = select(Account).where(
        Account.client_id == client_id
    )
    accounts_result = await db.execute(accounts_query)
    accounts = {acc.account_number: acc for acc in accounts_result.scalars().all()}
    
    # Skill eiendeler (1000-1999) fra gjeld/egenkapital (2000-2999)
    eiendeler = []
    gjeld_egenkapital = []
    
    for row in rows:
        account_number = row.account_number
        total_debit = float(row.total_debit or 0)
        total_credit = float(row.total_credit or 0)
        balance = total_debit - total_credit
        
        account = accounts.get(account_number)
        
        item = {
            "account_number": account_number,
            "account_name": account.account_name if account else "Ukjent konto",
            "balance": balance
        }
        
        if account_number.startswith("1"):
            eiendeler.append(item)
        else:
            gjeld_egenkapital.append(item)
    
    sum_eiendeler = sum(e["balance"] for e in eiendeler)
    sum_gjeld_egenkapital_raw = sum(g["balance"] for g in gjeld_egenkapital)
    
    # KRITISK FIX: Beregn udisponert overskudd (årets resultat)
    # Resultatregnskap = kontoer 3000-8999 (inntekter - kostnader)
    # Periode: ALLE posteringer frem til to_date (ikke bare inneværende år)
    
    resultat_query = (
        select(
            GeneralLedgerLine.account_number,
            func.sum(GeneralLedgerLine.debit_amount).label("total_debit"),
            func.sum(GeneralLedgerLine.credit_amount).label("total_credit")
        )
        .join(GeneralLedger, GeneralLedgerLine.general_ledger_id == GeneralLedger.id)
        .where(GeneralLedger.client_id == client_id)
        .where(GeneralLedger.status == "posted")
        .where(GeneralLedgerLine.account_number >= "3000")
        .where(GeneralLedgerLine.account_number <= "8999")
    )
    
    if to_date:
        resultat_query = resultat_query.where(GeneralLedger.accounting_date <= to_date)
    
    resultat_query = resultat_query.group_by(GeneralLedgerLine.account_number)
    
    resultat_result = await db.execute(resultat_query)
    resultat_rows = resultat_result.all()
    
    # Beregn årets resultat
    sum_inntekter = 0.0
    sum_kostnader = 0.0
    
    for row in resultat_rows:
        account_number = row.account_number
        total_debit = float(row.total_debit or 0)
        total_credit = float(row.total_credit or 0)
        
        if account_number.startswith("3"):
            # Inntekter: kredit - debit
            sum_inntekter += (total_credit - total_debit)
        else:
            # Kostnader: debit - kredit
            sum_kostnader += (total_debit - total_credit)
    
    udisponert_overskudd = sum_inntekter - sum_kostnader
    
    # Legg til udisponert overskudd under egenkapital
    # (negativ verdi siden det er kredit-side av balansen)
    gjeld_egenkapital.append({
        "account_number": "2999",  # Dummy kontonummer for udisponert overskudd
        "account_name": "Udisponert overskudd",
        "balance": -udisponert_overskudd  # Negativ fordi egenkapital er kredit
    })
    
    # Oppdater sum
    sum_gjeld_egenkapital = sum_gjeld_egenkapital_raw - udisponert_overskudd
    
    # Balansen skal balansere: Eiendeler = Gjeld + Egenkapital
    # (med omvendt fortegn siden gjeld/egenkapital er kredit-kontoer)
    is_balanced = abs(sum_eiendeler + sum_gjeld_egenkapital) < 0.01
    
    # VALIDERING: Hvis balansen IKKE balanserer, kast feil (dette skal være umulig!)
    if not is_balanced:
        raise HTTPException(
            status_code=500,
            detail=f"KRITISK FEIL: Balansen balanserer ikke! Eiendeler={sum_eiendeler:.2f}, Gjeld+EK={-sum_gjeld_egenkapital:.2f}, Differanse={sum_eiendeler + sum_gjeld_egenkapital:.2f}"
        )
    
    return {
        "client_id": str(client_id),
        "balance_date": to_date.isoformat() if to_date else date.today().isoformat(),
        "eiendeler": eiendeler,
        "sum_eiendeler": sum_eiendeler,
        "gjeld_egenkapital": gjeld_egenkapital,
        "sum_gjeld_egenkapital": abs(sum_gjeld_egenkapital),  # Vis som positivt
        "udisponert_overskudd": udisponert_overskudd,
        "is_balanced": is_balanced
    }


@router.get("/hovedbok")
async def get_hovedbok(
    client_id: UUID = Query(..., description="Client UUID"),
    account_number: Optional[str] = Query(None, description="Filtrer på enkeltkonto (deprecated, bruk account_from/account_to)"),
    account_from: Optional[str] = Query(None, description="Kontoområde fra"),
    account_to: Optional[str] = Query(None, description="Kontoområde til"),
    from_date: Optional[date] = Query(None, description="Fra-dato (inklusiv)"),
    to_date: Optional[date] = Query(None, description="Til-dato (inklusiv)"),
    limit: int = Query(1000, description="Max antall posteringer"),
    offset: int = Query(0, description="Offset for paginering"),
    db: AsyncSession = Depends(get_db)
):
    """
    Hovedbok - viser alle posteringer kronologisk, med filter på konto og periode.
    
    Dette er bokføringsspesifikasjonen (lovpålagt).
    
    NYTT: Støtter nå kontorange (account_from/account_to), f.eks. 6000-6999.
    """
    
    # Bygg query
    query = (
        select(
            GeneralLedger.id.label("entry_id"),
            GeneralLedger.voucher_number,
            GeneralLedger.accounting_date,
            GeneralLedger.description.label("entry_description"),
            GeneralLedgerLine.account_number,
            GeneralLedgerLine.line_description,
            GeneralLedgerLine.debit_amount,
            GeneralLedgerLine.credit_amount,
            GeneralLedgerLine.vat_code,
            GeneralLedgerLine.vat_amount
        )
        .join(GeneralLedgerLine, GeneralLedger.id == GeneralLedgerLine.general_ledger_id)
        .where(GeneralLedger.client_id == client_id)
        .where(GeneralLedger.status == "posted")
    )
    
    # FIX: Støtte for kontorange (account_from/account_to)
    if account_number:
        # Backward compatibility - single account
        query = query.where(GeneralLedgerLine.account_number == account_number)
    else:
        # New range support
        if account_from:
            query = query.where(GeneralLedgerLine.account_number >= account_from)
        if account_to:
            query = query.where(GeneralLedgerLine.account_number <= account_to)
    
    if from_date:
        query = query.where(GeneralLedger.accounting_date >= from_date)
    if to_date:
        query = query.where(GeneralLedger.accounting_date <= to_date)
    
    # Sorter kronologisk
    query = query.order_by(
        GeneralLedger.accounting_date,
        GeneralLedger.voucher_number,
        GeneralLedgerLine.line_number
    )
    
    # Paginering
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    rows = result.all()
    
    # Bygg response
    entries = []
    for row in rows:
        entries.append({
            "entry_id": str(row.entry_id),
            "voucher_number": row.voucher_number,
            "accounting_date": row.accounting_date.isoformat(),
            "entry_description": row.entry_description,
            "account_number": row.account_number,
            "line_description": row.line_description,
            "debit_amount": float(row.debit_amount or 0),
            "credit_amount": float(row.credit_amount or 0),
            "vat_code": row.vat_code,
            "vat_amount": float(row.vat_amount or 0) if row.vat_amount else None
        })
    
    # Beregn inngående/utgående saldo hvis spesifikk konto
    opening_balance = None
    closing_balance = None
    
    if account_number and from_date:
        # Inngående saldo = sum før from_date
        opening_query = (
            select(
                func.sum(GeneralLedgerLine.debit_amount).label("total_debit"),
                func.sum(GeneralLedgerLine.credit_amount).label("total_credit")
            )
            .join(GeneralLedger, GeneralLedgerLine.general_ledger_id == GeneralLedger.id)
            .where(GeneralLedger.client_id == client_id)
            .where(GeneralLedger.status == "posted")
            .where(GeneralLedgerLine.account_number == account_number)
            .where(GeneralLedger.accounting_date < from_date)
        )
        opening_result = await db.execute(opening_query)
        opening_row = opening_result.first()
        
        if opening_row:
            opening_debit = float(opening_row.total_debit or 0)
            opening_credit = float(opening_row.total_credit or 0)
            opening_balance = opening_debit - opening_credit
        else:
            opening_balance = 0.0
    
    if account_number:
        # Utgående saldo = inngående + bevegelser i perioden
        period_debit = sum(e["debit_amount"] for e in entries)
        period_credit = sum(e["credit_amount"] for e in entries)
        closing_balance = (opening_balance or 0) + (period_debit - period_credit)
    
    return {
        "client_id": str(client_id),
        "account_number": account_number,
        "account_from": account_from,
        "account_to": account_to,
        "from_date": from_date.isoformat() if from_date else None,
        "to_date": to_date.isoformat() if to_date else None,
        "opening_balance": opening_balance,
        "closing_balance": closing_balance,
        "entries": entries,
        "count": len(entries),
        "limit": limit,
        "offset": offset
    }


# ==================== EXPORT ENDPOINTS ====================
# PDF and Excel export for all reports

async def get_client_name(client_id: UUID, db: AsyncSession) -> str:
    """Helper function to get client name"""
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")
    return client.name


@router.get("/saldobalanse/pdf")
async def export_saldobalanse_pdf(
    client_id: UUID = Query(..., description="Client UUID"),
    from_date: Optional[date] = Query(None, description="Fra-dato (inklusiv)"),
    to_date: Optional[date] = Query(None, description="Til-dato (inklusiv)"),
    account_from: Optional[str] = Query(None, description="Kontoområde fra"),
    account_to: Optional[str] = Query(None, description="Kontoområde til"),
    db: AsyncSession = Depends(get_db)
):
    """Export Saldobalanse as PDF"""
    # Get data from existing endpoint logic
    data = await get_saldobalanse(client_id, from_date, to_date, account_from, account_to, db)
    client_name = await get_client_name(client_id, db)
    
    return generate_pdf_saldobalanse(data, client_name)


@router.get("/saldobalanse/excel")
async def export_saldobalanse_excel(
    client_id: UUID = Query(..., description="Client UUID"),
    from_date: Optional[date] = Query(None, description="Fra-dato (inklusiv)"),
    to_date: Optional[date] = Query(None, description="Til-dato (inklusiv)"),
    account_from: Optional[str] = Query(None, description="Kontoområde fra"),
    account_to: Optional[str] = Query(None, description="Kontoområde til"),
    db: AsyncSession = Depends(get_db)
):
    """Export Saldobalanse as Excel"""
    data = await get_saldobalanse(client_id, from_date, to_date, account_from, account_to, db)
    client_name = await get_client_name(client_id, db)
    
    return generate_excel_saldobalanse(data, client_name)


@router.get("/resultat/pdf")
async def export_resultat_pdf(
    client_id: UUID = Query(..., description="Client UUID"),
    from_date: Optional[date] = Query(None, description="Fra-dato (inklusiv)"),
    to_date: Optional[date] = Query(None, description="Til-dato (inklusiv)"),
    db: AsyncSession = Depends(get_db)
):
    """Export Resultatregnskap as PDF"""
    data = await get_resultatregnskap(client_id, from_date, to_date, db)
    client_name = await get_client_name(client_id, db)
    
    return generate_pdf_resultat(data, client_name)


@router.get("/resultat/excel")
async def export_resultat_excel(
    client_id: UUID = Query(..., description="Client UUID"),
    from_date: Optional[date] = Query(None, description="Fra-dato (inklusiv)"),
    to_date: Optional[date] = Query(None, description="Til-dato (inklusiv)"),
    db: AsyncSession = Depends(get_db)
):
    """Export Resultatregnskap as Excel"""
    data = await get_resultatregnskap(client_id, from_date, to_date, db)
    client_name = await get_client_name(client_id, db)
    
    return generate_excel_resultat(data, client_name)


@router.get("/balanse/pdf")
async def export_balanse_pdf(
    client_id: UUID = Query(..., description="Client UUID"),
    to_date: Optional[date] = Query(None, description="Balansedato (default = i dag)"),
    db: AsyncSession = Depends(get_db)
):
    """Export Balanse as PDF"""
    data = await get_balanse(client_id, to_date, db)
    client_name = await get_client_name(client_id, db)
    
    return generate_pdf_balanse(data, client_name)


@router.get("/balanse/excel")
async def export_balanse_excel(
    client_id: UUID = Query(..., description="Client UUID"),
    to_date: Optional[date] = Query(None, description="Balansedato (default = i dag)"),
    db: AsyncSession = Depends(get_db)
):
    """Export Balanse as Excel"""
    data = await get_balanse(client_id, to_date, db)
    client_name = await get_client_name(client_id, db)
    
    return generate_excel_balanse(data, client_name)


@router.get("/hovedbok/pdf")
async def export_hovedbok_pdf(
    client_id: UUID = Query(..., description="Client UUID"),
    account_number: Optional[str] = Query(None, description="Filtrer på enkeltkonto"),
    account_from: Optional[str] = Query(None, description="Kontoområde fra"),
    account_to: Optional[str] = Query(None, description="Kontoområde til"),
    from_date: Optional[date] = Query(None, description="Fra-dato (inklusiv)"),
    to_date: Optional[date] = Query(None, description="Til-dato (inklusiv)"),
    limit: int = Query(1000, description="Max antall posteringer"),
    offset: int = Query(0, description="Offset for paginering"),
    db: AsyncSession = Depends(get_db)
):
    """Export Hovedbok as PDF"""
    data = await get_hovedbok(client_id, account_number, account_from, account_to, 
                              from_date, to_date, limit, offset, db)
    client_name = await get_client_name(client_id, db)
    
    return generate_pdf_hovedbok(data, client_name)


@router.get("/hovedbok/excel")
async def export_hovedbok_excel(
    client_id: UUID = Query(..., description="Client UUID"),
    account_number: Optional[str] = Query(None, description="Filtrer på enkeltkonto"),
    account_from: Optional[str] = Query(None, description="Kontoområde fra"),
    account_to: Optional[str] = Query(None, description="Kontoområde til"),
    from_date: Optional[date] = Query(None, description="Fra-dato (inklusiv)"),
    to_date: Optional[date] = Query(None, description="Til-dato (inklusiv)"),
    limit: int = Query(1000, description="Max antall posteringer"),
    offset: int = Query(0, description="Offset for paginering"),
    db: AsyncSession = Depends(get_db)
):
    """Export Hovedbok as Excel"""
    data = await get_hovedbok(client_id, account_number, account_from, account_to, 
                              from_date, to_date, limit, offset, db)
    client_name = await get_client_name(client_id, db)
    
    return generate_excel_hovedbok(data, client_name)


# === ALIASES FOR RESKONTRO ENDPOINTS (Frontend compatibility) ===
from fastapi.responses import RedirectResponse

@router.get("/leverandor-reskontro/")
async def leverandor_reskontro_alias(
    client_id: UUID = Query(...),
    status: Optional[str] = Query(None),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    supplier_id: Optional[UUID] = None
):
    """
    Alias for supplier-ledger endpoint (Leverandørreskontro).
    Redirects to /supplier-ledger/
    """
    from starlette.datastructures import QueryParams
    params = {
        "client_id": str(client_id),
    }
    if status:
        params["status"] = status
    if date_from:
        params["date_from"] = str(date_from)
    if date_to:
        params["date_to"] = str(date_to)
    if supplier_id:
        params["supplier_id"] = str(supplier_id)
    
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return RedirectResponse(url=f"/supplier-ledger/?{query_string}", status_code=307)


@router.get("/kunde-reskontro/")
async def kunde_reskontro_alias(
    client_id: UUID = Query(...),
    status: Optional[str] = Query(None),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    customer_id: Optional[UUID] = None
):
    """
    Alias for customer-ledger endpoint (Kundereskontro).
    Redirects to /customer-ledger/
    """
    from starlette.datastructures import QueryParams
    params = {
        "client_id": str(client_id),
    }
    if status:
        params["status"] = status
    if date_from:
        params["date_from"] = str(date_from)
    if date_to:
        params["date_to"] = str(date_to)
    if customer_id:
        params["customer_id"] = str(customer_id)
    
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return RedirectResponse(url=f"/customer-ledger/?{query_string}", status_code=307)
