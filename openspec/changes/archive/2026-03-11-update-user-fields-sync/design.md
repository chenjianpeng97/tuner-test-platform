## Context

当前系统存在前端与后端的字段不一致问题：
- 前端用户新增/编辑表单（`users-action-dialog.tsx`）中要求必填 `firstName`、`lastName`、`email`、`phoneNumber` 四个字段
- 后端 `User` 实体（`domain/entities/user.py`）仅有 `username`、`password_hash`、`role`、`is_active` 四个字段，数据库表也只有对应四列
- 后端 `CreateUserRequest` 只接受 `username`、`password`、`role`，`UserQueryModel` 只返回 `id_`、`username`、`role`、`is_active`
- 前端填写的 `firstName`/`lastName`/`email`/`phoneNumber` 完全被丢弃，并不会发送到后端

## Goals / Non-Goals

**Goals:**
- 移除前端表单中后端不支持的 `firstName` 和 `lastName` 字段
- 将前端表单的 `email` 和 `phoneNumber` 改为可选字段
- 后端 `User` 实体、数据库映射、命令层、HTTP 层全链路支持 `email`（可选）和 `phone_number`（可选）
- 生成 Alembic migration 为 `users` 表新增 `email` 和 `phone_number` 列

**Non-Goals:**
- 不对 email 添加唯一性约束（当前 username 已是唯一键，email 仅为信息字段）
- 不添加邮件发送或手机验证功能
- 不修改认证流程（登录仍使用 username + password）
- 不修改现有的激活/反激活、密码修改等接口

## Decisions

### 决策 1：email 和 phone_number 作为可选字段存入 User 实体，而非独立 Profile 实体

**选择：** 直接在 `User` 实体上增加两个可选字段（`Optional[str]`）。

**理由：**
- 项目当前规模较小，引入独立 Profile 实体会大幅增加复杂度（新表、新仓储端口、新映射、新查询）
- 这两个字段是用户的基本联系信息，不属于独立的业务概念
- 可为空的列不破坏现有 User 实体的不变式

**已考虑的替代方案：**
- 独立 `UserProfile` 实体/表：过度设计，不在本次需求范围内

---

### 决策 2：移除 firstName / lastName，而不是保留为纯前端字段

**选择：** 完全移除这两个字段，不作为任何层的数据。

**理由：**
- 若前端留有这两个字段但不提交到后端，会造成用户困惑（填了却无效果）
- 后端也没有存储这些字段的计划
- 干净地删除比"静默忽略"更清晰

---

### 决策 3：数据库列可为空（nullable），无默认值

**选择：** `email` 和 `phone_number` 列均为 `String`、`nullable=True`。

**理由：**
- 大量现有用户记录不含这两个字段，设置 NOT NULL 需要提供回填值
- 可为空符合"可选联系方式"的业务语义

---

### 决策 4：前端 API 调用层仅传递非空字段

**选择：** 若 email / phoneNumber 为空字符串，则不传或传 `null`，后端接受 `None`。

**理由：** 保持后端字段语义清晰（`None` 表示未提供，而非空字符串）。

## Risks / Trade-offs

- **[风险] 现有集成测试依赖 `UserQueryModel` 的字段集** → 缓解：`email` 和 `phone_number` 是新增可选字段，不会破坏已有断言，仅新增可 assert 的内容
- **[风险] 前端 Faker 数据（`users/data/users.ts`）仍生成 `firstName`/`lastName`** → 缓解：同步删除这两个字段的 Faker 生成，以及 `User` 数据类型定义（`schema.ts`）中的对应属性
- **[风险] Alembic migration 执行顺序** → 缓解：新增单独 migration 文件，依赖现有 `users_auth` migration，遵循现有版本链

## Migration Plan

1. 生成 Alembic migration（`alembic revision --autogenerate -m "add_email_phone_to_users"`）
2. 在开发/测试环境执行 `alembic upgrade head`
3. 前端变更无需数据库操作，独立部署安全
4. **回滚策略**：执行 `alembic downgrade -1` 即可删除新增列（列为 nullable，无数据丢失风险）
