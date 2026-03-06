## MODIFIED Requirements

### Requirement: Nx SHALL expose the first batch of high-frequency project tasks
系统 SHALL 为当前阶段提供一组高价值且可直接复用模板原生命令的 Nx target，覆盖前端的开发、构建、检查、格式化与预览任务，以及后端的启动、检查、测试、覆盖率、本地环境准备、数据库运维和迁移任务。

#### Scenario: Run frontend build through Nx
- **WHEN** 开发者执行前端构建 target
- **THEN** 系统 SHALL 通过 Nx 调用当前前端模板的构建命令并返回执行结果

#### Scenario: Run frontend maintenance commands through Nx
- **WHEN** 开发者执行前端预览、格式检查、格式化或依赖清理分析相关的 Nx target
- **THEN** 系统 SHALL 通过 Nx 调用当前前端模板中对应的原生命令并返回执行结果

#### Scenario: Run backend checks through Nx
- **WHEN** 开发者执行后端检查、测试或覆盖率相关的 Nx target
- **THEN** 系统 SHALL 通过 Nx 调用当前后端模板中对应的原生命令并返回执行结果

#### Scenario: Run backend local environment operations through Nx
- **WHEN** 开发者执行后端环境准备、数据库容器运维或迁移相关的 Nx target
- **THEN** 系统 SHALL 通过 Nx 调用当前后端模板中对应的 `make`、Docker Compose 或迁移命令并保留原有前置条件与保护行为

## ADDED Requirements

### Requirement: Nx-managed targets SHALL include discoverable descriptions
系统 SHALL 为通过 Nx 暴露的现有模板命令提供可发现的 target 描述信息，使开发者在查看项目配置或使用相关工具时可以直接理解各个 target 的用途。

#### Scenario: Existing targets include descriptions
- **WHEN** 开发者查看当前已接入的 Nx target 配置
- **THEN** 每个已存在的 target SHALL 包含说明其用途的描述字段

#### Scenario: Newly added targets include descriptions
- **WHEN** 系统为模板原生命令新增 Nx target
- **THEN** 每个新增 target SHALL 在配置中携带简洁且语义明确的描述信息
