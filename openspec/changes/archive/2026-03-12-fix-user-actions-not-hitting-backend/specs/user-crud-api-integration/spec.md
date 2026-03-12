## ADDED Requirements

### Requirement: 前端创建用户操作 SHALL 调用后端创建接口
前端用户管理页面中，点击新增用户并提交表单后，系统 SHALL 调用 `POST /api/v1/users/` 向后端发送请求，并在成功后刷新用户列表。系统 SHALL NOT 仅展示 toast 或打印数据而不发送 HTTP 请求。

#### Scenario: 管理员成功创建新用户
- **WHEN** 管理员填写新增用户表单（username、password、role）并点击提交
- **THEN** 系统 SHALL 向 `POST /api/v1/users/` 发送请求，成功后用户列表 SHALL 包含新创建的用户

#### Scenario: 创建用户接口返回错误时前端显示错误提示
- **WHEN** 后端返回错误（如用户名已存在）
- **THEN** 前端 SHALL 展示错误 toast，且不关闭对话框

### Requirement: 前端编辑用户操作 SHALL 调用后端相应接口
前端用户编辑对话框提交时，系统 SHALL 根据实际变更调用相应后端接口：若密码被修改，SHALL 调用 `PUT /api/v1/users/{user_id}/password`；若角色发生变更，SHALL 调用相应的角色变更接口。系统 SHALL NOT 在用户未修改相关字段时调用对应接口。

#### Scenario: 管理员修改用户密码
- **WHEN** 管理员在编辑对话框中修改密码并提交
- **THEN** 系统 SHALL 调用 `PUT /api/v1/users/{user_id}/password`，成功后关闭对话框并刷新列表

#### Scenario: 管理员将用户角色从普通用户升级为 admin
- **WHEN** 管理员在编辑对话框中将用户角色改为 admin 并提交
- **THEN** 系统 SHALL 调用 `PUT /api/v1/users/{user_id}/roles/admin`，成功后关闭对话框并刷新列表

#### Scenario: 管理员将用户角色从 admin 降级
- **WHEN** 管理员在编辑对话框中将 admin 用户角色改为普通用户并提交
- **THEN** 系统 SHALL 调用 `DELETE /api/v1/users/{user_id}/roles/admin`，成功后关闭对话框并刷新列表

#### Scenario: 管理员未修改任何字段直接提交
- **WHEN** 管理员打开编辑对话框后未做修改直接提交
- **THEN** 系统 SHALL NOT 发送任何 API 请求，直接关闭对话框

### Requirement: 前端单个删除用户操作 SHALL 调用后端删除接口
前端用户删除确认对话框确认后，系统 SHALL 调用 `DELETE /api/v1/users/{user_id}` 向后端发送删除请求，成功后刷新用户列表。

#### Scenario: 管理员成功删除用户
- **WHEN** 管理员在删除确认对话框中正确输入用户名并确认
- **THEN** 系统 SHALL 向 `DELETE /api/v1/users/{user_id}` 发送请求，成功后用户列表 SHALL 不再包含该用户

### Requirement: 前端批量删除用户操作 SHALL 调用后端删除接口
批量删除确认后，系统 SHALL 对每个选中用户并发调用 `DELETE /api/v1/users/{user_id}`，全部成功后重置选择状态并刷新列表。

#### Scenario: 管理员成功批量删除多个用户
- **WHEN** 管理员选中多个用户，在批量删除对话框中输入确认词并确认
- **THEN** 系统 SHALL 并发调用多个删除请求，全部成功后用户列表 SHALL 不再包含这些用户

### Requirement: 前端单个激活/停用用户操作 SHALL 调用后端接口
用户行内激活/停用操作触发后，系统 SHALL 分别调用 `PUT /api/v1/users/{user_id}/activation`（激活）或 `DELETE /api/v1/users/{user_id}/activation`（停用），成功后刷新列表。

#### Scenario: 管理员激活单个用户
- **WHEN** 管理员对非激活用户触发激活操作
- **THEN** 系统 SHALL 调用激活接口，成功后该用户状态在列表中 SHALL 变为 active

#### Scenario: 管理员停用单个用户
- **WHEN** 管理员对活跃用户触发停用操作
- **THEN** 系统 SHALL 调用停用接口，成功后该用户状态在列表中 SHALL 变为 inactive

### Requirement: 前端批量激活/停用操作 SHALL 调用后端接口
批量状态变更操作触发后，系统 SHALL 对每个选中用户并发调用相应接口，全部完成后刷新列表并重置选择状态。

#### Scenario: 管理员批量激活多个用户
- **WHEN** 管理员选中多个用户并触发批量激活
- **THEN** 系统 SHALL 并发调用每个用户的激活接口，全部成功后用户列表中这些用户状态 SHALL 为 active

#### Scenario: 管理员批量停用多个用户
- **WHEN** 管理员选中多个用户并触发批量停用
- **THEN** 系统 SHALL 并发调用每个用户的停用接口，全部成功后用户列表中这些用户状态 SHALL 为 inactive

### Requirement: 用户写操作 SHALL 在成功后触发列表刷新
所有用户写操作（创建、编辑、删除、激活、停用）成功后，系统 SHALL 通过 `queryClient.invalidateQueries` 使用户列表缓存失效并重新获取最新数据。

#### Scenario: 任意写操作成功后列表自动刷新
- **WHEN** 前端完成任意用户写操作（如激活、删除）
- **THEN** 用户列表 SHALL 在操作成功后自动重新从后端拉取最新数据
