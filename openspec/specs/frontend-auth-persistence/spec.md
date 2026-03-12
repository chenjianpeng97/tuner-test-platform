### Requirement: 页面刷新后自动恢复认证状态
当已登录用户刷新页面时，系统 SHALL 通过调用 `/api/v1/users/me` 验证现有 Session Cookie，若有效则自动将用户信息写入认证 Store，无需用户重新登录。

#### Scenario: 刷新页面且 Session 有效
- **WHEN** 用户刷新浏览器页面，且 Session Cookie 仍然有效
- **THEN** 系统调用 `/api/v1/users/me` 返回用户信息，认证 Store 被更新，用户停留在原始页面而不被重定向到登录页

#### Scenario: 刷新页面且 Session 已过期
- **WHEN** 用户刷新浏览器页面，且 Session Cookie 已过期或无效
- **THEN** 系统调用 `/api/v1/users/me` 返回 401，用户被重定向到登录页，并携带 `redirect` 参数指向原始 URL

#### Scenario: Store 已有用户信息时跳过验证
- **WHEN** 认证 Store 中已存在有效的 `user` 对象（非 `null`）
- **THEN** 系统 SHALL 跳过 `/api/v1/users/me` 调用，直接放行导航（避免重复网络请求）
