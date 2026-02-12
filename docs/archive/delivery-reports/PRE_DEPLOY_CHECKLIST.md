# Pre-Deploy Checklist

**Use this checklist before every deployment to production or staging.**

Last Updated: 2026-02-08

---

## 🚀 Pre-Deploy Checklist

### ✅ Automated Tests

Run all smoke tests to verify system health:

```bash
cd tests/smoke
./run_all_smoke_tests.sh
```

- [ ] **Backend smoke tests pass**
  - Health check responds
  - Tenants API works
  - Clients API returns data
  - Dashboard API returns data
  - API docs accessible

- [ ] **Frontend smoke tests pass**
  - Homepage loads (HTTP 200)
  - No TypeScript errors
  - ESLint passes
  - Node modules installed

---

### 🧪 Manual Testing

Open the application in your browser and verify:

- [ ] **No console errors** in browser DevTools (F12)
  - Check Console tab for red errors
  - Yellow warnings are OK, red errors are NOT

- [ ] **Critical user flows work:**

  **Multi-Client Mode:**
  - [ ] Can load client list
  - [ ] Clients show correct status (🟢🟡🔴)
  - [ ] Can click on a client
  - [ ] Client dashboard loads

  **Single Client Mode:**
  - [ ] Can switch to "Klient" mode
  - [ ] Can select a client
  - [ ] Dashboard shows client-specific data
  - [ ] Reports section works

  **Navigation:**
  - [ ] Sidebar navigation works
  - [ ] Can switch between Multi/Klient modes
  - [ ] Breadcrumbs display correctly

---

### 🗄️ Backend Verification

- [ ] **Database migrations applied**
  ```bash
  cd backend
  alembic current  # Check current migration
  alembic upgrade head  # Apply any pending migrations
  ```

- [ ] **Environment variables set**
  - Check `.env` file exists
  - Verify `DATABASE_URL` is correct
  - Verify `OPENAI_API_KEY` is set (if using AI features)

- [ ] **Services running**
  ```bash
  # Check processes
  ps aux | grep uvicorn    # Backend
  ps aux | grep "npm.*dev" # Frontend
  ps aux | grep postgres   # Database
  ps aux | grep redis      # Redis (if used)
  ```

- [ ] **Database connectivity**
  ```bash
  # Test database connection
  psql $DATABASE_URL -c "SELECT 1;"
  ```

---

### 🌐 Frontend Verification

- [ ] **Build succeeds without errors**
  ```bash
  cd frontend
  npm run build
  ```
  - Should complete without errors
  - Check for any deprecation warnings

- [ ] **No critical dependencies vulnerabilities**
  ```bash
  cd frontend
  npm audit
  ```
  - Fix high/critical vulnerabilities: `npm audit fix`

---

### 📊 Data Verification

- [ ] **Demo tenant exists**
  ```bash
  curl http://localhost:8000/api/tenants/demo
  ```

- [ ] **Demo clients exist**
  ```bash
  curl http://localhost:8000/api/clients/ | jq 'length'
  ```
  - Should return > 0

- [ ] **Dashboard has data**
  ```bash
  TENANT_ID=$(curl -s http://localhost:8000/api/tenants/demo | jq -r '.id')
  curl "http://localhost:8000/api/dashboard/multi-client/tasks?tenant_id=$TENANT_ID" | jq '.summary'
  ```

---

### 🔒 Security Check

- [ ] **No secrets in code**
  ```bash
  # Search for common secret patterns
  cd /home/ubuntu/.openclaw/workspace/ai-erp
  grep -r "sk-" . --include="*.py" --include="*.ts" --include="*.tsx"
  grep -r "password" . --include=".env"
  ```

- [ ] **CORS configured correctly**
  - Check `app/main.py` CORS settings
  - Verify allowed origins

- [ ] **API keys in environment variables**
  - Not hardcoded in source

---

### 📝 Documentation

- [ ] **CHANGELOG.md updated** (if you have one)
  - List new features
  - List bug fixes
  - List breaking changes

- [ ] **README.md accurate**
  - Installation steps work
  - Environment variables documented

---

### 🎛️ Configuration

- [ ] **Correct environment selected**
  - Development: `NODE_ENV=development`
  - Production: `NODE_ENV=production`

- [ ] **Ports not conflicting**
  - Backend: 8000
  - Frontend: 3002 (dev) or 3000 (prod)
  - Database: 5432

---

## 🚨 Critical Issues (MUST FIX)

**Do NOT deploy if any of these are true:**

- ❌ Smoke tests fail
- ❌ Console shows React errors
- ❌ Users can't log in / view clients
- ❌ Database migrations fail
- ❌ Build fails
- ❌ Critical security vulnerabilities (npm audit)

---

## ⚠️ Known Issues (Document & Monitor)

If any issues exist but are non-blocking:

- List them here
- Add monitoring
- Create GitHub issues
- Plan to fix in next sprint

Example:
- [ ] Some TypeScript warnings in ClientContext (non-critical)
- [ ] Slow dashboard load for tenants with 100+ clients (monitoring)

---

## ✅ Deployment Approved

**Deployed by:** _________________  
**Date:** _________________  
**Version/Commit:** _________________

**Sign-off:**
- [ ] All checklist items completed
- [ ] Known issues documented
- [ ] Team notified of deployment

---

## 📞 Rollback Plan

**If something goes wrong after deployment:**

1. **Immediate rollback:**
   ```bash
   git revert HEAD
   git push origin main
   ```

2. **Restart services:**
   ```bash
   # Backend
   pkill -f uvicorn
   cd backend && uvicorn app.main:app --reload &

   # Frontend
   pkill -f "npm.*dev"
   cd frontend && npm run dev -- -p 3002 &
   ```

3. **Notify team:**
   - Post in Slack/Discord
   - Update status page
   - Create incident report

---

## 📚 Additional Resources

- **TESTING_STRATEGY.md** - Full testing documentation
- **tests/smoke/** - Smoke test scripts
- **Backend logs:** `/tmp/backend.log`
- **Frontend logs:** `/tmp/frontend.log`

---

**Remember:** It's better to delay deployment than to ship broken code. Take your time and verify thoroughly! ✅
