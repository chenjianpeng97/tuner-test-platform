# PRD：测试管理平台（BDD Platform）

> 版本：v0.1
> 日期：2026-03-12
> 状态：草稿

---

## 一、产品愿景

构建一个以 BDD 为核心的测试管理平台，让团队能够在统一的 Web 界面中管理 Feature 文件、追踪测试覆盖率、规划测试执行，并支持触发 Behave 自动化测试。平台定位类似 Cucumber Studio，但深度集成本地 Behave 生态。

**技术基础**：扩展现有 `fastapi-clean-example`（后端）+ `shadcn-admin`（前端）。

---

## 二、目标用户

- 测试工程师：管理 Feature 文件、查看覆盖率、执行自动化测试
- 开发工程师：在线查阅和编辑 Feature 文件
- 项目管理者：制定测试计划、追踪测试状态

> **第一期**：全员相同权限，无需角色分级。

---

## 三、功能需求

### 3.1 项目管理（多项目隔离）

| ID    | 优先级 | 需求描述                                                            |
| ----- | ------ | ------------------------------------------------------------------- |
| PM-01 | P0     | 系统 SHALL 支持创建、查看、编辑、删除 Project                       |
| PM-02 | P0     | 每个 Project SHALL 关联一个 Git 仓库（URL + Branch + Access Token） |
| PM-03 | P0     | 系统 SHALL 支持手动触发"从 Git 同步 Feature 文件"操作               |
| PM-04 | P0     | 不同 Project 的 Feature、测试计划、测试运行数据 SHALL 完全隔离      |

### 3.2 Feature 文件浏览

| ID    | 优先级 | 需求描述                                                            |
| ----- | ------ | ------------------------------------------------------------------- |
| FB-01 | P0     | 系统 SHALL 以树形结构展示 Project 内的 Feature 文件（支持目录层级） |
| FB-02 | P0     | 点击 Feature 文件 SHALL 展示其完整内容，带 Gherkin 语法高亮         |
| FB-03 | P0     | Feature 文件解析 SHALL 支持 Gherkin 6 语法（含 `Rule` 关键字）      |
| FB-04 | P0     | 树形结构 SHALL 展示 Feature > Rule（可选）> Scenario 三层层级       |
| FB-05 | P1     | 系统 SHALL 展示每个 Feature 文件的场景数量统计                      |

### 3.3 在线编辑器

| ID    | 优先级 | 需求描述                                                                                                                                               |
| ----- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| ED-01 | P0     | 系统 SHALL 提供在线文本编辑器，支持保存修改到 Git 仓库（新提交）                                                                                       |
| ED-02 | P0     | 编辑器 SHALL 提供 Gherkin 语法高亮（Feature/Rule/Scenario/Given/When/Then/And）                                                                        |
| ED-03 | P0     | 编辑器 SHALL 实现 Step 自动补全：用户输入 step 文本前缀时，匹配当前 Project 内所有 Feature 文件中已有的 step 文本，按前缀模糊匹配提示可复用的完整 step |
| ED-04 | P1     | 编辑器 SHALL 在保存前进行 Gherkin 语法校验，校验失败时给出行号和错误提示                                                                               |
| ED-05 | P1     | 系统 SHALL 要求每次保存时填写 Git Commit Message（可自动生成默认值）                                                                                   |

### 3.4 测试覆盖率

| ID    | 优先级 | 需求描述                                                                                             |
| ----- | ------ | ---------------------------------------------------------------------------------------------------- |
| CV-01 | P0     | 系统 SHALL 支持导入 behave 执行结果（JUnit XML 格式）                                                |
| CV-02 | P1     | 系统 SHOULD 支持导入 behave JSON 格式结果                                                            |
| CV-03 | P0     | 系统 SHALL 将导入的执行结果通过 `feature 名称 + scenario 名称` 映射到具体 Scenario                   |
| CV-04 | P0     | 系统 SHALL 在 Feature 树和 Scenario 列表中展示覆盖率标记：已覆盖（绿）/ 未覆盖（灰）/ 最近失败（红） |
| CV-05 | P0     | 系统 SHALL 展示 Project 级别的覆盖率 Dashboard：总场景数、已覆盖数、覆盖率百分比                     |
| CV-06 | P1     | 覆盖率 SHALL 基于最近一次成功导入的测试运行结果计算                                                  |

