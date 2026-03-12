## Context

### 当前状态
前端 `shadcn-admin` 的用户管理功能（`src/features/users/`）存在以下问题：
- `users-action-dialog.tsx`：新增/编辑用户表单提交时，调用 `showSubmittedData(values)` 仅展示一个 toast，不发送任何 HTTP 请求
- `users-delete-dialog.tsx`：单个删除确认后，调用 `showSubmittedData` 而不是调用后端接口
- `users-multi-delete-dialog.tsx`：批量删除使用 `sleep(2000)` 模拟成功，无真实 API 调用
- `data-table-bulk-actions.tsx`：批量激活/停用同样使用 `sleep(2000)` 模拟，无真实 API 调用

### 已具备条件
- 后端已有如下接口（通过 orval 生成了对应的 React Query mutation hooks）：
  - `POST /api/v1/users/` → `useCreateUserApiV1UsersPost`
  - `PUT /api/v1/users/{user_id}/activation` → `useActivateUserApiV1UsersUserIdActivationPut`
  - `DELETE /api/v1/users/{user_id}/activation` → `useDeactivateUserApiV1UsersUserIdActivationDelete`
  - `PUT /api/v1/users/{user_id}/password` → `useSetUserPasswordApiV1UsersUserIdPasswordPut`
  - `PUT /api/v1/users/{user_id}/roles/admin` → `useGrantAdminApiV1UsersUserIdRolesAdminPut`
  - `DELETE /api/v1/users/{user_id}/roles/admin` → `useRevokeAdminApiV1UsersUserIdRolesAdminDelete`
- **缺少**：删除用户接口（`DELETE /api/v1/users/{user_id}`）目前后端不存在

### 约束
- 前端用户 schema（`User`）中 `id` 字段来自后端 `UserQueryModel.id_`
- 编辑用户目前没有单一的 "update user" 接口，需要组合调用（密码 + 角色变更）

## Goals / Non-Goals

**Goals:**
- 将所有用户操作（创建、编辑、激活/停用、删除/批量删除）与真实后端 API 连接
- 操作成功后触发用户列表刷新（通过 `queryClient.invalidateQueries`）
- 后端补充删除用户接口
- 批量操作需并发调用（`Promise.all`），不逐一串行
- 用户可感知操作结果（成功 toast 或错误 toast）

**Non-Goals:**
- 不修改现有 BDD 测试场景本身（仅前端集成）
- 不重构用户列表分页、排序、搜索逻辑
- 不处理乐观更新（optimistic update），保持先请求后刷新的简单模式
- 不修改 orval 生成策略或 API 定义（除新增删除接口外）

## Decisions

### 决策 1：编辑用户采用"动作分离"而非"通用 PATCH"
**背景**：后端无 `PATCH /users/{id}` 通用更新接口，但有独立的密码设置和角色变更接口。

**决策**：`onSubmit` 在 edit 模式下根据表单变化分别调用：
1. 若密码字段被修改（`dirtyFields.password` 为 true），调用 `setUserPassword`
2. 若角色从 non-admin 变更为 admin，调用 `grantAdmin`；从 admin 变为 non-admin，调用 `revokeAdmin`

两个调用并发触发（`Promise.all`），全部成功后刷新列表。

**备选**：等待后端提供 PATCH 接口。否决，因为这会阻塞前端进度且后端 API 设计已固定。

### 决策 2：删除用户需在后端新增接口
**背景**：`DELETE /api/v1/users/{user_id}` 后端目前不存在，前端组件已有删除 UI 逻辑。

**决策**：在 fastapi-clean-example 后端补充删除用户接口，并在下一次 orval 生成后更新前端 hooks。删除操作需权限控制（仅 super admin 可操作）。

**备选**：仅前端禁用删除按钮，等待后端。否决，因删除功能完整性要求较高且与激活/停用同属用户管理核心操作。

### 决策 3：刷新策略采用 invalidateQueries
**背景**：用户列表由 `useListUsersApiV1UsersGet` 管理，任何写操作后需刷新。

**决策**：在每个 mutation 的 `onSuccess` 回调中调用 `queryClient.invalidateQueries({ queryKey: ['listUsersApiV1UsersGet'] })`，触发列表重新请求。

**备选**：手动更新缓存（optimistic update）。否决，实现复杂度较高，且用户数据一致性要求更重要。

### 决策 4：批量操作采用 Promise.all 并发调用
**背景**：批量激活/停用/删除需对多个用户 ID 分别调用接口。

**决策**：`Promise.all(userIds.map(id => api(id)))` 并发执行，全部 resolve 后刷新列表；任一 reject 则显示错误 toast。

## Risks / Trade-offs

- **后端删除接口需同步开发** → 前后端可并行开发，前端先用 feature flag 或 disabled 状态保护删除按钮，待接口就绪后启用
- **批量操作中部分失败** → 当前方案 `Promise.allSettled` 更安全但增加复杂度；初期采用 `Promise.all` 全或无语义，失败时显示错误并建议重试
- **角色变更逻辑依赖 dirty state** → 若用户打开编辑弹窗后未做修改即提交，仍会触发无意义的 API 调用。通过检查 `dirtyFields` 避免
