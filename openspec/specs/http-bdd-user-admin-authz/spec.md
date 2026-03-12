## ADDED Requirements

### Requirement: 用户授权子功能 Feature SHALL 固定放置在 features/user/user_auth.feature
系统 SHALL 将用户管理相关的授权子功能放置在 `features/user/user_auth.feature`，以体现其从属于用户主功能但又独立于主功能核心生命周期行为。

#### Scenario: 用户授权子功能位置正确
- **WHEN** 开发者查看用户授权相关 Feature 文件
- **THEN** 系统 SHALL 将其放置在 `features/user/user_auth.feature`

### Requirement: 用户授权子功能 SHALL 覆盖超级管理员赋予管理员权限行为
系统 SHALL 通过 HTTP 层 BDD 场景覆盖“super admin 向其他用户赋予 admin 权限”的行为，并验证目标用户的角色结果满足预期。

#### Scenario: 超级管理员成功赋予管理员权限
- **WHEN** 已认证的 super admin 通过 HTTP 请求将 Bob 提升为 admin
- **THEN** 系统 SHALL 返回成功状态，并使 Bob 拥有 admin 权限

### Requirement: 用户授权子功能 SHALL 验证未授权主体不能赋予管理员权限
系统 SHALL 通过 HTTP 层 BDD 场景验证不具备该权限的主体不能执行管理员赋权，以保证授权边界被 HTTP 行为契约覆盖。

#### Scenario: 非超级管理员尝试赋予管理员权限被拒绝
- **WHEN** 不具备超级管理员权限的主体通过 HTTP 请求尝试将 Alice 提升为 admin
- **THEN** 系统 SHALL 返回授权失败结果，并保持 Alice 的角色不变

### Requirement: 用户授权子功能 MUST 与用户主功能共享同一批身份数据
用户授权子功能相关场景 MUST 复用 `features/db` 中与用户主功能一致的身份基线，避免在授权场景中重新定义另一套用户命名或角色语义。

#### Scenario: 授权场景复用共享身份基线
- **WHEN** 开发者编写 `features/user/user_auth.feature` 中的场景
- **THEN** 场景 SHALL 复用 Alice、Bob 等共享身份，而不是另起一套仅服务于子功能的命名

### Requirement: 用户授权子功能 Feature SHALL 覆盖用户删除的权限边界
系统 SHALL 通过 HTTP 层 BDD 场景覆盖用户删除操作的权限检查，验证仅具备相应权限的主体才能执行删除操作。

#### Scenario: 超级管理员成功删除用户
- **WHEN** 已认证的 super admin 通过 HTTP 请求删除指定用户
- **THEN** 系统 SHALL 返回成功状态，该用户 SHALL 不再存在于系统中

#### Scenario: 非超级管理员尝试删除用户被拒绝
- **WHEN** 不具备删除权限的主体（如普通管理员或普通用户）通过 HTTP 请求尝试删除用户
- **THEN** 系统 SHALL 返回授权失败结果，该用户 SHALL 依然存在于系统中
