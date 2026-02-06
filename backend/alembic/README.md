# Alembic Migrations

This directory contains database migration files for the Kontali ERP system.

## Directory Structure

```
alembic/
├── versions/           # Migration files (one per migration)
├── env.py             # Alembic environment configuration
├── script.py.mako     # Template for generating new migrations
└── README.md          # This file
```

## Migration Files

### Current Migrations

| Revision | Created | Description |
|----------|---------|-------------|
| 001 | 2025-02-05 10:35 | Initial schema - All 16 core tables |

## Creating New Migrations

### Manual Migration

```bash
# Create a new empty migration
alembic revision -m "add_new_feature"

# Edit the generated file in versions/
# Implement upgrade() and downgrade() functions
```

### Auto-generate from Model Changes

```bash
# Alembic will detect model changes and generate migration
alembic revision --autogenerate -m "add_column_to_users"

# IMPORTANT: Always review auto-generated migrations!
# They may not catch everything (especially data migrations)
```

## Running Migrations

```bash
# Check current version
alembic current

# View pending migrations
alembic history

# Upgrade to latest
alembic upgrade head

# Upgrade to specific revision
alembic upgrade 001

# Downgrade one step
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade 001

# Downgrade to base (remove all)
alembic downgrade base
```

## Testing Migrations

### Dry Run (SQL Preview)

```bash
# Preview SQL without executing
alembic upgrade head --sql > preview.sql
less preview.sql
```

### Verification Script

```bash
# Run verification checks
python verify_migration.py
```

## Best Practices

### 1. Always Test First

```bash
# On development database
alembic upgrade head

# Verify with tests
pytest tests/test_database.py

# If OK, apply to staging
```

### 2. Reversible Migrations

Always implement both `upgrade()` and `downgrade()`:

```python
def upgrade() -> None:
    op.add_column('users', sa.Column('phone', sa.String(50)))

def downgrade() -> None:
    op.drop_column('users', 'phone')
```

### 3. Data Migrations

For data changes, use bulk operations:

```python
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # Schema change
    op.add_column('users', sa.Column('status', sa.String(20)))
    
    # Data migration
    connection = op.get_bind()
    connection.execute(
        sa.text("UPDATE users SET status = 'active' WHERE is_active = true")
    )
```

### 4. Tenant Safety

Always include tenant_id/client_id in WHERE clauses for data migrations:

```python
# ❌ BAD - affects all tenants
connection.execute(
    sa.text("UPDATE users SET role = 'admin' WHERE email = 'admin@example.com'")
)

# ✅ GOOD - only affects specific tenant
connection.execute(
    sa.text("""
        UPDATE users SET role = 'admin' 
        WHERE email = 'admin@example.com' 
        AND tenant_id = :tenant_id
    """),
    {"tenant_id": "some-uuid"}
)
```

### 5. Indexes on Large Tables

Create indexes concurrently in production:

```python
def upgrade() -> None:
    # Use postgresql_concurrently for production
    op.create_index(
        'ix_vendor_invoices_large',
        'vendor_invoices',
        ['client_id', 'invoice_date'],
        postgresql_concurrently=True
    )
```

### 6. Foreign Key Constraints

Be careful with CASCADE deletes:

```python
# ✅ GOOD - Prevent accidental deletion
sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='RESTRICT')

# ⚠️  USE WITH CAUTION - Auto-delete child records
sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE')
```

## Troubleshooting

### Migration Failed Mid-Way

```bash
# Check which migrations were applied
alembic current

# If partially applied, fix the issue and resume
alembic upgrade head

# If migration is broken, rollback
alembic downgrade -1

# Fix the migration file, then upgrade again
alembic upgrade head
```

### Merge Conflicts (Multiple Branches)

```bash
# Check for multiple heads
alembic heads

# If multiple heads exist, merge them
alembic merge -m "merge branches" head1 head2
```

### Production Deployment

```bash
# 1. Backup database first!
pg_dump ai_erp > backup_before_migration.sql

# 2. Test migration on staging
alembic upgrade head

# 3. If successful, deploy to production
alembic upgrade head

# 4. If issues occur, rollback
alembic downgrade -1

# 5. Restore backup if needed
psql ai_erp < backup_before_migration.sql
```

## Migration Checklist

Before deploying a migration to production:

- [ ] Migration tested on development database
- [ ] Upgrade and downgrade both work
- [ ] No data loss in downgrade (or documented)
- [ ] All foreign keys have proper CASCADE/RESTRICT
- [ ] Indexes created for new columns used in WHERE/JOIN
- [ ] tenant_id/client_id added to all new tables
- [ ] Verification script passes
- [ ] Code review completed
- [ ] Database backup taken
- [ ] Staging deployment successful
- [ ] Production maintenance window scheduled

## Useful Queries

### Check Migration Status

```sql
-- Current version
SELECT * FROM alembic_version;

-- List all tables
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- List all indexes
SELECT indexname, tablename FROM pg_indexes 
WHERE schemaname = 'public' 
ORDER BY tablename, indexname;

-- List all foreign keys
SELECT 
    tc.table_name, 
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
ORDER BY tc.table_name;
```

## Support

For issues with migrations:

1. Check `MIGRATIONS_COMPLETE.md` for common problems
2. Review Alembic docs: https://alembic.sqlalchemy.org/
3. Check SQLAlchemy docs: https://docs.sqlalchemy.org/
4. Run `verify_migration.py` for diagnostics

---

**Last Updated:** 2025-02-05  
**Current Version:** 001  
**Total Migrations:** 1
