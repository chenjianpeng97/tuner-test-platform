## 1. Workspace bootstrap

- [x] 1.1 在仓库根目录初始化 Nx workspace 所需的基础配置文件。
- [x] 1.2 在根目录补充用于承载 Nx 的 Node 依赖配置，并明确与现有前端模板依赖的关系。
- [x] 1.3 确认当前前端模板与后端模板的原始启动、构建、检查、测试命令，形成第一版接管清单。

## 2. Register current projects

- [x] 2.1 为 [shadcn-admin](shadcn-admin) 创建 Nx 项目配置，并注册为 `app-web`。
- [x] 2.2 为 [fastapi-clean-example](fastapi-clean-example) 创建 Nx 项目配置，并注册为 `app-api`。
- [x] 2.3 为两个项目补充基础 metadata，使其能被 Nx 项目列表和项目图识别。

## 3. Unify command targets

- [x] 3.1 为 `app-web` 配置 `serve`、`build`、`lint` 等第一批 target，并映射到现有前端命令。
- [x] 3.2 为 `app-api` 配置 `serve`、`lint`、`test-unit` 等第一批 target，并映射到现有后端命令。
- [x] 3.3 评估 `test-integration` 的当前可执行入口；如暂不具备稳定实现，则提供显式占位或受限说明。

## 4. Validate and document usage

- [x] 4.1 执行 `nx run app-web:serve`、`nx run app-web:build` 或同等级检查命令，验证前端接管成功。
- [x] 4.2 执行 `nx run app-api:lint`、`nx run app-api:test-unit` 或同等级检查命令，验证后端接管成功。
- [x] 4.3 在说明文档中记录新的统一入口，指导开发者优先通过 Nx 运行当前前后端工程。
- [x] 4.4 确认当前配置已为后续 `doc-api`、`fe-api-client`、`fe-mock-server` 和 BDD 项目预留稳定命名与扩展方式。