## ADDED Requirements

### Requirement: 新增 `features/ui_steps/` 目录作为 UI BDD 步骤层
系统 SHALL 在 `features/` 目录下新增 `ui_steps/` 子目录（与 `http_steps/` 并列），包含基于 Playwright 的 TypeScript UI 步骤实现，供 BDD Feature 文件以 `--stage ui` 模式运行。

目录结构 SHALL 包含：
- `features/ui_steps/`：Playwright 步骤主目录
- `ux-uat/playwright.config.ts`：Playwright 项目配置，引用 `features/ui_steps/` 作为测试目录
- `ux-uat/project.json` 中新增 target `ux-uat:test-ui-uat`：封装 Playwright 运行命令

#### Scenario: UI 步骤目录结构存在
- **WHEN** 检查 `features/ui_steps/` 目录
- **THEN** 目录存在，包含 Auth 和 User 场景的步骤实现文件

#### Scenario: `ux-uat:test-ui-uat` Nx target 可执行
- **WHEN** 执行 `pnpm exec nx run ux-uat:test-ui-uat`（前端 dev server 已启动且 MSW 已开启）
- **THEN** Playwright 测试运行，不报告"找不到测试文件"类错误

### Requirement: 实现 Auth 登录场景的 UI 步骤
`features/auth.feature` 中的 `Scenario: Login succeeds for an active identity` 场景 SHALL 有对应的 UI 步骤实现：
- Given 步骤通过 `features.factories` 注入测试用户（通过 Python subprocess 或直接调用）
- When 步骤通过 Playwright 在登录页面填写用户名/密码并点击提交
- Then 步骤断言页面跳转到已认证区域（如 dashboard 或 users 页）

相关 UI 组件 SHALL 具有 `data-testid` 属性，使 Playwright selector 稳定可靠：
- 用户名输入框：`data-testid="auth-signin-username"`
- 密码输入框：`data-testid="auth-signin-password"`
- 提交按钮：`data-testid="auth-signin-submit"`

#### Scenario: MSW 模式下登录 UI 测试通过
- **WHEN** 以 `VITE_MSW_ENABLED=true` 运行 dev server，Playwright 执行登录场景
- **THEN** 登录步骤成功，页面跳转到认证后区域，断言通过

#### Scenario: 集成后端模式下登录 UI 测试通过
- **WHEN** 真实后端运行，以 `VITE_MSW_ENABLED=false` 运行 dev server，Playwright 执行登录场景
- **THEN** 前端通过真实 API 完成登录，断言通过

### Requirement: 实现 User 列表查看场景的 UI 步骤
用户列表查看场景（已登录后访问 Users 页面）SHALL 有对应 UI 步骤实现，包含：
- 前置：注入具有 `admin` 角色的测试用户并完成登录
- 断言：页面上可见用户列表表格，至少一行数据可见

相关 UI 组件 SHALL 具有 `data-testid` 属性：
- 用户列表表格容器：`data-testid="users-table"`
- 表格行（可含序号）：`data-testid="users-table-row"`

#### Scenario: MSW 模式下用户列表页渲染正确
- **WHEN** MSW 启用，已登录用户导航至 Users 页面
- **THEN** Playwright 能找到 `data-testid="users-table"` 元素，且至少存在一行用户数据

### Requirement: Playwright 配置支持 MSW 和真实后端两种运行模式
`ux-uat/playwright.config.ts` SHALL 通过环境变量区分运行模式：
- `E2E_MODE=mock`：使用 MSW dev server（`VITE_MSW_ENABLED=true`），不依赖真实后端
- `E2E_MODE=integration`：使用真实后端，前端关闭 MSW

#### Scenario: mock 模式下无需后端服务即可执行 UI 测试
- **WHEN** 设置 `E2E_MODE=mock` 并执行 `ux-uat:test-ui-uat`（后端未启动）
- **THEN** 所有 mock 模式 UI 测试通过
