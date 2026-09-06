[简体中文](README.md) | **English**

# WeChat Article Skills

> **Open-source "digital employee" for WeChat Official Accounts.** Pick a style, say one sentence, and AI handles the full pipeline — topic research, writing, review, formatting, image generation, and publishing. **No design skills. No coding.**

[![License](https://img.shields.io/github/license/aiworkskills/wechat-article-skills)](LICENSE)
[![Stars](https://img.shields.io/github/stars/aiworkskills/wechat-article-skills?style=social)](https://github.com/aiworkskills/wechat-article-skills/stargazers)
[![Release](https://img.shields.io/github/v/release/aiworkskills/wechat-article-skills)](https://github.com/aiworkskills/wechat-article-skills/releases)
[![Platforms](https://img.shields.io/badge/platforms-13%2B%20Claw%20%7C%20Claude%20Code%20%7C%20Autohand%20Code%20%7C%20Cursor%20%7C%20Codex-blue)](#supported-ecosystem)

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

1. **Install an AI coding tool** — QClaw / WorkBuddy / Cursor / Claude Code / Autohand Code, etc. (full list below)
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

Plus mainstream AI coding tools: **Claude Code · Autohand Code · Cursor · Codex**.

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
| **Formatting** | Markdown → WeChat HTML, 7 built-in themes + 7 layout components | "Format it" |
| **Images** | 12 cover forms + 8 in-article forms, derived from the article | "Add images" |
| **Publishing** | WeChat API, multi-account, auto-compress, 2.35:1 cover crop | "Publish" |
| **Sticker** | Multi-image series flow | "Make a sticker post" |
| **Assets** | Product knowledge base (`products/{name}/`) + image lib + `.aws` preset import/export | "Import this preset" |

Each step pauses for confirmation. You can interrupt, edit, or restart anytime.

> **Product knowledge base**: before writing about your own product, the AI reads `.aws-article/products/{name}/` — intro docs and product screenshots you saved earlier get reused instead of regenerated.

> **Layout components**: a theme can only assign inline styles to tags — and WeChat article bodies have no pseudo-elements, so decorations like a numbered badge before a section title or the oversized quote mark on a pull quote have to be *real elements*. Components fill that gap, called with a `:::` block that leaves ordinary Markdown untouched. Seven ship built in (numbered section title, quote card, stat card, steps, compare, layers, checklist); their colors are read from the active theme, so any component works with any theme. Each carries `when_to_use` / `when_not_to_use` / `anti_pattern` so the agent can't reach for one just because it looks nice. **Images and components must not do the same job**: if the content has a spatial relationship (magnitude, flow, nesting) it's an image; if it's plain text in parallel, contrast, or a list, it's a component.

> **Images are derived, not templated**: covers go through a seven-step derivation (find the tension → pick the relation → find the metaphor → apply your visual language → lay out for 2.35:1 → write a prose brief → review), and each of the 12 cover forms carries its own title-text spec, so the output is a finished cover, not a background. For in-article images, the AI first asks "if this image were deleted, would the reader be lost or just bored?" — lost means the image must carry text copied verbatim from the article; bored means a pacing image with no text; neither means the slot gets dropped. One hand-drawn medium (whiteboard, grid notebook, sticky notes, chalkboard, kraft paper, terminal, annotated printout, flat vector) is picked per article — consistent within an article, rotated between articles.

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
<summary><b>Formatting Themes</b> — 16 themes in 5 families on the platform, shipped inside your <code>.aws</code>; 7 built into the skill as a fallback, plus custom YAML themes</summary>

![Formatting themes](https://aiworkskills.cn/images/sp/%E6%8E%92%E7%89%88%E9%A3%8E%E6%A0%BC%E9%A2%84%E8%AE%BE.png)

</details>

<details>
<summary><b>Image Styles</b> — presets set the visual language; what each image actually shows is derived from the content</summary>

![Image styles](https://aiworkskills.cn/images/sp/%E6%94%AF%E6%8C%81%E7%9A%84%E6%96%87%E7%AB%A0%E9%85%8D%E5%9B%BE%E9%A3%8E%E6%A0%BC.png)

</details>

<details>
<summary><b>Cover Styles</b> — pick a cover visual language; 12 cover forms turn it into a finished, titled cover</summary>

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
cp skills/aws-wechat-article-main/references/config.example.yaml .aws-article/config.yaml
cp skills/aws-wechat-article-main/references/env.example.yaml aws.env
# Edit config.yaml (account/style/models) and aws.env (API keys / WeChat credentials)
python3 skills/aws-wechat-article-main/scripts/validate_env.py
```

> On **Windows**, run `py -3 -X utf8 skills\aws-wechat-article-main\scripts\validate_env.py` instead — `python3` silently opens the Microsoft Store when Python isn't installed, and `-X utf8` keeps Chinese output from turning into mojibake.

- Requirements: Python 3.10+ and PyYAML; `Pillow` optional (image compression, cover cropping, cover crop boxes)
- Field reference: [first-time-setup.md](skills/aws-wechat-article-main/references/first-time-setup.md)
- Three-layer config: global `config.yaml` → per-article `article.yaml` → runtime dialog
- 7 preset extension points: `.aws-article/presets/{structures,closing-blocks,title-styles,formatting,cover-styles,image-styles,sticker-styles}/`

---

## 📋 Changelog

Full history in [CHANGELOG.md](CHANGELOG.md). Recent highlights:

- **2026-09-06** · **Layout component layer**: `:::` blocks for decorations a theme can't express (WeChat has no pseudo-elements); 7 built-in components, colors inherited from the active theme; images vs. components split by whether the content has a spatial relationship
- **2026-09-06** · Built-in themes up to 7 (added 克制 / 工程笔记 / 杂志); fixed all 16 platform themes rendering components in the fallback blue; captions now come only from an explicit markdown `title`
- **2026-09-05** · **Image system rebuilt**: covers derived through a seven-step method (12 cover forms with title-text specs); in-article images narrowed to 8 forms judged as "information" vs "pacing" slots; hand-drawn medium rotated between articles
- **2026-09-05** · Cover crop boxes on publish (`pic_crop_235_1` / `pic_crop_1_1`) — 2.35:1 feed image first, instead of letting WeChat center-crop the cover title away
- **2026-09-05** · Image script hardening: post-generation code-only check (`image_create.py check`), optional title compositing, structured aspect-ratio params, safer re-runs
- **2026-08-17** · Writing / image models are optional — unset models warn instead of blocking the pipeline
- **2026-06-16** · Writing guardrails against telltale AI phrasing
- **2026-06-01** · Review skill gained an "AI flavor" diagnostic dimension
- **2026-04-24** · `products/{name}/` knowledge base replaced the old assets layout (breaking)
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

[![Star History Chart](https://star-history.dera.page/svg?repos=aiworkskills/wechat-article-skills&type=Date)](https://star-history.dera.page/#aiworkskills/wechat-article-skills&Date)

---

## License

[Apache License 2.0](LICENSE)
