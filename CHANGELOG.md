# 更新日志

本文档记录 wechat-article-skills 的版本变更历史。

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，日期采用 ISO 8601 格式（YYYY-MM-DD）。

---

## [2026-04-03] — 素材管理与预设包导入

### 新增

- **assets skill**：用户图片批量入库（自动生成元数据描述文件）
- `.aws` 预设包一键导入：将主题、风格、结构模板打包分享给其他账号
- 导入时自动合并到 `.aws-article/presets/`，已有 config 不覆盖而是输出差异

### 更新

- 同步更新 config 示例和各 skill 文档

---

## [2026-04-02] — 技能与脚本维护

### 修复

- 更新各 skill 指令细节
- 忽略本地 `config.yaml`，避免误提交
- 清理脚本兼容性问题

---

## [2026-03-31] — 脚本迁移与发布入口统一

### 变更

- 完成所有 Python 脚本从 `shared/` 到各 skill 目录的迁移
- 统一发布配置入口——`article_init.py` 迁入 publish skill
- 消除脚本散落在多处的问题

---

## [2026-03-20] — 多平台安装 + 配置校验

### 新增

- `install-skills.sh` 支持 OpenClaw / Cursor / Claude Code / Codex 四平台一键安装
- 新增 ClawHub manifests

### 更新

- 预设目录规范化
- 配置校验流程与发布、写作模块对齐
- 优化主技能与子技能的路由逻辑，减少误触发

---

## [2026-03-18] — 架构升级与体验优化

### 新增

- **sticker skill**（贴图 / 多图推送）
- 嵌入元素支持：公众号名片 + 小程序卡片 + 往期文章，排版时自动转为微信标签
- 6 种预设类型的 schema + 自动发现机制（放入目录即生效）

### 变更

- 统一三层文件架构：全局 `config.yaml` → 本篇 `article.yaml` → 对话中临时指定
- 提取共享层，消除 Skill 间重复逻辑
- 渐进式披露重构：精简 SKILL.md 只保留核心指令，详细说明移入 references
- 所有 skill 加入配置检查阻断，无 config 时必须先完成首次引导
- 优化全部 8 个 skill 的触发词，减少误触发

---

## [2026-03-17] — 发布能力完善

### 新增

- publish skill 的微信公众号 API 发布，凭证从 `config.yaml` 读取
- 支持自定义 API 转发地址，解决公众号固定 IP 白名单限制
- 多账号发布支持，发布时指定账号即可

### 变更

- 封面标记不进正文 HTML，封面通过 API 单独上传
- 图片上传前自动压缩（封面 ≤ 10 MB，正文 ≤ 1 MB）

---

## [2026-03-16] — 审稿 skill 重写

### 新增

- 写作规范联动检查
- 敏感词 / 错别字 / 配图完整性逐项扫描
- 结果分三级（🔴 必须改 / 🟡 建议改 / 🟢 通过），必改项触发修改循环
- 支持自定义审稿规则

---

## [2026-03-15] — 排版 skill 重写

### 新增

- `format.py` 实现 Markdown → 微信 HTML 转换
- 4 套内置主题（经典蓝 / 优雅紫 / 暖橙 / 极简黑）
- 支持用户自定义主题导入，YAML 文件放入目录即刻可用

### 变更

- 脚本不再硬编码主题，全部从 YAML 动态读取

---

## [2026-03-14] — 配图 skill 重写

### 新增

- 14 种视觉风格 × 6 种图片类型的 Type × Style 二维体系
- 写作阶段自动标记配图位置，配图时直接使用
- 信息图支持 10 种高级布局（九宫格、漏斗、冰山、金字塔、时间线等）
- 图片生成后端对接，优先专用图片模型

---

## [2026-03-13] — 写作 skill 重写

### 新增

- 接入 DeepSeek / GPT / Qwen / Gemini 等第三方模型
- 也支持当前 AI 直写（无需第三方模型）
- 支持用户自定义写作规范（`.aws-article/writing-spec.md`）

### 变更

- 简化配置为 `base_url` + `api_key` + `model` 三项，去掉 provider 概念
- 优先用专用写作 API，未配置则降级为当前模型并告知用户

---

## [2026-03-12] — 选题 skill 重写

### 新增

- 四种输入模式：有明确话题 / 有方向没话题 / 完全没方向 / 系列策划
- 调研驱动，搜索热点和竞品文章后再推荐选题

---

## [2026-03-01] — 项目优化

### 变更

- 优化 8 个 skill 基础框架
- 全面优化各 skill 的中文描述、OpenClaw 元数据
- 优化「一条龙模式」路由

---

[2026-04-03]: https://github.com/aiworkskills/wechat-article-skills/releases/tag/v1.0.13
[2026-04-02]: https://github.com/aiworkskills/wechat-article-skills/releases/tag/v1.0.12
