#!/usr/bin/env python3
"""
Verify Migration Script
Validates that all expected tables, indexes, and constraints exist
"""

import asyncio
import sys
from sqlalchemy import text
from app.database import engine
from typing import List, Tuple

# Expected tables
EXPECTED_TABLES = [
    'tenants',
    'clients',
    'users',
    'chart_of_accounts',
    'vendors',
    'documents',
    'general_ledger',
    'general_ledger_lines',
    'vendor_invoices',
    'review_queue',
    'agent_tasks',
    'agent_events',
    'corrections',
    'agent_learned_patterns',
    'agent_decisions',
    'audit_trail',
    'alembic_version',
]

# Critical indexes that must exist
CRITICAL_INDEXES = [
    'ix_agent_tasks_claim',  # FOR UPDATE SKIP LOCKED support
    'ix_agent_events_unprocessed',  # Efficient event polling
    'ix_review_queue_status_priority',  # Priority routing
    'ix_corrections_batch_id',  # Batch support
]


async def check_tables() -> Tuple[bool, List[str]]:
    """Check if all expected tables exist"""
    print("🔍 Checking tables...")
    
    query = text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    
    async with engine.connect() as conn:
        result = await conn.execute(query)
        existing_tables = [row[0] for row in result]
    
    missing_tables = set(EXPECTED_TABLES) - set(existing_tables)
    extra_tables = set(existing_tables) - set(EXPECTED_TABLES)
    
    if missing_tables:
        print(f"  ❌ Missing tables: {', '.join(missing_tables)}")
        return False, list(missing_tables)
    
    if extra_tables:
        print(f"  ⚠️  Extra tables found: {', '.join(extra_tables)}")
    
    print(f"  ✅ All {len(EXPECTED_TABLES)} expected tables exist")
    return True, []


async def check_indexes() -> Tuple[bool, List[str]]:
    """Check if critical indexes exist"""
    print("\n🔍 Checking critical indexes...")
    
    query = text("""
        SELECT indexname 
        FROM pg_indexes 
        WHERE schemaname = 'public'
        ORDER BY indexname
    """)
    
    async with engine.connect() as conn:
        result = await conn.execute(query)
        existing_indexes = [row[0] for row in result]
    
    missing_indexes = set(CRITICAL_INDEXES) - set(existing_indexes)
    
    if missing_indexes:
        print(f"  ❌ Missing critical indexes: {', '.join(missing_indexes)}")
        return False, list(missing_indexes)
    
    print(f"  ✅ All {len(CRITICAL_INDEXES)} critical indexes exist")
    print(f"  ℹ️  Total indexes: {len(existing_indexes)}")
    return True, []


async def check_foreign_keys() -> Tuple[bool, int]:
    """Check foreign key constraints"""
    print("\n🔍 Checking foreign key constraints...")
    
    query = text("""
        SELECT COUNT(*) 
        FROM information_schema.table_constraints 
        WHERE constraint_type = 'FOREIGN KEY' 
        AND table_schema = 'public'
    """)
    
    async with engine.connect() as conn:
        result = await conn.execute(query)
        fk_count = result.scalar()
    
    if fk_count > 0:
        print(f"  ✅ {fk_count} foreign key constraints exist")
        return True, fk_count
    else:
        print("  ❌ No foreign key constraints found")
        return False, 0


async def check_alembic_version() -> Tuple[bool, str]:
    """Check current Alembic migration version"""
    print("\n🔍 Checking Alembic version...")
    
    query = text("SELECT version_num FROM alembic_version")
    
    try:
        async with engine.connect() as conn:
            result = await conn.execute(query)
            version = result.scalar()
        
        if version:
            print(f"  ✅ Current migration version: {version}")
            return True, version
        else:
            print("  ❌ No migration version found")
            return False, ""
    except Exception as e:
        print(f"  ❌ Error checking version: {e}")
        return False, ""


