## Context

当前后端应用已经通过 FastAPI 暴露用户与账户相关 HTTP 路由，核心入口集中在 `/api/v1/users` 与 `/api/v1/account`。从现有控制器可以确认，本次优先覆盖的 HTTP 行为包括：

- `POST /api/v1/users/`：创建用户。
- `PUT /api/v1/users/{user_id}/activation`：激活用户。
- `DELETE /api/v1/users/{user_id}/activation`：反激活用户。
- `PUT /api/v1/users/{user_id}/roles/admin`：赋予管理员权限。
- `POST /api/v1/account/login`：登录。
- `DELETE /api/v1/account/logout`：注销。

现有 Nx 后端项目 `app-api` 已具备 `serve`、`bootstrap-local`、`test-unit` 等 target，但 `test-integration` 仍然是占位命令。后端测试目录当前以 pytest 单元测试与少量集成测试为主，仓库顶层也尚未存在统一面向全项目功能描述的 `./features` 目录，因此当前既没有 Behave，也没有可被后端与未来前端共同复用的 Feature、步骤定义、测试数据基线与 stage 约定。

本次变更不是简单补几条测试，而是一次跨越测试工具链、目录治理、数据治理和 Nx 执行入口的横切改造，因此需要先把实现方案固定下来，避免后续 spec 与编码阶段出现目录漂移、命名失配或执行方式不一致。

## Goals / Non-Goals

**Goals:**

- 为整个仓库建立一套以 `behave --stage http` 为执行核心的顶层 Feature 测试结构，并先由后端 HTTP 层落地执行。
- 将 feature 文件按“主功能 + 子功能”稳定分层，使后续新增场景时可以保持一致命名和目录布局。
- 在顶层 `./features` 下建立独立的数据库基础数据维护区，使 Alice、Bob 等测试身份在后端、后续 UI、以及 OpenSpec 文档中保持一致。
- 为 Nx 引入独立的 BDD/UAT 入口 `app-api:test-uat`，避免混淆 `test-integration` 的语义。
- 为后续规范约束预留可自动检查的落点，包括目录形态、feature 命名、数据目录命名和 target 组织方式。

**Non-Goals:**

- 本次 design 不设计前端或 UI 自动化测试方案。
- 本次 design 不重构现有业务路由、鉴权模型或应用层交互器。
- 本次 design 不把所有现有后端测试统一迁移到 Behave；pytest 单元测试与非 BDD 集成测试继续保留。
- 本次 design 不引入新的认证协议或变更 cookie / token 传输语义。

## Decisions

### 1. Feature 文件采用仓库顶层 `./features` 根目录，而不是放入后端测试目录

决策：在仓库根目录新增统一的 Feature 根目录 `./features`，并在其下固定放置：

- `features/`：全项目 Feature 文件根目录。
- `features/db/`：BDD 数据维护目录。
- `features/http_environment.py`：HTTP stage 专用环境文件。
- `features/http_steps/`：HTTP stage 专用步骤目录。

原因：Feature 文件描述的是整个项目的功能行为，而不是单独某个后端工程的实现细节。把它们放在仓库顶层，才能让后续前端接入时继续复用同一套行为描述，而不需要把前端验收测试“倒挂”到后端测试目录中。`behave --stage http` 只要求 stage 前缀环境文件与步骤目录位于 feature 根目录附近，因此顶层 `./features` 与 `http_environment.py` / `http_steps/` 的组合完全符合 Behave 的 stage 机制。

备选方案：

- 直接把 feature 文件放进现有 `fastapi-clean-example/tests/`。放弃，因为 Feature 的所有权应属于整个项目，不应绑定在后端工程目录下。
- 使用默认 `environment.py` 和 `steps/`，不使用 stage 前缀。放弃，因为用户已经明确要求以 `behave --stage http` 驱动，设计应直接围绕该模式组织。

### 2. Feature 目录遵循“主功能文件 + 同名目录承载子功能”规则

决策：在 `features/` 下对每个主功能采用以下结构：

