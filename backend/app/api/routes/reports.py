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
    inntekter = []
    kostnader = []
    
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
        else:
            kostnader.append(item)
    
    sum_inntekter = sum(i["amount"] for i in inntekter)
    sum_kostnader = sum(k["amount"] for k in kostnader)
    resultat = sum_inntekter - sum_kostnader
    
    return {
        "client_id": str(client_id),
        "from_date": from_date.isoformat() if from_date else None,
        "to_date": to_date.isoformat() if to_date else None,
        "inntekter": inntekter,
        "sum_inntekter": sum_inntekter,
        "kostnader": kostnader,
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
    sum_gjeld_egenkapital = sum(g["balance"] for g in gjeld_egenkapital)
    
    # Balansen skal balansere: Eiendeler = Gjeld + Egenkapital
    # (men med omvendt fortegn siden gjeld/egenkapital er kredit-kontoer)
    is_balanced = abs(sum_eiendeler + sum_gjeld_egenkapital) < 0.01
    
    return {
        "client_id": str(client_id),
        "balance_date": to_date.isoformat() if to_date else date.today().isoformat(),
        "eiendeler": eiendeler,
        "sum_eiendeler": sum_eiendeler,
        "gjeld_egenkapital": gjeld_egenkapital,
        "sum_gjeld_egenkapital": abs(sum_gjeld_egenkapital),  # Vis som positivt
        "is_balanced": is_balanced
    }


@router.get("/hovedbok")
async def get_hovedbok(
    client_id: UUID = Query(..., description="Client UUID"),
    account_number: Optional[str] = Query(None, description="Filtrer på kontonummer"),
    from_date: Optional[date] = Query(None, description="Fra-dato (inklusiv)"),
    to_date: Optional[date] = Query(None, description="Til-dato (inklusiv)"),
    limit: int = Query(1000, description="Max antall posteringer"),
    offset: int = Query(0, description="Offset for paginering"),
    db: AsyncSession = Depends(get_db)
):
    """
    Hovedbok - viser alle posteringer kronologisk, med filter på konto og periode.
    
    Dette er bokføringsspesifikasjonen (lovpålagt).
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
    
    if account_number:
        query = query.where(GeneralLedgerLine.account_number == account_number)
    
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
        "from_date": from_date.isoformat() if from_date else None,
        "to_date": to_date.isoformat() if to_date else None,
        "opening_balance": opening_balance,
        "closing_balance": closing_balance,
        "entries": entries,
        "count": len(entries),
        "limit": limit,
        "offset": offset
    }
