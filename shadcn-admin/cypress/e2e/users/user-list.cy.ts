/**
 * Cypress E2E tests: Users list page rendering.
 *
 * Replaces the rendering assertions from the removed
 * features/ui/user_list_ui.feature.
 *
 * Covers:
 *  - Users table is visible after admin login
 *  - At least one user row is present
 *  - Role filter button is visible
 *  - Status filter button is visible
 *  - Invite User button is visible but disabled
 *
 * Functional user management scenarios (create/activate/deactivate)
 * are covered by BDD stage:ui (behave + Playwright) running against
 * user.feature.
 */

const ADMIN_USERNAME = Cypress.env('ADMIN_USERNAME') || 'charlie01'
const ADMIN_PASSWORD = Cypress.env('ADMIN_PASSWORD') || 'Charlie Password 123!'

/**
 * testIsolation: false — keeps cookies, localStorage, and JS heap intact
 * between tests in this describe block, so the Zustand auth store (in-memory,
 * non-persisted) stays populated after the single `before()` login.
 */
describe('Users list page — UI rendering', { testIsolation: false }, () => {
    before(() => {
        // Visit the protected page; the route guard redirects to /sign-in
        // with ?redirect=...  After login the app navigates back to /users.
        cy.visit('/users')
        cy.url().should('include', '/sign-in')
        cy.get('[data-testid="auth-signin-username"]').type(ADMIN_USERNAME)
        cy.get('[data-testid="auth-signin-password"]').type(ADMIN_PASSWORD)
        cy.get('[data-testid="auth-signin-submit"]').click()
        cy.url().should('include', '/users')
    })

    it('shows the users table', () => {
        cy.get('[data-testid="users-table"]').should('be.visible')
    })

    it('has at least one user row', () => {
        cy.get('[data-testid="users-table-row"]').should('have.length.gte', 1)
    })

    it('shows the role filter button', () => {
        cy.get('[data-testid="users-role-filter"]').should('be.visible')
    })

    it('shows the status filter button', () => {
        cy.get('[data-testid="users-status-filter"]').should('be.visible')
    })

    it('shows the Invite User button as disabled', () => {
        cy.get('[data-testid="users-invite-btn"]')
            .should('be.visible')
            .and('be.disabled')
    })
})
