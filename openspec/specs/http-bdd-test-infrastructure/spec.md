## ADDED Requirements

### Requirement: Feature 测试根目录 SHALL 使用仓库顶层 features
系统 SHALL 将整个项目的 BDD Feature、HTTP stage 环境文件、步骤定义以及共享数据维护目录统一放置在仓库顶层 `features` 根目录下，以支持后端先落地、前端后续复用的同一套行为描述。

#### Scenario: 顶层目录结构存在
- **WHEN** 开发者查看仓库中的 BDD 测试结构
- **THEN** 系统 SHALL 在仓库顶层提供 `features/`、`features/db/`、`features/http_environment.py` 与 `features/http_steps/`

### Requirement: HTTP stage 测试数据注入 MUST 收敛在 features/http_steps/factories
系统 MUST 将 Given 前置所需的数据建模与数据库注入逻辑集中在 `features/http_steps/factories/` 模块内，并允许该模块复用现有 unit test factory 思路及受控的 infrastructure 持久化能力。

#### Scenario: Given 前置数据由专用 factories 模块处理
- **WHEN** 某个 HTTP BDD 场景需要向数据库注入 Alice、Bob 等前置数据
- **THEN** 系统 SHALL 通过 `features/http_steps/factories/` 中的专用模块完成准备，而不是在通用步骤中散落实现细节

### Requirement: UAT 执行入口 SHALL 使用 app-api:test-uat 且默认不启动后端服务
系统 SHALL 为后端 HTTP BDD 提供独立的 Nx 入口 `app-api:test-uat`，并默认要求开发者手动先启动后端服务，而不是将服务启动逻辑内聚到该 target 中。

#### Scenario: 本地执行 UAT 前需手动启动服务
- **WHEN** 开发者在本地执行 `nx run app-api:test-uat`
- **THEN** 系统 SHALL 仅执行 UAT 测试，并假定 API 服务已由开发者预先启动

### Requirement: CI 首批结果输出 SHALL 提供 JUnit 格式报告
系统 SHALL 在 CI 中为 HTTP BDD 首批接入提供 JUnit 格式结果，以便被 CI 平台、测试聚合器与问题面板稳定消费；同时保留 Behave 的终端输出供开发者阅读。

#### Scenario: CI 执行 UAT 时产出 JUnit 结果
- **WHEN** CI 环境执行 `nx run app-api:test-uat`
- **THEN** 系统 SHALL 产出可被标准 CI 流水线识别的 JUnit 格式测试结果

### Requirement: 首批规范检查 SHALL 由仓库内 Python 脚本承担
系统 SHALL 在首批实现中使用仓库内 Python 脚本检查 Feature 命名、主功能与子功能目录结构、数据目录存在性以及 UAT/BDD 工程约束，而不是先引入复杂的自定义 Nx plugin。

#### Scenario: 规范检查通过 Python 脚本执行
- **WHEN** 开发者或 CI 运行 BDD 规范检查入口
- **THEN** 系统 SHALL 通过仓库内 Python 脚本完成首批规则校验

### Requirement: 跨端 Feature 工程约束 SHALL 由独立的 scope:ux UAT/BDD 工程承载
系统 SHALL 为 Feature 文件工程约束建立独立的 UAT/BDD 工程，并将其归入 `scope:ux` 范围，以承载不区分前后端的共享规范检查，而不是将这些检查挂在 `app-api` 项目下。

#### Scenario: 共享规范检查不挂在后端项目下
- **WHEN** 开发者配置 Feature 命名、目录结构或共享数据目录的检查入口
- **THEN** 系统 SHALL 将该入口挂载到独立的 `scope:ux` UAT/BDD 工程，而不是 `app-api`
