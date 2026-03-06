## Why

当前项目是从两个独立的开源模板起步：前端基于 `shadcn-admin`，后端基于 `fastapi-clean-example`。在这一阶段，如果继续分别使用前端的 `pnpm` 命令和后端的 `uv` / Python 命令来启动、测试和构建，会让工程入口分散，后续也难以把 OpenAPI、BDD、代码生成和依赖图纳入统一工作流。

现在引入 Nx 的第一步，不是重构现有模板代码，而是先让 Nx 接管当前前后端工程的常用命令入口，为后续的依赖图、变更影响分析、生成链编排和领域模块增量演进打基础。

## What Changes

- 在仓库根目录启用 Nx workspace，用于统一管理当前前后端模板工程。
- 将现有前端模板注册为 `app-web` 项目，将现有后端模板注册为 `app-api` 项目。
- 为前后端补充第一批 Nx target，优先覆盖当前最常用的命令入口，如 `serve`、`build`、`lint`、`test`。
- 通过 Nx target 包装并替代当前直接调用的前端 `pnpm` 命令和后端 `uv` / Python 命令。
- 为后续 OpenAPI 导出、前端 API client 生成、MSW mock、BDD 测试等能力预留可扩展的项目与 target 结构。
- 明确本阶段不要求立即重构模板内部目录，也不要求立即拆分为完整的前后端库结构。

## Capabilities

### New Capabilities
- `nx-command-unification`: 为当前基于模板起步的前后端项目提供统一的 Nx 命令入口，使开发、构建、检查和测试任务能够通过 Nx 执行与编排。
- `nx-project-registration`: 在 Nx 中登记当前前后端项目及其基础 target，为后续依赖图展示、受影响分析和增量扩展提供工程元数据基础。

### Modified Capabilities
- None.

## Impact

- 受影响代码范围：仓库根目录工程配置、前端模板目录、后端模板目录。
- 受影响依赖：需要增加 Nx 及其相关前端 workspace 依赖，并将现有前端 Node 工作流纳入 Nx；后端仍保留原有 Python 依赖体系，但通过 Nx 统一触发常用命令。
- 受影响工作流：开发者将从分别记忆前端和后端命令，过渡为优先使用 `nx run ...` 作为统一入口。
- 后续扩展影响：为 OpenAPI、orval、MSW、BDD、领域模块拆分和依赖图治理提供统一承载层。