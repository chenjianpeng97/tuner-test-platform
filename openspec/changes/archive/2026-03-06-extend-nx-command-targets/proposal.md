## Why

Nx 第一阶段接管的前后端命令还比较少，开发者仍然需要记忆不少模板原生命令，例如前端预览与格式化、后端覆盖率、本地数据库启动、环境准备和迁移命令。现在适合继续扩展 Nx 的包裹层，并为每个 target 补充说明描述，让项目在不改变底层模板工作流的前提下，提供更完整、更易理解的统一命令入口。

## What Changes

- 扩展现有 Nx 命令层，为前后端模板中已经存在且有较高价值的原生命令补充更多 target。
- 为现有和新增的 Nx target 增加 `metadata.description`，使每个 target 都能在配置和相关工具中直接说明自身用途。
- 保持当前包管理与运行时分工不变：前端 target 继续调用模板中的 `pnpm` 脚本，后端 target 继续调用模板中的 `uv`、`make`、Docker Compose 与迁移命令。
- 更新命令映射文档，让开发者可以清楚看到哪些原生命令已经被 Nx 接管，哪些仍属于后续规划。

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `nx-command-unification`: 扩展被 Nx 包装的模板原生命令范围，并要求 Nx 管理的 target 具备可发现的描述信息。

## Impact

- Affected code: [shadcn-admin/project.json](shadcn-admin/project.json)、[fastapi-clean-example/project.json](fastapi-clean-example/project.json) 以及命令清单相关说明文档。
- Affected workflows: 前端预览 / 格式化 / 维护类命令，以及后端格式化 / 覆盖率 / 环境准备 / 数据库运维 / 迁移类命令将可以通过 `nx run ...` 统一执行。
- Affected tooling: Nx 项目元数据会更完整，便于编辑器和后续任务发现能力使用。
