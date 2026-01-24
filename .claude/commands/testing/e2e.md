---
description: Generate end-to-end test scenarios with AI assistance
argument-hint: [user-flow or feature-name]
model: claude-sonnet-4-5-20250929
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, AskUserQuestion
---

Generate E2E tests for: **${ARGUMENTS}**

## What This Command Does

This command generates comprehensive end-to-end (E2E) tests that validate complete user journeys through your application. E2E tests simulate real user behavior, testing the entire stack from UI interactions to backend APIs and databases, ensuring all components work together seamlessly.

**Key Capabilities**:

- Generates browser automation tests (Playwright, Cypress, Selenium)
- Simulates real user interactions (clicks, form inputs, navigation)
- Tests complete user flows (registration, checkout, admin workflows)
- Validates UI elements and user feedback
- Tests across multiple browsers and devices
- Includes visual regression testing

## Step 1: Identify User Flow

Parse arguments to determine what flow to test:

```bash
# Common user flows
case "$ARGUMENTS" in
  *"registration"*|*"signup"*)
    FLOW="user_registration"
    ;;
  *"login"*|*"auth"*)
    FLOW="authentication"
    ;;
  *"checkout"*|*"purchase"*)
    FLOW="e_commerce_checkout"
    ;;
  *"admin"*|*"dashboard"*)
    FLOW="admin_workflow"
    ;;
  *)
    echo "Describe the user flow to test:"
    echo "Example: 'User signs up, creates project, invites team member'"
    read -r USER_FLOW
    ;;
esac
```

## Step 2: Detect E2E Framework

**Check project for E2E testing tools**:

```bash
# Detect framework
if grep -q "playwright" package.json; then
  FRAMEWORK="playwright"
  echo "Using Playwright"
elif grep -q "cypress" package.json; then
  FRAMEWORK="cypress"
  echo "Using Cypress"
elif grep -q "selenium" package.json; then
  FRAMEWORK="selenium"
  echo "Using Selenium WebDriver"
elif grep -q "puppeteer" package.json; then
  FRAMEWORK="puppeteer"
  echo "Using Puppeteer"
else
  # Recommend Playwright (modern, fast, multi-browser)
  echo "No E2E framework detected. Installing Playwright..."
  npm install -D @playwright/test
  npx playwright install
  FRAMEWORK="playwright"
fi
```

## Step 3: Analyze Application Structure

**Map user flow to pages/components**:

```bash
# Find page components
find src/ -name "*Page.tsx" -o -name "*page.ts"

# Find route definitions
grep -r "route\|path\|Router" src/ --include="*.tsx" --include="*.ts" | head -20

# Find form components
find src/ -name "*Form.tsx" -o -name "*form.ts"
```

**Read key pages**:

```javascript
// Read landing page
const landingPage = await Read({ file_path: 'src/pages/LandingPage.tsx' })

// Read signup form
const signupForm = await Read({ file_path: 'src/components/SignupForm.tsx' })

// Read dashboard
const dashboard = await Read({ file_path: 'src/pages/Dashboard.tsx' })
```

## Step 4: Map User Journey

**Create flow diagram**:

```
USER REGISTRATION FLOW:
┌──────────────────────────────────────────────────────┐
│ 1. Landing Page                                      │
│    - Navigate to /                                   │
│    - Verify hero text visible                        │
│    - Click "Sign Up" button                          │
├──────────────────────────────────────────────────────┤
│ 2. Registration Form                                 │
│    - Navigate to /signup                             │
│    - Enter email: test@example.com                   │
│    - Enter password: SecurePass123!                  │
│    - Enter name: Test User                           │
│    - Click "Create Account"                          │
├──────────────────────────────────────────────────────┤
│ 3. Email Verification                                │
│    - Redirect to /verify-email                       │
│    - Display "Check your email" message              │
│    - (In test: auto-verify with test token)          │
├──────────────────────────────────────────────────────┤
│ 4. Onboarding                                        │
│    - Navigate to /onboarding                         │
│    - Select preferences                              │
│    - Complete profile                                │
│    - Click "Get Started"                             │
├──────────────────────────────────────────────────────┤
│ 5. Dashboard                                         │
│    - Navigate to /dashboard                          │
│    - Verify user name displayed                      │
│    - Verify welcome message                          │
│    - Verify navigation menu accessible               │
└──────────────────────────────────────────────────────┘
```

