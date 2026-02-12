#!/usr/bin/env python3
import asyncio
from sqlalchemy import text
from app.database import engine

async def check_columns():
    async with engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'client_settings' 
            AND column_name IN ('supported_currencies', 'auto_update_rates', 'last_rate_update')
            ORDER BY column_name
        """))
        rows = result.fetchall()
        columns = [row[0] for row in rows]
        
        print("Checking client_settings columns...")
        needed = ['auto_update_rates', 'last_rate_update', 'supported_currencies']
        for col in needed:
            status = "✅" if col in columns else "❌"
            print(f"  {status} {col}")
        
        return len(columns) == len(needed)

if __name__ == "__main__":
    all_present = asyncio.run(check_columns())
    exit(0 if all_present else 1)
