## ADDED Requirements

### Requirement: Nx SHALL provide a unified command entry for existing frontend and backend projects
系统 SHALL 在仓库根目录提供统一的 Nx 命令入口，用于触发当前前端模板与后端模板的常用开发命令，而无需开发者分别记忆和直接调用各自原生命令。

#### Scenario: Start frontend through Nx
- **WHEN** 开发者执行面向前端开发启动的 Nx target
- **THEN** 系统 SHALL 调用当前前端模板已有的启动命令并启动前端开发服务

#### Scenario: Start backend through Nx
- **WHEN** 开发者执行面向后端开发启动的 Nx target
- **THEN** 系统 SHALL 调用当前后端模板已有的启动命令并启动后端服务或开发入口

### Requirement: Nx SHALL expose the first batch of high-frequency project tasks
系统 SHALL 为当前阶段至少提供高频任务的 Nx target，包括前端的开发、构建、检查任务，以及后端的启动、检查和测试任务。

#### Scenario: Run frontend build through Nx
- **WHEN** 开发者执行前端构建 target
- **THEN** 系统 SHALL 通过 Nx 调用当前前端模板的构建命令并返回执行结果

#### Scenario: Run backend checks through Nx
- **WHEN** 开发者执行后端检查或测试 target
- **THEN** 系统 SHALL 通过 Nx 调用当前后端模板的检查或测试命令并返回执行结果

### Requirement: Existing template workflows MUST remain usable during Nx adoption
在引入 Nx 的第一阶段，系统 MUST 保持现有前后端模板目录和原始命令体系仍可用，避免因接入 Nx 而强制要求立即重构源码布局或依赖管理方式。

#### Scenario: Preserve current template layout
- **WHEN** 完成第一阶段的 Nx 接入
- **THEN** 前端与后端源码目录结构 SHALL 仍可保持在现有模板目录中运行

#### Scenario: Preserve underlying package tooling
- **WHEN** 开发者需要排查 Nx target 背后的真实执行命令
- **THEN** 系统 SHALL 仍能追溯到原有的 `pnpm` 或 Python / `uv` 工作流，而不是用新的依赖体系替代它们