### 3.5 测试计划管理

| ID    | 优先级 | 需求描述                                                                          |
| ----- | ------ | --------------------------------------------------------------------------------- |
| TP-01 | P0     | 系统 SHALL 支持在 Project 内创建、查看、编辑、删除测试计划                        |
| TP-02 | P0     | 创建/编辑测试计划时，SHALL 支持从 Feature 树中勾选 Scenario 加入计划              |
| TP-03 | P0     | 测试计划中每个 Scenario 项 SHALL 有状态字段：`未执行 / 通过 / 失败 / 跳过 / 阻塞` |
| TP-04 | P0     | 系统 SHALL 支持手动更新测试计划中 Scenario 的状态                                 |
| TP-05 | P0     | 系统 SHALL 统计并展示测试计划的整体进度（待执行/通过/失败 数量）                  |
| TP-06 | P1     | 系统 SHALL 支持将测试运行结果批量同步到测试计划状态（自动更新匹配项）             |

### 3.6 BDD 自动化执行（第一期：Behave）

| ID    | 优先级 | 需求描述                                                                                  |
| ----- | ------ | ----------------------------------------------------------------------------------------- |
| EX-01 | P0     | 系统 SHALL 支持在界面上触发 behave 测试执行                                               |
| EX-02 | P0     | 执行时 SHALL 支持选择执行范围：整个 Project / 指定 Feature 文件 / 指定 Tag                |
| EX-03 | P0     | 后端 SHALL 通过 subprocess 在服务器本地执行 `behave` 命令                                 |
| EX-04 | P0     | 执行配置 SHALL 包含：behave 工作目录路径（服务器本地路径）、环境变量 KV 对、额外 CLI 参数 |
| EX-05 | P0     | 系统 SHALL 实时（或准实时）通过 SSE 推送执行日志到前端                                    |
| EX-06 | P0     | 执行完成后 SHALL 自动解析 JUnit XML 结果并更新 Test Run 状态 + 覆盖率                     |
| EX-07 | P0     | 系统 SHALL 记录历史 Test Run 列表，支持查看每次运行的详细结果                             |
| EX-08 | P1     | 每个 Test Run 结果 SHALL 可被关联到某个测试计划，自动更新测试计划状态                     |

---

## 四、数据模型（概念层）

```
Project ──< Feature ──< Scenario ──< Step（补全索引）
                  └──< TestRun ──< TestRunResult
Project ──< TestPlan ──< TestPlanItem >── Scenario
```

### Project

| 字段                     | 说明               |
| ------------------------ | ------------------ |
| id                       | 主键               |
| name, description        | 基本信息           |
| git_repo_url, git_branch | Git 仓库配置       |
| git_access_token         | 加密存储的 PAT     |
| behave_work_dir          | 服务器本地执行路径 |
| created_at, updated_at   | 时间戳             |

### Feature

| 字段           | 说明                      |
| -------------- | ------------------------- |
| id, project_id | 所属项目                  |
| file_path      | 相对于 repo root 的路径   |
| git_sha        | 最后同步时的 SHA          |
| content        | 文件内容缓存              |
| feature_name   | 从内容解析的 Feature 名称 |

### Scenario

| 字段                       | 说明                          |
| -------------------------- | ----------------------------- |
| id, feature_id, project_id | 关联关系                      |
| rule_name                  | nullable，Gherkin 6 Rule 支持 |
| scenario_name              | 场景名称                      |
| tags                       | 标签数组                      |
| line_number                | 在文件中的行号                |

### Step（补全索引）

| 字段                        | 说明                            |
| --------------------------- | ------------------------------- |
| id, scenario_id, project_id | 关联关系                        |
| keyword                     | Given / When / Then / And / But |
| text                        | step 文本，用于前缀模糊匹配     |

### TestPlan

| 字段                   | 说明     |
| ---------------------- | -------- |
| id, project_id         | 所属项目 |
| name, description      | 基本信息 |
| created_at, updated_at | 时间戳   |

