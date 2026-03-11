## 1. 清理 UI-only Feature 文件与 TypeScript Spec 文件

- [x] 1.1 删除 `features/ui/auth_ui.feature`
- [x] 1.2 删除 `features/ui/user_list_ui.feature`
- [x] 1.3 删除 `features/ui/steps/auth_ui_steps.py`
- [x] 1.4 删除 `features/ui/steps/user_list_ui_steps.py`
- [x] 1.5 删除 `features/ui/steps/__init__.py`
- [x] 1.6 删除 `features/ui_steps/auth/signin.spec.ts`
- [x] 1.7 删除 `features/ui_steps/user/user-list.spec.ts`
- [x] 1.8 删除 `features/ui_steps/support/db-factory.ts`
- [x] 1.9 删除 `features/ui_steps/` 下已空的 `auth/` 和 `user/` 目录

## 2. 迁移 Page Object 到 features/ui_steps/pages/

- [x] 2.1 在 `features/ui_steps/pages/` 目录创建 `__init__.py`
- [x] 2.2 将 `features/ui/pages/base_page.py` 迁移至 `features/ui_steps/pages/base_page.py`，保持 `BasePage` 类接口不变
- [x] 2.3 将 `features/ui/pages/sign_in_page.py` 迁移至 `features/ui_steps/pages/sign_in_page.py`，保持 `SignInPage` 类接口不变
- [x] 2.4 将 `features/ui/pages/users_page.py` 迁移至 `features/ui_steps/pages/users_page.py`，保持 `UsersPage` 类接口不变
- [x] 2.5 删除旧 `features/ui/pages/` 目录（含 `__init__.py`）

## 3. 建立 UI Stage Steps 结构

- [x] 3.1 在 `features/ui_steps/` 创建 `__init__.py`
- [x] 3.2 将 `features/ui/environment.py` 迁移至 `features/ui_environment.py`（behave `--stage ui` 约定路径），更新内部对 `pages/` 的导入路径
- [x] 3.3 创建 `features/ui_steps/auth_steps.py`，实现 `auth.feature` 中所有场景的 UI step 定义，全部通过 `SignInPage` Page Object 调用，步骤文件中无 CSS selector
- [x] 3.4 创建 `features/ui_steps/user_steps.py`，实现 `user.feature` 中所有场景的 UI step 定义，通过 `UsersPage` Page Object 调用，步骤文件中无 CSS selector

## 4. 验证 UsersPage Page Object 覆盖原 UI-only 断言

- [x] 4.1 确认 `UsersPage` 包含 `is_table_visible()` 方法
- [x] 4.2 确认 `UsersPage` 包含 `is_role_filter_visible()` 和 `is_status_filter_visible()` 方法
- [x] 4.3 确认 `UsersPage` 包含 `is_invite_button_visible()` 和 `is_invite_button_disabled()` 方法
- [x] 4.4 如缺少以上方法，在 `features/ui_steps/pages/users_page.py` 中补充实现

## 5. 配置 Nx BDD Targets

- [x] 5.1 在 `fastapi-clean-example/project.json` 中添加 `bdd-http` target，配置 behave 命令指向 `features/http_steps/` 为 steps-dir
- [x] 5.2 在 `fastapi-clean-example/project.json` 中添加 `bdd-ui` target，配置 behave 命令指向 `features/ui_steps/` 为 steps-dir，并设置 `BASE_URL` 和 `E2E_MODE` 环境变量
- [x] 5.3 验证 `pnpm nx run fastapi-clean-example:bdd-http` 正常运行（不启动浏览器）
- [x] 5.4 验证 `pnpm nx run fastapi-clean-example:bdd-ui` 可以启动并执行 UI stage 测试

## 6. 添加 Cypress 组件测试（shadcn-admin）

- [x] 6.1 在 `shadcn-admin/` 中确认或安装 Cypress 组件测试依赖（`cypress`已添加到 devDependencies，需运行 `pnpm install`）
- [x] 6.2 创建 `shadcn-admin/cypress/e2e/auth/sign-in.cy.ts`，覆盖登录表单渲染断言
- [x] 6.3 创建 `shadcn-admin/cypress/e2e/users/user-list.cy.ts`，覆盖用户列表表格、过滤按鈕、Invite 按鈕 disabled 状态
- [x] 6.4 在 `shadcn-admin/project.json` 中添加 `test-cypress` target

## 7. 清理与最终验证

- [x] 7.1 删除 `features/ui/` 目录（已无剩余内容）
- [x] 7.2 运行 `pnpm nx run fastapi-clean-example:bdd-http` 确认所有 HTTP stage 场景通过
- [x] 7.3 运行 `pnpm nx run fastapi-clean-example:bdd-ui` 确认所有 UI stage 场景通过
- [x] 7.4 检查 `features/ui_steps/` 目录，确认不含任何 `.ts` 文件
- [x] 7.5 检查 `features/ui_steps/` 下所有 step 文件，确认无直接 `page.locator(...)` 调用
