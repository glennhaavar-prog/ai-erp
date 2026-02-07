"""TaxCode model for Norwegian MVA codes and international tax rates."""

from sqlalchemy import Column, String, Numeric, Boolean, DateTime, UUID
from sqlalchemy.sql import func
from app.database import Base
import uuid


class TaxCode(Base):
    """
    Tax codes (MVA-koder) for VAT/sales tax calculations.
    
    Norwegian MVA codes (from kontali-accounting skill):
    - 1: 25% utgående (salg)
    - 3: 15% utgående (mat)
    - 5: Unntatt MVA (0%)
    - 6: Utenfor MVA-området (0%)
    - 11: 25% inngående (kjøp)
    - 13: 15% inngående (mat kjøp)
    - 31: 25% inngående (kjøp fra utlandet)
    - 33: 15% inngående (mat fra utlandet)
    """
    
    __tablename__ = "tax_codes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(10), nullable=False, index=True)
    description = Column(String(255), nullable=False)
    rate = Column(Numeric(5, 2), nullable=False)  # E.g., 25.00 for 25%
    direction = Column(String(20), nullable=False)  # outgoing/incoming
    account_number = Column(String(10), nullable=True)  # Default GL account (2700 for outgoing, 2740 for incoming)
    is_active = Column(Boolean, nullable=False, default=True)
    country_code = Column(String(2), nullable=False, default='NO')
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        # Unique constraint: one code per country
        {'sqlite_autoincrement': True},
    )
    
    def __repr__(self):
        return f"<TaxCode(code={self.code}, rate={self.rate}%, direction={self.direction})>"
