# AI-ERP Testing Strategy

**Version:** 1.0  
**Last Updated:** 2026-02-08  
**Owner:** Development Team

---

## Executive Summary

This document outlines the systematic testing strategy for the AI-ERP system. The goal is to ensure quality, catch regressions early, and give the team confidence to ship rapidly without manual QA bottlenecks.

**Key Principle:** *If the team can't find issues themselves through systematic testing, the project will take too long (because Glenn has to point them out).*

---

## Testing Philosophy

### The Testing Pyramid

We follow the classic testing pyramid approach:

```
        /\
       /  \     E2E Tests (10%)
      /____\    - Critical user flows
     /      \   - Happy paths only
    /________\  Integration Tests (30%)
   /          \ - API endpoints
  /____________\- Database interactions
 /              \ Unit Tests (60%)
/______________\ - Business logic
                  - Utilities
                  - Components
```

**Why this matters:**
- **Unit tests** are fast, cheap, and catch logic bugs
- **Integration tests** ensure modules work together
- **E2E tests** validate critical user journeys

---

## Testing Levels

### 1. Unit Testing

**What:** Test individual functions, components, and classes in isolation

**Tools:**
- **Backend:** `pytest` (Python)
- **Frontend:** `Jest` + `React Testing Library`

**Coverage Goal:** 70%+ for business logic

**Examples:**
- `calculate_client_statuses()` function
- Invoice validation logic
- Date formatting utilities
- React component rendering

**When:** Before every commit (pre-commit hook)

**Backend Example:**
```python
# tests/unit/test_dashboard.py
def test_calculate_client_statuses():
    tasks = [
        {"client_id": "1", "priority": "high"},
        {"client_id": "1", "priority": "low"},
    ]
    result = calculate_client_statuses(tasks)
    assert result["1"]["urgent_items"] == 1
```

**Frontend Example:**
```typescript
// __tests__/components/ClientListDashboard.test.tsx
test('renders loading state', () => {
  render(<ClientListDashboard />);
  expect(screen.getByText(/laster klienter/i)).toBeInTheDocument();
});
```

---

### 2. Integration Testing

**What:** Test interactions between modules, APIs, and database

**Tools:**
- **Backend:** `pytest` with `TestClient` (FastAPI)
- **Frontend:** `Jest` with mocked API calls
- **Database:** Test database with fixtures

**Coverage Goal:** All critical API endpoints

**Examples:**
- GET `/api/clients/` returns correct data
- POST `/api/tasks/` creates task in database
- Dashboard aggregation logic with real data
- Context providers fetch and update correctly

**When:** Before every deploy

**Backend Example:**
```python
# tests/integration/test_api.py
def test_get_clients(client):
    response = client.get("/api/clients/")
    assert response.status_code == 200
    assert len(response.json()) > 0
```

---

### 3. End-to-End (E2E) Testing

**What:** Test complete user flows from frontend to backend

**Tools:**
- **Playwright** (preferred for Next.js)
- Or **Cypress** (alternative)

**Coverage Goal:** 5-10 critical user journeys

**Examples:**
- User loads homepage → sees client list
- User clicks client → sees client dashboard
- User switches Multi/Klient mode → UI updates
- User submits invoice → appears in queue

**When:** Before production deploy, weekly regression

**Example:**
```typescript
// e2e/critical-flows.spec.ts
test('can load and navigate client list', async ({ page }) => {
  await page.goto('http://localhost:3002');
  await expect(page.locator('text=Klientoversikt')).toBeVisible();
  await page.click('text=Bergen Byggeservice');
  await expect(page).toHaveURL(/clients/);
});
```

---

### 4. Smoke Tests

**What:** Quick sanity checks that critical paths work

**When:** After every deploy, before accepting changes

**Duration:** < 30 seconds

**Examples:**
- Backend health check responds
- All API endpoints return 2xx
- Frontend loads without errors
- Database connection works

**Implementation:** See `tests/smoke/` directory

---

### 5. Regression Testing

**What:** Ensure old features still work after changes

**Strategy:**
- Build regression test suite from bug reports
- Add test for every fixed bug (so it never comes back)
- Run full suite before major releases

**Tools:**
- Automated: Playwright/Cypress suite
- Manual: Pre-deploy checklist (see `PRE_DEPLOY_CHECKLIST.md`)

---

## Testing Tools & Frameworks