## Step 5: Generate E2E Test - Playwright

**Create comprehensive Playwright test**:

```typescript
// tests/e2e/userRegistration.spec.ts
import { test, expect } from '@playwright/test'

test.describe('User Registration Flow', () => {
  // Use unique email for each test run
  const testEmail = `test${Date.now()}@example.com`
  const testPassword = 'SecurePass123!'
  const testName = 'E2E Test User'

  test('should complete full registration flow', async ({ page }) => {
    // Step 1: Landing Page
    await test.step('Navigate to landing page', async () => {
      await page.goto('/')

      // Verify page loaded
      await expect(page).toHaveTitle(/Welcome/)

      // Verify key elements visible
      await expect(page.locator('h1')).toContainText('Welcome')
      await expect(page.locator('[data-testid="signup-button"]')).toBeVisible()
    })

    // Step 2: Navigate to Signup
    await test.step('Click signup button', async () => {
      await page.click('[data-testid="signup-button"]')

      // Verify navigation
      await expect(page).toHaveURL(/\/signup/)

      // Verify form visible
      await expect(page.locator('form[data-testid="signup-form"]')).toBeVisible()
    })

    // Step 3: Fill Registration Form
    await test.step('Fill registration form', async () => {
      // Enter email
      await page.fill('input[name="email"]', testEmail)

      // Enter password
      await page.fill('input[name="password"]', testPassword)

      // Enter name
      await page.fill('input[name="name"]', testName)

      // Take screenshot before submission
      await page.screenshot({ path: 'screenshots/registration-form-filled.png' })

      // Submit form
      await page.click('button[type="submit"]')
    })

    // Step 4: Verify Email Verification Screen
    await test.step('Verify email verification prompt', async () => {
      // Wait for navigation
      await page.waitForURL(/\/verify-email/)

      // Verify message
      await expect(page.locator('text=Check your email')).toBeVisible()

      // In test environment, auto-verify
      const verifyToken = await page.evaluate(() => {
        return localStorage.getItem('pendingVerificationToken')
      })

      // Navigate to verify endpoint
      await page.goto(`/verify?token=${verifyToken}`)
    })

    // Step 5: Complete Onboarding
    await test.step('Complete onboarding', async () => {
      await page.waitForURL(/\/onboarding/)

      // Select preferences
      await page.check('input[name="notifications"]')
      await page.check('input[name="newsletter"]')

      // Select role
      await page.selectOption('select[name="role"]', 'developer')

      // Click continue
      await page.click('button:has-text("Get Started")')
    })

    // Step 6: Verify Dashboard Access
    await test.step('Verify dashboard access', async () => {
      // Wait for dashboard
      await page.waitForURL(/\/dashboard/)

      // Verify user name displayed
      await expect(page.locator('[data-testid="user-name"]')).toContainText(testName)

      // Verify welcome message
      await expect(page.locator('text=Welcome back')).toBeVisible()

      // Verify navigation menu
      await expect(page.locator('nav[data-testid="main-nav"]')).toBeVisible()

      // Verify user is authenticated
      const isLoggedIn = await page.evaluate(() => {
        return localStorage.getItem('authToken') !== null
      })
      expect(isLoggedIn).toBe(true)

      // Take final screenshot
      await page.screenshot({ path: 'screenshots/dashboard-success.png' })
    })
  })

  test('should show validation errors for invalid input', async ({ page }) => {
    await page.goto('/signup')

    // Try to submit empty form
    await page.click('button[type="submit"]')

    // Verify validation errors
    await expect(page.locator('text=Email is required')).toBeVisible()
    await expect(page.locator('text=Password is required')).toBeVisible()
    await expect(page.locator('text=Name is required')).toBeVisible()

    // Try invalid email
    await page.fill('input[name="email"]', 'invalid-email')
    await page.fill('input[name="password"]', 'short')
    await page.click('button[type="submit"]')

    await expect(page.locator('text=Invalid email format')).toBeVisible()
    await expect(page.locator('text=Password must be at least 8 characters')).toBeVisible()
  })

  test('should handle duplicate email registration', async ({ page }) => {
    // First registration
    await page.goto('/signup')
    await page.fill('input[name="email"]', 'duplicate@example.com')
    await page.fill('input[name="password"]', testPassword)
    await page.fill('input[name="name"]', 'First User')
    await page.click('button[type="submit"]')

    // Wait for success (or verification screen)
    await page.waitForURL(/\/verify-email|\/dashboard/)

    // Try to register again with same email
    await page.goto('/signup')
    await page.fill('input[name="email"]', 'duplicate@example.com')
    await page.fill('input[name="password"]', testPassword)
    await page.fill('input[name="name"]', 'Second User')
    await page.click('button[type="submit"]')

    // Verify error message
    await expect(page.locator('text=Email already exists')).toBeVisible()

    // Verify still on signup page
    await expect(page).toHaveURL(/\/signup/)
  })

  test('should persist form data on navigation', async ({ page }) => {
    await page.goto('/signup')

    // Fill form
    await page.fill('input[name="email"]', testEmail)
    await page.fill('input[name="name"]', testName)

    // Navigate away
    await page.goto('/')

    // Go back to signup
    await page.goBack()

    // Verify form data persisted (if app supports this)
    const emailValue = await page.inputValue('input[name="email"]')
    const nameValue = await page.inputValue('input[name="name"]')

    expect(emailValue).toBe(testEmail)
    expect(nameValue).toBe(testName)
  })
})

test.describe('Cross-Browser Testing', () => {
  test('should work in Chrome', async ({ browser }) => {
    const context = await browser.newContext({
      ...devices['Desktop Chrome']
    })
    const page = await context.newPage()

    await page.goto('/signup')
    await expect(page.locator('form')).toBeVisible()

    await context.close()
  })

  test('should work in Safari', async ({ webkit }) => {
    const context = await webkit.newContext({
      ...devices['Desktop Safari']
    })
    const page = await context.newPage()

    await page.goto('/signup')
    await expect(page.locator('form')).toBeVisible()

    await context.close()
  })

  test('should work on mobile', async ({ browser }) => {
    const context = await browser.newContext({
      ...devices['iPhone 13']
    })
    const page = await context.newPage()

    await page.goto('/signup')

    // Mobile-specific assertions
    const viewportSize = page.viewportSize()
    expect(viewportSize.width).toBe(390) // iPhone 13 width

    await expect(page.locator('form')).toBeVisible()

    await context.close()
  })
})

test.describe('Performance Testing', () => {
  test('should load registration page in < 3 seconds', async ({ page }) => {
    const startTime = Date.now()

    await page.goto('/signup')
    await page.waitForLoadState('networkidle')

    const loadTime = Date.now() - startTime
    expect(loadTime).toBeLessThan(3000)
  })

  test('should handle concurrent registrations', async ({ browser }) => {
    // Create 5 concurrent registration attempts
    const contexts = await Promise.all(
      Array(5).fill(null).map(() => browser.newContext())
    )

    const registrations = contexts.map(async (context, index) => {
      const page = await context.newPage()
      const email = `concurrent${index}@example.com`

      await page.goto('/signup')
      await page.fill('input[name="email"]', email)
      await page.fill('input[name="password"]', 'SecurePass123!')
      await page.fill('input[name="name"]', `User ${index}`)
      await page.click('button[type="submit"]')

      await page.waitForURL(/\/verify-email|\/dashboard/)

      return email
    })

    const results = await Promise.all(registrations)

    // Verify all succeeded
    expect(results).toHaveLength(5)

    // Clean up
    await Promise.all(contexts.map(ctx => ctx.close()))
  })
})

test.describe('Accessibility Testing', () => {
  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/signup')

    // Tab through form
    await page.keyboard.press('Tab') // Email field
    await page.keyboard.type(testEmail)

    await page.keyboard.press('Tab') // Password field
    await page.keyboard.type(testPassword)

    await page.keyboard.press('Tab') // Name field
    await page.keyboard.type(testName)

    await page.keyboard.press('Tab') // Submit button
    await page.keyboard.press('Enter') // Submit

    // Verify form submitted
    await page.waitForURL(/\/verify-email|\/dashboard/)
  })

  test('should have proper ARIA labels', async ({ page }) => {
    await page.goto('/signup')

    // Check for ARIA labels
    const emailInput = page.locator('input[name="email"]')
    const ariaLabel = await emailInput.getAttribute('aria-label')
    expect(ariaLabel).toBeTruthy()

    // Check for form role
    const form = page.locator('form')
    const formRole = await form.getAttribute('role')
    expect(formRole).toBeTruthy()
  })
})
```

