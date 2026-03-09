Feature: Authentication HTTP behaviour

  Scenario: Login succeeds for an active identity
    Given the shared identity "Charlie" exists as role "admin" and is active
    When I log in as "Charlie"
    Then the response status should be 204
    And the auth cookie should be issued
    And the current session should be allowed to access the protected user list endpoint

  Scenario: Login fails with wrong credentials
    Given the shared identity "Charlie" exists as role "admin" and is active
    When I attempt to log in as "Charlie" with password "Wrong Password 123!"
    Then the response status should be 401
    And the auth cookie should not be issued

  Scenario: Logout invalidates the current session
    Given the shared identity "Charlie" exists as role "admin" and is active
    And I am authenticated as "Charlie"
    When I log out
    Then the response status should be 204
    And the auth cookie should be cleared
    And the current session should be unauthorized to access the protected user list endpoint