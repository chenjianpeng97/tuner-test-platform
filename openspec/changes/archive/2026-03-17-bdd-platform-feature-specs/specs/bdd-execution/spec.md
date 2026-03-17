## ADDED Requirements

### Requirement: 系统 SHALL 支持触发 behave 测试执行
用户 SHALL 能通过 Web 界面触发 behave 执行，指定执行范围（project：执行所有 feature / feature：执行指定文件 / tag：执行带指定 tag 的场景）。触发后系统 SHALL 立即返回一条 status=pending 的 TestRun 记录，并在后台异步执行 behave 命令。

#### Scenario: 成功触发全量执行
- **WHEN** 用户提交 POST /api/v1/projects/{id}/test-runs，scope_type=project
- **THEN** 系统 SHALL 创建 TestRun 记录（status=pending），HTTP 状态码 202，响应包含 TestRun id 供后续轮询

#### Scenario: 按 Tag 筛选执行
- **WHEN** 用户提交执行请求，scope_type=tag，scope_value="@smoke"
- **THEN** 系统 SHALL 在 behave 命令中追加 `--tags @smoke`，仅执行带该 tag 的场景

#### Scenario: 触发执行时 behave 工作目录不存在
- **WHEN** Project 配置的 behave_work_dir 在服务器上不存在
- **THEN** 系统 SHALL 立即将 TestRun status 更新为 failed，返回错误信息说明工作目录无效，不启动 subprocess

### Requirement: 后端 SHALL 通过 asyncio subprocess 在本地执行 behave 命令
执行引擎 SHALL 使用 `asyncio.create_subprocess_exec` 在服务器本地异步执行 `behave` 命令，命令工作目录为 Project 配置的 behave_work_dir。执行时 SHALL 支持注入自定义环境变量（来自 executor_config），behave 输出格式 SHALL 包含 `--junit`（写出 JUnit XML）以便结果解析。执行过程中 TestRun status SHALL 更新为 running。

#### Scenario: behave 执行过程中 TestRun 状态为 running
- **WHEN** behave subprocess 已启动但尚未完成
- **THEN** 系统 SHALL 将 TestRun status 保持为 running

#### Scenario: behave 命令执行完成且有测试失败
- **WHEN** behave 进程以非零退出码结束（部分场景失败）
- **THEN** 系统 SHALL 将 TestRun status 更新为 completed（而非 failed），failed 只表示 behave 进程本身崩溃或无法启动

### Requirement: 系统 SHALL 通过 SSE 实时推送执行日志
执行期间系统 SHALL 提供 SSE endpoint，客户端连接后 SHALL 持续接收 behave 控制台输出的每一行日志，直至执行结束。连接关闭后 SHALL 发送终止事件。

#### Scenario: 客户端通过 SSE 接收实时日志
- **WHEN** 用户连接 GET /api/v1/projects/{id}/test-runs/{rid}/logs（SSE）
- **THEN** 服务端 SHALL 以 `data: <log_line>\n\n` 格式逐行推送 behave 输出，执行完成后推送 `event: done\ndata: {}\n\n` 并关闭连接

#### Scenario: TestRun 已完成时请求日志 SSE
- **WHEN** 用户连接已完成的 TestRun 的日志 SSE endpoint
- **THEN** 系统 SHALL 从日志文件读取全量历史日志一次性推送，随后发送 done 事件关闭连接

### Requirement: 系统 SHALL 在执行完成后自动解析结果并更新覆盖率
behave 执行完成后，系统 SHALL 自动读取 behave 生成的 JUnit XML 文件，解析每个 testcase，写入 TestRunResult，并触发覆盖率缓存更新（等同于手动导入 XML 的结果映射逻辑）。

#### Scenario: 执行完成后自动写入 TestRunResult
- **WHEN** behave subprocess 结束且 JUnit XML 文件生成成功
- **THEN** 系统 SHALL 解析 XML，为每个 testcase 写入 TestRunResult，TestRun status 更新为 completed

