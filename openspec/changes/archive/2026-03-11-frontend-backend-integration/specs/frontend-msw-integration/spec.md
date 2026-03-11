## ADDED Requirements

### Requirement: MSW 在开发环境通过环境变量条件启用
系统 SHALL 在 `shadcn-admin/src/main.tsx` 中根据 `VITE_MSW_ENABLED=true` 环境变量条件初始化 MSW browser worker，在生产构建中不包含任何 MSW 相关代码。

#### Scenario: MSW 启用时拦截 API 请求
- **WHEN** 以 `VITE_MSW_ENABLED=true` 启动 vite dev server，并访问 Users 页面
- **THEN** 浏览器 Network 面板中 `/api/v1/users` 请求被 service worker 拦截，返回 mock 数据

#### Scenario: MSW 禁用时请求直接到达后端
- **WHEN** 以 `VITE_MSW_ENABLED` 未设置或为 `false` 启动 vite dev server
- **THEN** 请求不经过 service worker，直接到达真实后端（或返回网络错误如后端未启动）

#### Scenario: 生产构建不包含 MSW 代码
- **WHEN** 执行 `vite build`（不设置 `VITE_MSW_ENABLED`）
- **THEN** 构建产物中不包含 `mockServiceWorker.js` 的引用代码

### Requirement: MSW handler 覆盖所有前端已使用的 API 端点
`shadcn-admin/src/mocks/handlers/` 中的 MSW handlers SHALL 覆盖以下端点的 mock 实现：
- `POST /api/v1/auth/login`（模拟登录成功和失败场景）
- `POST /api/v1/auth/logout`
- `GET /api/v1/users/me`（返回当前模拟用户信息）
- `GET /api/v1/users`（返回分页用户列表）
- `POST /api/v1/users`（模拟创建用户）
- `PATCH /api/v1/users/{user_id}/activate`
- `PATCH /api/v1/users/{user_id}/deactivate`

#### Scenario: 登录接口 mock 返回正确响应
- **WHEN** MSW 启用，前端提交登录表单（正确凭据）
- **THEN** mock handler 响应 204，并设置模拟 session cookie

#### Scenario: 用户列表 mock 返回含多条记录的数据
- **WHEN** MSW 启用，Users 页面请求 `GET /api/v1/users`
- **THEN** mock handler 返回至少包含 3 条用户记录的列表，字段符合后端 API schema

### Requirement: MSW mock 数据包含所有前端状态的演示数据
MSW handler 中的用户列表 mock 数据 SHALL 包含涵盖 `active`、`inactive`、`invited`、`suspended` 四种状态和 `super_admin`、`admin`、`user` 三种角色的演示用户记录，以支持前端 UI 的完整渲染展示。

`invited` 和 `suspended` 为前端 UI 保留状态，mock 可返回但真实后端 API 不返回这些值。

#### Scenario: 用户列表渲染所有状态徽章
- **WHEN** MSW 启用，打开 Users 页面
- **THEN** 列表中可见 Active、Inactive 状态的用户行（UI 层保留 Invited/Suspended 样式定义）

### Requirement: MSW service worker 文件位于 public 目录
`mockServiceWorker.js` SHALL 通过 `pnpm exec msw init public/` 初始化，文件置于 `shadcn-admin/public/` 目录。

#### Scenario: service worker 文件可被浏览器加载
- **WHEN** MSW 启用时访问前端应用
- **THEN** 浏览器控制台出现 "[MSW] Mocking enabled." 日志，无 404 或注册失败错误
