import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright configuration for UI UAT tests.
 *
 * Supports two modes controlled by the E2E_MODE env var:
 *  - "mock"        : Tests run against the Vite dev server with VITE_MSW_ENABLED=true
 *                    (the default for fast, offline UI tests)
 *  - "integration" : Tests run against the real app + real backend
 *
 * Usage examples:
 *   pnpm exec playwright test                         (mock mode, default)
 *   E2E_MODE=integration pnpm exec playwright test    (real backend)
 */

const E2E_MODE = process.env.E2E_MODE ?? 'mock'
const BASE_URL = process.env.BASE_URL ?? 'http://localhost:5173'

export default defineConfig({
    testDir: '../features/ui_steps',

    /* Run tests in files in parallel */
    fullyParallel: true,

    /* Fail the build on CI if you accidentally left test.only in the source code */
    forbidOnly: !!process.env.CI,

    /* Retry on CI only */
    retries: process.env.CI ? 2 : 0,

    /* Single worker in integration mode to avoid race conditions with shared DB */
    workers: E2E_MODE === 'integration' ? 1 : undefined,

    /* Reporter */
    reporter: 'list',

    use: {
        baseURL: BASE_URL,

        /* Collect traces on CI failures */
        trace: process.env.CI ? 'on-first-retry' : 'off',
    },

    projects: [
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] },
        },
    ],

    /* In mock mode, automatically start the Vite dev server before tests */
    ...(E2E_MODE === 'mock'
        ? {
            webServer: {
                command: 'VITE_MSW_ENABLED=true pnpm exec nx run app-web:serve',
                url: BASE_URL,
                reuseExistingServer: !process.env.CI,
                timeout: 120_000,
                env: {
                    VITE_MSW_ENABLED: 'true',
                },
            },
        }
        : {}),
})
