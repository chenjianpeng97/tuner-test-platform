## ADDED Requirements

### Requirement: 前端用户角色枚举与后端保持一致
前端应用中所有与用户角色相关的代码 SHALL 使用后端定义的三个角色值：`super_admin`、`admin`、`user`。

旧值（`superadmin`、`manager`、`cashier`）SHALL 从代码库中移除，不得在 schema、data 文件、组件、MSW handler 或测试中出现。

角色显示标签映射 SHALL 为：
- `super_admin` → "Super Admin"
- `admin` → "Admin"
- `user` → "User"

#### Scenario: 角色过滤器显示三个选项
- **WHEN** 打开 Users 页面，点击角色过滤器
- **THEN** 过滤选项中显示 "Super Admin"、"Admin"、"User" 三项，不显示 "Manager"、"Cashier"、"Superadmin"

#### Scenario: 前端 Zod schema 拒绝旧角色值
- **WHEN** 前端接收到包含 `"manager"` 角色值的 API 响应
- **THEN** Zod schema 解析失败，不将该值渲染为有效角色

#### Scenario: TypeScript 编译通过
- **WHEN** 完成枚举对齐后，执行 TypeScript 类型检查
- **THEN** 无任何因旧角色值引起的类型错误

### Requirement: 前端用户状态枚举 API 层与后端对齐
前端 API 层（axios 请求/响应）中使用的状态值 SHALL 仅包含后端支持的 `active` 和 `inactive`。

UI 展示层（筛选器、样式映射 `callTypes`）可保留 `invited` 和 `suspended` 状态定义，但这两个值仅来自 MSW mock 演示数据，真实 API 层不传递。

#### Scenario: 从后端获取的用户状态只有 active/inactive
- **WHEN** 前端通过真实 API（非 MSW）获取用户列表
- **THEN** 响应中所有用户的 `status` 字段值均为 `active` 或 `inactive`

#### Scenario: UI 过滤器保留四个状态选项
- **WHEN** 打开 Users 页面状态筛选器
- **THEN** 可见 Active、Inactive、Invited、Suspended 四个过滤选项（UI 保留完整演示能力）

### Requirement: 用户列表页路由的 role 参数校验同步更新
`shadcn-admin/src/routes/_authenticated/users/index.tsx` 中的 URL search schema SHALL 使用更新后的角色枚举值作为 `role` 参数的合法值集合。

#### Scenario: URL 中的旧角色值被过滤
- **WHEN** 访问 `/users?role=cashier`（旧角色值）
- **THEN** URL search schema 的 `catch` 处理将其过滤为空数组，不触发应用错误
