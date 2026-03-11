## ADDED Requirements

### Requirement: 获取当前登录用户信息端点
系统 SHALL 提供 `GET /api/v1/users/me` 端点，要求请求方携带有效的 session cookie，返回当前登录用户的基本信息。

该端点 SHALL：
- 读取请求中的 session cookie 以识别当前用户身份
- 从数据库中查询并返回该用户的 `id`、`username`、`role`、`is_active` 字段
- 在 session 无效或未登录时返回 401 Unauthorized
- 响应 schema 与 `GET /api/v1/users/{user_id}` 返回的用户对象保持一致

#### Scenario: 已登录用户成功获取自身信息
- **WHEN** 已登录用户（携带有效 session cookie）请求 `GET /api/v1/users/me`
- **THEN** 系统返回 200，响应体包含该用户的 `id`、`username`、`role`、`is_active`

#### Scenario: 未登录请求被拒绝
- **WHEN** 请求不携带 session cookie 或 cookie 已失效时访问 `GET /api/v1/users/me`
- **THEN** 系统返回 401 Unauthorized，不返回任何用户数据

#### Scenario: 响应字段完整性
- **WHEN** 已登录用户请求 `GET /api/v1/users/me`
- **THEN** 响应体中 `role` 字段值为后端枚举之一（`super_admin`、`admin`、`user`），`is_active` 为布尔值

### Requirement: 该端点纳入 OpenAPI 规范导出
系统 SHALL 确保 `GET /api/v1/users/me` 端点在 FastAPI 的 OpenAPI 规范中有完整的 `response_model` 注解，以便后续 Orval 代码生成可正确识别响应类型。

#### Scenario: OpenAPI 规范包含 me 端点
- **WHEN** 导出后端 OpenAPI JSON 规范
- **THEN** 规范中包含 `/api/v1/users/me` 的 GET 定义，且包含完整的 200 响应 schema
