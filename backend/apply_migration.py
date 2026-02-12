"""
Apply database migration for client contact fields
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.config import settings

async def apply_migration():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        # Add new columns
        await conn.execute(text("""
            ALTER TABLE clients 
            ADD COLUMN IF NOT EXISTS industry VARCHAR(100),
            ADD COLUMN IF NOT EXISTS start_date VARCHAR(10),
            ADD COLUMN IF NOT EXISTS address VARCHAR(500),
            ADD COLUMN IF NOT EXISTS contact_person VARCHAR(200),
            ADD COLUMN IF NOT EXISTS contact_email VARCHAR(255);
        """))
        
        # Create index
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_clients_industry ON clients(industry);
        """))
        
        print("✅ Migration applied successfully!")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(apply_migration())