#### Scenario: JUnit XML 文件生成失败
- **WHEN** behave 运行但 JUnit XML 输出目录不可写导致无法生成 XML
- **THEN** 系统 SHALL 将 TestRun status 设为 failed，记录错误信息，不写入 TestRunResult

### Requirement: 系统 SHALL 记录历史 TestRun 列表供查看
系统 SHALL 提供 API 返回指定 Project 的所有历史 TestRun，按 triggered_at 倒序排列，每项包含状态、触发时间、完成时间、执行范围和结果摘要（总数/通过/失败/跳过）。

#### Scenario: 获取历史 TestRun 列表
- **WHEN** 用户请求 GET /api/v1/projects/{id}/test-runs
- **THEN** 系统 SHALL 返回该 Project 的所有 TestRun，按 triggered_at 倒序，每项包含 id、status、scope_type、scope_value、triggered_at、completed_at 及结果摘要

### Requirement: 系统 SHALL 从仓库目录结构中发现可用的 behave Stage
系统 SHALL 在 Git 同步时扫描 behave 工作目录，识别所有符合 `*_steps/` 命名约定的目录（如 `http_steps/`、`ui_steps/`、`db_steps/`），将其注册为该 Project 下可用的 Stage。Stage 名称 SHALL 通过去掉 `_steps` 后缀推导（如 `http_steps/` → stage `http`）。

#### Scenario: 同步时发现多个 Stage 目录
- **WHEN** Git 仓库的 behave 工作目录下存在 `http_steps/` 和 `ui_steps/`
- **THEN** 系统 SHALL 注册 `http` 和 `ui` 两个 Stage，记录其目录路径和 Project 关联

#### Scenario: 用户自定义 Stage 目录被识别
- **WHEN** Git 仓库中存在 `db_steps/` 目录
- **THEN** 系统 SHALL 识别 `db` 为可用 Stage，后续执行时支持 `--stage db` 参数

#### Scenario: 无 *_steps/ 目录时无可用 Stage
- **WHEN** behave 工作目录下无任何符合约定的 steps 目录
- **THEN** 系统 SHALL 标记该 Project 无可用 Stage，触发自动执行时返回提示

### Requirement: 系统 SHALL 分析每个 Step 在各 Stage 下的自动化覆盖情况
系统 SHALL 在 Git 同步后分析各 Stage 的 step 定义文件，将其中的 step 装饰器模式（pattern）与 Feature 文件中的 Scenario Step 文本进行匹配，记录每个 Step 在每个 Stage 下是否有对应的自动化实现（StepCoverage）。

#### Scenario: Step 在某 Stage 下有自动化实现
- **WHEN** `http_steps/` 中存在匹配 "the shared identity {name} exists" 的 step 定义
- **THEN** 系统 SHALL 记录该 Scenario 中对应 Step 在 `http` Stage 下的 coverage_status 为 covered

#### Scenario: Step 在某 Stage 下无实现
- **WHEN** 某 Step 文本在 `ui_steps/` 中无任何匹配的 step 定义
- **THEN** 系统 SHALL 记录该 Step 在 `ui` Stage 下的 coverage_status 为 uncovered

#### Scenario: 同一 Step 在不同 Stage 均有实现
- **WHEN** 某 Step 同时在 `http_steps/` 和 `ui_steps/` 中均有匹配实现
- **THEN** 系统 SHALL 分别记录该 Step 在 `http` 和 `ui` 两个 Stage 下的 coverage_status 均为 covered

### Requirement: 系统 SHALL 支持对单个 Scenario 发起混合执行会话
用户 SHALL 能对测试计划中的某个 Scenario 发起"混合执行（Hybrid Execution）"会话。会话中系统 SHALL 展示该 Scenario 的每个 Step 及其在各 Stage 下的自动化覆盖状态，用户可逐步执行：对有自动化覆盖的 Step 选择 Stage 触发自动运行，对无覆盖的 Step 手动标记结果。每个 Step 的执行记录 SHALL 包含：执行模式（auto / manual）、执行状态（pass / fail / skip / pending）、操作人、操作时间、可选备注。

