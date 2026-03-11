## Context

**当前状态：**
- 后端（`app-api`）已实现用户管理（CRUD、activate/deactivate）和认证（login/logout）接口，基于 FastAPI 清洁架构，运行在 `http://localhost:8000`
- 认证机制为 **Cookie-based session**（登录成功后服务端 Set-Cookie，后续请求携带 cookie 鉴权），无 JWT access token
- 前端（`shadcn-admin`，TanStack Router + TanStack Query + axios）展示了 Users 列表页、SignIn 页、ForgotPassword 页，但全部使用 faker.js 硬编码假数据，未调用任何真实接口
- 前端 auth store（Zustand）目前管理 access token cookie，需改造为 session cookie 流程
- 前端角色枚举（`superadmin / admin / manager / cashier`）与后端（`super_admin / admin / user`）不一致
- BDD 测试（`features/`）目前只有 `http_steps`（Python behave），无 UI 层自动化步骤

**约束：**
- UI 风格与现有模板保持不变（shadcn-ui 组件、布局、配色）
- 已有依赖：`@tanstack/react-query`, `axios`, `zod`；无需重复引入
- Playwright 已在 workspace 根 `package.json` 层面可用（`ux-uat` 项目）

---

## Goals / Non-Goals

**Goals:**
- 建立 OpenAPI 契约导出 → Orval 代码生成 → MSW mock → 前端页面的完整契约驱动链路
- 前端 Users 页和 Auth 页的数据层从 faker.js 切换到 MSW（开发阶段）/ 真实 API（集成阶段）
- 对齐前后端角色和状态枚举
- 为所有自编写前端组件补充 `data-testid`
- 新增 Playwright `ui_steps` 步骤文件，使 BDD Feature 能在 UI 层跑通（先 MSW 后真实后端）
- 对未实现功能入口（Invite Users 等）添加安全占位，防止误触

**Non-Goals:**
- 不实现 ForgotPassword 实际逻辑（后端未实现，前端保持占位）
- 不改造 Tasks / Settings 等非 auth/user 页面
- 不引入新的状态管理库（沿用 Zustand）
- 不修改后端接口签名（契约以后端为准，单向流动）
- 不实现 Invite Users 功能（只做安全 stub）

---

## Decisions

### D1：OpenAPI 契约导出方式

**决策**：新增 Nx target `app-api:export-schema`，运行 Python 脚本通过 FastAPI 的 `/openapi.json` 端点（或直接 import app 对象调用 `app.openapi()`）将规范写入 `openspec/contracts/app-api.openapi.json`。

**理由**：FastAPI 内置 OpenAPI 生成，无需额外工具；将契约文件纳入 monorepo 版本控制，Orval 可直接读取本地文件，避免在代码生成时依赖运行中的后端服务。

**备选方案**：直接用 `curl http://localhost:8000/openapi.json` 在 serve 时导出 → 弃用，因为要求后端必须在线才能生成前端代码，破坏离线开发体验。

---

### D2：Orval 生成策略

**决策**：在 `shadcn-admin/` 下创建 `orval.config.ts`，配置两个 output：
1. **`api-client`**：生成 `src/api/generated/`，使用 `axios` 作为 HTTP client，`@tanstack/react-query` 作为 query 层（`react-query` mode）
2. **`msw-handlers`**：生成 `src/mocks/handlers/`，使用 `msw` 模式，产出 MSW request handler 函数

同时新增 Nx target `app-web:generate-api`（`pnpm exec orval --config orval.config.ts`）。

**理由**：两个输出分离关注点——一套用于真实 API 调用，一套用于 mock；同时保持生成代码与手写代码的边界清晰（生成代码禁止手动修改）。

**备选方案**：手写 API client → 弃用，失去类型安全保障且与契约变更脱节。

---

### D3：MSW 集成模式

**决策**：
- **开发环境**（`vite dev`）：在 `src/mocks/browser.ts` 中初始化 MSW browser worker，通过环境变量 `VITE_MSW_ENABLED=true` 控制启用，在 `src/main.tsx` 中条件引导
- **测试环境**（Playwright）：使用 MSW Node server（`setupServer`），在 Playwright 全局 setup 中启动
- **MSW mock 数据范围**：MSW handler 可模拟后端尚未支持的状态值（`invited` / `suspended`）和未实现功能（如 Invite Users API），用于保留 UI 演示能力和前端先行开发场景；这些模拟数据不会在后端集成测试中出现

**理由**：MSW 拦截 `fetch`/`XHR` 请求，对业务代码零侵入；同一套 handler 同时服务开发预览和 UI 自动化测试，保持一致性。

---

### D4：认证流程改造