### TestPlanItem

| 字段                          | 说明                                   |
| ----------------------------- | -------------------------------------- |
| id, test_plan_id, scenario_id | 关联关系                               |
| status                        | not_run / pass / fail / skip / blocked |
| notes, updated_at             | 备注和更新时间                         |

### TestRun

| 字段                         | 说明                                   |
| ---------------------------- | -------------------------------------- |
| id, project_id, test_plan_id | 关联关系（test_plan_id 可空）          |
| triggered_at, completed_at   | 执行时间                               |
| status                       | pending / running / completed / failed |
| scope_type, scope_value      | project / feature / tag + 具体值       |
| executor_config              | behave CLI 参数和环境变量（JSON）      |
| log_path                     | 服务器本地日志文件路径                 |

### TestRunResult

| 字段                         | 说明                                       |
| ---------------------------- | ------------------------------------------ |
| id, test_run_id, scenario_id | 关联关系（scenario_id 通过名称映射，可空） |
| feature_name, scenario_name  | 原始名称（用于映射）                       |
| status                       | pass / fail / skip / undefined             |
| duration_seconds             | 执行时长                                   |
| error_message, stack_trace   | 失败信息                                   |

---

## 五、API 设计（高层）

### 项目管理

```
POST   /api/v1/projects               创建项目
GET    /api/v1/projects               列出所有项目
GET    /api/v1/projects/{id}          项目详情
PUT    /api/v1/projects/{id}          更新项目
DELETE /api/v1/projects/{id}          删除项目
POST   /api/v1/projects/{id}/sync     触发 Git 同步
```

### Feature 管理

```
GET    /api/v1/projects/{id}/features                   Feature 树（含 Rule/Scenario）
GET    /api/v1/projects/{id}/features/{fid}             Feature 详情 + 原始内容
POST   /api/v1/projects/{id}/features                   新建 Feature 文件
PUT    /api/v1/projects/{id}/features/{fid}             更新 Feature 内容（Git commit）
GET    /api/v1/projects/{id}/steps/suggest?q=xxx        Step 自动补全查询
```

### 测试计划

```
POST   /api/v1/projects/{id}/test-plans                           创建测试计划
GET    /api/v1/projects/{id}/test-plans                           列出测试计划
GET    /api/v1/projects/{id}/test-plans/{pid}                     计划详情（含 items）
PUT    /api/v1/projects/{id}/test-plans/{pid}                     更新计划基本信息
DELETE /api/v1/projects/{id}/test-plans/{pid}                     删除计划
POST   /api/v1/projects/{id}/test-plans/{pid}/items               批量添加 Scenarios
PATCH  /api/v1/projects/{id}/test-plans/{pid}/items/{iid}         更新单项状态
POST   /api/v1/projects/{id}/test-plans/{pid}/sync-run/{rid}      从 TestRun 同步状态
```

### 测试执行

```
POST   /api/v1/projects/{id}/test-runs                  触发执行
GET    /api/v1/projects/{id}/test-runs                  历史列表
GET    /api/v1/projects/{id}/test-runs/{rid}            运行详情 + 结果
GET    /api/v1/projects/{id}/test-runs/{rid}/logs       日志流（SSE）
POST   /api/v1/projects/{id}/test-runs/import           导入外部 JUnit XML
```

### 覆盖率

```
GET    /api/v1/projects/{id}/coverage                   Project 级别覆盖率摘要
GET    /api/v1/projects/{id}/features/{fid}/coverage    Feature 级别覆盖率
```

---

## 六、前端页面规划

基于现有 `shadcn-admin` 扩展，新增以下页面：

