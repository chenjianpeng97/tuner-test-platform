## Why

前端使用基于 HTTP-only Session Cookie 的认证方案，但用户认证状态仅保存在内存中的 Zustand Store 里。刷新页面时，Store 重置为初始状态（`user: null`），路由守卫检测到未认证状态便立即跳转到登录页，即使 Session Cookie 仍然有效。这导致已登录用户在刷新页面后必须重新登录，严重影响使用体验。

## What Changes

- 在 `_authenticated` 路由的 `beforeLoad` 钩子中，当检测到 Store 中的 `user` 为 `null` 时，主动调用 `/api/v1/users/me` 接口验证当前 Session Cookie 是否有效
- 若接口返回成功，将用户信息写入 Auth Store 并继续原始导航（不再跳转登录页）
- 若接口返回 401/403，则按原逻辑跳转登录页
- `beforeLoad` 调整为异步函数，支持 await 接口调用

## Capabilities

### New Capabilities
- `frontend-auth-persistence`: 前端认证状态持久化——页面刷新时通过调用 `/users/me` 接口从已有 Session Cookie 中恢复用户状态

### Modified Capabilities
（无现有 spec 需要变更——此问题纯属前端实现层面修复）

## Impact

- **受影响文件**: `shadcn-admin/src/routes/_authenticated/route.tsx`
- **API 依赖**: `GET /api/v1/users/me`（已存在）
- **无 breaking change**: 对未登录用户行为不变，仍跳转登录页
