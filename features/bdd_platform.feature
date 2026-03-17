Feature: BDD Platform core workflows
  In order to manage BDD scenarios in one place
  As a QA engineer
  I want to sync features, edit content, execute tests, and record hybrid steps

  Background:
    Given a project with Git integration is configured

  Scenario: Sync project features from Git
    When I trigger project sync
    Then the feature tree is refreshed
    And available stages are discovered

  Scenario: Edit a feature and commit changes
    Given a feature file is selected
    When I save the updated content with a commit message
    Then the feature content is updated in Git
    And scenarios and steps are re-parsed

  Scenario: Trigger execution and stream logs
    When I trigger a project test run
    Then a pending test run is created
    And I can stream execution logs via SSE

  Scenario: Hybrid execution with manual override
    Given a scenario execution session is created
    And an auto step fails for a Given step
    When I manually mark the Given step as pass
    Then the manual pass is recorded
    And the auto failure record is preserved
