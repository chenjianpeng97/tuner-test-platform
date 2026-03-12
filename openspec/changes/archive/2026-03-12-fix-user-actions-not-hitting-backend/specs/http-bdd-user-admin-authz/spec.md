## ADDED Requirements

### Requirement: 用户授权子功能 Feature SHALL 覆盖用户删除的权限边界
系统 SHALL 通过 HTTP 层 BDD 场景覆盖用户删除操作的权限检查，验证仅具备相应权限的主体才能执行删除操作。

#### Scenario: 超级管理员成功删除用户
- **WHEN** 已认证的 super admin 通过 HTTP 请求删除指定用户
- **THEN** 系统 SHALL 返回成功状态，该用户 SHALL 不再存在于系统中

#### Scenario: 非超级管理员尝试删除用户被拒绝
- **WHEN** 不具备删除权限的主体（如普通管理员或普通用户）通过 HTTP 请求尝试删除用户
- **THEN** 系统 SHALL 返回授权失败结果，该用户 SHALL 依然存在于系统中
