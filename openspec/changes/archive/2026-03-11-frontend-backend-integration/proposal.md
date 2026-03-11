## Why

前端页面（用户列表、登录、忘记密码）目前通过硬编码的 faker.js 假数据来模拟页面状态，与后端已实现的 FastAPI 用户和认证接口完全脱节。同时前端枚举值（如用户角色）与后端定义不一致，导致前后端无法直接对接。现在后端接口趋于稳定，是推进前后端集成、建立契约驱动开发流程的最佳时机。

## What Changes

- 从 FastAPI 后端导出 OpenAPI 规范文档作为接口契约
- 使用 Orval 基于契约生成前端 API Client（类型安全的请求函数）和 MSW mock 处理器代码
- 将前端 Users 页面、Auth 登录页等从硬编码假数据迁移到 MSW mock server 驱动
- **BREAKING**: 统一用户角色枚举，将前端的 `superadmin / admin / manager / cashier` 替换为后端的 `super_admin / admin / user`，同步影响 schema、data、UI 显示层
- 统一用户状态枚举：后端目前只有 `active / inactive`，前端有 `invited / suspended`，需明确对齐范围（当前阶段前端 UI 保留额外状态但 API 层只使用后端支持的值）
- 为自编写的前端组件添加 `data-testid` 属性，提升 UI 自动化测试稳定性
- 在现有 BDD Feature 基础上新增 `ui_step` Playwright 步骤文件，实现端到端 UI 测试（先跑通 MSW mock，再集成后端）
- 对前端已展示但功能未实现的按钮（如 Invite Users）添加 `disabled` 属性或点击提示，防止用户误触，保留页面外观

## Capabilities

### New Capabilities

- `api-contract-export`: 从 FastAPI 导出 OpenAPI JSON 规范，作为前后端接口契约的唯一真相来源
- `frontend-api-client`: 使用 Orval 基于 OpenAPI 契约生成类型安全的前端 API Client 代码（react-query hooks + axios）
- `frontend-msw-integration`: 集成 MSW（Mock Service Worker），用 Orval 生成的 handler 替代 faker.js 硬编码数据，支持开发和测试环境
- `user-role-enum-alignment`: 统一前后端用户角色枚举定义（`super_admin / admin / user`），更新前端 schema、data 文件及 UI 显示层
- `ui-e2e-playwright-steps`: 新增 Playwright 驱动的 `ui_step` 步骤文件，补充现有 BDD Feature 中的端到端 UI 测试场景
- `unimplemented-feature-stubs`: 对尚未实现的前端功能入口进行安全处理（添加 disabled 或 toast 提示），避免用户误操作

### Modified Capabilities

（无需求级别变更，现有后端 BDD spec 不涉及前端 UI 层）

## Impact

- **前端代码**: `shadcn-admin/src/features/users/`, `shadcn-admin/src/features/auth/`，涉及 schema、data、组件文件
- **前端构建配置**: `shadcn-admin/` 的 `vite.config.ts`、`package.json`，需新增 Orval、MSW 依赖及配置
- **BDD 测试**: `features/` 目录，新增 `ui_step` 目录及 Playwright 步骤实现
- **Nx 项目配置**: `shadcn-admin/project.json`，可能新增 `orval:generate`、`msw:init` 等 target
- **后端 FastAPI**: `fastapi-clean-example/`，新增 openapi.json 导出脚本或 Nx target
- **依赖**: 新增 `orval`、`msw`、`@tanstack/react-query`（如未引入），以及测试侧的 `playwright`
