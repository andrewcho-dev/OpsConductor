# OpsConductor Testing Guide

## Overview
This guide covers testing strategies and procedures for the OpsConductor platform.

## Test Structure

### E2E Tests
Located in `tests/e2e/`:
- **smoke-test.spec.ts** - Basic functionality verification
- **comprehensive.spec.ts** - Full workflow testing

### API Tests  
Located in `tests/api/`:
- **api-comprehensive.spec.ts** - API endpoint testing

### Test Data
- **test-data.ts** - Shared test data and fixtures

## Running Tests

### Prerequisites
```bash
# Install test dependencies
cd tests
npm install
```

### Execute Tests
```bash
# Run all tests
npm test

# Run specific test suite
npm run test:smoke

# Run with UI
npm run test:ui
```

### Test Configuration
Test configuration is managed in `tests/playwright.config.ts` with proper Playwright setup.

## Test Development

### Writing New Tests
1. Follow existing patterns in `tests/e2e/pages/`
2. Use page object model for maintainability
3. Include proper assertions and error handling

### Best Practices
- Keep tests independent and atomic
- Use descriptive test names
- Clean up test data after execution
- Mock external dependencies when appropriate

## Continuous Integration
Tests are designed to run in CI/CD pipelines with proper reporting and artifact collection.