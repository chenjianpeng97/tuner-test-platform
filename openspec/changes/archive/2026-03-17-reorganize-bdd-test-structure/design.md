## Context

当前项目 BDD 测试结构处于过渡状态，存在以下问题：

1. `features/ui/` 下包含独立的 UI-only `.feature` 文件（`auth_ui.feature`、`user_list_ui.feature`），这些文件与系统级 `features/auth.feature`、`features/user.feature` 并列，但描述的是纯前端渲染断言，不是系统行为
2. `features/ui_steps/` 当前存放 TypeScript `.spec.ts` 文件（Playwright），与 behave (Python) 运行时完全隔离，造成两套 UI 测试机制并存
3. UI steps 已有雏形的 Page Object（`features/ui/pages/`），但其位置和归属不清晰
4. `features/http_environment.py` 和 `features/ui/environment.py` 分别管理 HTTP 和 UI 的 behave 生命周期，模式基本健全但需要统一目录约定

目标状态：一套 `.feature` 文件 → 两套 stage 运行：`stage:http`（behave + httpx）和 `stage:ui`（behave + playwright），Page Object 模式规范化。

## Goals / Non-Goals

**Goals:**
- 删除 `features/ui/*.feature` 中的纯 UI 渲染断言 feature 文件，前端渲染测试交给 Cypress
- 统一 BDD feature 文件：只保留 `features/` 根目录的系统级 `.feature` 文件（`auth.feature`、`user.feature`），同时服务 http 和 ui 两套 stage
- 将 `features/ui_steps/` 改造为 Python behave UI step 定义目录，包含 Page Objects
- 规范 Page Object 类的目录位置：迁移至 `features/ui_steps/pages/`
- 为 `shadcn-admin/` 添加 Cypress 组件测试，覆盖原 UI-only feature 中的渲染断言

**Non-Goals:**
- 不修改已有 `features/auth.feature` 和 `features/user.feature` 的 Gherkin 描述内容
- 不改变 `features/http_steps/` 中已有的 HTTP step 实现
- 不修改 `fastapi-clean-example/` 后端服务
- 不引入新的测试框架；Cypress 已是 `shadcn-admin/` 的预期生态

## Decisions

### Decision 1: 统一 feature 文件，通过 behave tag / profile 区分 stage

**选择**: 使用单一 `.feature` 文件集合 + behave `--include-re` 或 `tags` 方式分别运行 http step 和 ui step，而不维护两套 feature 文件。

**理由**: 避免场景漂移——两套 feature 文件长期会不同步。同一套场景描述通过不同 step 实现分别在 HTTP 层和浏览器层验证，是标准 BDD 多层测试实践。

**替代方案**: 分别维护 `features/http/` 和 `features/ui/` 目录 → 拒绝，因为 feature 文件重复维护成本高。

**实现**: 在 `nx.json` / `project.json` 中为 `fastapi-clean-example` 维护两个 behave 运行目标：`bdd-http`（使用 `features/http_steps/`）和 `bdd-ui`（使用 `features/ui_steps/`）。两者均指向同一 `features/*.feature`。

### Decision 2: Page Object 统一放置于 `features/ui_steps/pages/`

**选择**: 将现有 `features/ui/pages/` 迁移至 `features/ui_steps/pages/`，使 pages 与 steps 同目录。

**理由**: Page Object 是 UI steps 的专属基础设施，放在 steps 同级目录使依赖关系直观，也便于 behave 的 `environment.py` 导入。

**替代方案**: 放在顶层 `features/pages/` → 拒绝，因为 Page Object 概念仅属于 UI stage，不应暴露给 HTTP stage。

### Decision 3: UI behave environment 移至 `features/ui_steps/environment.py`

**选择**: 将 `features/ui/environment.py` 迁移并重命名为 `features/ui_steps/environment.py`，由此文件管理 Playwright browser/context 生命周期。

**理由**: behave 的 `environment.py` 文件约定是与 steps 同目录，当前 `features/ui/environment.py` 的位置是因为 feature 文件也在 `features/ui/`；feature 文件移除后，environment.py 应跟随 steps。

### Decision 4: TypeScript `.spec.ts` 文件从 `features/ui_steps/` 移除

**选择**: 删除 `features/ui_steps/auth/signin.spec.ts`、`features/ui_steps/user/user-list.spec.ts`、`features/ui_steps/support/db-factory.ts`。

**理由**: 这些文件是遗留的 Playwright TypeScript spec，不由 behave 驱动，也不属于 `ux-uat` Nx 项目的测试路径（`ux-uat` 使用独立的 `playwright.config.ts`）。保留会造成目录职责混乱。

### Decision 5: 前端渲染断言迁移至 Cypress 组件测试

**选择**: 在 `shadcn-admin/src/` 下添加 Cypress 组件测试（`.cy.tsx`），覆盖原来 `auth_ui.feature` / `user_list_ui.feature` 中的渲染断言。

**理由**: 是否可以渲染登录表单、用户列表表格、按钮状态——这些是纯前端组件行为，Cypress 组件测试比 BDD + Playwright 更轻量、更快、更贴近 React 组件的测试范式。

## Risks / Trade-offs

- **[Risk] step 定义冲突**: 两套 step 文件（http_steps 和 ui_steps）共用同一套 feature 文件时，behave 可能加载两套 steps 导致冲突。→ **Mitigation**: 通过不同 behave 命令行入口（`--steps-dir`）分别加载，确保运行时相互隔离。
- **[Risk] 共享 Background step 实现差异**: `Given I am signed in as "charlie01"` 在 http 和 ui 两套 steps 中实现逻辑不同（API 调用 vs 浏览器登录）。→ **Mitigation**: 两套 steps 分别实现同名 step，behave 按 steps-dir 加载，不会互相干扰。
- **[Risk] Page Object 迁移路径中临时断开**: `features/ui/pages/` 迁移期间旧路径导入会失败。→ **Mitigation**: 迁移与删除旧 feature 文件一并进行，不留中间状态。
- **[Trade-off] Cypress vs Playwright for 组件测试**: `shadcn-admin` 已有 Vite + React 生态，Cypress 组件测试需单独安装。但相比在 behave 层维护纯 UI 断言，Cypress 更符合前端项目的测试约定。
