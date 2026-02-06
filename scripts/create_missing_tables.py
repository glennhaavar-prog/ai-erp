#!/usr/bin/env python3
"""
Create missing tables directly (bank_transactions, customer_invoices)
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.ext.asyncio import create_async_engine
from app.database import Base
from app.models import BankTransaction, CustomerInvoice

DATABASE_URL = "postgresql+asyncpg://erp_user:erp_password@localhost:5432/ai_erp"

async def create_tables():
    print("Creating missing tables...")
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        # Create only BankTransaction and CustomerInvoice tables
        await conn.run_sync(Base.metadata.create_all, tables=[
            BankTransaction.__table__,
            CustomerInvoice.__table__
        ])
    
    print("✅ Tables created!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_tables())
