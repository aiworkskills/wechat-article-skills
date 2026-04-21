[简体中文](README.md) | **English**

# WeChat Article Skills

> **Open-source "digital employee" for WeChat Official Accounts.** Pick a style, say one sentence, and AI handles the full pipeline — topic research, writing, review, formatting, image generation, and publishing. **No design skills. No coding.**

[![License](https://img.shields.io/github/license/aiworkskills/wechat-article-skills)](LICENSE)
[![Stars](https://img.shields.io/github/stars/aiworkskills/wechat-article-skills?style=social)](https://github.com/aiworkskills/wechat-article-skills/stargazers)
[![Release](https://img.shields.io/github/v/release/aiworkskills/wechat-article-skills)](https://github.com/aiworkskills/wechat-article-skills/releases)
[![Platforms](https://img.shields.io/badge/platforms-13%2B%20Claw%20%7C%20Claude%20Code%20%7C%20Cursor%20%7C%20Codex-blue)](#supported-ecosystem)

![aiworkskills homepage](https://aiworkskills.cn/images/sp/aiworkskills%E9%A6%96%E9%A1%B5.png)

---

## 📚 Tutorials & Case Studies (Chinese)

- 📖 [How to use the aiworkskills platform — from config to publishing](https://mp.weixin.qq.com/s/rcnq_gg3XXRwJ7ovQtBo1A)
- 🔧 [Running a WeChat Official Account with WorkBuddy + AI Work Skills](https://mp.weixin.qq.com/s/GQjCY5UsArV9XI5AyoxWZQ)
- ⚡ [QClaw + aiworkskills: one-click WeChat operation](https://mp.weixin.qq.com/s/xLUJBc2bbrJvgeAesbhsFA)

---

## 🚀 Quick Start (No-Code)

Recommended path: use the visual config platform **[aiworkskills.cn](https://aiworkskills.cn/)** — fill in a form, export a preset, hand it to the AI.

```
① Install AI tool  →  ② Clone repo  →  ③ Fill config form  →  ④ Export .aws  →  ⑤ Say "write an article"
```

1. **Install an AI coding tool** — QClaw / WorkBuddy / Cursor / Claude Code, etc. (full list below)
2. **Clone this repo**
   ```bash
   git clone https://github.com/aiworkskills/wechat-article-skills.git
   ```
3. **Go to [aiworkskills.cn](https://aiworkskills.cn/)** and fill the form: Account → Strategy → Writing → Visual → Publishing (5 steps)
4. **Export the `.aws` preset bundle**, then tell the AI: "Import this preset for me"
5. **Start writing** — say to the AI: "Help me write a WeChat article" → full pipeline runs

---

## 🌐 Supported Ecosystem

### AI Coding Tools

![Platforms](https://aiworkskills.cn/images/sp/%E6%94%AF%E6%8C%81%E5%B9%B3%E5%8F%B0.png)

Built on the **OpenClaw standard**, compatible with 13+ Claw-series tools:

> QClaw · ArkClaw · JVSClaw · WorkBuddy · Linclaw · NemoClaw · AutoClaw · MaxClaw · KimiClaw · DuClaw · PowerClaw · ZeroClaw

Plus mainstream AI coding tools: **Claude Code · Cursor · Codex**.

### Language Models

> DeepSeek · Qwen · GLM · Kimi · Doubao · Wenxin · Spark · Hunyuan · MiniMax · Baichuan · Step · 01.AI · GPT · Claude

Works with any **OpenAI-compatible** API. API keys stored locally, never uploaded.

---

## ✨ 9 Skills, One Pipeline

| Skill | What it does | How to trigger |
|-------|--------------|----------------|
| **Orchestrator** | Chains everything together | "Help me write a WeChat article" |
| **Topics** | Research trends, recommend 3–5 topic cards | "Find me some topics" |
| **Writing** | Calls external LLM or writes directly, follows your spec | "Write an article on AI basics" |
| **Review** | Sensitive words, typos, spec compliance; 3-tier results | "Review this draft" |
| **Formatting** | Markdown → WeChat HTML, 4 built-in themes | "Format it" |
| **Images** | 14 visual styles × 6 image types | "Add images" |
| **Publishing** | WeChat API, multi-account, auto-compress | "Publish" |
| **Sticker** | Multi-image series flow | "Make a sticker post" |
| **Assets** | Stock image lib + `.aws` preset import/export | "Import this preset" |

Each step pauses for confirmation. You can interrupt, edit, or restart anytime.

---

## 📸 Visual Configuration

All config is done on [aiworkskills.cn](https://aiworkskills.cn/) — no code required.

<details>
<summary><b>Account & Target Reader</b> — tell the AI who you are and who you write for</summary>

![Account config](https://aiworkskills.cn/images/sp/%E8%B4%A6%E5%8F%B7%E4%B8%8E%E8%AF%BB%E8%80%85%E9%85%8D%E7%BD%AE.png)

</details>

<details>
<summary><b>Visual Presentation</b> — formatting themes + cover/inline image style presets</summary>

![Visual config](https://aiworkskills.cn/images/sp/%E8%A7%86%E8%A7%89%E5%91%88%E7%8E%B0%E9%85%8D%E7%BD%AE.png)

</details>

<details>
<summary><b>Formatting Themes</b> — 4 built-in themes (Classic Blue / Elegant Purple / Warm Orange / Minimal Black), plus custom YAML themes</summary>

![Formatting themes](https://aiworkskills.cn/images/sp/%E6%8E%92%E7%89%88%E9%A3%8E%E6%A0%BC%E9%A2%84%E8%AE%BE.png)

</details>

<details>
<summary><b>Image Styles</b> — 14+ visual styles across content types</summary>

![Image styles](https://aiworkskills.cn/images/sp/%E6%94%AF%E6%8C%81%E7%9A%84%E6%96%87%E7%AB%A0%E9%85%8D%E5%9B%BE%E9%A3%8E%E6%A0%BC.png)

</details>

<details>
<summary><b>Cover Styles</b> — multiple cover visual languages, mapped to content positioning</summary>

![Cover styles](https://aiworkskills.cn/images/sp/%E6%94%AF%E6%8C%81%E7%9A%84%E5%B0%81%E9%9D%A2%E9%85%8D%E5%9B%BE%E9%A3%8E%E6%A0%BC.png)

</details>

<details>
<summary><b>Publishing Settings</b> — WeChat API, sensitive-word list, footer embeds</summary>

![Publishing config](https://aiworkskills.cn/images/sp/%E5%8F%91%E5%B8%83%E9%85%8D%E7%BD%AE.png)

</details>

---

## 🛠️ Developer Path (Edit YAML Directly)

Prefer editing config files yourself? Skip the web platform:

```bash
git clone https://github.com/aiworkskills/wechat-article-skills.git
cd wechat-article-skills
bash scripts/install-skills.sh              # Install to .cursor / .claude
cp .aws-article/config.example.yaml .aws-article/config.yaml
# Edit config.yaml (account/style/formatting) and aws.env (API keys)
```

- Field reference: [first-time-setup.md](skills/aws-wechat-article-main/references/first-time-setup.md)
- Three-layer config: global `config.yaml` → per-article `article.yaml` → runtime dialog
- 6 preset extension points: `.aws-article/presets/{structures,closing-blocks,title-styles,formatting,cover-styles,sticker-styles}/`

---

## 📋 Changelog

Full history in [CHANGELOG.md](CHANGELOG.md). Recent highlights:

- **2026-04-03** · Added assets skill: image library + `.aws` preset import/export
- **2026-03-31** · Script migration & unified publishing entry
- **2026-03-20** · One-click install for 4 platforms + config validation
- **2026-03-18** · Three-layer architecture upgrade + embed element support

---

## 🏠 Community

- 💬 [GitHub Discussions](https://github.com/aiworkskills/wechat-article-skills/discussions) — usage questions, best practices
- 🐛 [Issues](https://github.com/aiworkskills/wechat-article-skills/issues) — bug reports, feature requests
- 🌐 [aiworkskills.cn](https://aiworkskills.cn/) — visual config platform

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=aiworkskills/wechat-article-skills&type=Date)](https://star-history.com/#aiworkskills/wechat-article-skills&Date)

---

## License

[Apache License 2.0](LICENSE)
