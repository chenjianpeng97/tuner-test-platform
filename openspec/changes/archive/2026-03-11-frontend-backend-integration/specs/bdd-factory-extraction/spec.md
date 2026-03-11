## ADDED Requirements

### Requirement: BDD 测试数据注入逻辑迁移至顶层 `features/factories/`
`features/http_steps/factories/seeding.py` 和 `features/http_steps/factories/identity_registry.py` SHALL 被移动（非复制）到 `features/factories/`，成为 HTTP 和 UI 两套 BDD 步骤的共享基础设施。

迁移后：
- `features/http_steps/factories/` 目录 SHALL 被移除（或仅保留空 `__init__.py` 用于向后兼容的重新导出）
- `features/http_steps/http_bdd_steps.py` 中的导入路径 SHALL 从 `features.http_steps.factories.*` 更新为 `features.factories.*`
- 现有 HTTP BDD 测试 SHALL 在迁移后继续通过，不引入功能变更

#### Scenario: HTTP BDD 测试在迁移后仍可通过
- **WHEN** 完成 factory 迁移后，执行 `pnpm exec nx run app-api:test-uat`
- **THEN** 所有现有 HTTP BDD 场景测试通过，无导入错误

#### Scenario: `features/factories/` 目录可被 UI 步骤直接导入
- **WHEN** `features/ui_steps/` 中的 Python 代码执行 `from features.factories.seeding import ensure_identity`
- **THEN** 导入成功，函数可正常调用

### Requirement: UI BDD 步骤复用共享 factory 进行数据库测试数据注入
`features/ui_steps/` 中的 Playwright BDD 步骤 SHALL 通过 `features.factories.seeding.ensure_identity()` 在数据库中注入测试前置数据，与 HTTP BDD 步骤使用同一套 `IDENTITIES` 身份字典和同一套数据注入逻辑。

#### Scenario: UI BDD Given 步骤与 HTTP BDD Given 步骤行为一致
- **WHEN** UI BDD 场景中执行 `Given the shared identity "Charlie" exists as role "admin" and is active`
- **THEN** `features.factories.seeding.ensure_identity("Charlie", role=UserRole.ADMIN, is_active=True)` 被调用，数据库中存在 charlie01 用户

#### Scenario: 同一身份在两套测试中使用相同凭据
- **WHEN** HTTP BDD 和 UI BDD 场景都引用同一身份（如 "Charlie"）
- **THEN** 两套步骤从 `features.factories.identity_registry.IDENTITIES` 获取相同的 username/password/role 定义

### Requirement: `ux-uat:check-features` lint 检查通过工厂迁移后仍有效
工厂目录迁移 SHALL 不破坏 `ux-uat:check-features` target 中的特征结构检查脚本。

#### Scenario: features 结构检查在迁移后通过
- **WHEN** 执行 `pnpm exec nx run ux-uat:check-features`
- **THEN** 所有结构检查脚本（`check_feature_pairs.py` 等）成功通过
