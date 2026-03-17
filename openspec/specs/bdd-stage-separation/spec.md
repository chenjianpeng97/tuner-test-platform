## Purpose

定义同一套 BDD feature 文件在 HTTP 与 UI 两种 stage 下独立运行的规范。

## Requirements

### Requirement: 同一 feature 文件集合支持两套 stage 运行
项目 BDD 测试 SHALL 支持使用同一套 `features/*.feature` 文件，分别以 `stage:http` 和 `stage:ui` 两种模式独立运行，不依赖分离的 feature 文件副本。

#### Scenario: HTTP stage 运行
- **WHEN** 执行 `pnpm nx run fastapi-clean-example:bdd-http`
- **THEN** behave SHALL 以 `features/http_steps/` 为 steps-dir
- **THEN** 所有场景 SHALL 通过 HTTP 客户端（httpx）与后端 API 交互完成验证
- **THEN** Playwright 浏览器 SHALL NOT 被启动

#### Scenario: UI stage 运行
- **WHEN** 执行 `pnpm nx run fastapi-clean-example:bdd-ui`
- **THEN** behave SHALL 以 `features/ui_steps/` 为 steps-dir
- **THEN** 所有场景 SHALL 通过 Playwright 浏览器与前端应用交互完成验证
- **THEN** HTTP 客户端 SHALL NOT 直接调用后端 API（除 DB seeding 基础设施外）

### Requirement: Nx project.json 中定义两个独立 BDD target
`fastapi-clean-example/project.json` SHALL 包含 `bdd-http` 和 `bdd-ui` 两个独立的 Nx target，分别配置各自的 behave 运行参数。

#### Scenario: bdd-http target 配置
- **WHEN** 查看 `fastapi-clean-example/project.json` 中的 `bdd-http` target
- **THEN** 该 target SHALL 配置 behave 命令并指定 `--steps-dir features/http_steps`
- **THEN** 该 target SHALL 指向 `features/` 根目录的 `.feature` 文件

#### Scenario: bdd-ui target 配置
- **WHEN** 查看 `fastapi-clean-example/project.json` 中的 `bdd-ui` target
- **THEN** 该 target SHALL 配置 behave 命令并指定 `--steps-dir features/ui_steps`
- **THEN** 该 target SHALL 配置 `BASE_URL` 和 `E2E_MODE` 环境变量

### Requirement: 删除 features/ui/ 中的独立 UI feature 文件
`features/ui/auth_ui.feature` 和 `features/ui/user_list_ui.feature` SHALL 被删除，不再作为 BDD 测试入口。

#### Scenario: 删除后 behave 不再执行 UI-only feature
- **WHEN** 运行任意 behave stage（http 或 ui）
- **THEN** `auth_ui.feature` 和 `user_list_ui.feature` 中描述的场景 SHALL NOT 被 behave 执行
- **THEN** 这些场景对应的前端渲染断言 SHALL 由 `shadcn-admin/` 中的 Cypress 测试覆盖

### Requirement: 删除 features/ui_steps/ 中的 TypeScript spec 文件
`features/ui_steps/` 目录下的 `.spec.ts` 文件（`auth/signin.spec.ts`、`user/user-list.spec.ts`、`support/db-factory.ts`）SHALL 被删除。

#### Scenario: ui_steps 目录仅包含 Python 文件
- **WHEN** 检查 `features/ui_steps/` 目录内容
- **THEN** 该目录 SHALL 只包含 Python 文件（`.py`）和子目录
- **THEN** 该目录 SHALL NOT 包含任何 `.ts` 或 `.spec.ts` 文件
