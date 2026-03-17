## ADDED Requirements

### Requirement: 系统 SHALL 支持导入 JUnit XML 格式的 behave 执行结果
系统 SHALL 提供 API 接收 JUnit XML 文件上传，解析其中每个 testcase 的 classname（对应 feature 名称）和 name（对应 scenario 名称），以及执行状态（pass / fail / skip），将结果写入 TestRunResult 并关联到匹配的 Scenario 记录。

#### Scenario: 成功导入 JUnit XML 并映射 Scenario
- **WHEN** 用户上传包含 testcase 的 JUnit XML 文件至 POST /api/v1/projects/{id}/test-runs/import
- **THEN** 系统 SHALL 创建一条 TestRun 记录（status=completed），并将每个 testcase 映射到对应 Scenario，写入 TestRunResult

#### Scenario: XML 中的 testcase 无法匹配到已知 Scenario
- **WHEN** JUnit XML 中的 feature 名称 + scenario 名称 在数据库中无对应记录
- **THEN** 系统 SHALL 仍然写入 TestRunResult，scenario_id 置为空，feature_name 和 scenario_name 保留原始值

#### Scenario: 上传文件不是合法 XML
- **WHEN** 用户上传非 XML 格式的文件
- **THEN** 系统 SHALL 返回 422 状态码并说明解析失败原因

### Requirement: 系统 SHALL 在 Feature 树中展示 Scenario 级别的覆盖标记
系统 SHALL 对每个 Scenario 根据最近一次 TestRun 的结果计算覆盖状态：已覆盖且通过（pass）、已覆盖但最近失败（fail）、未覆盖（无对应 TestRunResult）。该状态 SHALL 在 Feature 树 API 响应中随 Scenario 节点一并返回。

#### Scenario: Scenario 最近一次执行通过
- **WHEN** 用户请求 Feature 树且某 Scenario 的最近 TestRunResult status 为 pass
- **THEN** 该 Scenario 节点的 coverage_status 字段 SHALL 为 "covered"

#### Scenario: Scenario 最近一次执行失败
- **WHEN** 某 Scenario 的最近 TestRunResult status 为 fail
- **THEN** 该 Scenario 节点的 coverage_status 字段 SHALL 为 "failed"

#### Scenario: Scenario 从未被执行
- **WHEN** 某 Scenario 无任何 TestRunResult 记录
- **THEN** 该 Scenario 节点的 coverage_status 字段 SHALL 为 "uncovered"

### Requirement: 系统 SHALL 提供 Project 级别的覆盖率摘要
系统 SHALL 提供覆盖率摘要 API，返回指定 Project 的总 Scenario 数、已覆盖数（至少有一次 pass 记录）、最近失败数和覆盖率百分比（已覆盖数 / 总 Scenario 数 × 100）。

#### Scenario: 获取 Project 级别覆盖率摘要
- **WHEN** 用户请求 GET /api/v1/projects/{id}/coverage
- **THEN** 系统 SHALL 返回 total_scenarios、covered_scenarios、failed_scenarios、coverage_percentage 字段

#### Scenario: Project 无任何 TestRun 时的覆盖率
- **WHEN** Project 内没有任何 TestRun 记录
- **THEN** 系统 SHALL 返回 covered_scenarios=0，coverage_percentage=0.0
