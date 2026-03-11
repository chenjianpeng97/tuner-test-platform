## ADDED Requirements

### Requirement: 通过 Orval 生成类型安全的前端 API Client
系统 SHALL 提供 Nx target `app-web:generate-api`，基于 `openspec/contracts/app-api.openapi.json` 通过 Orval 生成以下代码：
- `shadcn-admin/src/api/generated/`：使用 axios + `@tanstack/react-query` 的类型安全请求 hooks
- `shadcn-admin/src/mocks/handlers/`：MSW request handler 函数

生成的代码 SHALL：
- 覆盖所有已导出的 API 端点
- 包含基于 OpenAPI schema 派生的 TypeScript 类型定义
- 不被手动修改（作为可重建产物管理）

#### Scenario: 执行代码生成后产物存在
- **WHEN** 执行 `pnpm exec nx run app-web:generate-api`
- **THEN** `shadcn-admin/src/api/generated/` 和 `shadcn-admin/src/mocks/handlers/` 目录被创建，包含 TypeScript 文件

#### Scenario: 生成代码可通过 TypeScript 编译
- **WHEN** 在 `shadcn-admin/` 目录执行 TypeScript 类型检查
- **THEN** 生成的 API client 文件无类型错误

### Requirement: 前端业务代码通过生成的 hooks 调用 API
前端 Users 页和 Auth 相关页面 SHALL 使用 Orval 生成的 react-query hooks 进行数据获取，而不是直接构造 axios 请求或使用硬编码数据。

#### Scenario: Users 页面使用生成的 query hook 获取列表
- **WHEN** Users 页面挂载且 MSW 或后端服务可用
- **THEN** 页面通过生成的 hook（如 `useGetUsers`）发起请求，并渲染返回的用户数据

#### Scenario: 登录使用生成的 mutation hook
- **WHEN** 用户提交登录表单
- **THEN** 表单使用生成的 `useLogin` mutation hook 调用 `POST /api/v1/auth/login`

### Requirement: 生成代码目录在 `.gitignore` 中标注为可重建产物
`shadcn-admin/src/api/generated/` 和 `shadcn-admin/src/mocks/handlers/` SHALL 被加入 `.gitignore`（或等效配置），明确标注为可重建文件，避免手动修改后被意外提交。

#### Scenario: 生成目录被 git 忽略或有明确注释
- **WHEN** 检查 `shadcn-admin/.gitignore` 或目录内的 README
- **THEN** 存在对生成代码目录的忽略规则或明确说明