### Backend (Python/FastAPI)

| Tool | Purpose | Installation |
|------|---------|--------------|
| **pytest** | Test runner | `pip install pytest` |
| **pytest-cov** | Coverage reports | `pip install pytest-cov` |
| **pytest-asyncio** | Async test support | `pip install pytest-asyncio` |
| **httpx** | API testing | `pip install httpx` (FastAPI TestClient) |
| **faker** | Test data generation | `pip install faker` |

**Run tests:**
```bash
cd backend
pytest                          # Run all tests
pytest --cov=app               # With coverage
pytest tests/unit/             # Only unit tests
pytest -v -s                   # Verbose with print statements
```

---

### Frontend (Next.js/React/TypeScript)

| Tool | Purpose | Installation |
|------|---------|--------------|
| **Jest** | Test runner | `npm install --save-dev jest` |
| **React Testing Library** | Component testing | `npm install --save-dev @testing-library/react` |
| **ts-jest** | TypeScript support | `npm install --save-dev ts-jest` |
| **MSW** | API mocking | `npm install --save-dev msw` |

**Run tests:**
```bash
cd frontend
npm test                       # Run all tests
npm test -- --coverage         # With coverage
npm test -- --watch           # Watch mode
```

---

### E2E Testing

| Tool | Purpose | Installation |
|------|---------|--------------|
| **Playwright** | E2E automation | `npm install --save-dev @playwright/test` |
| **Cypress** | Alternative E2E | `npm install --save-dev cypress` |

**Run E2E:**
```bash
cd frontend
npx playwright test            # Headless
npx playwright test --headed   # With browser
npx playwright test --ui       # Interactive UI
```

---

## Continuous Testing Strategy

### Pre-Commit (Developer)

**Goal:** Catch issues before they enter git history

**Checks:**
1. Linting (eslint/prettier/ruff)
2. Type checking (TypeScript/mypy)
3. Unit tests (fast only)

**Implementation:** Husky pre-commit hooks (see `.husky/pre-commit`)

---

### Pre-Push (Developer)

**Goal:** Ensure changes don't break main branch

**Checks:**
1. All unit tests pass
2. Integration tests pass
3. No console errors in dev mode

---

### Pre-Deploy (Team Lead)

**Goal:** Verify system is production-ready

**Checks:**
1. ✅ Smoke tests pass (backend + frontend)
2. ✅ No console errors in browser
3. ✅ Critical user flows work (manual or E2E)
4. ✅ Database migrations applied
5. ✅ Environment variables set

**Implementation:** Run `PRE_DEPLOY_CHECKLIST.md`

---

### Post-Deploy (Monitoring)

**Goal:** Catch production issues immediately

**Checks:**
1. Health endpoint responds
2. Error rate < 1%
3. Response time < 500ms
4. No critical logs

**Tools:**
- Application logs (`/tmp/backend.log`, `/tmp/frontend.log`)
- Health check: `curl http://localhost:8000/health`

---

## Smoke Testing

Smoke tests are lightweight, fast sanity checks that verify the system is fundamentally operational.

### Backend Smoke Tests

**Location:** `tests/smoke/backend_smoke.sh`

**Checks:**
- Health endpoint responds
- Tenants API works
- Clients API returns data
- Dashboard API returns data

**Run:**
```bash
cd tests/smoke
chmod +x backend_smoke.sh
./backend_smoke.sh
```

---

### Frontend Smoke Tests

**Location:** `tests/smoke/frontend_smoke.sh`

**Checks:**
- Homepage loads (HTTP 200)
- Build succeeds without errors
- No TypeScript errors

**Run:**
```bash
cd tests/smoke
chmod +x frontend_smoke.sh
./frontend_smoke.sh
```

---

## Load & Performance Testing

### When to Run

- Before major releases
- After infrastructure changes
- Monthly regression

### Tools

- **Locust** (Python-based load testing)
- **k6** (JavaScript-based, Grafana)

### Benchmarks

| Metric | Target | Critical |
|--------|--------|----------|
| **API Response Time** | < 200ms | < 500ms |
| **Page Load Time** | < 2s | < 5s |
| **Concurrent Users** | 50+ | 20+ |
| **Error Rate** | < 0.1% | < 1% |

**Example:**
```bash
# Install locust
pip install locust

# Run load test
cd tests/load
locust -f locustfile.py --host http://localhost:8000
```

