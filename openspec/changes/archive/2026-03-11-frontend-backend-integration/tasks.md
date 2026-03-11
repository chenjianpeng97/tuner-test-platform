## 0. 前置：BDD Factory 提取（不破坏现有 HTTP 测试）

- [x] 0.1 在 `features/` 下创建 `factories/` 目录和 `__init__.py`
- [x] 0.2 将 `features/http_steps/factories/identity_registry.py` 移动到 `features/factories/identity_registry.py`
- [x] 0.3 将 `features/http_steps/factories/seeding.py` 移动到 `features/factories/seeding.py`
- [x] 0.4 在 `features/http_steps/factories/__init__.py` 中添加从 `features.factories` 的重新导出（向后兼容）
- [x] 0.5 将 `features/http_steps/http_bdd_steps.py` 中的导入路径从 `features.http_steps.factories.*` 更新为 `features.factories.*`
- [x] 0.6 执行 `pnpm exec nx run app-api:test-uat-dry-run` 验证现有 HTTP BDD 步骤绑定无误
- [x] 0.7 执行 `pnpm exec nx run ux-uat:check-features` 验证特征结构检查仍通过

## 1. 后端：新增 `GET /api/v1/users/me` 端点（优先）

- [x] 1.1 在 `fastapi-clean-example/src/app/` 合适位置（如 query gateway 或 use-case 层）添加"根据 session 获取当前用户"的查询逻辑
- [x] 1.2 在路由层（`app/presentation/api/v1/`）新增 `GET /users/me` 路由，配置 `response_model` 注解，需鉴权
- [x] 1.3 确保未登录请求（无有效 session）返回 401
- [x] 1.4 为 `/users/me` 编写单元测试
- [x] 1.5 执行 `pnpm exec nx run app-api:test-unit` 验证新测试通过
- [x] 1.6 执行 `pnpm exec nx run app-api:lint` 验证代码规范

## 2. 后端：OpenAPI 契约导出

- [x] 2.1 在 `fastapi-clean-example/scripts/` 下创建 `export_openapi.py` 脚本：import FastAPI app 对象调用 `app.openapi()`，将结果写入 `openspec/contracts/app-api.openapi.json`
- [x] 2.2 在 `openspec/contracts/` 目录创建（如不存在）并确保不在 `.gitignore` 中
- [x] 2.3 在 `fastapi-clean-example/project.json` 中新增 `export-schema` Nx target，执行 `uv run python scripts/export_openapi.py`
- [x] 2.4 执行 `pnpm exec nx run app-api:export-schema`，验证 `openspec/contracts/app-api.openapi.json` 生成，内容包含 `/api/v1/users/me` 路由定义
- [x] 2.5 将 `openspec/contracts/app-api.openapi.json` 提交到版本控制

## 3. 前端：Orval 配置与代码生成

- [x] 3.1 在 `shadcn-admin/` 目录安装依赖：`pnpm add -D orval`（workspace root 层面）
- [x] 3.2 在 `shadcn-admin/` 根目录创建 `orval.config.ts`，配置两个 output：`api-client`（axios + react-query）和 `msw-handlers`（msw 模式），输入源指向 `../../openspec/contracts/app-api.openapi.json`
- [x] 3.3 在 `shadcn-admin/project.json` 中新增 `generate-api` Nx target：`pnpm exec orval --config orval.config.ts`，`cwd` 为 `shadcn-admin`
- [x] 3.4 执行 `pnpm exec nx run app-web:generate-api`，验证 `shadcn-admin/src/api/generated/` 和 `shadcn-admin/src/mocks/handlers/` 目录被创建
- [x] 3.5 在 `shadcn-admin/.gitignore` 中添加 `src/api/generated/` 和 `src/mocks/handlers/`（标注为可重建产物）
- [x] 3.6 新建 `shadcn-admin/src/lib/axios-instance.ts`：创建配置了 `withCredentials: true` 和 `baseURL: '/api/v1'` 的 axios 实例，供生成的 API client 使用
- [x] 3.7 在 `vite.config.ts` 中添加 dev proxy：将 `/api` 请求转发到 `http://localhost:8000`（仅 dev 环境）
- [x] 3.8 执行 TypeScript 类型检查，确认生成代码无类型错误