| 页面           | 路由                               | 核心功能                                 |
| -------------- | ---------------------------------- | ---------------------------------------- |
| 项目列表       | `/projects`                        | 项目 CRUD，进入项目                      |
| 项目概览       | `/projects/:id`                    | Feature 统计、覆盖率 Dashboard、快速入口 |
| Feature 浏览器 | `/projects/:id/features`           | 左树右内容，Gherkin 高亮预览             |
| Feature 编辑器 | `/projects/:id/features/:fid/edit` | CodeMirror 编辑，Step 补全，保存到 Git   |
| 覆盖率详情     | `/projects/:id/coverage`           | 按 Feature/Tag 维度的覆盖率表格 + 图表   |
| 测试计划列表   | `/projects/:id/test-plans`         | 计划 CRUD                                |
| 测试计划详情   | `/projects/:id/test-plans/:pid`    | Scenario 勾选、状态管理、进度统计        |
| 测试运行列表   | `/projects/:id/test-runs`          | 历史列表，触发新运行                     |
| 测试运行详情   | `/projects/:id/test-runs/:rid`     | 实时日志流（SSE）、Scenario 结果列表     |

---

## 七、技术架构决策

| 方面             | 选型                                        | 理由                                           |
| ---------------- | ------------------------------------------- | ---------------------------------------------- |
| Feature 文件存储 | Git 仓库 + GitPython                        | 版本可追溯，与开发流程天然整合                 |
| Gherkin 解析     | `gherkin-official` Python 包                | 官方支持 Gherkin 6 + Rule 关键字               |
| Step 补全索引    | 同步时解析 Step 写入 DB，API 前缀模糊匹配   | 低延迟，无需实时扫描文件                       |
| BDD 执行         | `asyncio.create_subprocess_exec` + `behave` | 非阻塞执行，支持并发日志读取                   |
| 日志推送         | Server-Sent Events (SSE)                    | 单向推送，前端无需轮询                         |
| 结果解析         | `behave --format json` 或 JUnit XML         | JSON 更结构化，XML 向后兼容                    |
| 前端编辑器       | CodeMirror 6                                | 支持自定义 Gherkin 语言 + 自定义补全 extension |
| 前端状态管理     | Zustand + TanStack Query                    | 复用现有模式                                   |

---

## 八、第一期范围边界

### 包含 ✅

- 多项目隔离管理
- Git 仓库同步 Feature 文件
- Feature 浏览（树形 + Gherkin 高亮预览）
- 在线编辑器（Step 补全 + Gherkin 校验 + Git 保存）
- **Gherkin 6 支持**（含 `Rule` 关键字）
- JUnit XML 覆盖率导入与展示
- 测试计划（创建/勾选 Scenario/手动状态管理）
- Behave 本地执行 + SSE 日志流 + 结果自动解析

### 不包含 ❌（第二期及以后）

- 用户权限与角色管理
- 远程 Agent/CI 触发执行（Jenkins、GitHub Actions）
- Playwright / 其他测试框架执行支持
- Webhook 与通知集成
- Feature 文件版本历史对比

---

## 九、里程碑规划（建议）

| 里程碑                   | 主要交付                                                      | 依赖       |
| ------------------------ | ------------------------------------------------------------- | ---------- |
| M1 - 数据模型 & API 框架 | DB Schema 设计、Alembic 迁移、项目/Feature CRUD API、Git 同步 | —          |
| M2 - Feature 浏览        | 前端 Feature 树组件、Gherkin 高亮预览页面                     | M1         |
| M3 - 在线编辑器          | CodeMirror 集成、Step 补全 API + 前端扩展、Git 保存流程       | M1、M2     |
| M4 - 覆盖率              | JUnit XML 导入 API、覆盖率 Dashboard 页面                     | M1         |
| M5 - 测试计划            | 测试计划 CRUD、Scenario 勾选 UI、状态管理                     | M1、M2     |
| M6 - BDD 执行            | Behave subprocess 管理、SSE 日志流、结果解析与写库            | M1、M4、M5 |

---

## 十、待确认事项

| #   | 问题                                                                   | 建议默认值           |
| --- | ---------------------------------------------------------------------- | -------------------- |
| Q1  | Git 鉴权是否仅支持 Personal Access Token（HTTP），还是也需要 SSH Key？ | 第一期仅 PAT         |
| Q2  | behave 工作目录是单机固定路径，还是需支持多节点动态配置？              | 第一期单机固定路径   |
| Q3  | Step 补全是仅前缀匹配还是支持任意子串匹配（类 VSCode 模糊）？          | 前缀匹配，后期可扩展 |
| Q4  | Feature 文件编码是否仅支持 UTF-8？                                     | 仅 UTF-8             |
