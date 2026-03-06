## Context

当前 workspace 已经把前端模板包装为 `app-web`、把后端模板包装为 `app-api`，但现有 target 仍只覆盖第一批高频命令。前面的探索结果表明，原始模板中仍有不少开发者会直接使用的原生命令尚未被接管，例如前端的预览、格式化和死代码分析，以及后端的格式化、聚合检查、覆盖率、环境准备、数据库容器操作和迁移命令。

这次实现需要在不改变当前包管理分工、也不重构模板目录布局的前提下扩展命令覆盖面。整体方案应保持轻量：Nx 仍然只是模板原生命令之上的统一包装层与发现层，而不是去替代 `pnpm`、`uv`、`make`、Docker Compose 或 Alembic 本身。

## Goals / Non-Goals

**Goals:**
- 为 `app-web` 和 `app-api` 补充更多高价值模板原生命令对应的 Nx target。
- 为现有和新增 target 增加 `metadata.description`，使每个命令在配置和工具中都具备自解释能力。
- 保持 target 命名稳定且可读，优先采用面向 Nx 的语义化名称，而不是直接照搬 Makefile 原始任务名。
- 保持两个模板当前的工作目录与底层命令执行方式不变。
- 更新命令清单说明，解释扩展后的映射关系。

**Non-Goals:**
- 不新增模板中原本不存在的全新工作流，例如前端测试或 OpenAPI 导出自动化。
- 不迁移前后端到新的物理目录布局。
- 不用新的 executor 或包管理模式替换 Makefile、`pnpm`、`uv` 或 Alembic。
- 不在本次变更中重新设计缓存、affected 规则或依赖图边界治理。

## Decisions

### Decision 1: Only wrap existing template-native commands
本次变更只暴露那些已经存在于前端 `package.json`、后端 `Makefile` 或后端文档化运维流程中的命令。

**Rationale:**
- 这样可以让本次变更专注于“命令统一入口”，而不是引入新的产品行为。
- 被包装的命令在 Nx 之外已经可用，因此可以减少执行语义上的歧义。
- 这样也更容易验证 spec：原生命令先存在，再变成可由 Nx 调用的 target。

**Alternatives considered:**
- 为未来规划中的工作流（例如 `app-web:test` 或 `app-api:export-openapi`）提前新增 target。拒绝原因是这些属于未来能力建设，而不是对现有模板命令的直接统一。

### Decision 2: Use semantic Nx target names rather than copying raw Makefile names
后端 target 将使用 `format`、`coverage`、`db-up`、`infra-down`、`migrate` 这类语义化名称，而不是直接复制 `code.format`、`up.db` 这类带点号的 Makefile 标识。

**Rationale:**
- 语义化 target 名称更容易记忆，也更符合现有 Nx 的 target 词汇体系。
- 这样可以在后端模板内部命名之上建立一层稳定的抽象接口。
- 后续新增库和服务时也更容易沿用相同命名方式。

**Alternatives considered:**
- 直接在 target 标识中镜像 Makefile 名称。拒绝原因是这会把模板内部命名细节泄漏到共享的 Nx 接口层。

### Decision 3: Add `metadata.description` to every managed target
每个现有和新增 target 都会在 `metadata.description` 下带有简短说明。

**Rationale:**
- JSON 不支持注释，因此 metadata 是更可维护的 target 用途说明方式。
- Nx 相关工具可以直接消费 metadata，用于更好的任务发现体验。
- 描述信息还能帮助区分一些名称相近的运维 target，例如“仅数据库”与“完整基础设施”两类命令。

**Alternatives considered:**
- 只依赖外部文档说明。拒绝原因是命令语义会与开发者实际查看的配置文件脱节。

### Decision 4: Prioritize command groups that improve daily discoverability
本次变更优先收编那些能够提升日常可发现性、或在新成员接入时最容易造成摩擦的命令组。

**Rationale:**
- 前端预览与格式化属于常见的本地开发操作。
- 后端格式化、覆盖率、环境准备、数据库生命周期和迁移属于本地开发中的常见操作步骤。
- 像目录树可视化这类价值较低的维护型命令，可以留待后续再考虑是否接入。

**Alternatives considered:**
- 一次性包装所有 Makefile 工具。拒绝原因是会让 target 面过大，不利于保持命令表面的聚焦与可读性。

## Risks / Trade-offs

- [Risk] target 变多后，项目配置可能显得更嘈杂。→ Mitigation: 使用简洁命名、统一分组，并为每个 target 增加 `metadata.description`。
- [Risk] 依赖 `APP_ENV` 的运维 target 在缺少前置条件时可能执行失败。→ Mitigation: 保留底层命令现有的 guard 行为，并通过描述信息明确说明用途。
- [Risk] 部分后端命令更适合本地环境而不是 CI。→ Mitigation: 将其定位为便利型 target，不对其附加过多缓存或编排假设。
- [Risk] 迁移命令采用文档中的 Alembic 调用方式，而不是直接来自 Makefile，会形成一个非 Makefile 例外。→ Mitigation: 在说明文档中明确该差异，并将范围限制在一个常见迁移命令上。

## Migration Plan

1. 更新 `app-web` target，加入新增的前端包装命令，并为每个 target 增加描述。
2. 更新 `app-api` target，加入选定的后端包装命令，并为每个 target 增加描述。
3. 更新命令清单说明，让 Nx 映射关系在配置文件之外也可见。
4. 验证一组具有代表性的新 target，确认它们能正确解析到预期的原生命令。

回滚方式较直接：从项目配置中移除新增 target 与 metadata 即可，不会影响底层模板本身。

## Open Questions

- 后端便利型 target（例如 `db-logs` 和 `db-shell`）是否要在这次一起纳入，还是在 target 数量过大时延后到后续变更。
- Alembic 迁移 target 是否应继续保持直接命令方式，还是后续为了统一性再包装回后端 Makefile。
