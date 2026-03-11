## MODIFIED Requirements

### Requirement: 用户主功能 Feature SHALL 覆盖用户创建行为
系统 SHALL 通过 HTTP 层 BDD 场景覆盖用户创建行为，包括请求入口、状态码结果以及新用户身份被正确建立的业务结果。创建用户接口的请求体 SHALL 支持可选的 `email` 和 `phone_number` 字段，且这两个字段均不得为必填。接口 SHALL NOT 再接受或处理 `first_name` / `last_name` 字段。

#### Scenario: 管理员成功创建普通用户（不含联系信息）
- **WHEN** 已认证且具备创建权限的用户通过 HTTP 请求，仅提供 `username`、`password`、`role` 创建一个名为 Bob 的普通用户
- **THEN** 系统 SHALL 返回 201 状态，并使 Bob 成为可被后续场景引用的已存在用户，其 `email` 和 `phone_number` 均为空

#### Scenario: 管理员成功创建带联系信息的普通用户
- **WHEN** 已认证且具备创建权限的用户通过 HTTP 请求，提供 `username`、`password`、`role`、`email` 和 `phone_number` 创建用户
- **THEN** 系统 SHALL 返回 201 状态，且后续查询该用户时 `email` 和 `phone_number` SHALL 与创建时传入的值一致

## ADDED Requirements

### Requirement: 用户列表查询 SHALL 返回 email 和 phone_number 字段
系统 SHALL 在 `GET /api/v1/users/` 的响应体中，每个用户对象包含 `email` 和 `phone_number` 字段（值为字符串或 null），以便前端展示和编辑时回显联系信息。

#### Scenario: 管理员查询用户列表，含联系信息字段
- **WHEN** 已认证管理员发起用户列表 GET 请求
- **THEN** 响应中每个用户对象 SHALL 包含 `email` 字段（字符串或 null）以及 `phone_number` 字段（字符串或 null）

### Requirement: 前端用户新增/编辑表单 SHALL NOT 包含 firstName 和 lastName 字段
前端用户管理界面的新增与编辑弹窗 SHALL NOT 展示 First Name 和 Last Name 输入框，表单验证 Schema 中 SHALL NOT 对这两个字段进行任何校验。

#### Scenario: 新增用户表单不含 First Name 和 Last Name
- **WHEN** 管理员打开新增用户对话框
- **THEN** 对话框 SHALL NOT 渲染 First Name 或 Last Name 输入框

### Requirement: 前端用户表单中 email 和 phoneNumber SHALL 为可选字段
前端新增/编辑用户表单中，`email` 和 `phoneNumber` 字段 SHALL NOT 设置非空必填校验，用户可在不填写联系信息的情况下成功提交表单。

#### Scenario: 不填写 email 和 phoneNumber 仍可提交表单
- **WHEN** 管理员在新增用户对话框中仅填写 username、password 和 role 后提交
- **THEN** 表单 SHALL 验证通过并允许提交，而不显示 email 或 phoneNumber 相关的错误提示
