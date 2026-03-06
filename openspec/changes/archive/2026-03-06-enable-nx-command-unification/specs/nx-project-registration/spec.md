## ADDED Requirements

### Requirement: Nx SHALL register the current frontend and backend template projects as named projects
系统 SHALL 在 Nx 中将当前前端模板和后端模板登记为稳定命名的项目，以便为统一命令入口、项目图展示和后续扩展提供工程元数据基础。

#### Scenario: Register frontend template project
- **WHEN** Nx workspace 完成第一阶段配置
- **THEN** 当前前端模板 SHALL 以 `app-web` 的项目名出现在 Nx 项目集合中

#### Scenario: Register backend template project
- **WHEN** Nx workspace 完成第一阶段配置
- **THEN** 当前后端模板 SHALL 以 `app-api` 的项目名出现在 Nx 项目集合中

### Requirement: Registered projects SHALL define explicit targets for future orchestration
系统 SHALL 在已登记项目上定义清晰、可扩展的 target 名称，使后续 OpenAPI、mock、BDD 和领域模块扩展可以沿用同一套编排方式。

#### Scenario: Project targets follow stable naming
- **WHEN** 开发者查看 Nx 项目配置
- **THEN** 前后端项目 SHALL 使用稳定且语义明确的 target 名称，如 `serve`、`build`、`lint`、`test-unit` 等

#### Scenario: Future capabilities can attach to registered projects
- **WHEN** 后续需要接入 OpenAPI 导出、API client 生成或 BDD 项目
- **THEN** 系统 SHALL 能在现有项目命名和 target 体系上继续扩展，而不需要先重命名当前项目

### Requirement: Project registration MUST support future dependency graph visibility
系统 MUST 通过项目登记为后续的 Nx 项目图、依赖分析和变更影响分析提供基础信息，即使第一阶段尚未启用完整的边界治理规则。

#### Scenario: Project graph can include registered projects
- **WHEN** 开发者使用 Nx 查看项目图或项目列表
- **THEN** 已登记的前后端项目 SHALL 能作为独立节点被识别

#### Scenario: Additional project nodes can be added later
- **WHEN** 后续新增 `doc-api`、`fe-api-client` 或 BDD 项目
- **THEN** 系统 SHALL 能在既有项目图中继续添加新节点并建立依赖关系
