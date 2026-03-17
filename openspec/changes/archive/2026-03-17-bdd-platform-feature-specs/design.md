## Context

现有平台基于 `fastapi-clean-example`（FastAPI + SQLAlchemy + PostgreSQL，clean architecture）和 `shadcn-admin`（React 18 + TypeScript + TanStack Router + TanStack Query + Zustand）。代码结构遵循领域分层，已有用户管理和认证模块作为参考范式。本次设计需在不破坏现有 API 的前提下，新增 BDD 平台的完整后端领域和前端页面。

新增功能涉及 1 个顶层共享域（projects）+ 4 个 BDD 子域（features / coverage / test-plans / execution）、约 14 张新数据表、Git 操作、Gherkin 文件解析、subprocess 进程管理和 SSE 日志推送，是一个跨多模块的系统级新增。

## Goals / Non-Goals

**Goals:**
- 完整的 BDD 测试管理生命周期：Feature 管理 → 覆盖率追踪 → 测试计划 → 执行（全自动 + 混合手动）
- Feature 文件通过 Git 版本控制，平台作为 Git 内容的读写代理
- Sub-Feature 目录树约定（同名目录为子 feature）统一代码仓库与平台视图
- 混合执行（Hybrid Execution）：逐 Step 执行，允许自动化与手动测试混合在一个 Scenario 会话中完成
- 第一期全员相同权限，API 无额外授权层

**Non-Goals:**
- 用户角色/权限管理
- 远程 Agent 或 CI/CD 触发执行
- Feature 文件历史版本对比（Git log viewer）
- Playwright/其他测试框架支持

---

## Decisions

### D1：Feature 文件存储与同步策略

**决策**：使用 GitPython 将 Git 仓库克隆/拉取到服务器本地临时目录，双写策略：内容缓存于 PostgreSQL（Feature.content 字段），以 git_sha 作为变更检测键，每次同步对比 SHA 判断是否需要重新解析。

**理由**：数据库缓存避免每次浏览都实时读文件；git_sha 对比避免重复解析无变化文件；GitPython 提供完整的 Git 操作 API（clone / pull / commit / push）。

**备选方案**：直接挂载文件系统目录 → 需要运维配置，不适合多 Project 隔离；调用 Git HTTP API → 增加外部依赖。

---

### D2：Sub-Feature 目录约定的识别算法

**决策**：Git 同步时对仓库目录树执行以下算法：
1. 递归扫描所有 `.feature` 文件，按文件路径排序
2. 对每个文件 `<dir>/<name>.feature`，检查同级是否存在目录 `<dir>/<name>/`
3. 若存在，将 `<dir>/<name>/` 下所有 `.feature` 文件的 `parent_feature_id` 指向该文件的 Feature 记录
4. 递归处理每一层，支持任意深度嵌套

**Feature 表新增字段**：`parent_feature_id` (nullable FK → Feature.id)，`depth`（缓存层级深度，减少递归查询）。

**理由**：约定优于配置，符合现有项目目录结构（`user.feature` + `user/`），前端无需额外配置即可呈现树形层级。

---

### D3：Gherkin 解析库选型

**决策**：使用 `gherkin-official`（PyPI 包 `gherkin`，Cucumber 官方 Python binding），并通过 `@cucumber/gherkin` 的 Python API 解析 `.feature` 文件为结构化 AST。

**理由**：官方维护，支持 Gherkin 6（`Rule` 关键字），解析输出完整的 AST，包含行号信息（用于 Step 定位），与 behave 使用相同语法标准。

**Step 录入**：解析时遍历每个 Scenario 的每个 Step，将 `keyword + text` 写入 `Step` 表，project_id 分区。Step 表仅作为补全索引，不参与执行逻辑。

---

### D4：BehaveStage 发现与 StepCoverage 分析

**决策**：Git 同步时扫描 behave 工作目录，识别所有 `*_steps/` 目录，注册为 `BehaveStage` 记录。随后对每个 stage 的步骤定义文件（`*.py`），使用正则表达式提取 `@step('...')` / `@given(...)` / `@when(...)` / `@then(...)` 装饰器中的 pattern 字符串，对每个 Scenario 的每个 Step 文本进行匹配，写入 `StepCoverage` 记录。

**匹配策略**：将 behave pattern 中的参数占位符（`{name}`、`"([^"]*)"` 等）转换为正则，对 Step 文本进行 fullmatch。

