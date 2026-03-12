## 1. 后端：新增删除用户接口

- [x] 1.1 在 `fastapi-clean-example` 中新增 `DELETE /api/v1/users/{user_id}` 路由及 handler
- [x] 1.2 实现删除用户 use case，user 不存在时返回 404，成功时返回 204
- [x] 1.3 添加权限控制：仅 super admin 可删除用户
- [x] 1.4 补充 BDD 场景：在 `features/user.feature` 或 `features/user/user_auth.feature` 中覆盖删除用户和权限边界场景

## 2. 前端：重新生成 API hooks

- [x] 2.1 在 `shadcn-admin` 中运行 `orval`（或对应 nx target）重新生成 `src/api/generated/users/users.ts`，获取删除用户的 hook

## 3. 前端：连接创建/编辑用户接口

- [x] 3.1 在 `users-action-dialog.tsx` 的 add 模式下，`onSubmit` 改为调用 `useCreateUserApiV1UsersPost`，成功后调用 `queryClient.invalidateQueries` 刷新列表，删除 `showSubmittedData`
- [x] 3.2 在 `users-action-dialog.tsx` 的 edit 模式下，`onSubmit` 根据 `dirtyFields` 判断：
  - 若密码被修改，调用 `useSetUserPasswordApiV1UsersUserIdPasswordPut`
  - 若角色变为 admin，调用 `useGrantAdminApiV1UsersUserIdRolesAdminPut`
  - 若角色从 admin 降级，调用 `useRevokeAdminApiV1UsersUserIdRolesAdminDelete`
  - 使用 `Promise.all` 并发调用，成功后刷新列表
- [x] 3.3 操作失败时展示错误 toast，成功时关闭对话框并展示成功提示

## 4. 前端：连接删除用户接口

- [x] 4.1 在 `users-delete-dialog.tsx` 中，`handleDelete` 改为调用生成的删除 hook，成功后刷新列表，删除 `showSubmittedData`
- [x] 4.2 在 `users-multi-delete-dialog.tsx` 中，`handleDelete` 改为 `Promise.all` 并发删除所有选中用户，全部成功后重置选择并刷新列表，替换 `sleep` 模拟

## 5. 前端：连接激活/停用接口

- [x] 5.1 在 `data-table-bulk-actions.tsx` 中，`handleBulkStatusChange` 改为 `Promise.all` 并发调用 activate 或 deactivate hook，成功后重置选择并刷新列表，替换 `sleep` 模拟
- [x] 5.2 若行内有单个激活/停用入口（如列状态切换），同样连接到对应 hook（如已在 row actions 中实现则可跳过）

## 6. 前端：修复用户数据映射

- [x] 6.1 在 `use-user-list.ts` 的映射中补充 `email` 和 `phoneNumber` 字段（从后端 `UserQueryModel` 映射到前端 `User` schema）

## 7. 验证

- [x] 7.1 启动前后端（`nx run app-api:serve` 和 `nx run app-web:dev:integration`），手动验证创建用户后列表刷新
- [x] 7.2 验证编辑用户（修改密码、修改角色）后列表刷新
- [x] 7.3 验证单个删除、批量删除后列表刷新
- [x] 7.4 验证批量激活/停用后用户状态正确更新
- [x] 7.5 验证接口错误时前端展示错误 toast 且不关闭对话框
