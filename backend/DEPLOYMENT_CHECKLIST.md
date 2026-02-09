# ✅ Backend Deployment Checklist

Use this checklist for fresh deployments or after dependency updates.

---

## 📦 Pre-Deployment

- [ ] Python 3.12+ installed
- [ ] PostgreSQL 14+ running
- [ ] Redis 7+ running
- [ ] `.env` file configured with production values
- [ ] Secret keys changed from defaults
- [ ] CORS origins configured correctly

---

## 🔧 Installation

```bash
# 1. Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# 2. Install dependencies (exact versions)
pip install -r requirements.txt

# 3. Verify critical versions
pip show anthropic httpx fastapi sqlalchemy uvicorn
```

**Expected versions:**
```
anthropic==0.39.0 ✅
httpx==0.27.0 ✅
fastapi==0.109.0 ✅
sqlalchemy==2.0.25 ✅
uvicorn==0.27.0 ✅
```

```bash
# 4. Check for conflicts
pip check  # Should return: "No broken requirements found."
```

---

## 🗄️ Database Setup

```bash
# 5. Run database setup
./setup_database.sh

# 6. Verify migrations
alembic current  # Should show current revision
alembic history  # Should show all migrations
```

---

## 🧪 Testing

```bash
# 7. Run test imports
python -c "from app.database import engine; print('DB OK')"

# 8. Start backend (test)
uvicorn app.main:app --reload

# 9. Check health endpoint
curl http://localhost:8000/api/v1/health
# Expected: {"status": "healthy", ...}

# 10. Run test suite (if available)
pytest tests/ -v
```

---

## 🚀 Production Start

```bash
# 11. Start production server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# OR: Use systemd service (see SETUP.md)
sudo systemctl start erp-backend
sudo systemctl status erp-backend
```

---

## 🔍 Post-Deployment Verification

- [ ] Backend responds on port 8000
- [ ] `/docs` Swagger UI accessible
- [ ] `/graphql` GraphQL playground works
- [ ] Database connections successful
- [ ] Redis cache accessible
- [ ] No error logs in `backend.log`
- [ ] Celery worker running (if using async tasks)

---

## 🚨 Rollback Plan

If deployment fails:

```bash
# 1. Stop backend
pkill -f uvicorn
# OR: sudo systemctl stop erp-backend

# 2. Rollback database (if needed)
alembic downgrade -1

# 3. Check logs
tail -100 backend.log

# 4. Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

## 📊 Monitoring

After deployment, monitor:
- CPU/Memory usage
- Database connection pool
- Redis memory usage
- API response times
- Error rate in logs
- Celery task queue length

---

## 📞 Support

- Setup issues? → See `SETUP.md`
- Dependency conflicts? → See `DEPENDENCY_LOCK_SUMMARY.md`
- General questions? → See `README.md`

---

**Last Updated:** 2026-02-08
