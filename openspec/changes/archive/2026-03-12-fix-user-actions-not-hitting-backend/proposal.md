## Why

前端用户管理页面的激活、停用、编辑（含新建、删除）等操作，目前仅调用了 `showSubmittedData` 展示 toast 并打印表单数据，从未向后端发起真实 API 请求。后端已存在对应接口（通过 orval 生成了 React Query mutation hooks），需要将前端组件与这些 hooks 连接起来，使操作真正生效。

## What Changes

- `users-action-dialog.tsx`：Edit 模式下 `onSubmit` 改为调用后端用户编辑相关接口（设置密码 + 授予/撤销 admin 角色），Add 模式下调用 `useCreateUserApiV1UsersPost`；删除 `showSubmittedData` 调用
- `users-delete-dialog.tsx`：`handleDelete` 改为调用后端删除用户接口（若接口不存在则先在后端补充）；删除 `showSubmittedData` 调用
- `users-multi-delete-dialog.tsx`：`handleDelete` 改为批量调用后端删除接口，替换掉 `sleep` 模拟延迟
- `data-table-bulk-actions.tsx`：`handleBulkStatusChange` 改为批量调用 activate/deactivate 接口，替换掉 `sleep` 模拟延迟
- `use-user-list.ts`：补充 `email`、`phoneNumber` 字段映射（后端已返回）
- 操作成功后刷新用户列表（invalidate query）

## Capabilities

### New Capabilities

- `user-crud-api-integration`：将前端用户管理操作（创建、编辑、激活/停用、删除）与后端 REST API 真实连接，替换掉所有 mock/演示实现

### Modified Capabilities

- `http-bdd-user-core`：用户 CRUD 的 HTTP 接口行为约束不变，但前端现在会真正调用这些接口，联调验证点增加
- `http-bdd-user-admin-authz`：管理员操作（授予/撤销 admin 角色、激活/停用用户）的接口权限已有规格，前端现在会真正触发这些授权检查

## Impact

- **前端（shadcn-admin）**：`src/features/users/components/` 下多个组件文件、`src/features/users/hooks/use-user-list.ts`
- **后端（fastapi-clean-example）**：若缺少删除用户接口，需新增 `DELETE /api/v1/users/{user_id}` 端点
- **orval 生成代码**：如后端新增接口，需重新运行 `orval` 更新生成文件
- **依赖**：React Query `queryClient.invalidateQueries` 用于刷新列表
