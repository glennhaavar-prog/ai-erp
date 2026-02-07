#!/usr/bin/env python3
"""
Auto-post due accruals (Periodisering)

This script is called by a daily cron job to automatically post
all pending accruals that are due today or earlier.

Usage:
    python scripts/auto_post_accruals.py [--date YYYY-MM-DD]
"""

import asyncio
import sys
from datetime import date
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import get_db
from app.services.accrual_service import AccrualService


async def main(as_of_date: date = None):
    """
    Auto-post all due accruals.
    
    Args:
        as_of_date: Date to check (defaults to today)
    """
    
    if as_of_date is None:
        as_of_date = date.today()
    
    print(f"🔄 Auto-posting accruals due on or before {as_of_date.isoformat()}...")
    
    service = AccrualService()
    
    async for db in get_db():
        try:
            result = await service.auto_post_due_accruals(
                db=db,
                as_of_date=as_of_date
            )
            
            if result["success"]:
                print(f"✅ Posted {result['posted_count']} accruals")
                print(f"💰 Total amount: {result['total_amount']:.2f} NOK")
                
                if result["errors"]:
                    print(f"⚠️  {len(result['errors'])} errors:")
                    for error in result["errors"]:
                        print(f"   - Posting {error['posting_id']}: {error['error']}")
            else:
                print("❌ Auto-posting failed")
                sys.exit(1)
        
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
        
        finally:
            break  # Only one iteration from async generator


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto-post due accruals")
    parser.add_argument(
        "--date",
        type=str,
        help="Date to check (YYYY-MM-DD), defaults to today"
    )
    
    args = parser.parse_args()
    
    target_date = None
    if args.date:
        target_date = date.fromisoformat(args.date)
    
    asyncio.run(main(target_date))
