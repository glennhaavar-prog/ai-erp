#!/usr/bin/env python3
"""
Auto-post accruals cron job

Runs daily to automatically post pending accruals that are due.
Should be scheduled via cron:
  0 6 * * * cd /path/to/backend && python scripts/auto_post_accruals.py >> logs/accruals_cron.log 2>&1

Or via systemd timer.
"""

import asyncio
import sys
import os
from datetime import date, datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.services.accrual_service import AccrualService
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_auto_post():
    """Main cron job function"""
    logger.info("=" * 60)
    logger.info(f"Starting accrual auto-post job at {datetime.now()}")
    logger.info("=" * 60)
    
    try:
        # Get database session
        async with AsyncSessionLocal() as db:
            service = AccrualService()
            
            # Auto-post all due accruals
            result = await service.auto_post_due_accruals(
                db=db,
                as_of_date=date.today()
            )
            
            logger.info(f"✅ Auto-post completed successfully")
            logger.info(f"   Posted: {result['posted_count']} accruals")
            logger.info(f"   Total amount: kr {result['total_amount']:,.2f}")
            
            if result['errors']:
                logger.warning(f"⚠️  {len(result['errors'])} errors occurred:")
                for error in result['errors']:
                    logger.error(f"   - Posting {error['posting_id']}: {error['error']}")
            
            logger.info("=" * 60)
            
            return result
    
    except Exception as e:
        logger.error(f"❌ Fatal error in auto-post job: {e}", exc_info=True)
        raise


async def main():
    """Entry point"""
    try:
        result = await run_auto_post()
        
        # Exit with error code if there were errors
        if result['errors']:
            sys.exit(1)
        else:
            sys.exit(0)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