---

## Security Testing

### OWASP Top 10 Checks

1. **SQL Injection** - Use parameterized queries (SQLAlchemy ORM)
2. **XSS** - Sanitize user input (React escapes by default)
3. **Authentication** - JWT tokens, secure sessions
4. **Authorization** - Role-based access control (RBAC)
5. **Sensitive Data Exposure** - Encrypt secrets, use HTTPS

### Tools

- **Bandit** (Python security linter)
- **npm audit** (Node.js vulnerability scanner)
- **OWASP ZAP** (Dynamic security testing)

**Run security checks:**
```bash
# Backend
pip install bandit
bandit -r app/

# Frontend
npm audit
npm audit fix
```

---

## Test Data Strategy

### Development Data

- **Use demo data** from `seed_demo_data.py`
- **Faker library** for generating realistic test data
- **Fixtures** for consistent test data

### Test Isolation

- Each test should create its own data
- Clean up after tests (fixtures/teardown)
- Use separate test database

**Example fixture:**
```python
@pytest.fixture
def test_client():
    return {
        "id": str(uuid.uuid4()),
        "name": "Test Client AS",
        "org_number": "999999999",
        "is_demo": True,
    }
```

---

## Measuring Testing Effectiveness

### Key Metrics

| Metric | Goal | How to Measure |
|--------|------|----------------|
| **Code Coverage** | 70%+ | `pytest --cov`, `jest --coverage` |
| **Bug Escape Rate** | < 5% | Bugs found in prod / total bugs |
| **Test Execution Time** | < 5 min | CI/CD pipeline duration |
| **Flaky Test Rate** | < 1% | Tests that fail intermittently |
| **Defect Detection Rate** | High | Bugs found in testing / total bugs |

### Coverage Reports

**Backend:**
```bash
cd backend
pytest --cov=app --cov-report=html
# Open htmlcov/index.html
```

**Frontend:**
```bash
cd frontend
npm test -- --coverage
# Open coverage/lcov-report/index.html
```

---

## Testing Best Practices

### ✅ DO

- Write tests BEFORE fixing bugs (TDD)
- Keep tests small and focused
- Use descriptive test names: `test_should_reject_invalid_email()`
- Mock external dependencies (APIs, databases)
- Run tests locally before pushing
- Add tests for every bug fix

### ❌ DON'T

- Write tests that depend on each other
- Test implementation details (test behavior, not code)
- Skip flaky tests (fix them!)
- Hardcode test data (use fixtures/factories)
- Ignore failing tests
- Test framework code (React, FastAPI)

---

## Resources & References

### Documentation

- [Playwright Docs](https://playwright.dev/)
- [Jest Docs](https://jestjs.io/)
- [Pytest Docs](https://docs.pytest.org/)
- [React Testing Library](https://testing-library.com/react)

### Best Practices

1. **Test Pyramid:** [Martin Fowler's Blog](https://martinfowler.com/bliki/TestPyramid.html)
2. **Testing Best Practices:** [Google Testing Blog](https://testing.googleblog.com/)
3. **ERP Testing:** [ElevatIQ - Top 10 ERP Testing Best Practices](https://www.elevatiq.com/post/top-erp-testing-best-practices/)

---

## Getting Started

### 1. Set up testing infrastructure

```bash
# Backend
cd backend
pip install pytest pytest-cov pytest-asyncio faker

# Frontend
cd frontend
npm install --save-dev jest @testing-library/react ts-jest

# E2E
cd frontend
npm install --save-dev @playwright/test
npx playwright install
```

### 2. Run smoke tests

```bash
cd tests/smoke
./backend_smoke.sh
./frontend_smoke.sh
```

### 3. Write your first test

- Pick a bug or feature
- Write a failing test
- Fix the code
- Verify test passes
- Commit both test and fix

---

## Ownership & Maintenance

**Test Strategy Owner:** Lead Developer  
**Review Frequency:** Monthly  
**Update Triggers:** New tools, major bugs, architecture changes

---

## Questions?

If you're unsure what to test or how to test it, ask:
1. **What could go wrong?** (Edge cases, error states)
2. **How would users break this?** (Invalid input, race conditions)
3. **What did we break last time?** (Regression tests)

**Remember:** Tests are documentation. Future-you will thank present-you for writing clear, comprehensive tests.

---

*This document is a living guide. Update it as you learn what works for your team.*
