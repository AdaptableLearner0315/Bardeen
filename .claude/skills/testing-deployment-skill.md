# Testing & Deployment Skill

A comprehensive workflow for integration testing, E2E testing, local deployment, and production deployment.

---

## Skill Overview

This skill covers the final phases of product development:
- Integration testing between modules
- End-to-end testing of user flows
- Local deployment verification
- Production deployment with git push

---

## Phase 4: Integration & E2E Testing

### Prerequisites

**DO NOT** start testing until:
- ALL modules are complete (per module completion criteria)
- ALL unit tests pass
- Code is merged to main

### Integration Tests

Test cross-module interactions:

```
tests/integration/
├── __init__.py
├── test_module_a_b_integration.py
├── test_module_b_c_integration.py
└── test_full_flow.py
```

#### Integration Test Example

```python
def test_module_integration():
    """Test that Module A correctly integrates with Module B."""
    # Setup
    module_a = ModuleA()
    module_b = ModuleB()

    # Execute
    result_a = module_a.process(data)
    result_b = module_b.consume(result_a)

    # Assert
    assert result_b.status == "success"
    assert result_b.data is not None
```

### E2E Tests

Test complete user flows:

```
tests/e2e/
├── __init__.py
├── test_user_journey_1.py
├── test_user_journey_2.py
└── test_error_scenarios.py
```

#### E2E Test Example

```python
def test_complete_user_flow():
    """Test complete user journey from signup to checkout."""
    # User signs up
    user = create_test_user()

    # User logs in
    session = login(user.email, user.password)

    # User performs actions
    product = browse_catalog(session)
    cart = add_to_cart(session, product)
    order = checkout(session, cart)

    # Verify end state
    assert order.status == "completed"
    assert order.user_id == user.id
```

### Test Completion Criteria

Phase is complete when:
- All integration tests pass
- All E2E tests pass
- No regressions in unit tests
- Performance benchmarks met (if applicable)

---

## Phase 5: Local Deployment

### Build & Deploy Locally

1. **Backend Deployment**:
   ```bash
   # Python/FastAPI
   uvicorn app.main:app --reload --port 8000

   # Node.js/Express
   npm start

   # Go
   go run main.go
   ```

2. **Frontend Deployment**:
   ```bash
   # Next.js
   npm run dev

   # React
   npm start

   # Vue
   npm run serve
   ```

3. **Database Setup**:
   ```bash
   # Run migrations
   alembic upgrade head

   # Seed data (if needed)
   python scripts/seed_db.py
   ```

### Deployment Verification Steps

After deployment:

1. **Verify backend is running**:
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status": "healthy", ...}
   ```

2. **Verify frontend is running**:
   ```bash
   curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
   # Should return: 200
   ```

3. **Run smoke tests**:
   ```bash
   pytest tests/smoke/ -v
   ```

4. **Manual verification**:
   - Open frontend URL in browser
   - Test critical user flows
   - Verify API endpoints
   - Check error handling

### Common Deployment Issues & Fixes

| Issue | Symptom | Fix |
|-------|---------|-----|
| **Missing Tailwind CSS** | `Cannot find module 'tailwindcss'` | `npm install tailwindcss@^3.4.0` |
| **Tailwind v4 PostCSS Error** | `The PostCSS plugin has moved to a separate package` | Downgrade: `npm install tailwindcss@^3.4.0` |
| **Port in use** | `Port 3000 is in use` | Next.js auto-increments or `lsof -ti:3000 \| xargs kill` |
| **Backend port conflict** | `Address already in use` | Use alternate: `--port 8001` |
| **Missing npm dependencies** | `sh: next: command not found` | Run `npm install` first |
| **PostCSS config error** | CSS compilation fails | Check `postcss.config.js` configuration |
| **Database connection** | `Connection refused` | Ensure database is running |
| **Environment variables** | `Missing required env var` | Check `.env` file |

---

## Git Push Protocol

### Pre-Push Checklist

```
┌─────────────────────────────────────────────────────────────────┐
│                    FINAL DEPLOYMENT CHECKLIST                   │
├─────────────────────────────────────────────────────────────────┤
│ ☐ All unit tests pass                                           │
│ ☐ All integration tests pass                                    │
│ ☐ All E2E tests pass                                            │
│ ☐ Local deployment successful                                   │
│ ☐ Smoke tests pass                                              │
│ ☐ Manual testing complete                                       │
│ ☐ CLAUDE.md is up to date                                       │
│ ☐ notes/ directory is complete                                  │
│ ☐ No sensitive data in code                                     │
│ ☐ .gitignore properly configured                                │
│ ☐ User approval for git push                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Git Push Steps

**DO NOT** push until explicit approval:

1. **Ask for permission**:
   > "Application deployed locally and all tests pass. Do you want me to push the code to git?"

2. **If approved, push to remote**:
   ```bash
   # Add all changes
   git add .

   # Commit with descriptive message
   git commit -m "feat: complete MVP implementation

   - All modules implemented and tested
   - Integration and E2E tests passing
   - Local deployment verified"

   # Push to remote
   git push origin main
   ```

3. **Verify push**:
   ```bash
   git log --oneline -5
   git status
   ```

---

## Production Deployment (Optional)

If deploying to production:

### Cloud Platforms

**Vercel (Frontend)**:
```bash
vercel --prod
```

**Heroku (Backend)**:
```bash
heroku create app-name
git push heroku main
```

**AWS**:
```bash
aws deploy push --application-name app-name
```

### Docker Deployment

```bash
# Build image
docker build -t app-name .

# Run container
docker run -p 8000:8000 app-name

# Push to registry
docker push registry/app-name:latest
```

### Post-Deployment Verification

1. Check application logs
2. Monitor error rates
3. Verify all endpoints
4. Test critical paths
5. Set up monitoring/alerts

---

## Quick Reference Commands

```bash
# Testing
pytest tests/integration/ -v
pytest tests/e2e/ -v
pytest tests/smoke/ -v

# Local Deployment
uvicorn app.main:app --reload  # Backend
npm run dev                     # Frontend

# Git Operations
git add .
git commit -m "message"
git push origin main

# Docker
docker build -t app .
docker run -p 8000:8000 app

# Health Checks
curl http://localhost:8000/health
curl http://localhost:3000
```

---

## Invocation

To use this skill, say:
> "Use the testing-deployment skill to test and deploy the application"

Or reference specific phases:
> "Run integration and E2E tests"
> "Deploy the application locally"
> "Push code to git repository"