- `features/user.feature`：用户主功能核心行为，如创建、激活、反激活。
- `features/user/`：用户主功能下的子功能目录。
- `features/user/user_auth.feature`：用户管理相关授权行为，如 super admin 赋予 admin 权限。
- `features/auth.feature`：认证主功能核心行为，如登录与注销。

原因：该规则和用户要求完全一致，同时能把“领域核心行为”和“围绕主功能延伸的子模块行为”分离。这样后续即便扩展出 `user_password`、`user_profile`、`auth_session` 等子功能，也不会挤进同一个超大 feature 文件。

备选方案：

- 按 HTTP 控制器文件名拆 feature。放弃，因为控制器粒度更偏技术实现，不利于 UI 复用与业务对话。
- 使用 `features/users/*.feature` 的扁平结构。放弃，因为无法明确主功能与子功能边界，也不满足当前规范要求。

### 3. BDD 测试数据采用“顶层数据目录 + Python data factory 注入”模式

决策：在 `features/db/` 下维护一套可读、稳定、与 feature 文本同名风格一致的基础数据语义，优先使用 Alice、Bob、Charlie 等业务可读身份名。第一阶段不强制把这些数据落成独立 SQL 或 YAML 文件，而是优先在 `http_steps/` 中通过 Python data factory 组织数据准备逻辑，复用现有 unit test 中的 factory 思路，并允许直接引用 infrastructure 层代码把数据注入数据库。

建议的组织方式：

- `db/base/`：所有 feature 共享的基础角色、用户、认证初值。
- `db/user/`：用户主功能场景依赖的数据增量或覆盖。
- `db/auth/`：登录、注销等认证场景依赖的数据增量或覆盖。
- `http_steps/factories/` 或等价模块：封装基于 Python data factory 的建模与注入入口，内部可借鉴 `tests/app/unit/factories` 的已有实现。

原因：BDD 的首要目标是让 feature 文本稳定且可读。如果测试数据使用随机用户名、技术性 ID 或场景内临时拼接命名，后续 UI 层接入时会被迫同步改 feature 文本，丢失 BDD 作为行为契约的价值。与此同时，当前仓库已经存在 unit test data factory，直接借鉴并适度引入 infrastructure 层注入逻辑，比先维护一套新的 SQL / YAML 体系更快落地，也更符合现阶段后端实现状态。

备选方案：

- 每个 Scenario 直接手写数据库插入代码。放弃，因为步骤会快速膨胀，且难以沉淀共享身份模型。
- 统一只维护 SQL dump。暂不采用，因为 SQL dump 可维护性较差，不利于表达场景意图；但可在后续稳定后作为快照优化手段引入。

### 4. HTTP BDD 场景通过真实应用进程和真实本地数据库执行

决策：HTTP 层 BDD 不走 mock，不直接调用交互器，而是以真实 HTTP 请求访问运行中的 FastAPI 应用，并依赖本地数据库完成状态变更验证。Nx 侧通过组合现有 `bootstrap-local`、`serve` 与新的 `test-uat` target 形成可重复的执行链路。

原因：本次目标是补齐 HTTP 层行为契约。如果从步骤定义直接调用应用层，将无法验证路由、鉴权依赖、cookie 传递、状态码映射和错误翻译，这些正是 HTTP 层 BDD 应覆盖的内容。

备选方案：

- 在步骤里直接调用 FastAPI TestClient。可作为本地加速备选，但不是主设计，因为用户明确要求以 `behave --stage http` 驱动，且当前更强调接近真实验收路径。
- 用纯 API mock server。放弃，因为失去对真实后端行为的保护价值。

### 5. Nx 使用独立 target `app-api:test-uat`，不复用 `app-api:test-integration`

决策：新增 `app-api:test-uat` 作为唯一的 BDD/UAT 运行入口。`app-api:test-integration` 保持其原本语义，用于未来非 BDD 的后端集成测试，不再承载 Behave 执行逻辑。

建议职责划分：

