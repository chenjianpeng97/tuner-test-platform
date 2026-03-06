# Nx 引入与落地总结

## 1. 当前项目背景

当前仓库不是从零开始手写，而是先引入了两个开源模板作为基础：

- 前端模板：[shadcn-admin](../shadcn-admin)
- 后端模板：[fastapi-clean-example](../fastapi-clean-example)

这意味着当前阶段的目标不是先把代码整体重构到理想形态，而是：

1. 先接管现有模板
2. 先统一工程入口
3. 再逐步把项目演进到目标的 monorepo 结构

---

## 2. 为什么在当前项目中引入 Nx

引入 Nx 的核心目的，不是替代 FastAPI、React、BDD、OpenAPI、Pencil 或 OpenSpec 本身，而是把这些东西组织成一个可执行、可追踪、可演进的工程体系。

结合当前项目，Nx 的预期收益包括：

### 2.1 统一前后端工作流

将原本零散的研发步骤组织成一条明确链路，例如：

1. Pencil 原型设计
2. Gherkin feature 编写
3. 接口文档 / OpenAPI 设计
4. 后端实现
5. 后端 BDD 验收通过
6. 前端实现
7. 前端 BDD 验收通过

Nx 的作用是把这些环节转化为统一的任务入口和依赖链，而不是只靠人工约定执行顺序。

### 2.2 图形化展示项目结构和依赖

Nx 可以把 app、lib、spec、tool 之间的关系可视化，便于理解：

- 前端如何依赖 API client
- API client 如何依赖 OpenAPI 文档
- BDD 如何依赖 features 和 app
- 后端各层如何组织边界

### 2.3 统一命令入口

引入 Nx 后，希望逐步用 `nx run ...` 替代当前分散的：

- 后端 `uv` / `pytest` / `ruff` / 自定义脚本
- 前端 `pnpm dev` / `pnpm build` / `eslint`

最终形成统一入口，例如：

- `nx run app-api:serve`
- `nx run app-web:serve`
- `nx run app-api:test-unit`
- `nx run app-api:export-openapi`
- `nx run fe-api-client:generate`

### 2.4 围绕“唯一信源”做变更追踪

Nx 本身不是唯一信源，但可以围绕唯一信源建立依赖链和检查链。

本项目中更合适的唯一信源定义是：

- 原型信源：Pencil 文件
- 需求信源：Gherkin features
- 实现约束信源：OpenSpec
- 接口契约信源：OpenAPI

Nx 用于回答：

- 哪个信源变了
- 影响了哪些项目
- 应该重跑哪些生成、测试和验收流程

---

## 3. 当前项目结构下的总体实施方案

### 3.1 总原则

不先大重构代码，而是先写足够的 Nx 配置，让 Nx 先接管命令、依赖关系和流程编排。

一句话概括：

> 先让 Nx 管命令和关系，再让 Nx 管目录和边界。

### 3.2 为什么不先重构模板代码

如果一开始就同时做“模板迁移 + 架构重构 + Nx 引入”，会有几个问题：

1. 难以区分问题来源
2. 容易破坏模板原本可运行性
3. 学习负担过高

因此当前更稳的路线是：

- 模板先原样保留为可运行 app
- Nx 先接管启动、构建、测试、生成链
- 后续再逐步抽出独立 lib 和边界规则

---

## 4. 第一阶段：先写足够的 Nx 配置

第一阶段的目标不是完美 monorepo，而是让当前项目先具备统一入口。

### 4.1 先接管当前两个模板

先将现有两个模板映射为两个 Nx app：

- `app-web` -> [shadcn-admin](../shadcn-admin)
- `app-api` -> [fastapi-clean-example](../fastapi-clean-example)

### 4.2 先统一启动命令

优先目标是让 Nx 代替当前的前后端直接启动命令。

也就是说，不再优先记忆：

- 后端 `uv` 相关启动命令
- 前端 `pnpm dev`

而是逐步过渡到：

- `nx run app-api:serve`
- `nx run app-web:serve`

### 4.3 第一批应该由 Nx 接管的 target

#### app-api

- `serve`
- `lint`
- `test-unit`
- `test-integration`
- `export-openapi`

#### app-web

- `serve`
- `build`
- `lint`
- `test`

此时重点不是拆目录，而是先把原有命令包装成统一 Nx target。

---

## 5. 第二阶段：补齐规格、契约和生成链

