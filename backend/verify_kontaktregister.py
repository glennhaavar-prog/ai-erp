#!/usr/bin/env python3
"""
Verify KONTAKTREGISTER tables exist and are properly structured
"""
import asyncio
import sys
from sqlalchemy import text
from app.database import engine

async def verify_tables():
    """Check if KONTAKTREGISTER tables exist"""
    
    tables_to_check = [
        'suppliers',
        'supplier_audit_logs',
        'customers',
        'customer_audit_logs'
    ]
    
    async with engine.begin() as conn:
        for table in tables_to_check:
            result = await conn.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table}'
                );
            """))
            exists = result.scalar()
            
            if exists:
                print(f"✓ Table '{table}' exists")
                
                # Get column count
                result = await conn.execute(text(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}';
                """))
                col_count = result.scalar()
                print(f"  - Columns: {col_count}")
                
                # Get row count
                result = await conn.execute(text(f"SELECT COUNT(*) FROM {table};"))
                row_count = result.scalar()
                print(f"  - Rows: {row_count}")
            else:
                print(f"✗ Table '{table}' DOES NOT exist")
        
        print("\n" + "="*50)
        print("Checking constraints...")
        print("="*50)
        
        # Check unique constraints
        result = await conn.execute(text("""
            SELECT
                tc.constraint_name,
                tc.table_name,
                kcu.column_name
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'UNIQUE' 
                AND tc.table_name IN ('suppliers', 'customers')
            ORDER BY tc.table_name, tc.constraint_name;
        """))
        
        constraints = result.fetchall()
        if constraints:
            print("\nUnique Constraints:")
            for row in constraints:
                print(f"  - {row[1]}.{row[2]} ({row[0]})")
        
        # Check foreign keys
        result = await conn.execute(text("""
            SELECT
                tc.constraint_name,
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name IN ('suppliers', 'customers', 'supplier_audit_logs', 'customer_audit_logs')
            ORDER BY tc.table_name;
        """))
        
        fkeys = result.fetchall()
        if fkeys:
            print("\nForeign Keys:")
            for row in fkeys:
                print(f"  - {row[1]}.{row[2]} -> {row[3]}.{row[4]}")
        
        # Check indexes
        result = await conn.execute(text("""
            SELECT
                indexname,
                tablename
            FROM pg_indexes
            WHERE tablename IN ('suppliers', 'customers', 'supplier_audit_logs', 'customer_audit_logs')
            ORDER BY tablename, indexname;
        """))
        
        indexes = result.fetchall()
        if indexes:
            print("\nIndexes:")
            for row in indexes:
                print(f"  - {row[1]}: {row[0]}")

if __name__ == "__main__":
    try:
        print("="*50)
        print("KONTAKTREGISTER Database Verification")
        print("="*50)
        print()
        
        asyncio.run(verify_tables())
        
        print("\n" + "="*50)
        print("✓ Verification Complete!")
        print("="*50)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
