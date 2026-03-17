## ADDED Requirements

### Requirement: 系统 SHALL 识别 Feature 文件与同名目录之间的父子关系
参照 Cucumber Studio 的设计理念，每个 `.feature` 文件本身等同于一个"场景文件夹"。当某个 Feature 需要进一步拆分子功能时，其子 Feature 文件 SHALL 放置在与该 `.feature` 文件同名的目录下（去掉 `.feature` 后缀）。系统 SHALL 识别此约定：若存在 `foo.feature` 且同级目录下存在 `foo/` 文件夹，则 `foo/` 下的所有 `.feature` 文件 SHALL 被视为 `foo.feature` 的子 Feature（Sub-Feature）。此约定可递归嵌套。

示例：
```
features/
  user.feature          ← 父 Feature（用户主功能）
  user/
    user_auth.feature   ← 子 Feature（用户授权子功能）
  auth.feature          ← 独立 Feature（无子 Feature）
```

#### Scenario: 识别同名目录下的子 Feature
- **WHEN** Git 仓库中存在 `user.feature` 且同级有 `user/user_auth.feature`
- **THEN** 系统 SHALL 将 `user_auth.feature` 的 parent_feature_id 指向 `user.feature` 对应的 Feature 记录

#### Scenario: 无同名目录的 Feature 为顶层独立节点
- **WHEN** Git 仓库中存在 `auth.feature` 但无 `auth/` 目录
- **THEN** 系统 SHALL 将 `auth.feature` 作为顶层 Feature 节点，parent_feature_id 为空

#### Scenario: 子 Feature 目录中再有同名子目录时递归嵌套
- **WHEN** 存在 `user.feature`、`user/profile.feature` 及 `user/profile/avatar.feature`
- **THEN** 系统 SHALL 识别三层嵌套：user → profile → avatar

### Requirement: 系统 SHALL 以树形结构展示 Feature 文件（含 Sub-Feature 层级）
系统 SHALL 提供 API 返回 Project 内所有 Feature 文件的树形结构，层级为：顶层 Feature > Sub-Feature（可多层嵌套）> Rule（可选）> Scenario。前端 SHALL 将该结构渲染为可展开/折叠的树形组件，Sub-Feature 节点在视觉上表现为父 Feature 的子项。

#### Scenario: 获取包含 Sub-Feature 的 Feature 树
- **WHEN** 用户请求 GET /api/v1/projects/{id}/features
- **THEN** 系统 SHALL 返回嵌套树形结构，Sub-Feature 作为父 Feature 的 children 节点，叶节点为 Scenario

#### Scenario: Feature 文件有 Rule 层级时正确嵌套
- **WHEN** 某 Feature 文件包含 Gherkin 6 `Rule` 关键字
- **THEN** 系统 SHALL 在 Feature 节点下展示 Rule 节点，Rule 节点下展示属于该 Rule 的 Scenario

### Requirement: 系统 SHALL 支持 Gherkin 6 语法解析（含 Rule 关键字）
Feature 文件解析器 SHALL 支持完整的 Gherkin 6 语法，包括 `Feature`、`Rule`、`Scenario`、`Scenario Outline`、`Background`、`Given`、`When`、`Then`、`And`、`But` 及 `Examples` 关键字。`Rule` 关键字 SHALL 作为 Scenario 的父级分组被记录在 Scenario 的 rule_name 字段中。

#### Scenario: 解析含 Rule 关键字的 Feature 文件
- **WHEN** Git 同步拉取到含 `Rule:` 关键字的 .feature 文件
- **THEN** 系统 SHALL 将该 Rule 下的每个 Scenario 的 rule_name 字段设置为该 Rule 的名称

#### Scenario: 解析不含 Rule 的 Feature 文件
- **WHEN** Git 同步拉取到标准 Gherkin 5 风格的 .feature 文件（无 Rule）
- **THEN** 系统 SHALL 正确解析所有 Scenario，其 rule_name 字段为空

### Requirement: 系统 SHALL 展示 Feature 文件的原始内容及 Gherkin 高亮
用户点击某个 Feature 文件时，前端 SHALL 展示其完整原始文本内容，并对 Gherkin 关键字（Feature / Rule / Scenario / Background / Given / When / Then / And / But / Examples）应用语法高亮，以区分关键字、文本描述和表格数据。

#### Scenario: 获取 Feature 文件原始内容
- **WHEN** 用户请求 GET /api/v1/projects/{id}/features/{fid}
- **THEN** 系统 SHALL 返回该 Feature 文件的 content 字段（完整 UTF-8 文本）

### Requirement: 系统 SHALL 展示每个 Feature 文件的场景数量统计
Feature 树的每个 Feature 节点 SHALL 展示其包含的 Scenario 总数，便于用户快速了解功能覆盖规模。

#### Scenario: Feature 树节点携带场景数量
- **WHEN** 用户请求 Feature 树
- **THEN** 响应中每个 Feature 节点 SHALL 包含 scenario_count 字段，值为该 Feature 内 Scenario 的数量
