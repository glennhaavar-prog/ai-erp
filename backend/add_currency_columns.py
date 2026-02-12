#!/usr/bin/env python3
"""Add currency columns to client_settings table"""
import asyncio
from sqlalchemy import text
from app.database import engine

async def add_columns():
    async with engine.begin() as conn:
        # Add supported_currencies column
        try:
            await conn.execute(text("""
                ALTER TABLE client_settings 
                ADD COLUMN IF NOT EXISTS supported_currencies JSON NOT NULL DEFAULT '["NOK"]'
            """))
            print("✅ Added supported_currencies column")
        except Exception as e:
            print(f"❌ Error adding supported_currencies: {e}")
        
        # Add auto_update_rates column
        try:
            await conn.execute(text("""
                ALTER TABLE client_settings 
                ADD COLUMN IF NOT EXISTS auto_update_rates BOOLEAN NOT NULL DEFAULT true
            """))
            print("✅ Added auto_update_rates column")
        except Exception as e:
            print(f"❌ Error adding auto_update_rates: {e}")
        
        # Add last_rate_update column
        try:
            await conn.execute(text("""
                ALTER TABLE client_settings 
                ADD COLUMN IF NOT EXISTS last_rate_update TIMESTAMP WITHOUT TIME ZONE
            """))
            print("✅ Added last_rate_update column")
        except Exception as e:
            print(f"❌ Error adding last_rate_update: {e}")
        
        print("\n✅ All columns added successfully!")

if __name__ == "__main__":
    print("Adding currency columns to client_settings table...\n")
    asyncio.run(add_columns())