## Step 6: Generate Cypress Tests (Alternative)

**Create Cypress test suite**:

```typescript
// cypress/e2e/userRegistration.cy.ts
describe('User Registration Flow', () => {
  const testEmail = `test${Date.now()}@example.com`
  const testPassword = 'SecurePass123!'

  beforeEach(() => {
    // Clear cookies and local storage
    cy.clearCookies()
    cy.clearLocalStorage()
  })

  it('should complete full registration', () => {
    // Visit landing page
    cy.visit('/')
    cy.contains('h1', 'Welcome').should('be.visible')

    // Click signup
    cy.get('[data-testid="signup-button"]').click()
    cy.url().should('include', '/signup')

    // Fill form
    cy.get('input[name="email"]').type(testEmail)
    cy.get('input[name="password"]').type(testPassword)
    cy.get('input[name="name"]').type('Cypress Test')

    // Submit
    cy.get('button[type="submit"]').click()

    // Verify success
    cy.url().should('match', /\/verify-email|\/dashboard/)

    // If on dashboard, verify elements
    cy.get('[data-testid="user-name"]').should('contain', 'Cypress Test')
  })

  it('should show validation errors', () => {
    cy.visit('/signup')

    // Submit empty form
    cy.get('button[type="submit"]').click()

    // Check errors
    cy.contains('Email is required').should('be.visible')
    cy.contains('Password is required').should('be.visible')
  })
})
```

