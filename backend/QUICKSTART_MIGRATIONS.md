# 🚀 Quick Start - Database Migrations

**One-page reference for getting the database up and running FAST.**

---

## ⚡ Super Quick Start (30 seconds)

```bash
cd /home/ubuntu/.openclaw/workspace/ai-erp/backend

# Run the automated setup script
./setup_database.sh

# Done! Database is ready.
```

---

## 📋 Manual Setup (5 minutes)

### 1. Install PostgreSQL
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### 2. Create Database
```bash
sudo -u postgres psql << EOF
CREATE USER erp_user WITH PASSWORD 'erp_password';
CREATE DATABASE ai_erp OWNER erp_user;
GRANT ALL PRIVILEGES ON DATABASE ai_erp TO erp_user;
EOF
```

### 3. Configure Environment
```bash
cp .env.example .env
# DATABASE_URL is already set correctly
```

### 4. Run Migrations
```bash
source venv/bin/activate
alembic upgrade head
```

### 5. Verify
```bash
python verify_migration.py
```

---

## 🔧 Essential Commands

### Check Status
```bash
alembic current          # Show current version
alembic history          # Show all migrations
```

### Run Migrations
```bash
alembic upgrade head     # Apply all migrations
alembic upgrade 001      # Apply specific migration
```

### Rollback
```bash
alembic downgrade -1     # Undo last migration
alembic downgrade base   # Remove all tables
```

### Preview Changes
```bash
alembic upgrade head --sql > preview.sql
```

---

## 🔍 Quick Verification

### Connect to Database
```bash
psql postgresql://erp_user:erp_password@localhost:5432/ai_erp
```

### Inside psql:
```sql
-- List tables (should see 17)
\dt

-- Check migration version
SELECT * FROM alembic_version;

-- Count tables
SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';

-- Exit
\q
```

---

## ✅ What You Get

After running migrations, you'll have:

- ✅ 17 tables (16 core + 1 system)
- ✅ 60 indexes for performance
- ✅ All foreign key constraints
- ✅ Multi-tenant architecture
- ✅ FOR UPDATE SKIP LOCKED support
- ✅ Audit trail for compliance

---

## 🆘 Troubleshooting

### PostgreSQL not running?
```bash
sudo systemctl start postgresql
pg_isready -h localhost
```

### Permission denied?
```bash
sudo -u postgres psql
GRANT ALL PRIVILEGES ON DATABASE ai_erp TO erp_user;
```

### Tables already exist?
```bash
# Stamp current version
alembic stamp 001
```

### Migration failed?
```bash
# Rollback
alembic downgrade -1

# Fix issue, then retry
alembic upgrade head
```

---

## 📚 Full Documentation

- **Complete guide:** `MIGRATIONS_COMPLETE.md`
- **Best practices:** `alembic/README.md`
- **Delivery report:** `MIGRATION_DELIVERY.md`

---

## 🎯 Migration Status

| Item | Status |
|------|--------|
| Alembic configured | ✅ |
| Migration 001 created | ✅ |
| All 17 tables defined | ✅ |
| All indexes included | ✅ |
| SQL validated | ✅ |
| Ready for production | ✅ |

---

## 🚀 Next Steps After Migration

1. **Verify:** `python verify_migration.py`
2. **Seed data:** Create initial tenants and users
3. **Test app:** `uvicorn app.main:app --reload`
4. **Access API:** `http://localhost:8000/docs`

---

**TL;DR:** Run `./setup_database.sh` and you're done. ✅
