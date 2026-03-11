/**
 * Cypress E2E tests: Sign-in page rendering.
 *
 * Replaces the rendering assertions from the removed
 * features/ui/auth_ui.feature.
 *
 * Covers:
 *  - Username input renders and is visible
 *  - Password input renders and is visible
 *  - Submit button renders and is visible
 *
 * Login success/failure flows are covered by BDD stage:ui
 * (behave + Playwright) running against auth.feature.
 */

describe('Sign-in page — UI rendering', () => {
    beforeEach(() => {
        cy.visit('/sign-in')
    })

    it('renders the username input', () => {
        cy.get('[data-testid="auth-signin-username"]').should('be.visible')
    })

    it('renders the password input', () => {
        cy.get('[data-testid="auth-signin-password"]').should('be.visible')
    })

    it('renders an enabled submit button', () => {
        cy.get('[data-testid="auth-signin-submit"]')
            .should('be.visible')
            .and('not.be.disabled')
    })
})
