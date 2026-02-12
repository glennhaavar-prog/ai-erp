"""
Apply migration for vat_registered column
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.config import settings

async def apply_migration():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        # Add vat_registered column
        await conn.execute(text("""
            ALTER TABLE clients 
            ADD COLUMN IF NOT EXISTS vat_registered BOOLEAN DEFAULT TRUE;
        """))
        
        print("✅ VAT migration applied successfully!")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(apply_migration())
