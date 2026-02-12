"""
Currency Exchange Rate API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta
from typing import List, Optional
from decimal import Decimal

from app.database import get_db
from app.services.currency_rate_service import CurrencyRateService
from pydantic import BaseModel


router = APIRouter(prefix="/api/currencies", tags=["currencies"])


# Pydantic models for request/response
class CurrencyRateResponse(BaseModel):
    currency_code: str
    base_currency: str
    rate: float
    rate_date: str
    source: str
    created_at: str
    updated_at: str


class LatestRatesResponse(BaseModel):
    rates: dict
    last_updated: Optional[str]


class ConversionRequest(BaseModel):
    amount: float
    from_currency: str
    to_currency: str
    date: Optional[str] = None


class ConversionResponse(BaseModel):
    original_amount: float
    original_currency: str
    converted_amount: float
    converted_currency: str
    rate: float
    conversion_date: str


@router.get("/rates", response_model=LatestRatesResponse)
async def get_latest_rates(db: AsyncSession = Depends(get_db)):
    """
    Get the latest exchange rates for all supported currencies
    
    Returns:
        Latest rates for USD, EUR, SEK, DKK, BTC against NOK
    """
    service = CurrencyRateService(db)
    rates = await service.get_latest_rates()
    
    rates_dict = {}
    last_updated = None
    
    for currency, rate_obj in rates.items():
        rates_dict[currency] = {
            "rate": float(rate_obj.rate),
            "date": rate_obj.rate_date.isoformat(),
            "source": rate_obj.source
        }
        
        # Track most recent update
        if last_updated is None or rate_obj.updated_at > last_updated:
            last_updated = rate_obj.updated_at
    
    return {
        "rates": rates_dict,
        "last_updated": last_updated.isoformat() if last_updated else None
    }


@router.get("/rates/{currency}", response_model=CurrencyRateResponse)
async def get_currency_rate(
    currency: str,
    date_param: Optional[str] = Query(None, alias="date"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the exchange rate for a specific currency
    
    Args:
        currency: Currency code (USD, EUR, SEK, DKK, BTC)
        date: Optional date (YYYY-MM-DD format). Defaults to today.
    
    Returns:
        Exchange rate for the specified currency and date
    """
    currency = currency.upper()
    service = CurrencyRateService(db)
    
    # Parse date
    target_date = date.today()
    if date_param:
        try:
            target_date = date.fromisoformat(date_param)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    rate = await service.get_rate_on_date(currency, target_date)
    
    if not rate:
        raise HTTPException(
            status_code=404,
            detail=f"No rate found for {currency} on or before {target_date}"
        )
    
    return CurrencyRateResponse(
        currency_code=rate.currency_code,
        base_currency=rate.base_currency,
        rate=float(rate.rate),
        rate_date=rate.rate_date.isoformat(),
        source=rate.source,
        created_at=rate.created_at.isoformat(),
        updated_at=rate.updated_at.isoformat()
    )


@router.get("/rates/{currency}/history")
async def get_currency_history(
    currency: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    days: Optional[int] = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Get historical exchange rates for a currency
    
    Args:
        currency: Currency code (USD, EUR, SEK, DKK, BTC)
        start_date: Start date (YYYY-MM-DD). Defaults to {days} days ago
        end_date: End date (YYYY-MM-DD). Defaults to today
        days: Number of days to look back if start_date not provided
    
    Returns:
        List of historical rates
    """
    currency = currency.upper()
    service = CurrencyRateService(db)
    
    # Parse dates
    end = date.today()
    if end_date:
        try:
            end = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")
    
    start = end - timedelta(days=days)
    if start_date:
        try:
            start = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
    
    rates = await service.get_historical_rates(currency, start, end)
    
    return {
        "currency": currency,
        "base_currency": "NOK",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "count": len(rates),
        "rates": [
            {
                "date": r.rate_date.isoformat(),
                "rate": float(r.rate),
                "source": r.source
            }
            for r in rates
        ]
    }


@router.post("/rates/refresh")
async def refresh_rates(db: AsyncSession = Depends(get_db)):
    """
    Manually trigger a refresh of all currency rates
    
    Fetches latest rates from:
    - Norges Bank API (USD, EUR, SEK, DKK)
    - CoinGecko API (BTC)
    
    Returns:
        Status of each currency update
    """
    service = CurrencyRateService(db)
    results = await service.update_all_rates()
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    return {
        "success": success_count == total_count,
        "updated": success_count,
        "total": total_count,
        "results": results,
        "timestamp": date.today().isoformat()
    }


@router.post("/convert", response_model=ConversionResponse)
async def convert_currency(
    request: ConversionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Convert an amount from one currency to another
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code
        to_currency: Target currency code
        date: Optional date for historical conversion (YYYY-MM-DD)
    
    Returns:
        Converted amount and exchange rate used
    """
    service = CurrencyRateService(db)
    
    # Parse date
    target_date = date.today()
    if request.date:
        try:
            target_date = date.fromisoformat(request.date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Convert
    from_currency = request.from_currency.upper()
    to_currency = request.to_currency.upper()
    amount = Decimal(str(request.amount))
    
    converted = await service.convert_amount(amount, from_currency, to_currency, target_date)
    
    if converted is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to convert {from_currency} to {to_currency} for date {target_date}"
        )
    
    # Calculate the effective rate used
    if from_currency == to_currency:
        effective_rate = 1.0
    else:
        effective_rate = float(converted / amount)
    
    return ConversionResponse(
        original_amount=float(amount),
        original_currency=from_currency,
        converted_amount=float(converted),
        converted_currency=to_currency,
        rate=effective_rate,
        conversion_date=target_date.isoformat()
    )


@router.get("/supported")
async def get_supported_currencies():
    """
    Get list of supported currencies
    
    Returns:
        List of supported currency codes and their names
    """
    return {
        "base_currency": "NOK",
        "supported_currencies": [
            {"code": "USD", "name": "US Dollar", "source": "Norges Bank"},
            {"code": "EUR", "name": "Euro", "source": "Norges Bank"},
            {"code": "SEK", "name": "Swedish Krona", "source": "Norges Bank"},
            {"code": "DKK", "name": "Danish Krone", "source": "Norges Bank"},
            {"code": "BTC", "name": "Bitcoin", "source": "CoinGecko"},
        ]
    }