#### Scenario: 创建混合执行会话
- **WHEN** 用户对某 TestPlanItem 发起 POST /api/v1/projects/{id}/scenario-executions，关联 scenario_id
- **THEN** 系统 SHALL 创建 ScenarioExecution 记录，并为该 Scenario 的每个 Step 生成 StepExecutionRecord（初始状态 pending），返回含各 Step 覆盖信息的会话详情

#### Scenario: 查看 Step 的可用 Stage 选项
- **WHEN** 用户打开混合执行会话
- **THEN** 每个 StepExecutionRecord SHALL 携带 available_stages 列表，列出该 Step 有自动化实现的 Stage 名称，无覆盖的 Step 该列表为空

### Requirement: 系统 SHALL 支持在混合执行会话中自动运行指定 Step
对于 available_stages 非空的 Step，用户 SHALL 能选择一个 Stage 触发该 Step 的自动化执行。系统 SHALL 使用 `behave --stage <stage> --include <feature_file> --name "<scenario_name>"` 执行该场景，但仅取对应 Step 的执行结果（pass/fail）更新 StepExecutionRecord。前置 Step（Given）的自动化执行 SHALL 同时完成环境 setup，为后续 Step 提供上下文。

#### Scenario: 用户选择 Stage 自动执行 Given Step
- **WHEN** 用户在会话中对 Given Step 选择 `http` Stage 并触发执行
- **THEN** 系统 SHALL 运行对应 behave 命令，将该 Step 的 StepExecutionRecord status 更新为 pass 或 fail，execution_mode 记录为 auto，记录执行时间

#### Scenario: 自动执行 Then Step 进行断言
- **WHEN** 用户在会话中对 Then Step 选择 `ui` Stage 触发执行（前提：Given 已执行）
- **THEN** 系统 SHALL 执行 UI Stage 的 behave 命令，以断言结果更新该 Step 的 StepExecutionRecord

#### Scenario: 自动执行时 Step 失败
- **WHEN** 自动执行结果显示该 Step assert 失败
- **THEN** 系统 SHALL 将 StepExecutionRecord status 设为 fail，记录 error_message，不阻止用户继续执行后续 Step

### Requirement: 系统 SHALL 支持在混合执行会话中手动记录 Step 执行结果
对于 available_stages 为空的 Step，或用户选择手动执行的 Step，用户 SHALL 能提交该 Step 的执行结果（pass / fail / skip），并可附加备注信息。系统 SHALL 记录操作人（当前用户标识）和操作时间。

#### Scenario: 手动标记 When Step 执行结果
- **WHEN** 用户对某 When Step 提交 PATCH /api/v1/scenario-executions/{eid}/steps/{sid}，携带 status=pass 和可选 notes
- **THEN** 系统 SHALL 更新该 StepExecutionRecord 的 status、execution_mode=manual、executor（操作人）、executed_at、notes

#### Scenario: 记录含备注的失败结果
- **WHEN** 用户将某 Step 标记为 fail 并填写备注 "需要确认数据库状态"
- **THEN** 系统 SHALL 将 notes 字段保存，供后续查看

### Requirement: 系统 SHALL 根据混合执行会话的 Step 结果汇总 Scenario 执行状态
混合执行会话完成后（所有 Step 均不为 pending），系统 SHALL 自动计算 ScenarioExecution 的整体状态：所有 Step pass → scenario pass；任一 Step fail → scenario fail；有 Step skip 且无 fail → scenario partial。该状态 SHALL 同步更新关联的 TestPlanItem status。

#### Scenario: 所有 Step 执行通过时 Scenario 状态为 pass
- **WHEN** ScenarioExecution 中最后一个 Step 被标记为 pass
- **THEN** 系统 SHALL 将 ScenarioExecution status 设为 pass，并更新关联 TestPlanItem status=pass

#### Scenario: 有 Step 失败时 Scenario 状态为 fail
- **WHEN** 任意一个 StepExecutionRecord status 为 fail
- **THEN** 系统 SHALL 将 ScenarioExecution status 设为 fail，关联 TestPlanItem status=fail
