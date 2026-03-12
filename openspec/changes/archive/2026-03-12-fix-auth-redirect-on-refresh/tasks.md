## 1. 修改认证路由守卫

- [x] 1.1 将 `shadcn-admin/src/routes/_authenticated/route.tsx` 的 `beforeLoad` 改为 `async` 函数
- [x] 1.2 在 `user` 为 `null` 时，调用 `getCurrentUserApiV1UsersMeGet()` 验证 Session Cookie
- [x] 1.3 调用成功后，使用返回值调用 `auth.setUser(...)` 写入 Store，并继续正常导航
- [x] 1.4 调用失败时（任何异常），执行跳转到 `/sign-in` 并携带 `redirect` 参数

## 2. 验证与测试

- [x] 2.1 手动验证：登录后刷新页面，确认停留在原页面而非跳转到登录页
- [x] 2.2 手动验证：在无有效 Session（清除 Cookie）的情况下访问受保护路由，确认仍正确跳转登录页
- [x] 2.3 手动验证：Store 已有用户信息时，确认不会触发额外的 `/users/me` 请求
