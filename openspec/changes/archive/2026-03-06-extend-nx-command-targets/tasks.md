## 1. Extend frontend target coverage

- [x] 1.1 为现有 `app-web` 的 Nx target 增加 `metadata.description`。
- [x] 1.2 为前端模板中的预览、格式检查、格式化与 knip 原生命令新增 Nx target，并使用稳定的语义化 target 名称。
- [x] 1.3 验证新增前端 target 仍然在 `shadcn-admin` 项目根目录下执行，并正确映射到预期的原生命令。

## 2. Extend backend target coverage

- [x] 2.1 为现有 `app-api` 的 Nx target 增加 `metadata.description`。
- [x] 2.2 为后端模板中的格式化、聚合检查、覆盖率、环境准备、数据库生命周期与迁移命令新增 Nx target，并使用语义化 target 名称。
- [x] 2.3 确保后端运维类 target 保留被包装命令原有的环境变量约束与 guard 行为。

## 3. Document and validate the mapping

- [x] 3.1 更新 Nx 命令清单说明，补充扩展后的前后端命令映射关系。
- [x] 3.2 验证一组具有代表性的新增 Nx target，并确认现有 target 仍按预期工作。
