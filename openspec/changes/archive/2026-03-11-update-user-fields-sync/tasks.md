## 1. 后端：Domain 层 - User 实体扩展

- [x] 1.1 在 `fastapi-clean-example/src/app/domain/entities/user.py` 的 `User.__init__` 中新增 `email: str | None = None` 和 `phone_number: str | None = None` 可选参数，并在实例属性中赋值
- [x] 1.2 在 `fastapi-clean-example/src/app/domain/services/user.py` 的 `create_user` 方法签名中新增 `email: str | None = None` 和 `phone_number: str | None = None` 参数，并传入 `User(...)` 构造

## 2. 后端：Persistence 层 - 数据库映射与 Migration

- [x] 2.1 在 `fastapi-clean-example/src/app/infrastructure/persistence_sqla/mappings/user.py` 的 `users_table` 中新增两列：`Column("email", String(320), nullable=True)` 和 `Column("phone_number", String(32), nullable=True)`
- [x] 2.2 在 `.venv` 激活状态下，进入 `fastapi-clean-example/` 目录执行 `alembic revision --autogenerate -m "add_email_phone_to_users"` 生成 migration 文件
- [x] 2.3 检查并修正生成的 migration 文件（确认 `op.add_column` 包含 `email` 和 `phone_number`，`downgrade` 中包含对应 `op.drop_column`）
- [x] 2.4 执行 `alembic upgrade head` 将 migration 应用到开发数据库

## 3. 后端：Application 层 - 命令与查询

- [x] 3.1 在 `fastapi-clean-example/src/app/application/commands/create_user.py` 的 `CreateUserRequest` dataclass 中新增 `email: str | None = None` 和 `phone_number: str | None = None` 字段
- [x] 3.2 在 `CreateUserInteractor.execute` 中将 `email` 和 `phone_number` 从 `request_data` 传递给 `user_service.create_user`
- [x] 3.3 在 `fastapi-clean-example/src/app/application/common/ports/user_query_gateway.py` 的 `UserQueryModel` TypedDict 中新增 `email: str | None` 和 `phone_number: str | None` 字段

## 4. 后端：Infrastructure 层 - Reader 与 DataMapper

- [x] 4.1 在 `fastapi-clean-example/src/app/infrastructure/adapters/user_reader_sqla.py` 的 `SqlaUserReader.read_all` SQL 查询中增加 `users_table.c.email` 和 `users_table.c.phone_number` 列的查询
- [x] 4.2 在 `UserQueryModel(...)` 的构造调用中新增 `email=row.email` 和 `phone_number=row.phone_number`

## 5. 后端：Presentation 层 - HTTP 控制器

- [x] 5.1 在 `fastapi-clean-example/src/app/presentation/http/controllers/users/create_user.py` 的 `CreateUserRequestPydantic` 中新增 `email: str | None = None` 和 `phone_number: str | None = None` 字段
- [x] 5.2 在 `create_user` 路由函数中将这两个字段从 `request_data_pydantic` 传入 `CreateUserRequest`

## 6. 前端：数据类型与 Mock 数据

- [x] 6.1 在 `shadcn-admin/src/features/users/data/schema.ts`（或同等类型定义文件）中，从 `User` 类型移除 `firstName` 和 `lastName` 字段，新增 `email?: string` 和 `phoneNumber?: string`（若尚不存在）
- [x] 6.2 在 `shadcn-admin/src/features/users/data/users.ts` 的 Faker 数据生成中，移除 `firstName`、`lastName` 相关变量及 `firstName`、`lastName` 属性赋值；将 `email` 和 `phoneNumber` 改为可选生成（或保留 Faker 生成，字段已为可选）

## 7. 前端：用户新增/编辑对话框

- [x] 7.1 在 `shadcn-admin/src/features/users/components/users-action-dialog.tsx` 的 `formSchema` 中，删除 `firstName: z.string().min(1, ...)` 和 `lastName: z.string().min(1, ...)` 字段
- [x] 7.2 将 `email` 字段改为可选：替换为 `email: z.string().email().optional().or(z.literal(''))` 或等效的宽松校验
- [x] 7.3 将 `phoneNumber` 字段改为可选：替换为 `phoneNumber: z.string().optional()`（移除 `.min(1, ...)` 约束）
- [x] 7.4 在 `useForm` 的两处 `defaultValues` 中，删除 `firstName: ''` 和 `lastName: ''` 键值对
- [x] 7.5 删除表单 JSX 中渲染 `firstName` 的 `<FormField>` 块
- [x] 7.6 删除表单 JSX 中渲染 `lastName` 的 `<FormField>` 块

## 8. 验证

- [x] 8.1 执行后端单元测试（`nx run app-api:test` 或等效命令），确认无回归
- [x] 8.2 启动后端服务，使用 Swagger UI 验证 `POST /api/v1/users/` 接受 `email`/`phone_number` 可选字段并正确返回
- [x] 8.3 启动前端开发服务，打开用户管理页面，验证新增/编辑对话框不显示 First Name/Last Name，且 Email 和 Phone Number 不再必填
