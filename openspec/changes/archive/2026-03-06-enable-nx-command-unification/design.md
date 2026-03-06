## Context

当前仓库以两个已存在的模板为起点：前端位于 [shadcn-admin](../../../../shadcn-admin)，后端位于 [fastapi-clean-example](../../../../fastapi-clean-example)。两者当前分别使用各自生态中的原生命令运行：前端基于 `pnpm` 和 `vite`，后端基于 Python / `uv` / `pytest` / `ruff` / `make` 等命令。

本次变更的目标不是立即调整业务代码结构，而是先建立一个足够轻量的 Nx 外层，使 Nx 成为统一的工程入口。这样可以在不破坏模板可运行性的前提下，先统一启动、构建、检查和测试命令，并为后续注册 OpenAPI、BDD、mock、代码生成和领域模块拆分提供项目图和 target 编排基础。

当前仓库还没有既有的 OpenSpec 主 spec，因此本次能力会以新增 capability 的方式定义。Nx 也将在第一阶段只承担“统一入口”和“登记项目”的职责，而不是立刻承接所有 monorepo 边界治理能力。

## Goals / Non-Goals

**Goals:**
- 在仓库根目录建立 Nx workspace，并让其成为前后端工程的统一命令入口。
- 将现有前端模板登记为 `app-web`，将现有后端模板登记为 `app-api`。
- 先包装当前最常用的命令，包括前端的 `dev/build/lint` 与后端的 `serve/lint/test`。
- 保持前后端模板目录基本不动，避免在引入 Nx 的同时做大规模重构。
- 为后续扩展 `doc-api`、`fe-api-client`、`fe-mock-server`、BDD 项目和更多领域模块时保留一致的 target 设计方式。

**Non-Goals:**
- 本阶段不把前后端源码立即迁移到 `apps/` / `libs/` 目标目录。
- 本阶段不实现完整的 affected 分析、缓存优化、远程缓存或严格的 tag 约束。
- 本阶段不接入 OpenAPI 导出、orval、MSW、BDD 执行链，只预留后续对接方式。
- 本阶段不改写后端的 clean architecture 分层，也不改写前端现有 feature 目录。

## Decisions

### Decision 1: 采用“包裹式接入”而不是“先迁移目录”

将 `shadcn-admin` 和 `fastapi-clean-example` 先视为现有项目根目录，并直接为这两个目录配置 `project.json`，而不是先把代码搬到新的 `apps/web`、`apps/api` 目录。

**Rationale:**
- 可最大程度保留两个模板现有可运行状态。
- 可以把风险集中在工程编排层，而不是同时处理代码迁移和命令迁移。
- 更适合当前阶段“先统一入口，后逐步重构”的目标。

**Alternatives considered:**
- 直接把模板整体搬迁到目标 monorepo 目录。该方式最终可能更整齐，但会显著增加首次引入 Nx 的成本和不确定性，因此不作为第一步。

### Decision 2: 前端与后端依旧保留各自依赖体系，由 Nx 只负责统一触发

前端继续使用现有 Node / `pnpm` 工作流，后端继续使用现有 Python / `uv` / `pytest` / `ruff` 工作流。Nx 本阶段不替代语言生态内的包管理器，而是负责统一命令入口。

**Rationale:**
- 这样可以避免把“依赖管理迁移”与“Nx 引入”耦合在一起。
- 对于 Python 项目，Nx 更适合作为任务编排器，而不是依赖管理器。
- 保留原有生态工具有助于快速验证当前模板命令是否已被正确接管。

**Alternatives considered:**
- 试图立即让 Nx 统一前后端依赖管理。该方式超出当前范围，且对 Python 项目并不现实。

### Decision 3: 第一批 target 以开发者高频命令为主

第一批 target 只覆盖高频命令：

- `app-web:serve`
- `app-web:build`
- `app-web:lint`
- `app-api:serve`
- `app-api:lint`
- `app-api:test-unit`
- `app-api:test-integration`（如当前只能先映射到现有测试命令，可先占位）

**Rationale:**
- 有利于快速建立“统一入口”的使用习惯。
- 有利于尽快验证 Nx 配置对当前项目是否足够实用。
- 可以为后续生成链和 BDD target 设计命名规范。

**Alternatives considered:**
- 一次性补齐所有 target，包括 OpenAPI、BDD、mock、代码生成。这会扩大首次变更范围，不利于分阶段落地。

### Decision 4: 使用稳定的项目命名作为未来扩展的锚点

本阶段使用：

- `app-web`
- `app-api`

后续新增项目可继续采用统一命名风格，例如：

- `doc-api`
- `fe-api-client`
- `fe-mock-server`
- `app-api-e2e-http`
- `app-web-e2e-ui`

**Rationale:**
- 项目命名一旦进入团队习惯和脚本调用后，不宜频繁修改。
- 先确定命名方式，有利于后续扩展依赖图和变更分析。

## Risks / Trade-offs

- [Risk] Nx 只是包装现有命令，短期内看起来“只是多套一层”。 → Mitigation：本阶段明确目标就是统一入口和项目登记，不以一次性获得全部收益为标准。
- [Risk] 前后端项目仍位于模板原目录，和理想 monorepo 目录不完全一致。 → Mitigation：先接受物理结构与逻辑结构分离，等后续新增领域模块时再逐步抽离。
- [Risk] 后端 `serve` / `test-integration` 的具体命令可能依赖环境变量、数据库或 `Makefile` 约定。 → Mitigation：优先映射当前最稳定的命令；对需要环境准备的 target 可先显式约束输入条件或先做占位。
- [Risk] 没有立即引入 tag 约束和 affected 规则，短期内图谱价值有限。 → Mitigation：先完成项目注册和常用 target，待项目数增加后再补充结构治理。

## Migration Plan

1. 在仓库根目录初始化 Nx 所需配置。
2. 注册 `app-web` 和 `app-api` 两个项目，并分别指向现有模板目录。
3. 为两个项目补齐第一批 target，确保至少能覆盖日常启动、构建、检查和基础测试命令。
4. 在 README 或 notes 中明确新入口，指导开发者优先使用 `nx run ...`。
5. 观察一轮实际开发使用情况，再进入下一阶段：补充 OpenAPI、mock、BDD 等项目。

如果首轮接管失败，可回退为继续使用模板原始命令，不会影响业务代码本身，因为本阶段没有大规模移动代码。

## Open Questions

- 后端 `serve` 是否统一走 `uv run`、`python -m` 还是 `make` 包装，需要在实施时结合模板实际入口确认。
- 前端后续是否保留独立的 `pnpm-lock.yaml`，还是提升为仓库根 workspace，需要在真正落地 Nx 依赖时决定。
- `test-integration` 是否在第一阶段提供真实实现，还是先映射为占位 target，需要视当前后端模板的测试准备成本决定。