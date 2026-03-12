Feature: User core HTTP behaviour

  Scenario: Admin creates a regular user
    Given the shared identity "Charlie" exists as role "admin" and is active
    And no user named "Bob" exists
    And I am authenticated as "Charlie"
    When I create the user "Bob" with password "Bob Password 123!" and role "user"
    Then the response status should be 201
    And the created user id should be returned
    And the user "Bob" should appear as role "user" and active "true"

  Scenario: Admin activates an existing inactive user
    Given the shared identity "Charlie" exists as role "admin" and is active
    And the shared identity "Bob" exists as role "user" and is inactive
    And I am authenticated as "Charlie"
    When I activate the user "Bob"
    Then the response status should be 204
    And the user "Bob" should appear as role "user" and active "true"

  Scenario: Admin deactivates an existing active user
    Given the shared identity "Charlie" exists as role "admin" and is active
    And the shared identity "Bob" exists as role "user" and is active
    And I am authenticated as "Charlie"
    When I deactivate the user "Bob"
    Then the response status should be 204
    And the user "Bob" should appear as role "user" and active "false"

  Scenario: Super admin deletes an existing user
    Given the shared identity "Alice" exists as role "super_admin" and is active
    And the shared identity "Bob" exists as role "user" and is active
    And I am authenticated as "Alice"
    When I delete the user "Bob"
    Then the response status should be 204
    And the user "Bob" should no longer exist