## Step 7: Visual Regression Testing

**Add visual regression checks**:

```typescript
test('should match visual baseline', async ({ page }) => {
  await page.goto('/signup')

  // Wait for page to stabilize
  await page.waitForLoadState('networkidle')

  // Take screenshot and compare to baseline
  await expect(page).toHaveScreenshot('signup-page.png', {
    maxDiffPixels: 100 // Allow minor differences
  })
})

test('should match visual baseline on mobile', async ({ browser }) => {
  const context = await browser.newContext({
    ...devices['iPhone 13']
  })
  const page = await context.newPage()

  await page.goto('/signup')
  await page.waitForLoadState('networkidle')

  await expect(page).toHaveScreenshot('signup-page-mobile.png')

  await context.close()
})
```

## Step 8: Run E2E Tests

**Execute test suite**:

```bash
# Run all E2E tests
npm run test:e2e

# Run with UI mode (Playwright)
npx playwright test --ui

# Run specific test
npx playwright test userRegistration.spec.ts

# Run in headed mode (see browser)
npx playwright test --headed

# Run on specific browser
npx playwright test --project=chromium
npx playwright test --project=webkit

# Generate report
npx playwright show-report

# Debug mode
npx playwright test --debug
```

## Step 9: Generate Test Report

```
═══════════════════════════════════════════════════
           E2E TEST GENERATION REPORT
═══════════════════════════════════════════════════

FLOW TESTED: User Registration

TEST FILE CREATED:
  tests/e2e/userRegistration.spec.ts

TEST SUITE SUMMARY:
  ✓ 12 E2E test scenarios generated
  ✓ Full happy path tested (5 steps)
  ✓ 3 error scenarios covered
  ✓ Cross-browser tests (Chrome, Safari, Mobile)
  ✓ Accessibility tests included
  ✓ Visual regression tests added

TEST BREAKDOWN:

  1. Happy Path (1 test)
     ✓ Complete registration from landing to dashboard
     - 6 steps validated
     - Screenshots captured
     - 8.5s execution time

  2. Validation Testing (2 tests)
     ✓ Empty form validation
     ✓ Invalid input validation

  3. Error Scenarios (2 tests)
     ✓ Duplicate email handling
     ✓ Network error handling

  4. Cross-Browser (3 tests)
     ✓ Chrome Desktop
     ✓ Safari Desktop
     ✓ iPhone 13 Mobile

  5. Accessibility (2 tests)
     ✓ Keyboard navigation
     ✓ ARIA labels present

  6. Visual Regression (2 tests)
     ✓ Desktop visual baseline
     ✓ Mobile visual baseline

TEST RESULTS:
  ✓ All 12 tests passing
  ⏱ Total duration: 45.3s
  📸 8 screenshots captured
  🌐 3 browsers tested

BROWSER COVERAGE:
  ✓ Chromium (v120.0)
  ✓ WebKit (Safari v17.0)
  ✓ Mobile (iPhone 13)

VIEWPORT TESTING:
  ✓ Desktop: 1920x1080
  ✓ Tablet: 768x1024
  ✓ Mobile: 390x844

═══════════════════════════════════════════════════

NEXT STEPS:

1. Review test code:
   code tests/e2e/userRegistration.spec.ts

2. Run tests locally:
   npx playwright test --ui

3. View screenshots:
   open screenshots/

4. Add to CI/CD:
   - Run E2E tests before deployment
   - Store screenshots as artifacts
   - Run on multiple platforms

5. Monitor test health:
   - Track flaky tests
   - Update visual baselines when UI changes
   - Keep tests fast (< 60s total)

═══════════════════════════════════════════════════
```

