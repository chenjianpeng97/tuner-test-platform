## Context

前端使用 TanStack Router，受保护路由通过 `_authenticated` 父路由的 `beforeLoad` 钩子实现鉴权。认证状态保存在 Zustand 内存 Store（`useAuthStore`）中，后端使用 HTTP-only Session Cookie 来标识用户身份。

**问题根因**：`beforeLoad` 仅检查内存 Store 中的 `user` 字段，而 Zustand Store 在页面刷新后会重置为初始值 `null`，导致即使 Session Cookie 仍有效，用户也会被重定向到登录页。

**现有能力**：`GET /api/v1/users/me` 接口已存在，可通过 Session Cookie 验证当前会话并返回用户信息。

## Goals / Non-Goals

**Goals:**
- 页面刷新后，若 Session Cookie 有效，自动恢复认证状态，不再跳转登录页
- 保持路由守卫的安全性：Session Cookie 无效或已过期时，仍跳转登录页

**Non-Goals:**
- 不引入 Token 刷新机制
- 不将认证状态持久化到 localStorage／sessionStorage
- 不修改后端认证逻辑
- 不处理多标签页同步问题

## Decisions

### 决策 1：在 `beforeLoad` 中异步验证 Session

**方案**：将 `_authenticated/route.tsx` 的 `beforeLoad` 改为 `async`，在 `user` 为 `null` 时先调用 `getCurrentUserApiV1UsersMeGet()`，成功则将返回值写入 Store 并继续导航；失败则跳转登录页。

**备选方案**：
- **方案 A：应用启动时全局预取**（在 `main.tsx` 的 `startApp()` 中调用 `/users/me`）——问题是增加了不必要的全局复杂度，公开路由也会触发该请求。
- **方案 B：持久化 Store 到 localStorage**——不适用，因为后端使用 HTTP-only Cookie，用户身份的真实状态以 Cookie 为准，localStorage 可能产生状态不一致。

**选择理由**：只在受保护路由的入口处做会话检查，符合"需要时才验证"的最小权限原则，且改动范围极小（仅修改一个文件）。

### 决策 2：错误处理策略

调用 `/users/me` 失败时（任何错误，包括网络错误和 401），统一跳转登录页并附带 `redirect` 参数，与现有行为一致。

## Risks / Trade-offs

- **[风险] 首次进入受保护页面时多一次网络请求** → 缓解：TanStack Router 的 `beforeLoad` 是串行执行的，用户在 Loading 期间不会看到内容闪烁；可通过 TanStack Query 缓存避免重复请求。
- **[风险] `/users/me` 接口响应慢时用户感知到页面加载延迟** → 缓解：Store 中一旦写入 `user`，后续同一会话内不再重复调用（Store 已有值直接放行）。
