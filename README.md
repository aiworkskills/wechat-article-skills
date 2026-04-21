**简体中文** | [English](README_EN.md)

# 微信公众号 AI 运营助手

> 开源公众号运营数字员工。选好风格，说一句话，AI 自动完成选题、写作、排版、配图到发布的全部流程。**不用懂设计，不用会代码。**

[![License](https://img.shields.io/github/license/aiworkskills/wechat-article-skills)](LICENSE)
[![Stars](https://img.shields.io/github/stars/aiworkskills/wechat-article-skills?style=social)](https://github.com/aiworkskills/wechat-article-skills/stargazers)
[![Release](https://img.shields.io/github/v/release/aiworkskills/wechat-article-skills)](https://github.com/aiworkskills/wechat-article-skills/releases)
[![Platforms](https://img.shields.io/badge/platforms-13%2B%20Claw%20%7C%20Claude%20Code%20%7C%20Cursor%20%7C%20Codex-blue)](#支持的-ai-编程工具)



---

## 📚 教程与案例

- 📖 [如何用好 aiworkskills 平台？从配置到发文一文读懂](https://mp.weixin.qq.com/s/rcnq_gg3XXRwJ7ovQtBo1A) · 官方使用指南
- 🔧 [WorkBuddy 如何使用 AI Work Skills 运行公众号](https://mp.weixin.qq.com/s/GQjCY5UsArV9XI5AyoxWZQ) · WorkBuddy 组合案例
- ⚡ [QClaw + aiworkskills 一键运营公众号](https://mp.weixin.qq.com/s/xLUJBc2bbrJvgeAesbhsFA) · QClaw 组合案例

---

## 🚀 3 分钟上手（零代码）

推荐路径：用可视化配置台 **[aiworkskills.cn](https://aiworkskills.cn/)** 填表，导出预设包给 AI。
![aiworkskills 首页](https://aiworkskills.cn/images/sp/aiworkskills%E9%A6%96%E9%A1%B5.png)
```
① 装 AI 编程工具  →  ② 克隆本仓库  →  ③ 网页填表配置  →  ④ 导出 .aws  →  ⑤ 说一句话开始
```

1. **装一个 AI 编程工具** — QClaw / WorkBuddy / Cursor / Claude Code 等（完整列表见下）
2. **克隆仓库**
   ```bash
   git clone https://github.com/aiworkskills/wechat-article-skills.git
   ```
3. **去 [aiworkskills.cn](https://aiworkskills.cn/) 填表**：账号 → 策略 → 文风 → 视觉 → 发布，5 步完成
4. **点导出，下载 `.aws` 预设包**，扔给 AI：「帮我导入这个预设包」
5. **开写** — 对 AI 说：「帮我写一篇公众号文章」，选题到发布全流程跑完

---

## 🌐 支持生态

### 支持的 AI 编程工具

![支持平台](https://aiworkskills.cn/images/sp/%E6%94%AF%E6%8C%81%E5%B9%B3%E5%8F%B0.png)

基于 **OpenClaw 标准**，兼容 13+ Claw 系列工具：

> QClaw · ArkClaw · JVSClaw · WorkBuddy · Linclaw · NemoClaw · AutoClaw · MaxClaw · KimiClaw · DuClaw · PowerClaw · ZeroClaw

同时支持 **Claude Code · Cursor · Codex** 等主流 AI 编程工具。

### 支持的大模型

> DeepSeek · 通义千问 · 智谱 GLM · Kimi · 豆包 · 文心一言 · 讯飞星火 · 腾讯混元 · MiniMax · 百川 · 阶跃星辰 · 零一万物 · GPT · Claude

兼容所有 **OpenAI 接口**大模型，API Key 本地存储不上传。

---

## ✨ 9 个 Skill 分工

| Skill | 能力 | 你这样说 |
|-------|------|---------|
| **主流程** | 串联全流程 | 「帮我写一篇公众号文章」 |
| **选题** | 调研热点，推荐 3–5 个选题卡片 | 「帮我找几个选题」 |
| **写作** | 调用大模型 / AI 直写，遵循文风规范 | 「写一篇 AI 入门」 |
| **审稿** | 敏感词 / 错别字 / 规范比对，三级结果 | 「审一下这篇」 |
| **排版** | Markdown → 微信 HTML，4 套主题 | 「排版」 |
| **配图** | 14 种视觉风格 × 6 种图片类型 | 「配个图」 |
| **发布** | 微信 API 直发，多账号，自动压缩 | 「发布」 |
| **贴图** | 多图推送独立流程 | 「做一组贴图」 |
| **素材** | 图库管理 + `.aws` 预设包导入导出 | 「导入这个预设」 |

每一步暂停等你确认，不会自动跳转。全程可以打断、修改、重来。

---

## 📸 可视化配置一览

所有配置在 [aiworkskills.cn](https://aiworkskills.cn/) 填表完成。

<details>
<summary><b>账号定位与目标读者</b> — 一次性说清 AI 你是谁、写给谁</summary>

![账号与读者](https://aiworkskills.cn/images/sp/%E8%B4%A6%E5%8F%B7%E4%B8%8E%E8%AF%BB%E8%80%85%E9%85%8D%E7%BD%AE.png)

</details>

<details>
<summary><b>视觉呈现</b> — 排版主题 + 封面/配图风格预设</summary>

![视觉呈现](https://aiworkskills.cn/images/sp/%E8%A7%86%E8%A7%89%E5%91%88%E7%8E%B0%E9%85%8D%E7%BD%AE.png)

</details>

<details>
<summary><b>排版主题</b> — 4 套内置主题（经典蓝 / 优雅紫 / 暖橙 / 极简黑），也可以 YAML 自定义</summary>

![排版主题](https://aiworkskills.cn/images/sp/%E6%8E%92%E7%89%88%E9%A3%8E%E6%A0%BC%E9%A2%84%E8%AE%BE.png)

</details>

<details>
<summary><b>配图风格</b> — 14+ 视觉风格，对应不同内容类型</summary>

![配图风格](https://aiworkskills.cn/images/sp/%E6%94%AF%E6%8C%81%E7%9A%84%E6%96%87%E7%AB%A0%E9%85%8D%E5%9B%BE%E9%A3%8E%E6%A0%BC.png)

</details>

<details>
<summary><b>封面风格</b> — 多种封面视觉语言，和内容定位一一对应</summary>

![封面风格](https://aiworkskills.cn/images/sp/%E6%94%AF%E6%8C%81%E7%9A%84%E5%B0%81%E9%9D%A2%E9%85%8D%E5%9B%BE%E9%A3%8E%E6%A0%BC.png)

</details>

<details>
<summary><b>发布设置</b> — 微信 API、敏感词、文末嵌入元素</summary>

![发布配置](https://aiworkskills.cn/images/sp/%E5%8F%91%E5%B8%83%E9%85%8D%E7%BD%AE.png)

</details>

---

## 🛠️ 开发者路径（自己编辑 YAML）

如果你更习惯直接改配置，跳过 aiworkskills.cn：

```bash
git clone https://github.com/aiworkskills/wechat-article-skills.git
cd wechat-article-skills
bash scripts/install-skills.sh              # 安装到 .cursor / .claude
cp .aws-article/config.example.yaml .aws-article/config.yaml
# 编辑 config.yaml（账号/文风/排版）和 aws.env（API Key）
```

- 字段含义：[first-time-setup.md](skills/aws-wechat-article-main/references/first-time-setup.md)
- 三层配置体系：全局 `config.yaml` → 本篇 `article.yaml` → 对话中临时指定
- 6 种预设扩展点：`.aws-article/presets/{structures,closing-blocks,title-styles,formatting,cover-styles,sticker-styles}/`

---

## 📋 更新日志

完整变更历史见 [CHANGELOG.md](CHANGELOG.md)。最近几次：

- **2026-04-03** · 新增 assets skill：图片入库 + `.aws` 预设包导入导出
- **2026-03-31** · 脚本迁移与发布入口统一
- **2026-03-20** · 四平台一键安装 + 配置校验对齐
- **2026-03-18** · 三层文件架构升级 + 嵌入元素支持

---

## 🏠 社区

- 💬 [GitHub Discussions](https://github.com/aiworkskills/wechat-article-skills/discussions) — 使用问题、最佳实践
- 🐛 [Issues](https://github.com/aiworkskills/wechat-article-skills/issues) — Bug 反馈、功能建议
- 🌐 [aiworkskills.cn](https://aiworkskills.cn/) — 可视化配置台

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=aiworkskills/wechat-article-skills&type=Date)](https://star-history.com/#aiworkskills/wechat-article-skills&Date)

---

## License

[Apache License 2.0](LICENSE)
