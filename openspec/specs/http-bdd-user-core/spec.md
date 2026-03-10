## ADDED Requirements

### Requirement: 顶层用户主功能 Feature SHALL 固定放置在 features/user.feature
系统 SHALL 在仓库顶层 `features` 目录中为用户主功能维护单独的 `user.feature` 文件，用于描述用户领域核心 HTTP 行为，而不是将这些场景拆散到后端工程私有测试目录或授权子功能文件中。

#### Scenario: 用户主功能 Feature 位置正确
- **WHEN** 开发者查看仓库中的用户主功能 Feature 文件
- **THEN** 系统 SHALL 将该文件放置在 `features/user.feature`

### Requirement: 用户主功能 Feature SHALL 覆盖用户创建行为
系统 SHALL 通过 HTTP 层 BDD 场景覆盖用户创建行为，包括请求入口、状态码结果以及新用户身份被正确建立的业务结果。

#### Scenario: 管理员成功创建普通用户
- **WHEN** 已认证且具备创建权限的用户通过 HTTP 请求创建一个名为 Bob 的普通用户
- **THEN** 系统 SHALL 返回成功状态，并使 Bob 成为可被后续场景引用的已存在用户

### Requirement: 用户主功能 Feature SHALL 覆盖用户激活与反激活行为
系统 SHALL 通过 HTTP 层 BDD 场景覆盖用户激活与反激活行为，并验证用户状态变更能够被后续请求或数据读取观察到。

#### Scenario: 管理员激活已存在用户
- **WHEN** 已认证且具备权限的用户通过 HTTP 请求激活 Alice
- **THEN** 系统 SHALL 返回成功状态，并使 Alice 处于激活状态

#### Scenario: 管理员反激活已存在用户
- **WHEN** 已认证且具备权限的用户通过 HTTP 请求反激活 Bob
- **THEN** 系统 SHALL 返回成功状态，并使 Bob 处于非激活状态

### Requirement: 用户主功能场景 MUST 使用统一的可读身份命名
用户主功能相关场景 MUST 使用与共享测试数据一致的可读身份命名，如 Alice、Bob、Charlie，而不是随机用户名、技术性主键或临时拼接标识。

#### Scenario: 主功能场景使用共享身份名
- **WHEN** 开发者新增或维护 `features/user.feature` 中的场景
- **THEN** 场景中的参与者 SHALL 使用共享数据体系中的可读身份名
