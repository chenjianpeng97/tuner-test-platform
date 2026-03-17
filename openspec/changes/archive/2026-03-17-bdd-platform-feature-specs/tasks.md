## 0. UX Prototype (Pencil First)

- [x] 0.1 使用 Pencil 输出核心页面低保真原型：Projects 列表、Feature Browser、Feature Editor、Test Plan、Execution
- [x] 0.2 在原型中标注关键交互流：Git 同步、Step 补全、执行触发、SSE 日志、Hybrid Step 手工/自动切换
- [x] 0.3 组织一次原型评审，收集并记录页面结构与交互修改项
- [x] 0.4 根据评审结果更新原型并确认基线（冻结首版页面信息架构）

## 1. Data Model & Migrations

- [x] 1.1 创建 Alembic 迁移：`projects` 与 `project_git_configs`（含唯一约束与外键）
- [x] 1.2 创建 Alembic 迁移：`project_behave_configs`、`features`（含 `parent_feature_id`、`depth`）
- [x] 1.3 创建 Alembic 迁移：`scenarios`、`steps`、`behave_stages`、`step_coverages`
- [x] 1.4 创建 Alembic 迁移：`test_plans`、`test_plan_items`、`test_runs`、`test_run_results`
- [x] 1.5 创建 Alembic 迁移：`scenario_executions`、`step_execution_records`，并验证 downgrade 可回滚

## 2. Shared Projects Module (Top-Level)

- [x] 2.1 新增 `src/projects/domain`：`Project`、`ProjectGitConfig` 实体与 `ProjectRepository` 协议
- [x] 2.2 新增 `src/projects/gateway/sqlalchemy_project_repo.py`，实现 Project 与 GitConfig 的 CRUD
- [x] 2.3 新增 `src/projects/gateway/git_sync_service.py`，实现 clone/pull/commit/push 基础能力
- [x] 2.4 新增 `src/projects/api` 路由与 schema：Project CRUD、Git 配置读写（不回传 PAT 明文）
- [x] 2.5 在 `api_v1_router` 注册 `projects` 路由并补充 project_id 数据隔离校验

## 3. BDD Features Sync & Parsing

- [x] 3.1 新增 `bdd/features` 的 repository/service，串联 Git 同步入口 `POST /projects/{id}/sync`
- [x] 3.2 实现 D2 同名目录子特性算法，写入 `parent_feature_id` 与 `depth`
- [x] 3.3 接入 `gherkin` 解析 `.feature`，落库 Feature/Scenario/Step（含 Rule 与 line_number）
- [x] 3.4 实现 Feature 树查询 API：返回多层 children、Rule 节点与 `scenario_count`
- [x] 3.5 实现 Feature 详情 API：返回原始 content（UTF-8）供前端高亮展示

## 4. Feature Editing & Step Suggestion

- [x] 4.1 实现编辑保存 API（PUT）：提交 Git、重新解析、失败时回滚 commit 并返回 502
- [x] 4.2 实现新建 Feature API（POST）：路径冲突返回 409，成功后写库
- [x] 4.3 实现“新建 Sub-Feature”路径推导：`foo/bar.feature -> foo/bar/<name>.feature`（可覆盖）
- [x] 4.4 实现 step 补全 API：`GET /projects/{id}/steps/suggest?q=`，按前缀匹配并去重，最多 20 条
- [x] 4.5 增加项目隔离校验：所有 features/steps 查询强制 `project_id`

## 5. Stage Discovery & Step Coverage Matrix

- [x] 5.1 在 Git 同步后扫描 behave 目录，注册 `*_steps/` 到 `behave_stages`
- [x] 5.2 实现 step 装饰器 pattern 提取（`@given/@when/@then/@step`）
- [x] 5.3 实现 pattern 到正则转换与 Step 文本 fullmatch
- [x] 5.4 写入 `step_coverages`（covered/uncovered）并支持多 stage 并存
- [x] 5.5 为混合执行查询接口补充 `available_stages`

