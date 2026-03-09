## 1. 顶层 BDD 骨架

- [x] 1.1 在仓库顶层创建 `features/`、`features/db/`、`features/http_steps/` 与 `features/http_environment.py` 基础结构
- [x] 1.2 在 `features/` 下创建 `user.feature`、`auth.feature` 与 `user/user_auth.feature` 的主功能和子功能文件骨架
- [x] 1.3 为 `behave --stage http` 配置顶层 feature 根目录与 stage 约定，确保 `http_environment.py` 和 `http_steps/` 能被正确加载

## 2. Behave 与执行基础设施

- [x] 2.1 在后端项目依赖中接入 Behave 及执行 HTTP BDD 所需的最小依赖
- [x] 2.2 在后端项目中补充运行 Behave 所需的配置文件或命令参数，固定 `--stage http`
- [x] 2.3 在 `app-api` 的 Nx 配置中新增 `test-uat` target，并确保其默认不负责启动后端服务
- [x] 2.4 为 `test-uat` 增加本地 dry-run 或等价预检查能力，用于尽早发现 steps 缺失和目录命名错误

## 3. 测试数据工厂与数据库注入

- [x] 3.1 在 `features/http_steps/factories/` 中建立共享测试数据注入模块
- [x] 3.2 借鉴现有 `tests/app/unit/factories` 的模式，封装 Alice、Bob、Charlie 等共享身份的 Python data factory
- [x] 3.3 在受控边界内接入 infrastructure 持久化能力，使 factories 可以稳定向本地数据库写入前置数据
- [x] 3.4 建立 `features/db/base/`、`features/db/user/` 与 `features/db/auth/` 对应的数据语义组织方式，并让 factories 与之对齐

## 4. 用户主功能 HTTP BDD 场景

- [x] 4.1 为 `features/user.feature` 编写用户创建场景，覆盖成功创建与共享身份引用
- [x] 4.2 为 `features/user.feature` 编写用户激活场景，覆盖状态变更可观察结果
- [x] 4.3 为 `features/user.feature` 编写用户反激活场景，覆盖状态变更可观察结果
- [x] 4.4 在 `features/http_steps/` 中实现用户主功能相关的 Given / When / Then 步骤，并复用共享 data factory

## 5. 用户授权与认证 HTTP BDD 场景

- [x] 5.1 为 `features/user/user_auth.feature` 编写超级管理员赋予管理员权限场景
- [x] 5.2 为 `features/user/user_auth.feature` 编写未授权主体赋权失败场景
- [x] 5.3 为 `features/auth.feature` 编写登录成功、登录失败与注销成功场景
- [x] 5.4 在 `features/http_steps/` 中实现授权与认证相关步骤，并验证会话建立与失效行为

## 6. Nx 约束与校验脚本

- [x] 6.1 在仓库内新增 Python 校验脚本，检查主功能 feature 与同名目录是否成对存在
- [x] 6.2 在仓库内新增 Python 校验脚本，检查子功能 feature 是否满足 `主功能_子功能.feature` 命名
- [x] 6.3 在仓库内新增 Python 校验脚本，检查 `features/db/` 与主功能目录的数据映射是否存在
- [x] 6.4 新增独立的 UAT/BDD Nx 工程（例如 `ux-uat`）并赋予 `scope:ux` 范围，用于承载跨端 feature 工程约束
- [x] 6.5 在该独立 UAT/BDD 工程中新增用于执行上述规则检查的 target，并将其作为 feature 工程规范的唯一入口，而不是挂在 `app-api` 下

## 7. CI 与结果输出

- [x] 7.1 为 `app-api:test-uat` 增加 JUnit 结果输出配置，满足 CI 首批消费要求
- [x] 7.2 梳理并记录 CI 执行 `test-uat` 所需的显式步骤，包括数据库启动、迁移、应用启动、健康检查与 UAT 执行顺序
- [x] 7.3 验证本地手动启动服务 + `nx run app-api:test-uat` 的开发流程，以及 CI 串行执行流程都可稳定运行