/**
 * UI steps for the User list scenario
 *
 * BDD feature: features/user.feature
 * Scenario mapped: User list visible after login (admin user)
 *
 * Modes:
 *   - mock (default)         MSW handles all API calls; no DB seeding needed.
 *   - integration            Real backend required; Python DB seeding used.
 */
import { test, expect } from '@playwright/test'
import { ensureIdentity, deleteIdentity } from '../support/db-factory'

const E2E_MODE = process.env.E2E_MODE ?? 'mock'

// BDD identity used: Charlie (admin) — can access the user list
const CHARLIE = {
    name: 'Charlie',
    username: 'charlie01',
    password: 'Charlie Password 123!',
} as const

/** Helper: log in as Charlie admin via the sign-in form */
async function loginAsCharlie(page: import('@playwright/test').Page) {
    const base = process.env.BASE_URL ?? 'http://localhost:5173'
    await page.goto(`${base}/sign-in`)
    await page.getByTestId('auth-signin-username').fill(CHARLIE.username)
    await page.getByTestId('auth-signin-password').fill(CHARLIE.password)
    await page.getByTestId('auth-signin-submit').click()
    // Wait for the redirect to the dashboard
    await expect(page).toHaveURL(`${base}/`, { timeout: 10_000 })
}

test.describe('Users: User list page', () => {
    test.beforeAll(async () => {
        if (E2E_MODE === 'integration') {
            // Given: ensure Charlie (admin) exists and is active
            ensureIdentity(CHARLIE.name, { role: 'admin', is_active: true })
        }
    })

    test.afterAll(async () => {
        if (E2E_MODE === 'integration') {
            deleteIdentity(CHARLIE.name)
        }
    })

    test('User list table is visible for authenticated admin', async ({ page }) => {
        // Given: Charlie admin is logged in
        await loginAsCharlie(page)

        // When: navigate to the users list
        const base = process.env.BASE_URL ?? 'http://localhost:5173'
        await page.goto(`${base}/users`)

        // Then: the users table container should be visible
        await expect(page.getByTestId('users-table')).toBeVisible({ timeout: 15_000 })

        // And: at least one table row should exist
        const rows = page.getByTestId('users-table-row')
        await expect(rows.first()).toBeVisible({ timeout: 10_000 })
    })

    test('Role filter button is visible on users page', async ({ page }) => {
        await loginAsCharlie(page)
        const base2 = process.env.BASE_URL ?? 'http://localhost:5173'
        await page.goto(`${base2}/users`)

        await expect(page.getByTestId('users-table')).toBeVisible({ timeout: 15_000 })
        await expect(page.getByTestId('users-role-filter')).toBeVisible()
        await expect(page.getByTestId('users-status-filter')).toBeVisible()
    })

    test('Invite User button is disabled (feature in development)', async ({ page }) => {
        await loginAsCharlie(page)
        const base3 = process.env.BASE_URL ?? 'http://localhost:5173'
        await page.goto(`${base3}/users`)

        await expect(page.getByTestId('users-table')).toBeVisible({ timeout: 15_000 })

        const inviteBtn = page.getByTestId('users-invite-btn')
        await expect(inviteBtn).toBeVisible()
        await expect(inviteBtn).toBeDisabled()
    })
})
