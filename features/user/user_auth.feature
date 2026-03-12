Feature: User authorization HTTP behaviour

  Scenario: Super admin grants admin role to a regular user
    Given the shared identity "Alice" exists as role "super_admin" and is active
    And the shared identity "Bob" exists as role "user" and is active
    And I am authenticated as "Alice"
    When I grant admin role to "Bob"
    Then the response status should be 204
    And the user "Bob" should appear as role "admin" and active "true"

  Scenario: Admin cannot grant admin role to another user
    Given the shared identity "Charlie" exists as role "admin" and is active
    And the shared identity "Bob" exists as role "user" and is active
    And I am authenticated as "Charlie"
    When I grant admin role to "Bob"
    Then the response status should be 403
    And the user "Bob" should appear as role "user" and active "true"

  Scenario: Super admin can delete a regular user
    Given the shared identity "Alice" exists as role "super_admin" and is active
    And the shared identity "Bob" exists as role "user" and is active
    And I am authenticated as "Alice"
    When I delete the user "Bob"
    Then the response status should be 204
    And the user "Bob" should no longer exist

  Scenario: Admin cannot delete a user
    Given the shared identity "Charlie" exists as role "admin" and is active
    And the shared identity "Bob" exists as role "user" and is active
    And I am authenticated as "Charlie"
    When I delete the user "Bob"
    Then the response status should be 403
    And the user "Bob" should appear as role "user" and active "true"