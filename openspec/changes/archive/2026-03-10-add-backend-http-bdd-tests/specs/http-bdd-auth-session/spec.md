## ADDED Requirements

### Requirement: 顶层认证主功能 Feature SHALL 固定放置在 features/auth.feature
系统 SHALL 在仓库顶层 `features` 目录中为认证主功能维护 `auth.feature` 文件，用于描述登录与注销等认证会话行为。

#### Scenario: 认证主功能 Feature 位置正确
- **WHEN** 开发者查看认证相关主功能 Feature 文件
- **THEN** 系统 SHALL 将其放置在 `features/auth.feature`

### Requirement: 认证主功能 SHALL 覆盖登录成功后的会话建立行为
系统 SHALL 通过 HTTP 层 BDD 场景覆盖登录成功行为，并验证登录成功后会话状态已经建立，以便后续受保护请求可以使用该认证结果。

#### Scenario: 用户成功登录
- **WHEN** 已存在且可登录的 Alice 通过 HTTP 请求提交正确的认证凭据
- **THEN** 系统 SHALL 返回成功结果，并建立可供后续请求使用的认证会话

### Requirement: 认证主功能 SHALL 覆盖登录失败行为
系统 SHALL 通过 HTTP 层 BDD 场景覆盖登录失败行为，并验证错误凭据或不满足认证条件时不会建立会话。

#### Scenario: 用户使用错误凭据登录失败
- **WHEN** Alice 通过 HTTP 请求提交错误的认证凭据
- **THEN** 系统 SHALL 返回认证失败结果，并且不得建立有效会话

### Requirement: 认证主功能 SHALL 覆盖注销后的会话失效行为
系统 SHALL 通过 HTTP 层 BDD 场景覆盖注销行为，并验证注销成功后先前建立的认证会话不再可用。

#### Scenario: 已登录用户成功注销
- **WHEN** 已登录的 Bob 通过 HTTP 请求执行注销
- **THEN** 系统 SHALL 返回成功结果，并使 Bob 当前会话失效