**决策**：
- 后端 `POST /api/v1/auth/login` 返回 204 + `Set-Cookie: session=...`（HTTP-only cookie）
- 前端登录成功后**不存储 token**，改为调用 `GET /api/v1/users/me`（或等效端点）获取当前用户信息，写入 auth store 的 `user` 字段
- auth store 的 `accessToken` 字段废弃，改用 `user: AuthUser | null` 判断登录态
- axios 实例配置 `withCredentials: true` 确保 cookie 随跨域请求发送

**理由**：与后端 session cookie 机制对齐，消除前端维护 token 字符串的多余逻辑。

---

### D5：角色与状态枚举对齐

**决策**：

| 维度 | 后端值        | 前端旧值（废弃）      | 前端新值                  | 显示标签    |
| ---- | ------------- | --------------------- | ------------------------- | ----------- |
| 角色 | `super_admin` | `superadmin`          | `super_admin`             | Super Admin |
| 角色 | `admin`       | `admin`               | `admin`                   | Admin       |
| 角色 | `user`        | `manager` / `cashier` | `user`                    | User        |
| 状态 | `active`      | `active`              | `active`                  | Active      |
| 状态 | `inactive`    | `inactive`            | `inactive`                | Inactive    |
| 状态 | _不存在_      | `invited`             | （UI 保留，API 层不使用） | Invited     |
| 状态 | _不存在_      | `suspended`           | （UI 保留，API 层不使用） | Suspended   |

**策略**：`schema.ts` 中 `userRoleSchema` 和 `userStatusSchema` 以后端为准更新；`data.ts` 中 `roles` 数组同步；Zod 搜索过滤 schema 跟随变更。UI 状态 `invited` / `suspended` 保留在 `callTypes` 样式映射和过滤器 UI 中，但 MSW handler 和真实 API 层不会返回这些值（为未来扩展预留）。

---

### D6：Playwright UI 步骤与 BDD 集成

**决策**：
- 新建目录 `features/ui_steps/`（与 `features/http_steps/` 并列），使用 TypeScript + Playwright，以 `--stage ui` 区分
- `ux-uat/project.json` 当前未配置 `--stage ui`，需新增 Nx target `ux-uat:test-ui-uat`，封装 Playwright 运行命令，并在该 target 中设置 `VITE_MSW_ENABLED` 等环境变量
- 优先为已有的 auth 和 user feature 场景添加 UI 步骤（登录、查看用户列表）
- 先以 `VITE_MSW_ENABLED=true` 启动前端 dev server 跑通 mock 测试，再通过环境变量切换到真实后端
- Playwright 配置文件放在 `ux-uat/playwright.config.ts`；需在 workspace 根 `package.json` 补充 `@playwright/test` devDependency（若未存在）

**理由**：复用现有 BDD Feature 文件，步骤层与实现层分离；`--stage` 机制与现有 HTTP BDD 测试一致，风格统一；将 Playwright 配置收敛到 `ux-uat` 项目避免散落。

---

### D7：`data-testid` 策略

**决策**：对 `shadcn-admin/src/features/` 下**自编写**的容器组件和关键交互元素（表格行、操作按钮、表单字段、筛选器）添加 `data-testid`，格式为 `{feature}-{component}-{element}`（如 `users-table-row`, `auth-signin-submit`）。第三方 shadcn-ui 原始组件（如 `<Button>`, `<Table>`）不强加 testid，只在包装层加。

---

### D9：后端新增 `GET /api/v1/users/me` 端点（优先实现）

**决策**：
- 后端当前无「获取当前登录用户信息」端点，需在 `fastapi-clean-example` 中新增 `GET /api/v1/users/me`
- 该端点读取当前请求的 session cookie，返回当前登录用户的 `id`、`username`、`role`、`is_active` 字段
- 响应 schema 与 `GET /api/v1/users/{user_id}` 保持一致
- **优先级**：本 change 中最先实现，是前端 Auth 流程改造（D4）的基础依赖

**理由**：前端登录后需要知道当前用户的 role 和基本信息以渲染权限相关 UI（如导航菜单、操作按钮可见性）；session cookie 机制下无 JWT payload 可解析，必须通过服务端端点获取。

---

### D10：BDD 测试数据注入逻辑提取到顶层 `features/factories/`

**决策**：
- 当前 `features/http_steps/factories/`（含 `seeding.py`、`identity_registry.py`）的 DB 注入逻辑与 HTTP 步骤耦合
- 将这两个模块**移动**到 `features/factories/`（顶层），成为 HTTP 和 UI 两套步骤的共享基础设施
- `features/http_steps/http_bdd_steps.py` 中的导入路径从 `features.http_steps.factories.*` 更新为 `features.factories.*`
- `features/ui_steps/` 的 Playwright before-all hook 可直接调用 `features.factories.seeding.ensure_identity()` 在数据库中注入测试数据，实现与 HTTP BDD 完全相同的场景前置条件
- `IdentitySpec` 和 `IDENTITIES` 字典在两套测试中共享同一份定义，杜绝重复维护

