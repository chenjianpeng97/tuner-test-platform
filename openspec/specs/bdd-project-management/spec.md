## Purpose

定义 BDD 平台中的 Project 管理、Git 配置与同步能力。

## Requirements

### Requirement: 系统 SHALL 支持创建 Project
用户 SHALL 能通过 Web 界面创建新项目，提供项目名称、描述、关联 Git 仓库 URL、Git 分支、Personal Access Token（PAT）及服务器本地 behave 工作目录路径。PAT SHALL 加密存储，不得在任何响应中以明文返回。

#### Scenario: 成功创建 Project
- **WHEN** 用户提交有效的项目名称、Git 仓库 URL、分支和 PAT
- **THEN** 系统 SHALL 返回新建 Project 的详情（不含 PAT 明文），HTTP 状态码 201

#### Scenario: 创建 Project 缺少必填字段
- **WHEN** 用户提交缺少 git_repo_url 的项目创建请求
- **THEN** 系统 SHALL 返回 422 状态码并说明缺失字段

### Requirement: 系统 SHALL 支持查看、编辑、删除 Project
用户 SHALL 能列出所有 Project，查看单个 Project 详情，更新 Project 的配置字段，以及删除 Project（级联删除其所有 Feature、Scenario、TestPlan、TestRun 数据）。

#### Scenario: 列出所有 Project
- **WHEN** 用户请求 GET /api/v1/projects
- **THEN** 系统 SHALL 返回所有 Project 的列表，每项包含 id、name、description、git_repo_url、git_branch

#### Scenario: 查看单个 Project 详情
- **WHEN** 用户请求 GET /api/v1/projects/{id}
- **THEN** 系统 SHALL 返回该 Project 的详情（包含 id、name、description），若不存在返回 404

#### Scenario: 更新 Project 基础信息
- **WHEN** 用户请求 PATCH /api/v1/projects/{id} 更新 name/description
- **THEN** 系统 SHALL 返回更新后的 Project 详情，若不存在返回 404

#### Scenario: 删除 Project 时级联清理数据
- **WHEN** 用户删除一个存在 Feature 文件和 TestPlan 的 Project
- **THEN** 系统 SHALL 删除该 Project 及其所有关联的 Feature、Scenario、Step、TestPlan、TestPlanItem、TestRun、TestRunResult 数据，HTTP 状态码 204

### Requirement: 系统 SHALL 支持管理 Project 的 Git 配置
用户 SHALL 能读取与更新 Project 的 Git 配置（repo URL、branch、PAT），系统 SHALL 不回传 PAT 明文。

#### Scenario: 获取 Git 配置
- **WHEN** 用户请求 GET /api/v1/projects/{id}/git-config
- **THEN** 系统 SHALL 返回 git_repo_url 与 git_branch，不包含 git_access_token，若未配置返回 404

#### Scenario: 更新 Git 配置
- **WHEN** 用户请求 PUT /api/v1/projects/{id}/git-config 提交 repo URL、branch 与 PAT
- **THEN** 系统 SHALL 保存配置并返回 git_repo_url 与 git_branch（不包含 PAT 明文）

### Requirement: 系统 SHALL 支持手动触发 Git 同步
用户 SHALL 能对指定 Project 触发"从 Git 同步"操作，系统将拉取该 Project 关联 Git 仓库指定分支上的所有 `.feature` 文件，按照"同名目录即子 Feature"约定解析父子关系，更新数据库中的 Feature（含 parent_feature_id）、Scenario、Step 数据。

#### Scenario: Git 同步成功拉取新 Feature 文件
- **WHEN** 用户触发 POST /api/v1/projects/{id}/sync
- **THEN** 系统 SHALL 克隆或拉取 Git 仓库，递归扫描所有 .feature 文件，按同名目录约定建立父子关系后解析并持久化，返回同步摘要（新增/更新/删除的文件数）

#### Scenario: Git 同步正确建立 Sub-Feature 父子关系
- **WHEN** Git 仓库中存在 `user.feature` 和 `user/user_auth.feature`
- **THEN** 系统 SHALL 将 `user_auth.feature` 对应 Feature 记录的 parent_feature_id 设置为 `user.feature` 的 id

#### Scenario: Git 同步时 PAT 无效
- **WHEN** 用户触发同步但 Project 的 PAT 已失效
- **THEN** 系统 SHALL 返回 502 状态码并附带 Git 认证失败的错误信息

### Requirement: 不同 Project 的数据 SHALL 完全隔离
所有 Feature、Scenario、TestPlan、TestRun 查询 SHALL 以 project_id 为强制过滤条件，不同 Project 的数据 SHALL NOT 在任何 API 响应中混用。

#### Scenario: 查询 Feature 列表时数据隔离
- **WHEN** 用户请求 Project A 的 Feature 列表
- **THEN** 系统 SHALL 仅返回属于 Project A 的 Feature，不包含 Project B 的数据
