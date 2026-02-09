# 🚀 AI-Agent ERP Backend - Setup Guide

Complete setup guide for development and production environments.

---

## 📋 Prerequisites

### Required Software

- **Python 3.12+** (tested on 3.12.x)
- **PostgreSQL 14+** (database)
- **Redis 7+** (caching & task queue)
- **Git** (version control)

### System Dependencies (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y \
    python3.12 \
    python3.12-venv \
    python3-pip \
    postgresql \
    postgresql-contrib \
    redis-server \
    build-essential \
    libpq-dev \
    tesseract-ocr \
    tesseract-ocr-nor \
    poppler-utils
```

### Optional but Recommended

- **AWS CLI** (for S3 document storage)
- **Docker** (for containerized deployment)

---

## 🔧 Step-by-Step Setup

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd ai-erp/backend
```

### 2. Create Virtual Environment

**IMPORTANT:** Always use a virtual environment to avoid system-wide package conflicts.

```bash
# Create venv
python3.12 -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

### 3. Install Dependencies

```bash
# Production dependencies only
pip install -r requirements.txt

# OR: Development setup (includes testing tools)
pip install -r requirements-dev.txt
```

**Verify critical versions:**

```bash
pip show anthropic httpx fastapi sqlalchemy uvicorn
```

Expected versions:
- `anthropic==0.39.0` ✅
- `httpx==0.27.0` ✅
- `fastapi==0.109.0` ✅
- `sqlalchemy==2.0.25` ✅
- `uvicorn==0.27.0` ✅

### 4. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit with your configuration
nano .env  # or use your preferred editor
```

**Required Configuration:**

```env
# Database
DATABASE_URL="postgresql+asyncpg://erp_user:erp_password@localhost:5432/ai_erp"

# Redis
REDIS_URL="redis://localhost:6379/0"

# Anthropic API
ANTHROPIC_API_KEY="sk-ant-..." # Get from console.anthropic.com

# Security (CHANGE IN PRODUCTION!)
SECRET_KEY="your-secret-key-min-32-chars-random-string"

# CORS (add your frontend URL)
CORS_ORIGINS="http://localhost:3000,http://localhost:5173"
```

**Optional but recommended:**

```env
# AWS (for document storage)
AWS_ACCESS_KEY=""
AWS_SECRET_KEY=""
AWS_REGION="eu-north-1"
S3_BUCKET_DOCUMENTS="ai-erp-documents"

# Unimicro PEPPOL (for EHF invoicing)
UNIMICRO_API_KEY=""
UNIMICRO_WEBHOOK_SECRET=""
```

### 5. Set Up Database

**Option A: Using setup script (recommended)**

```bash
chmod +x setup_database.sh
./setup_database.sh
```

This will:
- Create PostgreSQL user and database
- Run Alembic migrations
- Set up initial schema

**Option B: Manual setup**

```bash
# Start PostgreSQL service
sudo systemctl start postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE USER erp_user WITH PASSWORD 'erp_password';
CREATE DATABASE ai_erp OWNER erp_user;
GRANT ALL PRIVILEGES ON DATABASE ai_erp TO erp_user;
\c ai_erp
GRANT ALL ON SCHEMA public TO erp_user;
EOF

# Run migrations
alembic upgrade head
```

### 6. Set Up Redis

```bash
# Start Redis service
sudo systemctl start redis-server

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

### 7. Generate Demo Data (Optional)

```bash
python generate_demo_data.py
```

This creates sample:
- Chart of accounts
- Customers and suppliers
- Transactions
- Invoices

### 8. Start the Backend

**Development mode (with auto-reload):**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Production mode:**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Verify it's running:**

- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- GraphQL: http://localhost:8000/graphql

### 9. Start Celery Worker (for async tasks)

In a separate terminal (with venv activated):

```bash
celery -A app.celery.worker worker --loglevel=info
```

---

## ✅ Verification Checklist

After setup, verify everything works:

```bash
# 1. Check Python version
python --version  # Should be 3.12+

