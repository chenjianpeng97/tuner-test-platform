## Purpose

定义 BDD 平台中的测试计划管理与执行结果同步能力。

## Requirements

### Requirement: 系统 SHALL 支持创建、查看、编辑、删除测试计划
用户 SHALL 能在指定 Project 内管理测试计划的完整生命周期：创建（提供名称和描述）、列出所有计划、查看单个计划详情（含所有 TestPlanItem）、更新计划基本信息、删除计划（级联删除其 TestPlanItem）。

#### Scenario: 成功创建测试计划
- **WHEN** 用户提交 POST /api/v1/projects/{id}/test-plans，携带 name 和 description
- **THEN** 系统 SHALL 返回新建 TestPlan 详情，HTTP 状态码 201

#### Scenario: 查看测试计划详情含 Item 列表
- **WHEN** 用户请求 GET /api/v1/projects/{id}/test-plans/{pid}
- **THEN** 系统 SHALL 返回 TestPlan 基本信息及其所有 TestPlanItem，每项包含 scenario 名称、feature 名称、当前状态

### Requirement: 系统 SHALL 支持从 Feature 树勾选 Scenario 加入测试计划
用户 SHALL 能批量选择 Project 内的 Scenario（通过 scenario_id 列表）添加到指定测试计划，重复添加的 Scenario SHALL 被忽略（幂等），每个新加入的 Item 初始状态 SHALL 为 not_run。

#### Scenario: 批量添加 Scenarios 到测试计划
- **WHEN** 用户提交 POST /api/v1/projects/{id}/test-plans/{pid}/items，携带 scenario_ids 数组
- **THEN** 系统 SHALL 为每个未存在于该计划中的 scenario_id 创建 TestPlanItem（status=not_run），返回新增的 items 列表

#### Scenario: 添加已存在于计划中的 Scenario
- **WHEN** 用户提交的 scenario_ids 中包含已在该测试计划中的 Scenario
- **THEN** 系统 SHALL 忽略重复项，仅添加新项，HTTP 状态码 200，不返回错误

### Requirement: 系统 SHALL 支持手动更新测试计划中 Scenario 的状态
用户 SHALL 能将测试计划中单个 TestPlanItem 的状态更新为以下之一：not_run、pass、fail、skip、blocked。更新时 SHALL 记录 updated_at 时间戳。

#### Scenario: 成功更新 TestPlanItem 状态
- **WHEN** 用户提交 PATCH /api/v1/projects/{id}/test-plans/{pid}/items/{iid}，携带 status=pass
- **THEN** 系统 SHALL 更新该 TestPlanItem 的 status 字段和 updated_at，返回更新后的 Item，HTTP 状态码 200

#### Scenario: 提交无效状态值
- **WHEN** 用户提交不在允许值列表内的 status（如 "unknown"）
- **THEN** 系统 SHALL 返回 422 状态码

### Requirement: 系统 SHALL 展示测试计划的整体进度统计
测试计划详情 API SHALL 返回进度统计字段：total（总 item 数）、not_run、pass、fail、skip、blocked 各状态的数量。

#### Scenario: 测试计划进度统计正确反映各状态数量
- **WHEN** 用户请求测试计划详情
- **THEN** 系统 SHALL 在响应的 progress 字段中包含各状态数量统计，total = 所有状态之和

### Requirement: 系统 SHALL 支持从 TestRun 结果批量同步测试计划状态
用户 SHALL 能将指定 TestRun 的结果批量同步到测试计划中，系统将通过 feature 名称 + scenario 名称匹配，自动更新对应 TestPlanItem 的状态（pass/fail/skip）。无法匹配的 TestRunResult SHALL 被忽略，已是终态（pass/fail）的 Item SHOULD 被覆盖更新。

#### Scenario: 从 TestRun 同步状态到测试计划
- **WHEN** 用户提交 POST /api/v1/projects/{id}/test-plans/{pid}/sync-run/{rid}
- **THEN** 系统 SHALL 将 TestRun 中每条 TestRunResult 与测试计划中同名 Scenario 的 Item 匹配，更新其 status，返回更新数量摘要