**理由**：静态分析步骤定义，无需运行 behave 即可得到覆盖矩阵；与 behave 原生 stage 机制一致（`--stage <name>` 查找 `<name>_steps/`）。

---

### D5：混合执行（Hybrid Execution）的状态机

**决策**：引入 `ScenarioExecution` 表记录单次会话，`StepExecutionRecord` 表记录每个 Step 的执行状态（pending → pass / fail / skip）。

**状态机**：
```
ScenarioExecution.status:
  in_progress → (所有 step ≠ pending) → pass / fail / partial

StepExecutionRecord.status:
  pending → (auto: behave 结果) → pass / fail
  pending → (manual: 用户提交) → pass / fail / skip
```

**自动执行实现**：对单个 Step 的自动化执行，通过 `behave --stage <stage> --no-capture --include <file> --name "<scenario>"` 运行整个 Scenario，从 behave 的 JSON 输出中提取对应 Step 的执行结果，不依赖 behave 的 step-level 执行控制。

**失败兜底规则（Q4 决议）**：当 `Given` 的自动执行失败时，不阻断后续人工流程。用户可对该 `Given` 以 manual 模式补录并标记为 `pass`，但系统必须保留自动执行失败记录（`execution_mode=auto, status=fail`）及对应日志链接/片段（`test_runs.log_path` + `step_execution_records.error_message`），用于测试开发定位与修复自动化脚本。

**理由**：behave 不支持单步执行，但可以通过解析 JSON 格式报告取得每个 step 的结果，粒度足够。

---

### D6：SSE 日志推送架构

**决策**：使用 FastAPI 的 `StreamingResponse` + `asyncio.Queue` 模式：behave subprocess 的 stdout 通过 `asyncio.create_subprocess_exec` 的 `PIPE` 捕获，每读到一行写入 asyncio Queue，SSE endpoint 从同一 Queue 消费并以 `data: ...\n\n` 格式推送。日志同时写入服务器本地文件（`log_path`），供历史回看。

**理由**：asyncio 原生支持，无需引入 Redis 或消息队列；Queue 解耦生产（subprocess）和消费（SSE 连接），支持多客户端同时连接同一 TestRun 的日志流（广播模式可通过维护多个 Queue 实现）。

---

### D7：前端编辑器 Step 补全实现

**决策**：使用 CodeMirror 6 的 `@codemirror/autocomplete` 扩展，在用户输入 `Given `、`When `、`Then `、`And `、`But ` 关键字后的文本时，触发对 `GET /api/v1/projects/{id}/steps/suggest?q=<prefix>` 的异步请求，将返回结果显示为补全候选列表。

**触发时机**：检测到当前行以 Gherkin step 关键字开头且光标在关键字后，防抖 300ms 触发请求。

---

### D8：数据库 Schema 总览

新增表及关键字段（Alembic 迁移顺序）：

```
── 顶层共享域 ──

1. projects
   id, name, description, created_at, updated_at
   （仅项目核心信息，不含任何工具或协议细节）

2. project_git_configs          ← projects 模块子表
   id, project_id (→ projects.id, UNIQUE),
   git_repo_url, git_branch, git_access_token_encrypted
   （Git 集成配置；预留给未来手工测试/单元测试复用）

── BDD 域 ──

3. project_behave_configs       ← bdd/features 模块子表
   id, project_id (→ projects.id, UNIQUE),
   behave_work_dir
   （behave 执行配置；仅 BDD 域使用）

4. features
   id, project_id, file_path, git_sha, content,
   feature_name, parent_feature_id (→ features.id), depth, parsed_at

5. scenarios
   id, feature_id, project_id, rule_name, scenario_name,
   tags (JSONB), line_number

6. steps (补全索引)
   id, scenario_id, project_id, keyword, text

7. behave_stages
   id, project_id, stage_name, steps_dir_path

8. step_coverages
   id, step_id, stage_id, coverage_status (covered/uncovered)

9. test_plans
   id, project_id, name, description, created_at, updated_at

10. test_plan_items
    id, test_plan_id, scenario_id, status, notes, updated_at

11. test_runs
    id, project_id, test_plan_id (nullable), triggered_at, completed_at,
    status, scope_type, scope_value, executor_config (JSONB), log_path

12. test_run_results
    id, test_run_id, scenario_id (nullable), feature_name, scenario_name,
    status, duration_seconds, error_message, stack_trace

13. scenario_executions
    id, project_id, scenario_id, test_plan_item_id (nullable),
    status (in_progress/pass/fail/partial), created_at, completed_at

14. step_execution_records
    id, scenario_execution_id, step_id, step_order,
    execution_mode (auto/manual), status (pending/pass/fail/skip),
    stage_id (nullable), executor, executed_at, notes, error_message
```

