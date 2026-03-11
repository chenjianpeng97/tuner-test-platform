## Why

当前 `features/ui/` 目录下存在专为前端界面编写的独立 Gherkin 文件（`auth_ui.feature`、`user_list_ui.feature`），这些文件将前端渲染逻辑与系统级 BDD 测试混为一谈，导致测试覆盖策略分裂：系统功能没有被统一描述，纯 UI 渲染细节（按钮是否可见、表格是否渲染）被错误地放入 BDD 层。同时，`features/ui_steps/` 当前包含 TypeScript + Playwright 的 `.spec.ts` 文件，与基于 Python behave 的主 BDD 运行时完全脱节。现在是时候整理清楚分层边界，让 BDD 专注于系统功能验证。

## What Changes

- **BREAKING**: 删除 `features/ui/auth_ui.feature` 和 `features/ui/user_list_ui.feature`，这两个文件描述的是纯前端渲染断言，不属于系统级 BDD 范畴
- **BREAKING**: 删除 `features/ui_steps/auth/signin.spec.ts`、`features/ui_steps/user/user-list.spec.ts`、`features/ui_steps/support/db-factory.ts`——这些 TypeScript Playwright spec 文件不属于 behave 驱动的 BDD 流程
- 将原 `auth_ui.feature` / `user_list_ui.feature` 中涉及的纯前端渲染断言迁移为 Cypress 组件测试，放入 `shadcn-admin/` 项目
- 统一 BDD 测试入口：所有系统功能 Gherkin 描述只存在于 `features/` 根目录（已有 `auth.feature`、`user.feature`），同一套 `.feature` 文件同时服务 `stage:http` 和 `stage:ui` 两套 step 实现
- 新建 `features/ui_steps/` 目录（Python），存放基于 Python + Playwright + behave 的 UI stage step 定义，使用 Page Object 设计模式
- 迁移并规范已有的 Page Object 类（`features/ui/pages/`）到 `features/ui_steps/pages/`，统一作为 UI steps 的基础设施
- 新建 `features/ui_environment.py`（或使用 behave 环境钩子），用于管理 Playwright browser/page 生命周期

## Capabilities

### New Capabilities
- `bdd-ui-step-layer`: UI stage 的 behave step 实现，Python + Playwright，覆盖 `auth.feature` 和 `user.feature` 中场景的浏览器端验证
- `bdd-stage-separation`: 明确区分 `stage:http`（behave + httpx，驱动 `features/http_steps/`）与 `stage:ui`（behave + playwright，驱动 `features/ui_steps/`）的运行配置，同一套 `.feature` 文件通过不同 stage 分别执行
- `bdd-page-objects`: Page Object 模式的结构规范，定义 `BasePage`、`SignInPage`、`UsersPage` 等类的接口契约，作为 UI steps 的可复用基础设施

### Modified Capabilities
<!-- 无现有 spec 级行为变更，feature 文件本身描述的系统行为不变 -->

## Impact

- `features/ui/auth_ui.feature` — 删除
- `features/ui/user_list_ui.feature` — 删除
- `features/ui/steps/auth_ui_steps.py`、`features/ui/steps/user_list_ui_steps.py` — 删除（被新 ui_steps 替代）
- `features/ui_steps/*.spec.ts` — 删除（TypeScript Playwright spec，不属于 behave 体系）
- `features/ui/pages/` — 迁移至 `features/ui_steps/pages/`
- `features/ui_steps/`（Python）— 新建，包含 step 定义和 Page Objects
- `shadcn-admin/` — 新增 Cypress 组件测试，覆盖原 UI-only feature 文件中的渲染断言
- `fastapi-clean-example/` 后端服务无变更
