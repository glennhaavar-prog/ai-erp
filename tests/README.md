# Tests Directory

This directory contains all testing infrastructure for the AI-ERP system.

## Structure

```
tests/
├── smoke/                  # Smoke tests (quick sanity checks)
│   ├── backend_smoke.sh
│   ├── frontend_smoke.sh
│   └── run_all_smoke_tests.sh
├── unit/                   # Unit tests (coming soon)
├── integration/            # Integration tests (coming soon)
├── e2e/                    # End-to-end tests (coming soon)
└── README.md              # This file
```

---

## Quick Start

### Run All Smoke Tests

```bash
cd tests/smoke
./run_all_smoke_tests.sh
```

This runs both backend and frontend smoke tests in sequence.

### Run Individual Smoke Tests

**Backend only:**
```bash
cd tests/smoke
./backend_smoke.sh
```

**Frontend only:**
```bash
cd tests/smoke
./frontend_smoke.sh
```

---

## Smoke Tests

**Purpose:** Quick sanity checks that critical functionality works  
**Duration:** < 30 seconds  
**When to run:** Before every deploy, after major changes

**What they test:**
- ✅ Backend health endpoint
- ✅ Critical API endpoints (tenants, clients, dashboard)
- ✅ Frontend accessibility
- ✅ TypeScript type checking
- ✅ ESLint validation

---

## Unit Tests (Coming Soon)

**Purpose:** Test individual functions and components  
**Tools:** pytest (backend), Jest (frontend)

**Directory structure:**
```
tests/unit/
├── backend/
│   ├── test_dashboard.py
│   ├── test_models.py
│   └── test_utils.py
└── frontend/
    ├── components/
    ├── contexts/
    └── utils/
```

**Run backend unit tests:**
```bash
cd backend
pytest tests/unit/
```

**Run frontend unit tests:**
```bash
cd frontend
npm test
```

---

## Integration Tests (Coming Soon)

**Purpose:** Test interactions between modules  
**Tools:** pytest + TestClient (backend), MSW (frontend)

**Examples:**
- API endpoint returns correct data from database
- Context providers fetch and cache correctly
- Database transactions commit properly

**Run integration tests:**
```bash
cd backend
pytest tests/integration/
```

---

## E2E Tests (Coming Soon)

**Purpose:** Test complete user journeys  
**Tools:** Playwright or Cypress

**Directory structure:**
```
tests/e2e/
├── critical-flows.spec.ts
├── client-dashboard.spec.ts
└── multi-client-mode.spec.ts
```

**Example test:**
```typescript
test('can load client list and navigate', async ({ page }) => {
  await page.goto('http://localhost:3002');
  await expect(page.locator('text=Klientoversikt')).toBeVisible();
  await page.click('text=Bergen Byggeservice');
  await expect(page).toHaveURL(/clients/);
});
```

**Run E2E tests:**
```bash
cd frontend
npx playwright test
```

---

## Test Data

All tests should use **demo data** or **fixtures**.

**Backend fixtures:**
- Use `seed_demo_data.py` for consistent test data
- Create test-specific fixtures with `@pytest.fixture`

**Frontend fixtures:**
- Mock API responses with MSW
- Use React Testing Library's `render()` with providers

---

## CI/CD Integration

### GitHub Actions (Future)

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run smoke tests
        run: ./tests/smoke/run_all_smoke_tests.sh
      - name: Run unit tests
        run: |
          cd backend && pytest
          cd frontend && npm test
```

---

## Contributing

When adding new tests:

1. **Choose the right level:**
   - Unit: Single function/component
   - Integration: Multiple modules
   - E2E: Full user flow

2. **Name tests clearly:**
   ```python
   def test_should_calculate_urgent_items_correctly():
       ...
   ```

3. **Keep tests isolated:**
   - Don't depend on other tests
   - Clean up after yourself

4. **Document edge cases:**
   ```python
   # Test handles empty client list
   # Test handles invalid tenant ID
   # Test handles network timeout
   ```

---

## Resources

- [TESTING_STRATEGY.md](../TESTING_STRATEGY.md) - Full testing documentation
- [PRE_DEPLOY_CHECKLIST.md](../PRE_DEPLOY_CHECKLIST.md) - Deployment checklist

---

**Questions?** Check `TESTING_STRATEGY.md` or ask the team!
