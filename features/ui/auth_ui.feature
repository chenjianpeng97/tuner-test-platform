Feature: Authentication UI
    End-to-end browser tests for the sign-in workflow.
    These scenarios drive the frontend via Playwright and verify visual
    and navigation outcomes that HTTP-level tests cannot cover.

    Background:
        Given I open the sign-in page

    Scenario: Login succeeds for an active identity
        When I enter username "charlie01" and password "Charlie Password 123!"
        And I submit the login form
        Then I should be redirected to the dashboard
        And the app navigation sidebar should be visible

    Scenario: Login fails with wrong credentials
        When I enter username "charlie01" and password "WrongPassword!"
        And I submit the login form
        Then I should remain on the sign-in page