## 4. 前端：Auth Store 改造（对齐 session cookie 流程）

- [x] 4.1 修改 `shadcn-admin/src/stores/auth-store.ts`：移除 `accessToken` 相关字段，改为仅使用 `user: AuthUser | null` 判断登录态
- [x] 4.2 更新 `AuthUser` 接口：字段对齐后端响应（`id`、`username`、`role`、`is_active`）
- [x] 4.3 改造登录流程：登录成功后调用生成的 `GET /api/v1/users/me` hook 获取用户信息，写入 auth store
- [x] 4.4 改造退出登录流程：调用 `POST /api/v1/auth/logout` 后清空 auth store `user` 字段
- [x] 4.5 更新所有引用 `auth.accessToken` 的代码，改为检查 `auth.user` 是否为 null
- [x] 4.6 更新认证路由守卫（`_authenticated/route.tsx`），基于 `auth.user` 判断登录态

## 5. 前端：MSW 集成

- [x] 5.1 安装 `msw` 包：在 `shadcn-admin/` 目录执行 `pnpm add -D msw`
- [x] 5.2 执行 `pnpm exec msw init shadcn-admin/public/`，将 `mockServiceWorker.js` 放入 `public/`
- [x] 5.3 在 `shadcn-admin/src/mocks/` 下创建 `browser.ts`：初始化 MSW browser worker，引入 Orval 生成的 handlers
- [x] 5.4 修改 `shadcn-admin/src/mocks/` 下创建手写的 `custom-handlers.ts`：为生成 handler 中数据不足的端点补充响应数据（含 `invited`/`suspended` 演示用户、登录模拟 cookie 等），扩展生成的基础 handler
- [x] 5.5 修改 `shadcn-admin/src/main.tsx`：添加条件引导逻辑，当 `import.meta.env.VITE_MSW_ENABLED === 'true'` 时在应用挂载前启动 MSW worker
- [x] 5.6 在 `shadcn-admin/` 根目录创建 `.env.development` 文件（或更新），添加 `VITE_MSW_ENABLED=true`
- [x] 5.7 以 `VITE_MSW_ENABLED=true` 启动 dev server，验证浏览器控制台出现 "[MSW] Mocking enabled."
- [x] 5.8 `src/features/users/data/users.ts` 仅被 Clerk demo 路由引用，保留文件；Group 7 对齐枚举时一并处理

## 6. 前端：Users 页面数据层迁移

- [x] 6.1 在 `shadcn-admin/src/features/users/` 下创建（或更新）`hooks/` 目录，封装对生成 API client 的调用（如 `useUserList`，内部调用生成的 `useGetUsers`）
- [x] 6.2 更新 Users 列表组件：将数据来源从静态 `users` 数组改为调用 `useUserList` hook
- [x] 6.3 实现分页查询参数传递（page、pageSize 传入 API query）
- [x] 6.4 实现角色/状态过滤参数传递（role、status 过滤条件传入 API query）
- [x] 6.5 处理加载状态（skeleton 或 spinner）和错误状态（toast 提示）

## 7. 前端：用户角色与状态枚举对齐

