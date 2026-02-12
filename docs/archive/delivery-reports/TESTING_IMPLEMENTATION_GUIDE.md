# Testing Implementation Guide

**Quick start guide for implementing tests in the AI-ERP system**

---

## ✅ What's Already Set Up

1. **Smoke Tests** - Ready to use!
   ```bash
   cd tests/smoke
   ./run_all_smoke_tests.sh
   ```

2. **Pre-Commit Hooks** - Installed at `.git/hooks/pre-commit`
   - Automatically runs linting before commits
   - Can be bypassed with `git commit --no-verify` (not recommended)

3. **Testing Strategy** - See `TESTING_STRATEGY.md` for full documentation

4. **Pre-Deploy Checklist** - See `PRE_DEPLOY_CHECKLIST.md` for deployment verification

---

## 🚀 Next Steps (To Be Implemented)

### 1. Set Up Backend Unit Tests (30 minutes)

**Install dependencies:**
```bash
cd backend
pip install pytest pytest-cov pytest-asyncio faker
```

**Create test structure:**
```bash
mkdir -p tests/unit
touch tests/unit/__init__.py
touch tests/unit/test_dashboard.py
```

**Example test (`tests/unit/test_dashboard.py`):**
```python
import pytest
from app.services.dashboard import calculate_client_statuses

def test_calculate_client_statuses_empty():
    result = calculate_client_statuses([])
    assert result == {}

def test_calculate_client_statuses_with_tasks():
    tasks = [
        {
            "client_id": "client-1",
            "client_name": "Test Client",
            "priority": "high",
            "category": "invoicing",
            "confidence": 85
        }
    ]
    result = calculate_client_statuses(tasks)
    assert "client-1" in result
    assert result["client-1"]["urgent_items"] == 1
```

**Run tests:**
```bash
cd backend
pytest
pytest --cov=app  # With coverage
```

---

### 2. Set Up Frontend Unit Tests (30 minutes)

**Install dependencies:**
```bash
cd frontend
npm install --save-dev jest @testing-library/react @testing-library/jest-dom ts-jest
```

**Create Jest config (`frontend/jest.config.js`):**
```javascript
const nextJest = require('next/jest')

const createJestConfig = nextJest({
  dir: './',
})

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
}

module.exports = createJestConfig(customJestConfig)
```

**Create setup file (`frontend/jest.setup.js`):**
```javascript
import '@testing-library/jest-dom'
```

**Create test (`frontend/__tests__/components/ClientListDashboard.test.tsx`):**
```typescript
import { render, screen } from '@testing-library/react'
import { ClientListDashboard } from '@/components/ClientListDashboard'

// Mock TenantContext
jest.mock('@/contexts/TenantContext', () => ({
  useTenant: () => ({
    tenantId: 'test-tenant',
    tenantName: 'Test Tenant',
    isLoading: false,
    error: null,
  }),
}))

test('renders loading state', () => {
  render(<ClientListDashboard />)
  expect(screen.getByText(/laster klienter/i)).toBeInTheDocument()
})
```

**Add test script to `package.json`:**
```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage"
  }
}
```

**Run tests:**
```bash
cd frontend
npm test
```

---

### 3. Set Up E2E Tests with Playwright (45 minutes)

**Install Playwright:**
```bash
cd frontend
npm install --save-dev @playwright/test
npx playwright install
```

**Create Playwright config (`frontend/playwright.config.ts`):**
```typescript
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  use: {
    baseURL: 'http://localhost:3002',
    trace: 'on-first-retry',
  },
  webServer: {
    command: 'npm run dev -- -p 3002',
    port: 3002,
    reuseExistingServer: true,
  },
})
```

**Create E2E test directory:**
```bash
mkdir -p frontend/e2e
```

**Create test (`frontend/e2e/critical-flows.spec.ts`):**
```typescript
import { test, expect } from '@playwright/test'

test('homepage loads and shows client list', async ({ page }) => {
  await page.goto('/')
  
  // Wait for client list to load
  await expect(page.locator('text=Klientoversikt')).toBeVisible()
  
  // Check that we have clients
  const clientRows = page.locator('[class*="client"]')
  await expect(clientRows.first()).toBeVisible()
})

test('can navigate to client dashboard', async ({ page }) => {
  await page.goto('/')
  
  // Click on a client
  await page.click('text=Bergen Byggeservice')
  
  // Should navigate to client page
  await expect(page).toHaveURL(/clients/)
})
```