**表拆分理由**：`projects` 只持有项目本身的信息（名称、描述），Git 集成配置与 behave 执行配置各自内聚于独立子表，通过 `project_id` 外键关联。未来新增手工测试域时，只需读 `projects` 和 `project_git_configs`，无需感知 `project_behave_configs`。

---

### D9：后端模块结构（clean architecture 沿用）

**核心原则**：`projects` 是跨业务域的共享实体，提升为顶层模块；`bdd/` 只包含 BDD 特定逻辑，通过依赖注入引用顶层 `projects` 域的 Repository。未来新增 `manual_test/`、`unit_test/` 域时，同样引用顶层 `projects/`，无需触碰 `bdd/`。

```
fastapi-clean-example/src/
  projects/                          ← 顶层共享域（与 user/ auth/ 平级）
    domain/
      project.py                     (Project, ProjectGitConfig entities)
      project_repository.py          (ProjectRepository protocol)
    gateway/
      sqlalchemy_project_repo.py     (SQLAlchemy impl)
      git_sync_service.py            (GitPython clone/pull/push)
    api/
      router.py                      (Project CRUD + Git config endpoints)
      schemas.py

  bdd/                               ← BDD 业务域（引用 projects/，不反向依赖）
    features/
      domain/
        feature.py                   (Feature, Scenario, Step, ProjectBehaveConfig)
        feature_repository.py
      gateway/
        sqlalchemy_feature_repo.py
        gherkin_parser.py            (gherkin-official AST 解析)
        step_coverage_analyzer.py    (正则匹配 @step 装饰器)
      api/
    coverage/
      domain/   (JUnit XML importer, coverage calculator)
      gateway/
      api/
    test_plans/
      domain/
      gateway/
      api/
    execution/
      domain/   (TestRun, ScenarioExecution, StepExecutionRecord)
      gateway/  (BehaveRunner, SSE log streamer, result parser)
      api/
```

**依赖关系**：`bdd/*` → `projects/domain`（单向），`projects/` 不导入任何 `bdd/` 符号。

---

## Risks / Trade-offs

- **[Git 操作阻塞]** GitPython 的 clone/pull 在大型仓库可能耗时较长 → 将 Git 同步操作放入 BackgroundTasks，立即返回 202，前端轮询同步状态
- **[Step pattern 解析不完整]** 正则提取 Python 装饰器 pattern 可能漏掉动态注册的 step（如 `step_matcher`）→ 第一期仅支持标准装饰器，复杂场景标记为 uncovered
- **[并发执行锁]** 同一 Project 同时触发多个 TestRun 可能引发 behave 工作目录冲突 → 第一期每个 Project 同一时刻只允许一个 running 状态的 TestRun，重复触发返回 409
- **[PAT 安全存储]** Access Token 需加密存储 → 使用 `cryptography.fernet` 对称加密，密钥通过环境变量注入，不存入数据库
- **[SSE 连接泄漏]** 客户端断连后服务端需清理 asyncio Queue → 使用 `try/finally` 确保 SSE generator 退出时释放资源

## Migration Plan

1. 新增 Alembic 迁移文件（按 D8 顺序，14 张表；顺序：projects → project_git_configs → project_behave_configs → features → … → step_execution_records）
2. 后端新增顶层 `projects/` 模块和 `bdd/` 模块，在 `api_v1_router` 中注册新路由，不修改现有 user/auth 路由
3. 前端在 `shadcn-admin/src/routes/` 下新增 `/projects` 路由树，不修改现有路由
4. 第一期无需数据迁移（全为新表新数据）

**回滚**：迁移脚本提供 `downgrade`，直接 `alembic downgrade` 即可回退所有新表。

## Open Questions

- Q1：Git Access Token 是否需要支持 SSH Key（第一期建议仅 PAT，待确认）
- Q2：behave 工作目录是否需要支持 SSH/SCP 远程路径（第一期建议仅本地路径）
- Q3：Step pattern 匹配是否需要支持 behave 的 `use_step_matcher("re")` 正则 matcher（第一期仅默认 parse matcher）
