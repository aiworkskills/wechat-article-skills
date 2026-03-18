---
name: aws-wechat-article-main
description: 微信公众号内容运营总流程与路由。管理选题→写稿→审稿→排版→配图→发布的完整链路，支持一条龙模式与单步模式。当用户提到「公众号运营」「自动运营」「发文章」「内容规划」「怎么运营」或需要了解整体流程时使用。
version: 0.1.0
metadata:
  openclaw:
    homepage: https://github.com/aiworkskills/wechat-article-skills#aws-wechat-article-main
---

# 公众号运营总览

管理微信公众号内容全流程，路由到对应子 skill。

## 流程

```
选题 → 写稿 → 审稿 → 排版 → 配图 → 发布
```

| 步骤 | 子 skill | 职责 |
|------|---------|------|
| 选题与标题 | aws-wechat-article-topics | 选题列表、标题候选、摘要候选、排期 |
| 写稿 | aws-wechat-article-writing | 长文写作或改写，产出完整正文 |
| 审稿 | aws-wechat-article-review | 合规检查、敏感词、错别字、链接 |
| 排版 | aws-wechat-article-formatting | 应用预设排版规则，输出格式化内容 |
| 配图 | aws-wechat-article-images | 封面图与正文配图 |
| 发布 | aws-wechat-article-publish | 发布前检查与提交指引 |

## 路由规则

根据用户说法路由到对应子 skill：

| 用户说法 | 路由到 |
|---------|--------|
| 选题、起标题、摘要、排期、爆款、内容日历 | aws-wechat-article-topics |
| 写正文、改写、公众号风格、结构、开头结尾 | aws-wechat-article-writing |
| 审稿、合规、敏感词、检查 | aws-wechat-article-review |
| 排版、版式、字号、段落、样式 | aws-wechat-article-formatting |
| 封面、配图、贴图、生成图片、多图推送 | aws-wechat-article-images |
| 发布、提交、群发 | aws-wechat-article-publish |

## 运行模式

### 一条龙模式

当用户说「从选题到发布全做」「一条龙」「完整流程」时启用。

复制并跟踪进度：

```
一条龙进度：
- [ ] 第1步：选题与标题
- [ ] 第2步：写稿
- [ ] 第3步：审稿
- [ ] 第4步：排版
- [ ] 第5步：配图
- [ ] 第6步：发布检查
```

**执行规则**：
1. 按顺序执行每一步，调用对应子 skill
2. 每步完成后**暂停**，展示产出给用户
3. 用户说「继续」→ 进入下一步
4. 用户提出修改 → 按意见调整后重新展示，确认后继续
5. 更新进度清单中的勾选状态

### 单步模式

用户只提到某一步时，仅执行该步骤的子 skill。

### 贴图（多图推送）模式

多图推送走精简流程，跳过写稿和排版：

```
贴图进度：
- [ ] 第1步：选题（贴图文案与主题）
- [ ] 第2步：配图（图序、配文、规格）
- [ ] 第3步：审稿
- [ ] 第4步：发布检查
```

## 配置

所有子 skill 共享一份配置文件 `config.yaml`。

| 优先级 | 来源 |
|--------|------|
| 1（最高） | 用户当次对话中的说法 |
| 2 | 项目级 `.aws-article/config.yaml` |
| 3 | 用户级 `~/.aws-article/config.yaml` |

- 无配置时触发首次引导：[references/first-time-setup.md](references/first-time-setup.md)
- 配置字段说明：[references/config-schema.md](references/config-schema.md)
