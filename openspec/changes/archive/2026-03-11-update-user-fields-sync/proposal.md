## Why

前端用户新增/编辑表单要求 First Name、Last Name、Email 和 Phone Number 为必填字段，但后端的 User 实体和数据库表中根本不存储这些字段（除 Email/Phone 外甚至没有对应列），导致前端填写的数据被无声丢弃。需要消除前后端之间的这一不一致，让前端只收集后端实际支持的字段，同时让后端能正确持久化 Email 和 Phone Number。

## What Changes

- 移除前端用户新增/编辑表单中的 `firstName` 和 `lastName` 字段（包括 UI 组件、Zod Schema、默认值）
- 将前端表单中的 `email` 和 `phoneNumber` 改为可选字段（去除必填验证）
- 后端 User 实体增加 `email` 和 `phone_number` 可选字段
- 后端数据库表 `users` 新增 `email` 和 `phone_number` 列（可为空），并生成对应 Alembic migration
- 后端 `CreateUserRequest` / `CreateUserInteractor` / `UserQueryModel` 支持 `email` 和 `phone_number`
- 后端 HTTP 层 `CreateUserRequestPydantic` 和 `ListUsersQM` / `UserQueryModel` 增加这两个可选字段
- 前端 API 调用层更新，传递 `email` 和 `phoneNumber`（可选）

## Capabilities

### New Capabilities
<!-- 无新能力需要引入 -->

### Modified Capabilities
- `http-bdd-user-core`: 用户创建和查询接口的请求/响应字段发生变化（新增可选 email、phone_number；移除 first_name/last_name）

## Impact

- **后端**
  - `fastapi-clean-example/src/app/domain/entities/user.py` — User 实体新增字段
  - `fastapi-clean-example/src/app/infrastructure/persistence_sqla/mappings/user.py` — 表映射新增列
  - `fastapi-clean-example/src/app/infrastructure/persistence_sqla/alembic/versions/` — 新增 migration 文件
  - `fastapi-clean-example/src/app/application/commands/create_user.py` — CreateUserRequest / Interactor
  - `fastapi-clean-example/src/app/application/common/ports/user_query_gateway.py` — UserQueryModel
  - `fastapi-clean-example/src/app/infrastructure/adapters/user_reader_sqla.py` — 查询结果映射
  - `fastapi-clean-example/src/app/presentation/http/controllers/users/create_user.py` — HTTP 请求 Schema
  - `fastapi-clean-example/src/app/domain/services/user.py` — create_user 方法签名

- **前端**
  - `shadcn-admin/src/features/users/components/users-action-dialog.tsx` — 表单 Schema、字段、默认值