## 6. Coverage Import & Dashboard

- [x] 6.1 实现 JUnit XML 上传导入 API：创建 completed TestRun 与 TestRunResult
- [x] 6.2 实现 testcase 到 Scenario 映射（feature_name + scenario_name），不匹配置空 `scenario_id`
- [x] 6.3 实现 Scenario 覆盖状态聚合（covered/failed/uncovered）并注入 Feature 树响应
- [x] 6.4 实现 Project 覆盖率摘要 API（total/covered/failed/percentage）
- [x] 6.5 补充非法 XML 422 错误路径与解析错误信息

## 7. Test Plan Management

- [x] 7.1 实现测试计划 CRUD API 与 `test_plan_items` 级联删除
- [x] 7.2 实现批量添加 Scenario 到计划 API（重复项幂等忽略，初始 `not_run`）
- [x] 7.3 实现单条 Item 状态更新 API（not_run/pass/fail/skip/blocked）
- [x] 7.4 实现测试计划进度统计字段（total + 各状态计数）
- [x] 7.5 实现从 TestRun 批量同步计划状态 API，并返回更新摘要

## 8. Test Run Execution & SSE Logs

- [x] 8.1 实现触发执行 API：scope_type(project/feature/tag) 创建 pending TestRun（202）
- [x] 8.2 实现 asyncio subprocess BehaveRunner：状态流转 pending->running->completed/failed
- [x] 8.3 实现 `--junit` 结果文件解析自动入库与失败分支处理
- [x] 8.4 实现 SSE 日志流：运行中实时推送，已完成回放历史并发送 done 事件
- [x] 8.5 实现同 Project 并发锁（仅允许一个 running TestRun，冲突返回 409）

## 9. Hybrid Scenario Execution

- [x] 9.1 实现创建 ScenarioExecution API：初始化每个 Step 的 `StepExecutionRecord(pending)`
- [x] 9.2 实现单 Step 自动执行 API：选择 stage 运行并回填该 step 的 auto 结果
- [x] 9.3 实现单 Step 手工记录 API：写入 manual 状态、executor、executed_at、notes
- [x] 9.4 落实 Q4 规则：Given auto fail 可 manual 补录 pass，但保留 auto fail 记录与日志引用
- [x] 9.5 实现会话汇总：all pass=pass，any fail=fail，skip 且无 fail=partial，并同步 TestPlanItem

## 10. Frontend Pages (shadcn-admin)

- [x] 10.1 新增 `/projects` 路由树与 Project 列表/创建/编辑页面
- [x] 10.2 新增 Feature Browser 树组件（含 Sub-Feature、Rule、Scenario、coverage 标记）
- [x] 10.3 新增 Feature Editor（CodeMirror6 + Gherkin 高亮 + 300ms step 自动补全）
- [x] 10.4 新增 Test Plan 页面（场景勾选、状态更新、进度统计、同步 TestRun）
- [x] 10.5 新增 Execution 页面（触发执行、SSE 日志、Hybrid Step 操作与状态展示）

## 11. Validation & Documentation

- [x] 11.1 为新增后端 API 编写单元/集成测试（成功流 + 422/409/502 异常流）
- [x] 11.2 为关键流程编写端到端验证脚本（Git 同步、编辑提交、执行日志、Hybrid 会话）
- [x] 11.3 复核跨 Project 数据隔离用例，确保所有查询均受 `project_id` 约束
- [x] 11.4 更新项目文档：模块结构、迁移顺序、运行说明与已知限制（Q1-Q3）
- [x] 11.5 执行 `openspec validate --change bdd-platform-feature-specs --strict` 并修复告警

## 12. Follow-up Fixes & Integration

- [x] 12.6 修复 Projects 页面：列表/新建/详情接入真实后端（`dev:integration`），`dev:mock` 仍使用 mock 数据
- [x] 12.7 Local DB 创建缺失表（执行迁移/引导本地数据库）
