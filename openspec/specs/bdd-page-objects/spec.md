## Purpose

定义 UI BDD Page Object 的目录结构、职责边界与交互封装规范。

## Requirements

### Requirement: Page Object 类统一位于 features/ui_steps/pages/
所有 UI Page Object 类 SHALL 位于 `features/ui_steps/pages/` 目录下，现有 `features/ui/pages/` 中的类 SHALL 迁移至此目录。

#### Scenario: Page Object 目录迁移完成
- **WHEN** 检查项目文件结构
- **THEN** `features/ui_steps/pages/base_page.py` SHALL 存在，包含 `BasePage` 类
- **THEN** `features/ui_steps/pages/sign_in_page.py` SHALL 存在，包含 `SignInPage` 类
- **THEN** `features/ui_steps/pages/users_page.py` SHALL 存在，包含 `UsersPage` 类
- **THEN** `features/ui/pages/` 旧目录 SHALL 被删除

### Requirement: BasePage 提供通用浏览器操作基类
`BasePage` 类 SHALL 作为所有 Page Object 的抽象基类，封装通用导航和可见性断言方法，使子类无需直接操作 `playwright.sync_api.Page` 对象的底层 API。

#### Scenario: BasePage 提供 navigate 方法
- **WHEN** 调用 `base_page.navigate("/users")`
- **THEN** browser SHALL 导航至 `{BASE_URL}/users`
- **THEN** 方法 SHALL 接受相对路径并自动拼接 `base_url`

#### Scenario: BasePage 提供可见性断言方法
- **WHEN** 调用 `base_page.wait_for_visible(selector)`
- **THEN** 方法 SHALL 等待指定元素在页面上可见，超时后抛出异常

### Requirement: SignInPage 封装登录表单交互
`SignInPage` 类 SHALL 封装登录页面的所有 DOM 交互，包括填写用户名/密码并提交表单。

#### Scenario: SignInPage.login 方法执行完整登录流程
- **WHEN** 调用 `sign_in_page.login(username="charlie01", password="Charlie Password 123!")`
- **THEN** 页面 SHALL 导航至登录路由
- **THEN** 用户名和密码输入框 SHALL 被填充
- **THEN** 提交按钮 SHALL 被点击
- **THEN** 方法 SHALL 等待登录成功后的页面跳转

### Requirement: UsersPage 封装用户管理页面交互
`UsersPage` 类 SHALL 封装 `/users` 管理页面的所有 DOM 断言和交互，包括表格可见性、过滤器按钮状态和 Invite 按钮状态。

#### Scenario: UsersPage 提供用户表格可见性断言
- **WHEN** 调用 `users_page.is_table_visible()`
- **THEN** 方法 SHALL 返回 bool 值，反映用户列表表格是否在 DOM 中可见

#### Scenario: UsersPage 提供过滤器按钮状态查询
- **WHEN** 调用 `users_page.is_role_filter_visible()` 和 `users_page.is_status_filter_visible()`
- **THEN** 方法 SHALL 分别返回角色过滤按钮和状态过滤按钮的可见性状态

#### Scenario: UsersPage 提供 Invite 按钮状态查询
- **WHEN** 调用 `users_page.is_invite_button_disabled()`
- **THEN** 方法 SHALL 返回 bool 值，反映 Invite User 按钮是否处于 disabled 状态

### Requirement: Page Object 类不包含 behave step 逻辑
Page Object 类 SHALL 只封装浏览器交互和断言，SHALL NOT 包含 behave `@given`/`@when`/`@then` 装饰器或对 `context` 对象的引用。

#### Scenario: Page Object 与 behave 解耦
- **WHEN** 审查任意 Page Object 类文件
- **THEN** 文件 SHALL NOT 导入 `behave` 模块
- **THEN** 文件 SHALL NOT 使用 `@given`、`@when`、`@then` 装饰器
- **THEN** 类的方法 SHALL 只接受业务参数，不接受 `context` 参数
