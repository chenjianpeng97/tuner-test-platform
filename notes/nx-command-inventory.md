# Nx 命令接管清单（第一阶段）

## 0. 使用说明

第一阶段的目标是让仓库根目录的 Nx 成为统一入口，而不是替换前后端各自的依赖管理器。

- 根目录负责安装和提供 `Nx`
- [shadcn-admin](../shadcn-admin) 继续保留自己的 `pnpm` 依赖体系
- [fastapi-clean-example](../fastapi-clean-example) 继续保留自己的 `uv` / Python 依赖体系

因此，开发者后续优先使用：

- `npx nx run app-web:serve`
- `npx nx run app-web:build`
- `npx nx run app-api:serve`
- `npx nx run app-api:lint`
- `npx nx run app-api:test-unit`

## 1. 当前模板原始命令

### 前端模板 [shadcn-admin](../shadcn-admin)

- 启动开发服务：`pnpm dev`
- 构建：`pnpm build`
- 检查：`pnpm lint`

### 后端模板 [fastapi-clean-example](../fastapi-clean-example)

- 启动服务：`APP_ENV=local uv run python src/app/run.py`
- 代码检查：`uv run make code.lint`
- 单元测试：`uv run pytest -v`
- 集成测试：第一阶段暂未稳定接入，预留 `test-integration` target 说明位

## 2. 第一阶段对应的 Nx target

- `nx run app-web:serve`
- `nx run app-web:build`
- `nx run app-web:lint`
- `nx run app-api:serve`
- `nx run app-api:lint`
- `nx run app-api:test-unit`
- `nx run app-api:test-integration`

> 说明：`app-api:test-integration` 在第一阶段先作为显式占位 target，用来保留稳定命名，后续再接到真实 DB / BDD HTTP 验收链路。

## 3. 命名与扩展预留

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
