import { defineConfig } from 'cypress'

export default defineConfig({
    // E2E tests: rendered-page assertions (replaces former BDD UI-only feature files)
    e2e: {
        baseUrl: 'http://localhost:5173',
        specPattern: 'cypress/e2e/**/*.cy.{ts,tsx}',
        supportFile: false,
    },
    // Component tests: isolated React component rendering
    component: {
        devServer: {
            framework: 'react',
            bundler: 'vite',
        },
        specPattern: 'src/**/*.cy.{ts,tsx}',
        supportFile: false,
    },
})
