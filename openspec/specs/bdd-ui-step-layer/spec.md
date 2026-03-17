## Purpose

定义 UI stage 下 behave step 实现的职责、约束与运行隔离规范。

## Requirements

### Requirement: UI stage step 定义覆盖 auth.feature 场景
UI step layer SHALL 为 `features/auth.feature` 中的所有场景提供 behave step 实现，通过 Playwright 在浏览器中执行登录、登出等动作并验证页面状态。

#### Scenario: UI step 实现登录成功场景
- **WHEN** behave 以 `features/ui_steps/` 为 steps-dir 运行 `auth.feature` 的"Login succeeds"场景
- **THEN** step `Given I am signed in as "charlie01"` SHALL 导航浏览器至登录页并完成表单提交
- **THEN** step `Then the auth cookie should be issued` SHALL 通过浏览器 storage/cookie 断言验证通过

#### Scenario: UI step 覆盖 user.feature 的用户管理场景
- **WHEN** behave 以 `features/ui_steps/` 为 steps-dir 运行 `user.feature` 的任意场景
- **THEN** 相关 step 定义 SHALL 存在于 `features/ui_steps/` 目录下的 Python 文件中
- **THEN** 所有 step 断言 SHALL 通过 Page Object 方法调用，steps 文件中 SHALL NOT 包含任何 CSS selector 或 XPath 字符串

### Requirement: UI step 文件不包含选择器字符串
UI steps 实现文件 SHALL 不直接使用 CSS selector 或 XPath。所有 DOM 交互 SHALL 委托给对应的 Page Object 方法。

#### Scenario: Step 实现委托 Page Object
- **WHEN** 代码审查 `features/ui_steps/` 下的任意 step 定义文件
- **THEN** 文件中 SHALL NOT 出现形如 `page.locator("...")` 或 `page.click("...")` 的直接选择器调用
- **THEN** 所有浏览器交互 SHALL 通过 `SignInPage`、`UsersPage` 等 Page Object 类的方法完成

### Requirement: UI behave 运行时独立于 HTTP behave 运行时
运行 UI stage BDD 测试 SHALL 不加载 `features/http_steps/` 中的任何 step 定义。

#### Scenario: 分离 steps-dir 确保隔离
- **WHEN** 通过 `behave --steps-dir features/ui_steps features/*.feature` 运行 UI stage
- **THEN** behave SHALL 仅加载 `features/ui_steps/` 下的 step 定义
- **THEN** `features/http_steps/http_bdd_steps.py` 中的 step 定义 SHALL NOT 被加载