- [x] 7.1 修改 `shadcn-admin/src/features/users/data/schema.ts`：`userRoleSchema` 更新为 `super_admin | admin | user`，移除 `superadmin`、`manager`、`cashier`
- [x] 7.2 修改 `shadcn-admin/src/features/users/data/data.ts`：`roles` 数组更新为三项（`super_admin`/`admin`/`user`），标签分别为 "Super Admin"/"Admin"/"User"，选配合适图标
- [x] 7.3 修改 `shadcn-admin/src/routes/_authenticated/users/index.tsx`：更新 URL search schema 中 `role` 参数的合法値集合
- [x] 7.4 全局搜索并修复所有引用旧角色値（`superadmin`、`manager`、`cashier`）的代码
- [x] 7.5 执行 TypeScript 类型检查，确认无旧角色値引起的类型错误

## 8. 前端：添加 `data-testid` 属性

- [x] 8.1 为 SignIn 页面的关键元素添加 testid：用户名输入框 `auth-signin-username`、密码输入框 `auth-signin-password`、提交按鈕 `auth-signin-submit`
- [x] 8.2 为 Users 列表页容器添加 testid：表格容器 `users-table`、表格行 `users-table-row`（每行）
- [x] 8.3 为 Users 页面操作按鈕添加 testid：角色过滤器触发按鈕 `users-role-filter`、状态过滤器触发按鈕 `users-status-filter`
- [x] 8.4 为未实现功能按鈕添加 testid：Invite Users 按鈕 `users-invite-btn`
- [x] 8.5 检查其他自编写容器组件（非第三方 shadcn-ui 原始组件），补充缺失的 testid

## 9. 前端：未实现功能占位处理

- [x] 9.1 找到 Users 页面中的 "Invite Users" 按鈕，添加 `disabled` 属性和 `title="功能开发中"` tooltip
- [x] 9.2 扫描 Users 页面和 Auth 页面中其他无对应后端 API 的操作按鈕，统一添加 `disabled` + `title`
- [x] 9.3 验证 disabled 按鈕视觉外观与其他按鈕风格一致（不强制灰化）

## 10. UI E2E：配置 Playwright + ux-uat target

- [x] 10.1 确认 workspace 根 `package.json` 包含 `@playwright/test` devDependency，如缺失则安装
- [x] 10.2 在 `ux-uat/` 目录创建 `playwright.config.ts`：配置 `testDir` 指向 `../features/ui_steps`，配置 `baseURL`（默认 `http://localhost:5173`），支持通过 `E2E_MODE` 环境变量区分 mock/integration 模式
- [x] 10.3 在 `ux-uat/project.json` 中新增 `test-ui-uat` Nx target：`cwd` 为 `ux-uat`，命令为 `pnpm exec playwright test`，`inputs` 包含 `features/ui_steps/**/*` 和 `ux-uat/playwright.config.ts`
- [x] 10.4 执行 `pnpm exec nx run ux-uat:test-ui-uat --help`（或 dry-run），验证 target 可被识别

## 11. UI E2E：实现 `features/ui_steps/` 步骤

- [x] 11.1 在 `features/ui_steps/` 下创建目录结构：`auth/`、`user/` 以及公用的 `support/` 目录
- [x] 11.2 在 `features/ui_steps/support/db-factory.ts` 中封装调用 Python `features/factories/seeding.py` 的逻辑（通过 Node child_process 执行 `uv run python` 脚本注入测试数据）
- [x] 11.3 实现 Auth 登录场景步骤文件 `features/ui_steps/auth/signin.spec.ts`：Given（注入 Charlie admin 用户）、When（Playwright 填写登录表单并提交）、Then（断言跳转到认证区域）
- [x] 11.4 实现 User 列表场景步骤文件 `features/ui_steps/user/user-list.spec.ts`：Given（注入 Charlie admin 用户并登录）、Then（断言 `users-table` 可见，且至少一行 `users-table-row` 存在）
- [x] 11.5 以 MSW 模式执行 `pnpm exec nx run ux-uat:test-ui-uat`（需先确保 dev server 以 `VITE_MSW_ENABLED=true` 运行），验证所有 UI 步骤通过
- [x] 11.6 以集成模式执行（后端已启动），验证 Auth 和 User 列表场景在真实后端下也通过
