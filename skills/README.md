# 微信公众号自动运营 Skills

7 个子 skill 组成的公众号内容全流程工具链，运行在 Cursor / OpenClaw 上。

## 流程

```
选题 → 写稿 → 审稿 → 排版 → 配图 → 发布
```

## 子 skill 列表

| 目录 | 职责 | 说明 |
|------|------|------|
| aws-wechat-article-main | 总览与路由 | 管理全流程，支持一条龙/单步/贴图模式 |
| aws-wechat-article-topics | 选题与标题 | 选题列表、标题候选、摘要候选、排期 |
| aws-wechat-article-writing | 长文写作 | 按结构模板写作或改写 |
| aws-wechat-article-review | 审稿与合规 | 敏感词、错别字、链接、合规检查 |
| aws-wechat-article-formatting | 排版 | 从预设读取规则，格式化输出 |
| aws-wechat-article-images | 配图 | 封面与正文配图，自动分析风格 |
| aws-wechat-article-publish | 发布 | 发布前检查与提交指引 |

## 安装

**一键安装（项目级）**：

```bash
bash scripts/install-skills.sh
```

将 7 个子 skill 安装到 `.cursor/skills/`，供 Cursor 加载。

或手动复制到 `.cursor/skills/`（项目级）或 `~/.cursor/skills/`（用户级）。

## 配置

所有 skill 共享一份配置文件。

1. 复制示例：`cp .aws-article/config.example.yaml .aws-article/config.yaml`
2. 按需编辑 `config.yaml`
3. 或首次使用时由 main skill 引导生成

配置路径优先级：项目 `.aws-article/config.yaml` → 用户 `~/.aws-article/config.yaml`。
