"""
Currency Rate model - Exchange rates for multi-currency support
"""
from sqlalchemy import (
    Column, String, Numeric, DateTime, Date, Index
)
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, date
import uuid

from app.database import Base


class CurrencyRate(Base):
    """
    Currency Exchange Rates
    
    Stores exchange rates from various sources (Norges Bank API, CoinGecko)
    Base currency is always NOK (Norwegian Krone)
    
    Example:
    - currency_code: "USD", rate: 10.50 means 1 USD = 10.50 NOK
    - currency_code: "EUR", rate: 11.80 means 1 EUR = 11.80 NOK
    - currency_code: "BTC", rate: 750000.00 means 1 BTC = 750,000 NOK
    """
    __tablename__ = "currency_rates"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Currency Information
    currency_code = Column(String(10), nullable=False, index=True)  # USD, EUR, SEK, DKK, BTC
    base_currency = Column(String(3), nullable=False, default="NOK")  # Always NOK
    
    # Rate (how many NOK for 1 unit of currency_code)
    rate = Column(Numeric(20, 6), nullable=False)  # High precision for BTC
    
    # Date this rate applies to
    rate_date = Column(Date, nullable=False, index=True, default=date.today)
    
    # Source of the rate
    source = Column(String(50), nullable=False)  # 'norges_bank', 'coingecko'
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Composite index for fast lookups
    __table_args__ = (
        Index('idx_currency_date', 'currency_code', 'rate_date'),
        Index('idx_date_currency', 'rate_date', 'currency_code'),
    )
    
    def __repr__(self):
        return (
            f"<CurrencyRate(currency={self.currency_code}, "
            f"rate={self.rate}, date={self.rate_date}, source={self.source})>"
        )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "currency_code": self.currency_code,
            "base_currency": self.base_currency,
            "rate": float(self.rate),
            "rate_date": self.rate_date.isoformat(),
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
