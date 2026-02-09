#!/usr/bin/env python3
"""
Auto-Booking Agent - Scheduled Job Runner
Run this script via cron every 5 minutes to automatically process new invoices

USAGE:
    python run_auto_booking.py [--client-id CLIENT_ID] [--limit LIMIT]

CRON EXAMPLE (every 5 minutes):
    */5 * * * * cd /path/to/backend && /path/to/venv/bin/python scripts/run_auto_booking.py >> logs/auto_booking.log 2>&1
"""
import asyncio
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import async_session
from app.services.auto_booking_agent import run_auto_booking_batch
from uuid import UUID

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_auto_booking_job(client_id: str = None, limit: int = 50):
    """
    Run auto-booking agent job
    """
    logger.info("=" * 80)
    logger.info(f"Auto-Booking Job Started - {datetime.utcnow().isoformat()}")
    logger.info("=" * 80)
    
    try:
        client_uuid = UUID(client_id) if client_id else None
        
        async with async_session() as db:
            result = await run_auto_booking_batch(
                db=db,
                client_id=client_uuid,
                limit=limit
            )
            
            if result['success']:
                logger.info(
                    f"✅ Batch complete: {result['processed_count']} processed, "
                    f"{result['auto_booked_count']} auto-booked, "
                    f"{result['review_queue_count']} to review, "
                    f"{result['failed_count']} failed"
                )
                
                # Calculate success rate
                if result['processed_count'] > 0:
                    success_rate = (
                        result['auto_booked_count'] / result['processed_count'] * 100
                    )
                    logger.info(f"Success rate: {success_rate:.1f}%")
                    
                    # Skattefunn compliance check
                    if success_rate >= 95.0:
                        logger.info("✅ Skattefunn compliant (>= 95% success)")
                    else:
                        logger.warning(
                            f"⚠️ Below Skattefunn requirement: {success_rate:.1f}% < 95%"
                        )
                
                return True
            else:
                logger.error(f"❌ Batch failed: {result.get('error')}")
                return False
    
    except Exception as e:
        logger.error(f"❌ Auto-booking job failed: {str(e)}", exc_info=True)
        return False
    
    finally:
        logger.info("=" * 80)
        logger.info(f"Auto-Booking Job Finished - {datetime.utcnow().isoformat()}")
        logger.info("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description='Run auto-booking agent to process new invoices'
    )
    parser.add_argument(
        '--client-id',
        type=str,
        help='Process invoices for specific client only (UUID)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='Maximum number of invoices to process (default: 50)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run the job
    success = asyncio.run(run_auto_booking_job(
        client_id=args.client_id,
        limit=args.limit
    ))
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
