# OpsConductor Tests

This directory contains all automated tests for the OpsConductor platform.

## Structure

```
tests/
├── api/                    # API integration tests
│   └── api-comprehensive.spec.ts
├── e2e/                    # End-to-end tests
│   ├── pages/             # Page object models
│   ├── comprehensive.spec.ts
│   ├── smoke-test.spec.ts
│   └── test-data.ts
├── playwright.config.ts   # Test configuration
├── package.json           # Test dependencies
└── README.md              # This file
```

## Quick Start

### Install Dependencies
```bash
cd tests
npm install
```

### Run Tests
```bash
# All tests
npm test

# Smoke tests only
npm run test:smoke

# API tests only  
npm run test:api

# E2E tests only
npm run test:e2e

# With browser UI
npm run test:ui
```

### View Reports
```bash
npm run report
```

## Test Types

### Smoke Tests
Basic functionality verification to ensure the system is operational.

### API Tests
Comprehensive testing of all REST API endpoints including:
- Authentication
- CRUD operations
- Error handling
- Data validation

### E2E Tests
Full user workflow testing including:
- User login/logout
- Job creation and execution
- Target management
- System monitoring

## Development

### Adding New Tests
1. Follow the page object model pattern
2. Use descriptive test names
3. Include proper setup/teardown
4. Add appropriate assertions

### Test Data
Shared test data is located in `test-data.ts`. Use this for consistent test scenarios.

### Page Objects
Page objects are located in `e2e/pages/` and provide reusable methods for interacting with UI elements.

## CI/CD Integration

Tests are configured to run in CI/CD pipelines with:
- Parallel execution
- Retry logic for flaky tests
- HTML reporting
- Trace collection on failures