当基础 app 已能通过 Nx 启动后，再把需求资产和生成流程也纳入管理。

建议逐步引入这些项目：

- `spec-features`
- `spec-openspec`
- `doc-api`
- `tool-openapi`
- `fe-api-client`
- `fe-mock-server`

### 5.1 目标链路

逐步形成下面这条工程链：

1. `app-api:export-openapi`
2. `tool-openapi:run`
3. `doc-api:check`
4. `fe-api-client:generate`
5. `fe-mock-server:generate`

这样后续接口文档变化时，可以自动驱动前端 client 和 mock 同步更新。

---

## 6. 第三阶段：补齐 BDD 入口

在前后端基本链路稳定后，再将 BDD 收编到 Nx。

建议引入：

- `app-api-e2e-http`
- `app-web-e2e-ui`
- `tool-bdd`

### 6.1 后端 BDD

这里当前策略可先简化为：

- 优先做“后端集成 DB 的接口验收测试”
- 即 `bdd-http` 阶段先直接验证真实后端接口行为

也就是先不急着把 mock 注入编排验证做全，而是先把真实接口验收链跑通。

### 6.2 前端 BDD

前端建议保留两种模式：

- `mock`：只用 mock server 验证前端行为
- `dev`：前后端同时启动，做联调验收

最终对应 target 可以是：

- `app-api-e2e-http:bdd-real`
- `app-web-e2e-ui:bdd-mock`
- `app-web-e2e-ui:bdd-dev`

---

## 7. 新增一个领域模块时的推荐做法

后续新需求不建议先直接堆代码，而是推荐“配置先行”。

以新增一个领域模块为例，推荐流程如下。

### 7.1 先补规格资产

先创建：

- `specs/features/<module>/`
- `specs/openspec/<module>/`

即先让需求和规格有归属位置。

### 7.2 先补 Nx 任务链

在写业务代码前，先想清楚这个模块会经过哪些链路：

- 是否影响 OpenAPI
- 是否需要重新生成前端 client
- 是否需要更新 MSW mock
- 是否需要新增 HTTP BDD
- 是否需要新增 UI BDD

先在 Nx 配置中把这些 target 接好。

### 7.3 再把代码先落到现有模板结构中

在当前阶段，新增模块的代码可以先放在原模板中：

- 后端放进现有 clean architecture 结构
- 前端放进现有 feature 目录结构

这样做的原因是：

- 先保持模板可运行
- 先让流程跑通
- 避免一开始就过度拆分

### 7.4 模块稳定后再抽 lib

当模块稳定后，再逐步把它抽离成更清晰的可复用单元，例如：

- 后端逐步抽到 `be-domain` / `be-application` / `be-presentation`
- 前端逐步抽到 `fe-ui` / `fe-shared` / 业务 feature lib

---

## 8. 最终希望达到的效果

当 Nx 接管程度逐步提高后，希望项目具备以下能力：

### 8.1 统一命令入口

所有关键流程都可以通过 `nx` 统一执行，而不是分散在 `uv`、`pnpm`、脚本、手工命令中。

### 8.2 生成依赖图

可以使用 Nx 清晰查看：

- 当前有哪些 app 和 lib
- 它们之间如何依赖
- 新增领域模块位于哪条链路中

### 8.3 做链路影响分析

当某个模块、feature、OpenAPI 文档发生变化时，可以更容易判断：

- 哪些生成步骤需要重跑
- 哪些测试需要重跑
- 哪些前后端模块受影响

### 8.4 逐步补齐边界治理

等项目稳定后，可以继续增加：

- tag 约束
- 分层依赖规则
- affected 执行
- cacheable target

这样 Nx 才会从“统一脚本入口”升级成“真正的 monorepo 工程骨架”。

---

## 9. 当前阶段的建议结论

对于当前“从前后端开源模板起步”的项目，最合适的引入方式是：

1. 先保留模板原貌
2. 先让 Nx 代替当前前后端启动与常用命令入口
3. 再纳入 OpenAPI、orval、MSW、BDD 等生成与测试链
4. 以后每实现一个新的领域模块，就补全一部分 Nx 配置
5. 最终让 Nx 成为整个项目的统一执行层、依赖图层和变更分析层

简化总结：

> 不是先把代码重构到理想状态再上 Nx，
> 而是先让 Nx 接管项目，再随着业务增长逐步补全 Nx 能力。