## Usage Examples

**Test user registration flow**:

```bash
/testing:e2e "user registration"
```

**Test checkout flow**:

```bash
/testing:e2e "add item to cart, checkout, payment"
```

**Test admin workflow**:

```bash
/testing:e2e "admin login, create user, assign permissions"
```

**Test mobile flow**:

```bash
/testing:e2e "mobile navigation and search"
```

## Business Value / ROI

**Cost of Production Bugs**:

- Critical user flow broken: $50,000-$500,000 in lost revenue
- Payment flow broken: $100,000+ per hour
- Authentication broken: Complete service outage
- **E2E tests catch these before deployment**

**Time Savings**:

- Manual E2E testing: 2-4 hours per flow
- Automated E2E tests: 1-2 minutes per flow
- **ROI: 98% time reduction**

**Quality Improvements**:

- Catches integration issues across entire stack
- Validates real user experiences
- Tests cross-browser compatibility
- **Reduces production incidents by 80-90%**

**Deployment Confidence**:

- Automated smoke tests before release
- Catch regressions immediately
- Safe to deploy multiple times per day
- **Enables continuous deployment**

## Success Metrics

**Test Coverage**:

- [ ] All critical user flows tested
- [ ] Happy path fully validated
- [ ] Error scenarios covered
- [ ] Mobile experience tested
- [ ] Accessibility verified

**Test Quality**:

- [ ] Tests simulate real user behavior
- [ ] Clear, descriptive test names
- [ ] Proper wait strategies (no arbitrary sleeps)
- [ ] Screenshots for debugging
- [ ] Independent tests (no interdependencies)

**Performance**:

- [ ] Full suite completes in < 5 minutes
- [ ] Individual flows complete in < 60 seconds
- [ ] Tests run in parallel
- [ ] No flaky tests (98%+ consistency)

**Reliability**:

- [ ] Tests pass consistently in CI
- [ ] Work across all target browsers
- [ ] Visual regression tests stable
- [ ] Proper cleanup (no test pollution)

## Integration with Development Workflow

**Before Every Deployment**:

- Run E2E smoke tests (critical paths)
- Verify in staging environment
- Block deployment if tests fail

**In CI/CD Pipeline**:

- Run on every PR to main
- Run full suite nightly
- Store test artifacts (screenshots, videos)
- Report test results to team

**Monitoring**:

- Track test execution time
- Identify flaky tests
- Update baselines for visual tests
- Maintain test health dashboard

---

**Model**: Sonnet (complex E2E scenario generation)
**Estimated time**: 20-40 minutes per user flow
**Tip**: Focus on critical user journeys first, expand coverage incrementally!
