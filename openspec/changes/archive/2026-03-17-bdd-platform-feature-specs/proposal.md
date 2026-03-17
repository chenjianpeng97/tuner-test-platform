## Why

当前平台仅具备用户管理和认证等基础 API，没有 BDD 测试生命周期的统一管理入口。团队需要一个类似 Cucumber Studio 的平台，在 Web 界面中集中管理 Feature 文件、追踪覆盖率、规划测试执行并触发 Behave 自动化——以便将 BDD 活动从分散的命令行操作转变为可见、可追溯的工程实践。

## What Changes

- 新增多项目隔离管理：每个 Project 关联一个 Git 仓库，Feature 文件通过 Git 读写
- 新增 Feature 文件浏览：树形结构展示（支持 Gherkin 6 `Rule` 关键字层级），带语法高亮
- 新增在线编辑器：基于 CodeMirror 6，含 Step 自动补全（前缀匹配已有 step 文本）和 Git commit 保存
- 新增测试覆盖率看板：导入 JUnit XML 结果，按 feature+scenario 名称映射，展示覆盖状态
- 新增测试计划管理：从 Feature 树勾选 Scenario 组成计划，支持手动状态更新
- 新增 BDD 自动化执行：后端 subprocess 执行 behave，SSE 实时推送日志，自动解析结果写库

## Capabilities

### New Capabilities

- `bdd-project-management`: Project 的 CRUD 管理，Git 仓库关联配置（URL / Branch / Access Token / 本地 work dir），手动触发 Git 同步拉取 Feature 文件，多项目数据完全隔离
- `bdd-feature-browser`: 以树形结构（目录 > Feature > Rule > Scenario）展示 Project 内的 Feature 文件，支持 Gherkin 6 语法解析（含 `Rule`），点击预览带高亮的原始内容，展示场景数量统计
- `bdd-feature-editor`: 在线 CodeMirror 编辑器，提供 Gherkin 语法高亮与校验，Step 自动补全（前缀模糊匹配本 Project 内所有已有 step 文本），保存时提交 Git commit（含 commit message）
- `bdd-coverage`: 导入 behave JUnit XML 执行结果，通过 `feature 名称 + scenario 名称` 映射到具体 Scenario，在 Feature 树中展示覆盖标记（已覆盖/未覆盖/最近失败），提供 Project 级覆盖率 Dashboard
- `bdd-test-plan`: Project 内创建/编辑/删除测试计划，从 Feature 树勾选 Scenario 加入计划，每项状态（未执行/通过/失败/跳过/阻塞）可手动更新，展示整体进度，支持从 TestRun 结果批量同步状态
- `bdd-execution`: 在界面触发 behave 执行（范围：Project / Feature / Tag），后端 asyncio subprocess 执行，SSE 实时推送日志，执行完成后自动解析 JUnit XML 写入 TestRunResult 并更新覆盖率，历史 TestRun 列表可查

### Modified Capabilities

<!-- 现有 specs 均为 user/auth 相关 API 行为，本次变更不涉及其需求变更 -->

## Impact

- **后端**（`fastapi-clean-example/src/`）：新增 5 个领域模块（projects / features / coverage / test-plans / execution），新增 Alembic 迁移（Project、Feature、Scenario、Step、TestPlan、TestPlanItem、TestRun、TestRunResult 表），引入 `GitPython`、`gherkin-official` 依赖，SSE endpoint 需 FastAPI `StreamingResponse`；在线编辑器为纯前端 UI 能力，其保存操作复用 features 模块的写接口（PUT + Git commit），step 补全为 features 模块下的查询接口
- **前端**（`shadcn-admin/src/`）：新增 9 个页面路由，引入 `CodeMirror 6` 编辑器及 Gherkin 语言扩展，复用现有 TanStack Query + Zustand 模式
- **API**：新增 `/api/v1/projects/**` 路由族，不影响现有 `/api/v1/users/**` 和 `/api/v1/auth/**`
- **依赖**：后端新增 `gitpython`、`gherkin-official`；前端新增 `@codemirror/state`、`@codemirror/view`、`@codemirror/lang-*`
