## ADDED Requirements

### Requirement: 未实现功能按钮须处于 disabled 状态
前端页面中所有触发后端尚未实现功能的按钮或操作入口（包括但不限于 "Invite Users" 按钮） SHALL 添加 `disabled` HTML 属性，防止用户点击触发任何行为。

已确认需要 stub 的功能入口：
- Users 页面的 "Invite Users" 按钮
- 其他后端未提供对应 API 的操作按钮（在实现阶段通过代码扫描确认）

#### Scenario: Invite Users 按钮不可点击
- **WHEN** 打开 Users 页面
- **THEN** "Invite Users" 按钮处于 disabled 状态，点击无任何副作用（无路由跳转、无表单弹出）

#### Scenario: disabled 按钮具有提示信息
- **WHEN** 用户将鼠标悬停在 disabled 的 "Invite Users" 按钮上
- **THEN** 出现浏览器原生 tooltip 或 `title` 属性内容，提示"功能开发中"或等效语义文本

### Requirement: 未实现功能按钮保持原有视觉风格
功能按钮 SHALL 在 disabled 状态下保持与设计稿一致的视觉外观（不强制更改为灰色或移除），使用浏览器原生 disabled 行为实现交互禁用。

#### Scenario: disabled 按钮视觉与设计稿一致
- **WHEN** 打开 Users 页面并截图
- **THEN** "Invite Users" 按钮的颜色、形状、位置与其他同类主要操作按钮保持一致风格

### Requirement: 未实现功能入口具有 `data-testid` 属性
所有被 stub 的功能按钮 SHALL 添加 `data-testid` 属性，格式为 `{feature}-{action}-btn`（如 `users-invite-btn`），以支持 UI 自动化测试验证其 disabled 状态。

#### Scenario: Playwright 可通过 testid 定位 disabled 按钮
- **WHEN** Playwright 测试查找 `data-testid="users-invite-btn"`
- **THEN** 能找到该元素，且 `disabled` 属性为 `true`
