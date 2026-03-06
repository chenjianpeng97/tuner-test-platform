# Nx 命令接管清单（第一阶段）

## 0. 使用说明

第一阶段的目标是让仓库根目录的 Nx 成为统一入口，而不是替换前后端各自的依赖管理器。

- 根目录负责安装和提供 `Nx`
- [shadcn-admin](../shadcn-admin) 继续保留自己的 `pnpm` 依赖体系
- [fastapi-clean-example](../fastapi-clean-example) 继续保留自己的 `uv` / Python 依赖体系

因此，开发者后续优先使用：

- `npx nx run app-web:serve`
- `npx nx run app-web:build`
- `npx nx run app-web:format-check`
- `npx nx run app-api:serve`
- `npx nx run app-api:lint`
- `npx nx run app-api:test-unit`
- `APP_ENV=local npx nx run app-api:env`

## 1. 当前模板原始命令

### 前端模板 [shadcn-admin](../shadcn-admin)

- 启动开发服务：`pnpm dev`
- 构建：`pnpm build`
- 检查：`pnpm lint`
- 预览构建结果：`pnpm preview`
- 检查格式：`pnpm format:check`
- 格式化代码：`pnpm format`
- 分析未使用依赖与导出：`pnpm knip`

### 后端模板 [fastapi-clean-example](../fastapi-clean-example)

- 启动服务：`APP_ENV=local uv run python src/app/run.py`
- 代码检查：`uv run make code.lint`
- 单元测试：`uv run pytest -v`
- 代码格式化：`uv run make code.format`
- 聚合检查：`uv run make code.check`
- 覆盖率统计：`uv run make code.cov`
- 覆盖率 HTML：`uv run make code.cov.html`
- 打印当前环境：`uv run make env`
- 生成 `.env`：`uv run make dotenv`
- 启动数据库容器：`uv run make up.db`
- 停止数据库容器：`uv run make down.db`
- 启动完整基础设施：`uv run make up`
- 停止完整基础设施：`uv run make down`
- 执行迁移：`uv run alembic upgrade head`
- 集成测试：第一阶段暂未稳定接入，预留 `test-integration` target 说明位

## 2. 当前已接管的 Nx target

- `nx run app-web:serve`
- `nx run app-web:build`
- `nx run app-web:lint`
- `nx run app-web:preview`
- `nx run app-web:format-check`
- `nx run app-web:format`
- `nx run app-web:knip`
- `nx run app-api:serve`
- `nx run app-api:lint`
- `nx run app-api:test-unit`
- `nx run app-api:test-integration`
- `nx run app-api:format`
- `nx run app-api:check`
- `nx run app-api:coverage`
- `nx run app-api:coverage-html`
- `nx run app-api:env`
- `nx run app-api:dotenv`
- `nx run app-api:db-up`
- `nx run app-api:db-down`
- `nx run app-api:infra-up`
- `nx run app-api:infra-down`
- `nx run app-api:migrate`

> 说明 1：`app-api:test-integration` 当前仍是显式占位 target，用来保留稳定命名，后续再接到真实 DB / BDD HTTP 验收链路。

> 说明 2：后端 `env`、`dotenv`、`db-up`、`db-down`、`infra-up`、`infra-down`、`migrate` 等 target 依旧保留底层命令对 `APP_ENV` 的约束；如需特定环境，请在执行 Nx 命令前显式设置环境变量。

## 3. 当前优先使用的语义化命名

后端模板内部的 Makefile 使用 `code.format`、`up.db` 这类命名；在 Nx 层统一收敛为更稳定的语义化 target：

- `code.format` → `app-api:format`
- `code.check` → `app-api:check`
- `code.cov` → `app-api:coverage`
- `code.cov.html` → `app-api:coverage-html`
- `up.db` → `app-api:db-up`
- `down.db` → `app-api:db-down`
- `up` → `app-api:infra-up`
- `down` → `app-api:infra-down`

## 4. 命名与扩展预留

当前已固定的项目命名：

- `app-web`
- `app-api`

后续建议沿用的扩展命名：

- `doc-api`
- `fe-api-client`
- `fe-mock-server`
- `app-api-e2e-http`
- `app-web-e2e-ui`

这样做的目的是让后续新增 OpenAPI、前端 client、MSW、BDD 等项目时，可以直接进入同一套 Nx 项目图与 target 命名体系，而不必回头重命名当前项目。
