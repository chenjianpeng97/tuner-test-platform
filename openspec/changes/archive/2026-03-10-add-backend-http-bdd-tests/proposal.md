## Why

当前后端已经具备用户创建、激活、反激活、管理员权限赋予，以及登录与注销等 HTTP 功能，但缺少一套以业务语言表达、可直接驱动 HTTP 层的 BDD 集成测试。现在补齐这部分测试，可以把已实现能力固化为可回归的行为契约，并为后续 UI 层复用同一套基础数据与 feature 文档打下稳定基础。

## What Changes

- 为整个仓库新增以 `behave --stage http` 驱动的顶层 Feature 测试方案，Feature 文件统一放在仓库根目录 `./features` 下，覆盖当前已实现的后端用户与认证 HTTP 行为，并为后续前端复用预留同一套行为描述。
- 按主功能与子功能拆分 feature 目录，建立严格的命名与层级规范：主功能使用同名 `.feature` 文件，子功能放入同级主功能目录下并使用 `主功能_子功能.feature` 命名。
- 在 BDD 顶层新增数据库初始化数据维护目录，放在 `./features` 下与 Feature 文件同层治理，维护与 feature 文本一致的基础命名数据，如 Alice、Bob 等，确保后端集成测试与未来 UI 测试能够共享同一批可读测试数据。
- 识别并补全当前已实现能力对应的场景集合，至少覆盖用户创建、用户激活、用户反激活、超级管理员赋予管理员权限、登录、注销等关键 HTTP 行为。
- 为 BDD / 验收测试单独引入业务侧更易理解的专用 Nx 入口 `app-api:test-uat`；现有 `app-api:test-integration` 不作为 BDD 入口使用。同时，为 feature 命名、目录结构、测试数据目录这类不区分前后端的约束新增独立的 UAT/BDD 工程承载检查职责，并归入 `scope:ux` 范围。
- 后续本 change 中产生的 OpenSpec proposal、design、spec、tasks 等内容正文统一使用中文，方便与团队中文协作及现有提示词约束对齐。

## Capabilities

### New Capabilities
- `http-bdd-user-core`: 规范并覆盖用户主功能的 HTTP BDD 场景，包括用户创建、激活、反激活，以及对应的主功能 feature 文件与步骤组织方式。
- `http-bdd-user-admin-authz`: 规范并覆盖用户管理中的授权子功能 HTTP BDD 场景，包括超级管理员向其他用户赋予管理员权限等角色授权行为及其子功能 feature 布局。
- `http-bdd-auth-session`: 规范并覆盖认证相关 HTTP BDD 场景，包括登录、注销、认证态前后置条件与会话结果验证。
- `http-bdd-test-infrastructure`: 定义 `behave --stage http` 所需的测试基建，包括顶层 `./features` 目录规范、数据库初始化数据目录与命名规则、基于 Python data factory 的数据注入方式、HTTP 测试启动方式，以及基于 Nx 的执行与校验约束。

### Modified Capabilities
- 无

## Impact

- 影响仓库顶层测试目录与后端执行方式，预计主要位于仓库根目录 `./features` 下新增或重组 Feature 文件、数据初始化目录、stage 环境文件与 step definitions，并在后端工程内补充相应的数据注入代码。
- 影响后端项目依赖与测试工具链，预计需要接入 Behave 及其 HTTP stage 所需的测试支持代码。
- 影响 Nx 项目配置，预计新增 `app-api:test-uat` 作为后端 HTTP BDD/UAT 运行入口；`app-api:test-integration` 保持为非 BDD 的集成测试语义；同时预计新增一个独立的 `scope:ux` UAT/BDD 工程承载跨端规范检查型 target。
- 影响后续测试编写规范，新的 feature 命名、目录层次、基础数据命名与 OpenSpec 中文化约束将成为新增测试的默认标准。