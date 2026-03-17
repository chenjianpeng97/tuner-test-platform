## Purpose

定义 BDD 平台中的 Feature 在线编辑、新建与 Step 自动补全能力。

## Requirements

### Requirement: 系统 SHALL 支持在线编辑 Feature 文件内容
系统 SHALL 提供 API 接收更新后的 Feature 文件文本内容，将其提交到该 Project 关联 Git 仓库的指定分支（生成新 commit），并重新解析内容更新数据库中的 Scenario 和 Step 数据。每次保存 SHALL 要求提供 commit message，若未提供则系统 SHALL 自动生成默认值（如 `chore: update <file_path>`）。

#### Scenario: 成功保存编辑后的 Feature 文件
- **WHEN** 用户提交 PUT /api/v1/projects/{id}/features/{fid}，携带新内容和 commit message
- **THEN** 系统 SHALL 将文件内容提交到 Git，重新解析 Scenario/Step，返回更新后的 Feature 详情，HTTP 状态码 200

#### Scenario: 保存时未提供 commit message
- **WHEN** 用户提交更新请求但 commit_message 字段为空字符串
- **THEN** 系统 SHALL 自动生成默认 commit message 并继续保存，不得返回错误

#### Scenario: 保存时 Git 推送失败
- **WHEN** 用户保存内容但 Git 远端推送因网络问题失败
- **THEN** 系统 SHALL 回滚 Git commit，不更新数据库，返回 502 状态码并说明 Git 推送失败原因

### Requirement: 系统 SHALL 支持新建 Feature 文件
用户 SHALL 能在指定 Project 内创建新的 Feature 文件，提供文件路径（相对于 repo root）和初始内容，系统将该文件提交到 Git 仓库并解析。

#### Scenario: 成功创建新 Feature 文件
- **WHEN** 用户提交 POST /api/v1/projects/{id}/features，携带 file_path 和初始 content
- **THEN** 系统 SHALL 在 Git 仓库中创建该文件，解析内容写库，返回新建 Feature 详情，HTTP 状态码 201

#### Scenario: 文件路径已存在
- **WHEN** 用户提交的 file_path 与该 Project 中已有的 Feature 文件路径重复
- **THEN** 系统 SHALL 返回 409 状态码并说明路径冲突

### Requirement: 系统 SHALL 支持为已有 Feature 创建 Sub-Feature
用户 SHALL 能在前端对某个已有 Feature 节点执行"新建子 Feature"操作。系统 SHALL 自动按照同名目录约定推导新文件路径：若父 Feature 路径为 `foo/bar.feature`，则子 Feature 路径 SHALL 为 `foo/bar/<子名称>.feature`。推导路径 SHALL 在请求中可覆盖。

#### Scenario: 成功为父 Feature 创建 Sub-Feature
- **WHEN** 用户对 `user.feature` 节点发起"新建子 Feature"，子名称为 "profile"
- **THEN** 系统 SHALL 在 Git 仓库中创建 `user/profile.feature`，解析写库，并将其 parent_feature_id 指向 `user.feature`，HTTP 状态码 201

#### Scenario: 推导路径与已有文件冲突
- **WHEN** 系统推导出的 Sub-Feature 路径已存在于该 Project
- **THEN** 系统 SHALL 返回 409 状态码，提示路径冲突

### Requirement: 系统 SHALL 提供 Step 自动补全查询接口
系统 SHALL 提供 API，接收查询字符串（用户已输入的 step 文本前缀），在当前 Project 内所有已知 Step 的 text 字段中进行前缀模糊匹配，返回最多 20 条匹配的完整 step 文本（含 keyword）供前端展示补全建议。

#### Scenario: 输入前缀匹配到已有 step
- **WHEN** 用户请求 GET /api/v1/projects/{id}/steps/suggest?q=system+knows
- **THEN** 系统 SHALL 返回该 Project 内所有包含 "system knows" 前缀的 step 文本列表，每项包含 keyword 和 text 字段

#### Scenario: 输入前缀无匹配
- **WHEN** 用户请求 step 补全但无任何 step 文本包含该前缀
- **THEN** 系统 SHALL 返回空数组，HTTP 状态码 200

#### Scenario: 补全结果跨 Feature 文件聚合
- **WHEN** Project 内有多个 Feature 文件定义了相同前缀的 step
- **THEN** 系统 SHALL 去重后返回唯一的 step 文本，不重复列出相同内容
