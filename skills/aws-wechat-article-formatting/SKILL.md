---
name: aws-wechat-article-formatting
description: Applies preset layout rules to WeChat article content; reads preset from files and outputs formatted Markdown or HTML. Use when the user asks for "排版", "版式", "字号", "段落", "引导语", or styled article output.
---

# 排版规范

从**预设**直接读取排版规则后应用到正文，不在现场临时编规则。预设解析顺序：① 用户当次指定 ② 本 skill 或共享配置（.aws-article）中的默认预设 ③ 无则让用户选预设。

## 步骤

1. **确定预设**：按上述顺序得到预设名（用户指定 / 配置 default_format_preset / AskUserQuestion）。  
2. **读取预设**：从本项目约定的预设目录直接读取该预设文件（如 `references/presets/<preset>.md` 或 YAML/样式文件）。不在 SKILL 正文中写死具体字号、空行等规则。  
3. **应用**：对给定正文（writing 的产出或用户提供）按该预设的规则应用，生成排版结果。  
4. **输出**：按所选预设应用后的结果（Markdown 或 HTML，由实现定）；若输出为文件，可约定备份与下游所需信息。

## 预设目录与格式

- 预设存放在 `references/presets/`（或项目约定的其他路径）。  
- 每预设一份可被直接读取的文件：可为「描述该预设排版规则的 YAML + 片段」、样式/模板文件、或脚本可读的配置；格式由实现时决定。  
- 预设列表与适用场景可在 SKILL 或 references 中说明，供用户/配置选择。

## 配置

- 若使用共享配置：从 .aws-article 等约定路径读取默认预设名（如 default_format_preset），不写死别家路径或键名。