- `app-api:test-uat`：执行 `behave --stage http`，必要时串接 DB 初始化与环境准备。
- `app-api:test-integration`：保留给 pytest 或其他非 BDD 集成测试。
- 独立的 `scope:ux` UAT/BDD 工程 target：用于检查 BDD 目录形态、命名规范和数据目录完整性。

原因：一旦把 BDD 混进 `test-integration`，后续团队会把“行为契约验收”和“技术性集成校验”视为同一件事，导致职责边界不断模糊。单独 target 名称也更利于 CI、文档和 onboarding。

备选方案：

- 直接改造 `test-integration` 运行 Behave。放弃，因为会破坏语义清晰度，也与用户明确要求冲突。

### 6. 规范约束优先通过 Nx target + 轻量校验脚本落地

决策：不把规范仅停留在文档层，而是通过 Nx 增加显式校验入口。由于 feature 文件工程约束是跨前后端的共享规则，这些检查不应挂在 `app-api` 项目上，而应由独立的 UAT/BDD 工程承载，并归入 `scope:ux` 范围。校验内容建议包括：

- 主功能 feature 文件是否与同名目录成对出现。
- 子功能 feature 是否满足 `主功能_子功能.feature` 命名。
- `db/` 下是否存在与主功能对应的数据目录或基线文件。
- `test-uat` 是否固定使用 `behave --stage http`。

原因：仅靠 code review 很难长期保证目录规范不漂移。将其做成独立 target 后，团队可以在本地与 CI 中重复执行。

补充约束：

- `app-api:test-uat` 只承担后端 HTTP UAT 的执行职责。
- Feature 命名、目录结构、共享数据目录等跨端规范检查，应由独立的 `scope:ux` UAT/BDD 工程负责，而不是由 `app-api` 持有。

备选方案：

- 仅靠 README 说明规范。放弃，因为缺少强约束。
- 把所有逻辑塞进一个复杂自定义 Nx plugin。当前阶段先不采用，因为成本偏高；先用 run-commands + repo 内脚本即可满足约束与演进需求。

### 7. Python data factory 可以复用 infrastructure，但要限制在“测试数据注入边界”内

决策：允许 BDD 测试代码借鉴现有 unit test factories，并在专用的测试数据注入层中直接引用 infrastructure 层代码写入数据库；但这种引用必须被限制在 `features/http_steps/` 及其配套的 factory / seeding 模块内，不能扩散到 feature 文本、步骤业务语句或生产代码路径中。

边界控制的重点是避免两类问题：

- 第一类问题是“自测实现本身”。如果数据准备直接调用待测的应用层 use case、HTTP 接口，或复用与生产行为完全同一路径的业务命令去造前置数据，那么测试前置条件本身就可能被待测逻辑污染，导致场景失败时难以判断是“准备错了”还是“功能坏了”。
- 第二类问题是“测试代码无限制依赖实现细节”。如果 step definitions 到处直接 new repository、直接操作 SQLAlchemy model、直接拼事务逻辑，测试会快速和内部实现强耦合，后续稍有重构就大面积碎裂。

因此这里的推荐边界是：

- Feature 文件只描述业务行为，不出现 infrastructure 细节。
- Step definitions 只表达“给定 Alice 是已激活用户”这类场景语言，不直接散落数据库写入逻辑。
- 将真正的数据准备集中到单独的 `features/http_steps/factories/` 模块。
- 该 seeding 模块内部允许复用现有 unit test factory 的建模能力，并允许调用 infrastructure repository、session、uow 或等价持久化入口，把数据稳定写入 DB。
- 不允许为了准备数据去调用待测 HTTP 接口本身，也不建议调用本次正在验证的 application command 作为主要 seed 手段。

这样做的收益是：

- 场景前置数据仍然可读，可复用 Alice、Bob 等统一身份名。
- 测试实现对基础设施有“受控耦合”，但不会让所有步骤都被实现细节淹没。
- 即使未来 persistence 实现调整，也只需要收敛修改 seeding 边界，而不是修改所有 feature 和 step。

## Risks / Trade-offs