**理由**：HTTP BDD 和 UI BDD 的 Feature 文件描述的是同一批业务场景，`Given` 步骤中的数据注入逻辑（"the shared identity X exists as role Y"）语义完全相同；提取到顶层后，未来新增测试层（如移动端）无需再复制一套 factory。

---

### D8：未实现功能占位策略

**决策**：
- 未实现功能按钮（如 Invite Users）添加 `disabled` 属性 + `title="功能开发中"` tooltip
- 使用 `sonner` toast 作为备用（点击时显示"该功能暂未开放"），但优先 `disabled` 以避免任何 click handler 触发
- 视觉样式保持不变（不调整样式为灰色，使用浏览器原生 disabled 行为）

---

## Risks / Trade-offs

- **[风险] Orval 生成代码与手写业务代码耦合** → 缓解：将生成代码放入 `src/api/generated/` 和 `src/mocks/handlers/`，通过 `.gitignore` 标注为可重建产物，手写代码只 import 生成接口不直接修改生成文件
- **[风险] 后端 OpenAPI 规范不够完整（缺少字段描述、response schema）** → 缓解：导出后人工审查，必要时在 FastAPI 路由处补充 `response_model` 注解；短期影响 Orval 生成质量，不阻塞进度
- **[风险] Session cookie 跨域问题（前端 localhost:5173 vs 后端 localhost:8000）** → 缓解：vite 配置 proxy 将 `/api` 转发到 `localhost:8000`，避免跨域，session cookie 在 same-origin 下正常工作；MSW 模式下跳过 proxy
- **[风险] MSW service worker 需要部署到 `/` 根路径** → 缓解：`pnpm exec msw init public/` 将 `mockServiceWorker.js` 写入 `public/`
- **[风险] Playwright 测试与 MSW dev server 时序问题** → 缓解：Playwright global setup 等待 `localhost:5173` 可用后再运行，MSW Node server 与 Playwright 进程内联启动

---

## Migration Plan

1. 导出 OpenAPI 契约：新增 `app-api:export-schema` Nx target，生成 `openspec/contracts/app-api.openapi.json`
2. 配置 Orval：安装 `orval` / `msw`，创建 `orval.config.ts`，新增 `app-web:generate-api` target
3. 改造 auth store：对齐 session cookie 流程，axios 加 `withCredentials`，vite dev 加 proxy
4. 更新枚举：修改 `schema.ts` / `data.ts`，对齐角色和状态值
5. 集成 MSW：`src/mocks/` setup，`main.tsx` 条件引导，替换 faker.js 数据
6. 添加 `data-testid`：遍历 `features/users/` 和 `features/auth/` 组件
7. 未实现功能 stub：找到所有未实现按钮，添加 `disabled` + tooltip
0. **（前置）** 提取 `features/http_steps/factories/` → `features/factories/`，更新 http_steps 导入路径
1. 后端新增 `GET /api/v1/users/me` 端点（D9，优先）
2. 导出 OpenAPI 契约：新增 `app-api:export-schema` Nx target，生成 `openspec/contracts/app-api.openapi.json`
3. 配置 Orval：安装 `orval` / `msw`，创建 `orval.config.ts`，新增 `app-web:generate-api` target
4. 改造 auth store：对齐 session cookie 流程，axios 加 `withCredentials`，vite dev 加 proxy
5. 更新枚举：修改 `schema.ts` / `data.ts`，对齐角色和状态值
6. 集成 MSW：`src/mocks/` setup，`main.tsx` 条件引导，替换 faker.js 数据（含 invited/suspended 演示数据）
7. 添加 `data-testid`：遍历 `features/users/` 和 `features/auth/` 组件
8. 未实现功能 stub：找到所有未实现按钮，添加 `disabled` + tooltip
9. 配置 `ux-uat/playwright.config.ts`，新增 `ux-uat:test-ui-uat` Nx target
10. Playwright UI 步骤：创建 `features/ui_steps/`，共享 `features/factories/` 数据注入，实现登录和用户列表场景，先 MSW 验证，再真实后端

**回滚策略**：所有生成文件可重新运行 `app-web:generate-api` 恢复；枚举变更通过 TypeScript 编译错误发现遗漏点，无静默失败风险。

---

## Open Questions

（已全部解决，转化为 D9、D10 及 D3/D6 更新。）
