Feature: User List page UI
    End-to-end browser tests for the /users admin page.
    An authenticated admin user must be able to see the user table,
    use filter controls, and observe the disabled Invite button.

    Background:
        Given I am signed in as "charlie01" with password "Charlie Password 123!"
        And I navigate to the users list page

    Scenario: User list table is visible for an authenticated admin
        Then the users table should be visible
        And at least one user row should be present

    Scenario: Role and status filter buttons are visible
        Then the role filter button should be visible
        And the status filter button should be visible

    Scenario: Invite User button is visible but disabled
        Then the invite user button should be visible
        And the invite user button should be disabled
