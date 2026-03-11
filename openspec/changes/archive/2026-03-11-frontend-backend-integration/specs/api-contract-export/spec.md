## ADDED Requirements

### Requirement: 后端 OpenAPI 规范可通过 Nx target 导出为本地文件
系统 SHALL 提供 Nx target `app-api:export-schema`，执行后将 FastAPI 应用的 OpenAPI JSON 规范写入 `openspec/contracts/app-api.openapi.json`。

该 target SHALL：
- 通过直接 import FastAPI app 对象调用 `app.openapi()` 获取规范（不依赖运行中的服务）
- 在无后端服务运行的情况下可执行（离线可用）
- 将输出文件路径固定为 `openspec/contracts/app-api.openapi.json`

#### Scenario: 离线导出 OpenAPI 规范
- **WHEN** 本地后端服务未启动，执行 `pnpm exec nx run app-api:export-schema`
- **THEN** 命令成功退出，`openspec/contracts/app-api.openapi.json` 文件被创建或更新，内容为合法 JSON

#### Scenario: 导出内容包含所有已实现路由
- **WHEN** 执行完 `app-api:export-schema`
- **THEN** 导出的规范中包含 `/api/v1/auth/login`、`/api/v1/auth/logout`、`/api/v1/users`（列表）、`/api/v1/users/{user_id}`、`/api/v1/users/me` 等关键路由定义

### Requirement: 契约文件纳入版本控制
导出的 `openspec/contracts/app-api.openapi.json` SHALL 被提交到 git 版本控制中，作为前后端接口的唯一真相来源。

#### Scenario: 契约文件存在于仓库中
- **WHEN** 在 git 已追踪文件中查找 `openspec/contracts/app-api.openapi.json`
- **THEN** 该文件存在且不在 `.gitignore` 中

### Requirement: Orval 代码生成依赖本地契约文件
Orval 配置 SHALL 引用本地 `openspec/contracts/app-api.openapi.json` 作为输入源，而不是远程 URL 或运行中的服务端点。

#### Scenario: 断网环境下可执行代码生成
- **WHEN** 无网络连接且后端服务未运行时执行 `app-web:generate-api`
- **THEN** Orval 代码生成成功完成（依赖本地契约文件）