- [Risk] 使用真实数据库和真实 HTTP 进程会让 BDD 比单元测试更慢。 → Mitigation：将 BDD 保持在验收层，不替代单元测试；通过共享基础数据、减少重复启动和分层 target 降低开销。
- [Risk] `features/` 与 `db/` 两套目录如果缺乏映射规则，后续容易各自演化。 → Mitigation：在校验脚本中显式检查主功能目录和数据目录是否成对存在。
- [Risk] Alice、Bob 等可读名称在场景增加后可能不够表达复杂上下文。 → Mitigation：允许在同一命名体系中扩展为 `Alice Admin`、`Bob Inactive` 这类语义化身份，但仍避免随机命名。
- [Risk] Behave stage 目录命名如果实现时理解偏差，可能造成步骤未加载。 → Mitigation：严格遵循 `features/http_environment.py` 与 `features/http_steps/` 的 stage 前缀约定，并在 `app-api:test-uat` 中加入 dry-run 校验步骤。
- [Risk] BDD 与未来 UI 场景共享数据后，会提高数据基线变更成本。 → Mitigation：区分共享基础数据与场景增量数据，避免所有场景都绑定在一份大而脆弱的数据快照上。

### 8. 执行策略采用“本地开发友好 + CI 可重复”双模式

决策：`app-api:test-uat` 采用面向业务理解的名称，但在执行策略上区分本地与 CI 两种场景。

本地建议：

- 使用已有 `app-api:bootstrap-local` 准备数据库。
- 在独立终端运行 `app-api:serve`，保持应用可访问。
- 通过 `app-api:test-uat` 执行完整 HTTP BDD，必要时支持透传 Behave 参数，例如仅跑某个主功能或标签。
- 可增加一个轻量预检查模式，例如在 target 中先跑一次 `behave --stage http --dry-run`，用于快速发现步骤缺失或目录命名错误。

补充约束：

- `app-api:test-uat` 默认要求开发者手动开启后端服务，不整合后端启动功能。
- 本地 UAT target 只负责执行验收测试，不负责启动 API、迁移数据库或托管长期运行进程。

CI 建议：

- 不依赖开发者手工启动的本地服务，CI job 应显式完成数据库启动、迁移、应用启动和 UAT 执行。
- 优先采用单 job 串行方式保证稳定性：准备数据库 → migration → 启动 API → 健康检查 → `nx run app-api:test-uat`。
- 如果后续耗时明显增长，再考虑按标签或主功能拆分多个 UAT job，但首批不建议并行切分，以降低诊断复杂度。
- CI 首批应输出 JUnit 结果，便于被 CI 平台、测试聚合器和问题面板稳定消费；Behave 的终端输出继续保留给开发者阅读。

原因：本地开发更关注反馈速度与可调试性，CI 更关注环境自洽与可重复执行。把两者混成一个固定模式，要么开发太重，要么 CI 不稳定。

## Migration Plan

1. 在仓库顶层落下 `features` 目录骨架，包括 `db/`、`http_environment.py` 与 `http_steps/`，并建立主功能与子功能的 feature 文件结构。
2. 在项目依赖中接入 Behave，并为本地配置增加稳定的执行入口。
3. 基于现有 unit test factory 思路补充 Python data factory 与 infrastructure 注入逻辑，先支撑 `features/db/` 所定义的基础身份模型。
4. 新增 `app-api:test-uat` target，固定通过 `behave --stage http` 运行 HTTP BDD。
5. 新增独立的 `scope:ux` UAT/BDD 工程，承载跨端的 feature 工程规范检查 target。
6. 先实现用户与认证最小闭环场景：创建用户、激活、反激活、赋予管理员、登录、注销。
7. 再补充 repo 内 Python 校验脚本和独立 UAT/BDD 工程中的检查 target，使目录与命名规则进入自动校验链路。
8. 若后续需要回滚，只需移除新增 UAT target、独立 UAT/BDD 工程、Behave 依赖和顶层 `features` 目录，不影响现有业务代码和 pytest 单元测试结构。

## Open Questions

- 当前无新增开放问题。后续若进入实现阶段发现运行时约束、CI 时长或报告消费存在新矛盾，再在新的 design 迭代中补充。