**Run E2E tests:**
```bash
cd frontend
npx playwright test                # Headless
npx playwright test --headed       # With browser
npx playwright test --ui           # Interactive UI
```

---

### 4. Set Up Backend Integration Tests (30 minutes)

**Create test structure:**
```bash
mkdir -p backend/tests/integration
touch backend/tests/integration/__init__.py
touch backend/tests/integration/test_api.py
```

**Create test (`backend/tests/integration/test_api.py`):**
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_get_clients(client):
    response = client.get("/api/clients/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_get_tenant_demo(client):
    response = client.get("/api/tenants/demo")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "name" in data
    assert data["is_demo"] == True
```

**Run integration tests:**
```bash
cd backend
pytest tests/integration/
```

---

## 📊 Measuring Progress

### Check Test Coverage

**Backend:**
```bash
cd backend
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

**Frontend:**
```bash
cd frontend
npm test -- --coverage
# Open coverage/lcov-report/index.html
```

**Goal:** 70%+ coverage for business logic

---

## 🔄 CI/CD Integration (Future)

### GitHub Actions Workflow (`.github/workflows/tests.yml`)

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install backend dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run backend tests
        run: |
          cd backend
          pytest --cov=app
      
      - name: Set up Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '18'
      
      - name: Install frontend dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Run frontend tests
        run: |
          cd frontend
          npm test
      
      - name: Run smoke tests
        run: ./tests/smoke/run_all_smoke_tests.sh
```

---

## 🐛 Testing Workflow for Bug Fixes

When you find a bug:

1. **Write a failing test** that reproduces the bug
2. **Run the test** - it should fail
3. **Fix the code**
4. **Run the test again** - it should pass
5. **Commit both test and fix together**

Example:
```bash
# Found bug: ClientListDashboard infinite loading

# 1. Write test
echo "test('stops loading when error occurs')" >> tests/components/ClientListDashboard.test.tsx

# 2. Verify it fails
npm test

# 3. Fix the code
# ... edit ClientListDashboard.tsx ...

# 4. Verify it passes
npm test

# 5. Commit
git add tests/ src/components/
git commit -m "fix: Stop infinite loading in ClientListDashboard

- Added error state handling
- Added test for error scenarios
- Added retry button
"
```

---

## 📚 Resources

- **Documentation:**
  - [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) - Full strategy
  - [PRE_DEPLOY_CHECKLIST.md](./PRE_DEPLOY_CHECKLIST.md) - Deployment checklist
  - [tests/README.md](./tests/README.md) - Tests directory guide

- **External:**
  - [Pytest Documentation](https://docs.pytest.org/)
  - [Jest Documentation](https://jestjs.io/)
  - [Playwright Documentation](https://playwright.dev/)
  - [React Testing Library](https://testing-library.com/react)

---

## ❓ FAQ

### Q: Do I need to write tests for everything?

**A:** No. Focus on:
- Business logic
- Bug fixes
- Critical user flows
- Complex algorithms

Skip tests for:
- Simple getters/setters
- Framework code
- Generated code

---

### Q: My tests are slow. What do I do?

**A:**
- Mock external dependencies (API calls, databases)
- Use test database with fixtures
- Run unit tests frequently, integration tests less often
- Use `pytest -k "test_name"` to run specific tests

---

### Q: How do I test React components with contexts?

**A:** Wrap your component in a test provider:
```typescript
import { TenantProvider } from '@/contexts/TenantContext'

render(
  <TenantProvider>
    <YourComponent />
  </TenantProvider>
)
```

Or mock the context:
```typescript
jest.mock('@/contexts/TenantContext', () => ({
  useTenant: () => ({ tenantId: 'test', isLoading: false })
}))
```

---

### Q: Tests pass locally but fail in CI?

**A:** Common issues:
- Environment variables not set
- Database not seeded
- Ports already in use
- Timing issues (use proper waits)

---

## 🎯 Success Metrics

You'll know testing is working when:

- ✅ Smoke tests run in < 30 seconds
- ✅ Team catches bugs before Glenn does
- ✅ Deployments happen confidently
- ✅ Regression bugs are rare
- ✅ Code coverage > 70%

---

**Remember:** Tests are an investment. They slow you down initially but speed you up long-term by catching bugs early.

Happy testing! 🧪
