#!/usr/bin/env python3
"""
Daily Currency Rate Update Script

This script fetches and updates all currency exchange rates.
Should be run daily via cron or scheduled task.

Add to crontab:
# Update currency rates daily at 9:00 AM
0 9 * * * cd /path/to/backend && python scripts/update_currency_rates.py
"""
import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.services.currency_rate_service import CurrencyRateService


async def update_rates():
    """Update all currency rates"""
    print(f"[{datetime.now()}] Starting currency rate update...")
    
    # Import async engine
    from app.database import async_session_maker
    from sqlalchemy import select
    
    async with async_session_maker() as db:
    
    try:
        # Create service and fetch rates
        service = CurrencyRateService(db)
        results = await service.update_all_rates()
        
        # Report results
        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)
        
        print(f"[{datetime.now()}] Updated {success_count}/{total_count} currency rates")
        
        for currency, success in results.items():
            status = "✅" if success else "❌"
            print(f"  {status} {currency}")
        
        # Update client settings with last update time
        from app.models.client_settings import ClientSettings
        from sqlalchemy import select, update
        
        # Get clients with auto-update enabled
        result = await db.execute(
            select(ClientSettings).where(ClientSettings.auto_update_rates == True)
        )
        clients_with_auto_update = result.scalars().all()
        
        # Update their last_rate_update timestamp
        for client_setting in clients_with_auto_update:
            client_setting.last_rate_update = datetime.utcnow()
        
        await db.commit()
        
        print(f"[{datetime.now()}] Updated last_rate_update for {len(clients_with_auto_update)} clients")
        print(f"[{datetime.now()}] Currency rate update complete!")
        
        return success_count == total_count
    
    except Exception as e:
        print(f"[{datetime.now()}] ERROR: {e}")
        await db.rollback()
        return False


def main():
    """Main entry point"""
    success = asyncio.run(update_rates())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
