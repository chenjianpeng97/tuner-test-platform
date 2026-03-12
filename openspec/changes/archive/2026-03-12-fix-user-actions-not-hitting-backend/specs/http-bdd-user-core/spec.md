## ADDED Requirements

### Requirement: 后端 SHALL 提供删除用户接口
系统 SHALL 提供 `DELETE /api/v1/users/{user_id}` 接口，允许具有管理员权限的主体删除指定用户。接口 SHALL 在成功时返回 204 或 200，在用户不存在时返回 404。

#### Scenario: 超级管理员成功删除用户
- **WHEN** 已认证的 super admin 通过 `DELETE /api/v1/users/{user_id}` 删除存在的用户
- **THEN** 系统 SHALL 返回成功状态，且之后查询用户列表时该用户 SHALL 不再出现

#### Scenario: 删除不存在的用户时返回 404
- **WHEN** 任意请求方请求删除不存在的用户 ID
- **THEN** 系统 SHALL 返回 404 状态码