# 2. Check dependencies
pip list | grep -E "(anthropic|httpx|fastapi|sqlalchemy)"

# 3. Check database connection
python -c "from app.database import engine; print('DB OK')"

# 4. Check Redis connection
redis-cli ping

# 5. Run tests
pytest tests/ -v

# 6. Check API health
curl http://localhost:8000/api/v1/health
```

---

## 🔄 Common Commands

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# View migration history
alembic history
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_hovedbok_api.py -v

# Run only unit tests (fast)
pytest tests/unit/ -v
```

### Code Quality

```bash
# Format code
black app/ tests/

# Lint code
ruff check app/ tests/

# Type checking
mypy app/
```

---

## 🐛 Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'anthropic'`

**Solution:**
```bash
# Ensure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: `Connection refused` to PostgreSQL

**Solution:**
```bash
# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql  # Auto-start on boot

# Check status
sudo systemctl status postgresql
```

### Issue: `anthropic` version conflict with `httpx`

**Solution:**
This is why we locked versions! Ensure you have:
```bash
pip install anthropic==0.39.0 httpx==0.27.0
```

**DO NOT** upgrade anthropic beyond 0.39.0 until httpx compatibility is verified.

### Issue: Alembic migration fails

**Solution:**
```bash
# Check current database version
alembic current

# View pending migrations
alembic history

# Reset database (⚠️ DESTROYS DATA)
./setup_database.sh
```

### Issue: Redis connection refused

**Solution:**
```bash
# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test connection
redis-cli ping
```

---

## 📦 Dependency Management

### Adding New Dependencies

1. Install package:
   ```bash
   pip install package-name==x.y.z
   ```

2. Update requirements.txt:
   ```bash
   pip freeze | grep package-name >> requirements.txt
   # Then manually organize into correct category
   ```

3. Test thoroughly:
   ```bash
   pytest
   uvicorn app.main:app --reload
   ```

4. Document any special configurations

### Updating Dependencies

**⚠️ CRITICAL:** Do NOT blindly run `pip install --upgrade`

The `anthropic` + `httpx` compatibility issue taught us:

1. **Check compatibility first**:
   - Read package changelogs
   - Check GitHub issues
   - Test in isolated venv

2. **Update one package at a time**:
   ```bash
   pip install package-name==new.version
   pytest  # Verify nothing broke
   ```

3. **Lock the new version**:
   Update `requirements.txt` with exact version

4. **Document breaking changes**:
   Update this SETUP.md if configuration changes

---

## 🚀 Production Deployment

### Environment Preparation

1. **Never use default passwords**
2. **Set `DEBUG=false`**
3. **Use strong `SECRET_KEY`** (min 32 chars, random)
4. **Configure CORS** properly (no wildcards)
5. **Set up SSL/TLS** certificates
6. **Use environment-specific .env** files

### Using Docker (recommended)

```bash
# Build image
docker build -t ai-erp-backend .

# Run container
docker run -d \
  --name erp-backend \
  -p 8000:8000 \
  --env-file .env.production \
  ai-erp-backend
```

### Using systemd (Ubuntu/Debian)

Create `/etc/systemd/system/erp-backend.service`:

```ini
[Unit]
Description=AI-Agent ERP Backend
After=postgresql.service redis.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/path/to/ai-erp/backend
Environment="PATH=/path/to/ai-erp/backend/venv/bin"
ExecStart=/path/to/ai-erp/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable erp-backend
sudo systemctl start erp-backend
```

---

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **GraphQL Playground**: http://localhost:8000/graphql
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/
- **Anthropic API**: https://docs.anthropic.com/

---

## 🆘 Getting Help

1. Check logs: `tail -f backend.log`
2. Review error messages in `/docs` Swagger UI
3. Run health check: `curl http://localhost:8000/api/v1/health`
4. Check service status: `systemctl status postgresql redis-server`

---

**Last Updated:** 2026-02-08  
**Python Version:** 3.12+  
**Critical Locked Versions:** `anthropic==0.39.0`, `httpx==0.27.0`