async def check_partial_indexes() -> Tuple[bool, List[str]]:
    """Check partial indexes (with WHERE clause)"""
    print("\n🔍 Checking partial indexes...")
    
    query = text("""
        SELECT indexname, indexdef
        FROM pg_indexes 
        WHERE schemaname = 'public' 
        AND indexdef LIKE '%WHERE%'
        ORDER BY indexname
    """)
    
    async with engine.connect() as conn:
        result = await conn.execute(query)
        partial_indexes = [(row[0], row[1]) for row in result]
    
    if partial_indexes:
        print(f"  ✅ Found {len(partial_indexes)} partial indexes:")
        for idx_name, idx_def in partial_indexes:
            # Extract WHERE clause
            where_clause = idx_def.split('WHERE', 1)[1].strip() if 'WHERE' in idx_def else ''
            print(f"    • {idx_name}: WHERE {where_clause}")
        return True, [idx[0] for idx in partial_indexes]
    else:
        print("  ❌ No partial indexes found")
        return False, []


async def check_tenant_columns() -> Tuple[bool, List[str]]:
    """Verify all tables have tenant_id or client_id for multi-tenancy"""
    print("\n🔍 Checking multi-tenancy columns...")
    
    # Tables that should have tenant_id or client_id (except system tables)
    tenant_tables = [t for t in EXPECTED_TABLES if t not in ['alembic_version', 'tenants']]
    
    query = text("""
        SELECT table_name, column_name
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND column_name IN ('tenant_id', 'client_id')
        ORDER BY table_name
    """)
    
    async with engine.connect() as conn:
        result = await conn.execute(query)
        tables_with_tenant = {row[0]: row[1] for row in result}
    
    missing_tenant = []
    for table in tenant_tables:
        if table not in tables_with_tenant:
            missing_tenant.append(table)
    
    if missing_tenant:
        print(f"  ❌ Tables missing tenant_id/client_id: {', '.join(missing_tenant)}")
        return False, missing_tenant
    
    print(f"  ✅ All {len(tables_with_tenant)} tables have tenant_id or client_id")
    return True, []


async def main():
    """Run all verification checks"""
    print("=" * 60)
    print("🔬 DATABASE MIGRATION VERIFICATION")
    print("=" * 60)
    print()
    
    all_checks_passed = True
    
    try:
        # Check tables
        tables_ok, missing_tables = await check_tables()
        all_checks_passed = all_checks_passed and tables_ok
        
        # Check Alembic version
        version_ok, version = await check_alembic_version()
        all_checks_passed = all_checks_passed and version_ok
        
        # Check indexes
        indexes_ok, missing_indexes = await check_indexes()
        all_checks_passed = all_checks_passed and indexes_ok
        
        # Check partial indexes
        partial_ok, partial_indexes = await check_partial_indexes()
        all_checks_passed = all_checks_passed and partial_ok
        
        # Check foreign keys
        fk_ok, fk_count = await check_foreign_keys()
        all_checks_passed = all_checks_passed and fk_ok
        
        # Check multi-tenancy
        tenant_ok, missing_tenant = await check_tenant_columns()
        all_checks_passed = all_checks_passed and tenant_ok
        
        # Summary
        print()
        print("=" * 60)
        if all_checks_passed:
            print("✅ ALL CHECKS PASSED")
            print("=" * 60)
            print()
            print("Summary:")
            print(f"  • Tables: {len(EXPECTED_TABLES)}")
            print(f"  • Critical indexes: {len(CRITICAL_INDEXES)}")
            print(f"  • Partial indexes: {len(partial_indexes) if partial_ok else 0}")
            print(f"  • Foreign keys: {fk_count}")
            print(f"  • Migration version: {version}")
            print()
            print("🚀 Database is ready for use!")
            return 0
        else:
            print("❌ SOME CHECKS FAILED")
            print("=" * 60)
            print()
            print("Please review the errors above and run migrations again.")
            return 1
            
    except Exception as e:
        print(f"\n❌ Verification failed with error: {e}")
        print("\nIs the database running and accessible?")
        print("Check your DATABASE_URL in .env")
        return 1
    finally:
        await engine.dispose()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification interrupted by user")
        sys.exit(1)
