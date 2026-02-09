#!/usr/bin/env python3
"""
Database Migration: Create auto_booking_stats table

Run this script to add the auto_booking_stats table to the database.

USAGE:
    python scripts/create_auto_booking_stats_table.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS auto_booking_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    period_date DATE NOT NULL,
    period_type VARCHAR(20) DEFAULT 'daily' NOT NULL,
    
    -- Processing counts
    invoices_processed INTEGER DEFAULT 0 NOT NULL,
    invoices_auto_booked INTEGER DEFAULT 0 NOT NULL,
    invoices_to_review INTEGER DEFAULT 0 NOT NULL,
    invoices_failed INTEGER DEFAULT 0 NOT NULL,
    
    -- Calculated rates (percentages)
    success_rate NUMERIC(5,2) DEFAULT 0.00 NOT NULL,
    escalation_rate NUMERIC(5,2) DEFAULT 0.00 NOT NULL,
    failure_rate NUMERIC(5,2) DEFAULT 0.00 NOT NULL,
    
    -- Confidence metrics
    avg_confidence_auto_booked NUMERIC(5,2),
    avg_confidence_escalated NUMERIC(5,2),
    
    -- False positive tracking (Skattefunn critical)
    false_positives INTEGER DEFAULT 0 NOT NULL,
    false_positive_rate NUMERIC(5,2) DEFAULT 0.00 NOT NULL,
    
    -- Pattern learning metrics
    patterns_applied INTEGER DEFAULT 0 NOT NULL,
    patterns_created INTEGER DEFAULT 0 NOT NULL,
    
    -- Financial metrics
    total_amount_processed NUMERIC(15,2) DEFAULT 0.00 NOT NULL,
    total_amount_auto_booked NUMERIC(15,2) DEFAULT 0.00 NOT NULL,
    avg_processing_time_seconds NUMERIC(8,2),
    
    -- Breakdown by category (JSON)
    escalation_reasons JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_auto_booking_stats_client 
    ON auto_booking_stats(client_id);

CREATE INDEX IF NOT EXISTS idx_auto_booking_stats_period 
    ON auto_booking_stats(period_date);

CREATE INDEX IF NOT EXISTS idx_auto_booking_stats_period_type 
    ON auto_booking_stats(period_type);

-- Unique constraint: one record per client per period
CREATE UNIQUE INDEX IF NOT EXISTS idx_auto_booking_stats_unique 
    ON auto_booking_stats(client_id, period_date, period_type);

-- Comment for documentation
COMMENT ON TABLE auto_booking_stats IS 
    'Auto-booking performance metrics for Skattefunn AP1+AP2 compliance (95%+ accuracy requirement)';
"""


async def run_migration():
    """
    Run the migration to create auto_booking_stats table
    """
    print("=" * 80)
    print("Database Migration: Create auto_booking_stats table")
    print("=" * 80)
    
    try:
        async with engine.begin() as conn:
            print("\n✓ Connected to database")
            
            # Execute CREATE TABLE
            print("✓ Creating auto_booking_stats table...")
            await conn.execute(text(CREATE_TABLE_SQL))
            
            print("✓ Table created successfully")
            
            # Verify table exists
            print("✓ Verifying table...")
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'auto_booking_stats'
                );
            """))
            
            exists = result.scalar()
            
            if exists:
                print("✅ Migration completed successfully!")
                print("\n✓ Table: auto_booking_stats")
                print("✓ Indexes: idx_auto_booking_stats_client, idx_auto_booking_stats_period")
                print("✓ Unique constraint: (client_id, period_date, period_type)")
                
                # Show table info
                result = await conn.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'auto_booking_stats'
                    ORDER BY ordinal_position;
                """))
                
                print("\n📋 Table Schema:")
                print("-" * 60)
                for row in result:
                    print(f"  {row[0]:30s} {row[1]}")
                print("-" * 60)
                
                return True
            else:
                print("❌ Table verification failed")
                return False
    
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print("=" * 80)


async def rollback_migration():
    """
    Rollback: Drop auto_booking_stats table
    """
    print("=" * 80)
    print("Database Migration Rollback: Drop auto_booking_stats table")
    print("=" * 80)
    
    try:
        async with engine.begin() as conn:
            print("\n✓ Connected to database")
            
            # Drop table
            print("✓ Dropping auto_booking_stats table...")
            await conn.execute(text("DROP TABLE IF EXISTS auto_booking_stats CASCADE;"))
            
            print("✅ Rollback completed successfully!")
            return True
    
    except Exception as e:
        print(f"❌ Rollback failed: {str(e)}")
        return False
    
    finally:
        print("=" * 80)


def main():
    """
    Main entry point
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Create auto_booking_stats table for tracking agent performance'
    )
    parser.add_argument(
        '--rollback',
        action='store_true',
        help='Drop the table (rollback migration)'
    )
    
    args = parser.parse_args()
    
    if args.rollback:
        confirm = input("⚠️  Are you sure you want to drop auto_booking_stats table? (yes/no): ")
        if confirm.lower() == 'yes':
            success = asyncio.run(rollback_migration())
        else:
            print("Rollback cancelled")
            success = False
    else:
        success = asyncio.run(run_migration())
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
