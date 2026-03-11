/**
 * UI steps for the Auth: Login scenario
 *
 * BDD feature: features/auth.feature
 * Scenario mapped: "Login succeeds for an active identity"
 *
 * Modes:
 *   - mock (default)        MSW intercepts all API calls; no DB seeding needed.
 *   - integration           Real backend must be running; Python seeding is used.
 */
import { test, expect } from '@playwright/test'
import { ensureIdentity, deleteIdentity } from '../support/db-factory'

const E2E_MODE = process.env.E2E_MODE ?? 'mock'

// BDD identity used for these tests (mirrors identity_registry.py "Charlie")
const CHARLIE = {
    name: 'Charlie',
    username: 'charlie01',
    password: 'Charlie Password 123!',
} as const

test.describe('Auth: Login', () => {
    test.beforeAll(async () => {
        if (E2E_MODE === 'integration') {
            // Given: ensure the shared identity "Charlie" exists as role "admin" and is active
            ensureIdentity(CHARLIE.name, { role: 'admin', is_active: true })
        }
        // In mock mode MSW custom-handlers.ts already has charlie01 / Charlie Password 123!
    })

    test.afterAll(async () => {
        if (E2E_MODE === 'integration') {
            deleteIdentity(CHARLIE.name)
        }
    })

    test('Login succeeds for an active identity — Charlie admin', async ({ page }) => {
        // When: navigate to sign-in page
        const base = process.env.BASE_URL ?? 'http://localhost:5173'
        await page.goto(`${base}/sign-in`)
        await expect(page.getByTestId('auth-signin-username')).toBeVisible()

        // Fill in credentials
        await page.getByTestId('auth-signin-username').fill(CHARLIE.username)
        await page.getByTestId('auth-signin-password').fill(CHARLIE.password)

        // When: submit the login form
        await page.getByTestId('auth-signin-submit').click()

        // Then: should redirect to the authenticated area (dashboard)
        await expect(page).toHaveURL(`${base}/`, { timeout: 10_000 })
        // And: the app sidebar is visible, confirming we are in the authenticated layout
        await expect(page.locator('[data-sidebar="sidebar"]').first()).toBeVisible()
    })

    test('Login fails with wrong credentials', async ({ page }) => {
        // When: navigate and enter wrong password
        const base2 = process.env.BASE_URL ?? 'http://localhost:5173'
        await page.goto(`${base2}/sign-in`)
        await page.getByTestId('auth-signin-username').fill(CHARLIE.username)
        await page.getByTestId('auth-signin-password').fill('WrongPassword!')
        await page.getByTestId('auth-signin-submit').click()

        // Then: the user stays on the sign-in page
        await expect(page).toHaveURL(`${base2}/sign-in`)
    })
})
