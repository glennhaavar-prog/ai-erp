"""
Currency Rate Service - Fetch and manage exchange rates
"""
import httpx
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, desc, select

from app.models.currency_rate import CurrencyRate


class CurrencyRateService:
    """
    Service for fetching and managing currency exchange rates
    
    Supports:
    - Norges Bank API: USD, EUR, SEK, DKK
    - CoinGecko API: BTC
    - Base currency: NOK
    """
    
    # Supported currencies
    FIAT_CURRENCIES = ["USD", "EUR", "SEK", "DKK"]
    CRYPTO_CURRENCIES = ["BTC"]
    ALL_CURRENCIES = FIAT_CURRENCIES + CRYPTO_CURRENCIES
    
    # API endpoints
    NORGES_BANK_API = "https://data.norges-bank.no/api/data/EXR/B.{currency}.NOK.SP"
    COINGECKO_API = "https://api.coingecko.com/api/v3/simple/price"
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def fetch_norges_bank_rate(self, currency: str) -> Optional[Dict]:
        """
        Fetch exchange rate from Norges Bank API
        
        Args:
            currency: Currency code (USD, EUR, SEK, DKK)
        
        Returns:
            Dict with rate and date, or None if failed
        """
        if currency not in self.FIAT_CURRENCIES:
            return None
        
        url = self.NORGES_BANK_API.format(currency=currency)
        params = {
            "format": "sdmx-json",
            "lastNObservations": 1
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Parse SDMX-JSON format
                # Structure: data.dataSets[0].series.{key}.observations
                dataset = data.get("data", {}).get("dataSets", [{}])[0]
                series = dataset.get("series", {})
                
                # Get the first series (there should only be one)
                if not series:
                    return None
                
                series_key = list(series.keys())[0]
                observations = series[series_key].get("observations", {})
                
                if not observations:
                    return None
                
                # Get the latest observation
                obs_key = list(observations.keys())[0]
                rate_value = observations[obs_key][0]
                
                # Get the date from structure
                structure = data.get("data", {}).get("structure", {})
                dimensions = structure.get("dimensions", {}).get("observation", [])
                
                # Find time dimension
                time_values = None
                for dim in dimensions:
                    if dim.get("id") == "TIME_PERIOD":
                        time_values = dim.get("values", [])
                        break
                
                rate_date = date.today()
                if time_values and int(obs_key) < len(time_values):
                    date_str = time_values[int(obs_key)].get("id")
                    if date_str:
                        rate_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                
                return {
                    "currency": currency,
                    "rate": Decimal(str(rate_value)),
                    "date": rate_date,
                    "source": "norges_bank"
                }
        
        except Exception as e:
            print(f"Error fetching Norges Bank rate for {currency}: {e}")
            return None
    
    async def fetch_coingecko_btc_rate(self) -> Optional[Dict]:
        """
        Fetch BTC/NOK rate from CoinGecko API
        
        Returns:
            Dict with rate and date, or None if failed
        """
        params = {
            "ids": "bitcoin",
            "vs_currencies": "nok"
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.COINGECKO_API, params=params)
                response.raise_for_status()
                data = response.json()
                
                btc_nok = data.get("bitcoin", {}).get("nok")
                if not btc_nok:
                    return None
                
                return {
                    "currency": "BTC",
                    "rate": Decimal(str(btc_nok)),
                    "date": date.today(),
                    "source": "coingecko"
                }
        
        except Exception as e:
            print(f"Error fetching CoinGecko BTC rate: {e}")
            return None
    
    async def fetch_all_rates(self) -> Dict[str, Dict]:
        """
        Fetch all supported currency rates
        
        Returns:
            Dict mapping currency code to rate info
        """
        results = {}
        
        # Fetch fiat currencies from Norges Bank
        for currency in self.FIAT_CURRENCIES:
            rate_data = await self.fetch_norges_bank_rate(currency)
            if rate_data:
                results[currency] = rate_data
        
        # Fetch BTC from CoinGecko
        btc_data = await self.fetch_coingecko_btc_rate()
        if btc_data:
            results["BTC"] = btc_data
        
        return results
    
    async def save_rate(self, currency: str, rate: Decimal, rate_date: date, source: str) -> CurrencyRate:
        """
        Save or update a currency rate in the database
        
        Args:
            currency: Currency code
            rate: Exchange rate
            rate_date: Date of the rate
            source: Source of the rate
        
        Returns:
            CurrencyRate object
        """
        # Check if rate already exists for this date
        result = await self.db.execute(
            select(CurrencyRate).filter(
                and_(
                    CurrencyRate.currency_code == currency,
                    CurrencyRate.rate_date == rate_date
                )
            )
        )
        existing = result.scalars().first()
        
        if existing:
            # Update existing rate
            existing.rate = rate
            existing.source = source
            existing.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            # Create new rate
            new_rate = CurrencyRate(
                currency_code=currency,
                base_currency="NOK",
                rate=rate,
                rate_date=rate_date,
                source=source
            )
            self.db.add(new_rate)
            await self.db.commit()
            await self.db.refresh(new_rate)
            return new_rate
    
    async def update_all_rates(self) -> Dict[str, bool]:
        """
        Fetch and save all currency rates
        
        Returns:
            Dict mapping currency to success status
        """
        rates = await self.fetch_all_rates()
        results = {}
        
        for currency, rate_data in rates.items():
            try:
                await self.save_rate(
                    currency=rate_data["currency"],
                    rate=rate_data["rate"],
                    rate_date=rate_data["date"],
                    source=rate_data["source"]
                )
                results[currency] = True
            except Exception as e:
                print(f"Error saving rate for {currency}: {e}")
                results[currency] = False
        
        return results
    
    async def get_latest_rates(self) -> Dict[str, CurrencyRate]:
        """
        Get the latest rates for all currencies
        
        Returns:
            Dict mapping currency code to CurrencyRate object
        """
        rates = {}
        
        for currency in self.ALL_CURRENCIES:
            result = await self.db.execute(
                select(CurrencyRate)
                .filter(CurrencyRate.currency_code == currency)
                .order_by(desc(CurrencyRate.rate_date))
            )
            latest = result.scalars().first()
            
            if latest:
                rates[currency] = latest
        
        return rates
    
    async def get_rate_on_date(self, currency: str, target_date: date) -> Optional[CurrencyRate]:
        """
        Get the rate for a specific currency on a specific date
        Falls back to most recent rate before that date if exact match not found
        
        Args:
            currency: Currency code
            target_date: Date to get rate for
        
        Returns:
            CurrencyRate object or None
        """
        # Try exact match first
        result = await self.db.execute(
            select(CurrencyRate).filter(
                and_(
                    CurrencyRate.currency_code == currency,
                    CurrencyRate.rate_date == target_date
                )
            )
        )
        exact = result.scalars().first()
        
        if exact:
            return exact
        
        # Fall back to most recent rate before target date
        result = await self.db.execute(
            select(CurrencyRate)
            .filter(
                and_(
                    CurrencyRate.currency_code == currency,
                    CurrencyRate.rate_date <= target_date
                )
            )
            .order_by(desc(CurrencyRate.rate_date))
        )
        previous = result.scalars().first()
        
        return previous
    
    async def get_historical_rates(
        self,
        currency: str,
        start_date: date,
        end_date: date
    ) -> List[CurrencyRate]:
        """
        Get historical rates for a currency within a date range
        
        Args:
            currency: Currency code
            start_date: Start date
            end_date: End date
        
        Returns:
            List of CurrencyRate objects
        """
        result = await self.db.execute(
            select(CurrencyRate)
            .filter(
                and_(
                    CurrencyRate.currency_code == currency,
                    CurrencyRate.rate_date >= start_date,
                    CurrencyRate.rate_date <= end_date
                )
            )
            .order_by(CurrencyRate.rate_date)
        )
        return result.scalars().all()
    
    async def convert_amount(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str,
        target_date: Optional[date] = None
    ) -> Optional[Decimal]:
        """
        Convert an amount from one currency to another
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            target_date: Date for the exchange rate (defaults to today)
        
        Returns:
            Converted amount or None if conversion failed
        """
        if target_date is None:
            target_date = date.today()
        
        # If same currency, return original amount
        if from_currency == to_currency:
            return amount
        
        # If one is NOK, only need one rate
        if from_currency == "NOK":
            to_rate = await self.get_rate_on_date(to_currency, target_date)
            if not to_rate:
                return None
            return amount / to_rate.rate
        
        if to_currency == "NOK":
            from_rate = await self.get_rate_on_date(from_currency, target_date)
            if not from_rate:
                return None
            return amount * from_rate.rate
        
        # Both are non-NOK currencies, convert through NOK
        from_rate = await self.get_rate_on_date(from_currency, target_date)
        to_rate = await self.get_rate_on_date(to_currency, target_date)
        
        if not from_rate or not to_rate:
            return None
        
        # Convert to NOK first, then to target currency
        nok_amount = amount * from_rate.rate
        return nok_amount / to_rate.rate
