## 改了什么

<!-- 简要说明这次修改的内容（1-3 句话） -->

## 为什么改

<!-- 解决了什么问题 / 实现了什么需求。如果关联 Issue 请用 Closes #123 -->

## 涉及范围

<!-- 在改动的部分前打 [x] -->

- [ ] 主流程 / 路由（aws-wechat-article-main）
- [ ] 选题（topics）
- [ ] 写作（writing）
- [ ] 审稿（review）
- [ ] 排版（formatting）
- [ ] 配图（images）
- [ ] 发布（publish）
- [ ] 贴图（sticker）
- [ ] 素材管理（assets）
- [ ] 安装脚本（install-skills.sh）
- [ ] 文档（README / SKILL.md / references）
- [ ] 配置示例（config.example.yaml / env.example.yaml）
- [ ] 其他：

## 测试验证

<!-- 描述你做了哪些验证。建议至少跑一遍以下基础检查： -->

- [ ] `python3 -m py_compile` 检查改动的 Python 脚本语法
- [ ] `python3 -c "import yaml; yaml.safe_load(open('xxx.yaml'))"` 检查改动的 YAML
- [ ] 实际跑过对应 Skill 的完整流程
- [ ] 在多个平台（OpenClaw / Cursor / Claude Code / Codex）验证（如改了通用逻辑）
- [ ] README / SKILL.md / references 同步更新

## 截图 / 演示（可选）

<!-- 如果是 UI、排版、配图风格相关改动，建议附图对比 -->

## 兼容性说明

<!-- 是否破坏了已有用户的配置？是否需要迁移说明？ -->

- [ ] 完全向后兼容
- [ ] 需要用户手动迁移（迁移步骤已在改动说明中描述）
- [ ] 破坏性变更（已在 PR 标题加 `[Breaking]` 前缀）

## 补充信息

<!-- 任何其他需要 reviewer 注意的事项 -->
